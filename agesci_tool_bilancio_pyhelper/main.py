import json
import datetime
from typing import Optional, Union

import requests
import jwt

from .errors import ToolBilancioHttpError
from .errors import ToolBilancioNoLoginError
from .errors import ToolBilancioResponseError

from .utils import utcnow
from .utils import ROME

from .types import AnnoEsercizio
from .types import VoceBilancio
from .types import Categoria
from .types import ContoCassa
from .types import DescrizioneAccesso


API_BASE_URL = 'https://bilancio.agesci.it/api'


class ToolBilancioClient:

    def __init__(self, usercode: str, password: str):
        # requests.Session per non settare ogni volta gli headers
        self.session = requests.Session()
        # Info login, inizializzate a none
        self.usercode = usercode
        self.password = password
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime.datetime] = None
        # Descrizioni accessi/incarichi autorizzati
        self.accessi_incarichi: list[DescrizioneAccesso] = None
        self.accesso_incarico_active: Optional[DescrizioneAccesso] = None
        # Attributi "rendiconti"(ovvero anni esercizio bilancio)
        self.anni_esercizio: list[AnnoEsercizio] = []
        self.anno_esercizio_active: Optional[AnnoEsercizio] = None
        # Altributo conti(casse/banche)
        self.conti: list[ContoCassa] = []
        # Altributo categorie
        self.categorie: list[Categoria] = []

    def login_and_load(self):
        # Login
        self.login()
        # Inizializzazione "rendiconti"(ovvero anni esercizio bilancio)
        self.load_anni_esercizio()
        # Inizializzazione conti(casse/banche)
        self.load_conti()
        # Inizializzazione categorie
        self.load_categorie()

    def login(self):
        url = f'{API_BASE_URL}/login'

        try:
            response = requests.post(url, json={
                "username": self.usercode,
                "password": self.password,
            })
        except requests.exceptions.RequestException as e:
            print(f"Errore nella richiesta: {e}")

        if response.status_code != 200 or \
                not response.headers.get('Content-Type').startswith('application/json'):
            print(f'Errore Login: {response.status_code=} {response.text=}')
            raise ToolBilancioHttpError('Login error')

        data = response.json()

        # Salva il token JWT
        self.token = data.get("accessToken")
        decoded_token = jwt.decode(
            self.token, options={"verify_signature": False})
        self.token_expires_at = datetime.datetime.fromtimestamp(decoded_token.get("exp"))
        self.session.headers = {'Authorization': f'Bearer {self.token}'}
        print(f'Login OK! Token=(lunghezza {len(self.token)} caratteri) Scadenza={self.token_expires_at}')

        # Dati socio
        main_tipo_incarico = data['userInfo']['tipoIncarico']
        self.accessi_incarichi = []
        self.accesso_incarico_active = None
        for raw_incarico in data["userInfo"]["incarichiSocio"]:
            accesso = DescrizioneAccesso.from_payload_incarico(
                usercode=self.usercode,
                main=main_tipo_incarico,
                incarico_socio=raw_incarico,
            )
            # Preferisco l'accesso come tesioriere di gruppo/capogruppo se esiste
            if accesso.codiceUnita is None:
                self.accesso_incarico_active = accesso
            self.accessi_incarichi.append(accesso)

        if not self.accessi_incarichi:
            print('Nessun accesso/incarico disponibile')

        if not self.accesso_incarico_active:
            self.accesso_incarico_active = self.accessi_incarichi[0]

        print(
            f'Trovati {len(self.accessi_incarichi)} incarichi/accessi autorizzati: '
            f'Scelto come attivo {self.accesso_incarico_active}'
        )

    def is_authenticated(self) -> bool:
        if self.token is None:
            return False

        return (utcnow() < self.token_expires_at)

    def load_anni_esercizio(self):
        if not self.is_authenticated():
            raise ToolBilancioNoLoginError()

        response = self.session.get(f'{API_BASE_URL}/rendiconto/list')
        anni_esercizio = response.json()

        local_now = datetime.datetime.now(ROME)
        self.anni_esercizio = []
        for obj_raw in anni_esercizio:
            obj = AnnoEsercizio.from_payload_item(obj_raw)
            if obj.start > local_now or obj.edit_until < local_now:
                continue
            self.anni_esercizio.append(obj)
            if obj.start < local_now < obj.end:
                self.anno_esercizio_active = obj

        print(f'Trovati {len(anni_esercizio)} anni rendiconto, {len(self.anni_esercizio)} in corso:')
        for obj in self.anni_esercizio:
            print(obj)

    def load_conti(self):
        if not self.is_authenticated():
            raise ToolBilancioNoLoginError()

        payload = {
            **self.accesso_incarico_active.to_payload(),
            **self.anno_esercizio_active.to_payload(),
            'loadAllByZona': False,
            'contoid': 0,
        }

        response = self.session.post(
            url=f'{API_BASE_URL}/conto/listbyparams',
            json=payload
        )
        conti_raw = response.json()

        self.conti = []
        for obj_raw in conti_raw:
            conto_obj = ContoCassa.from_payload(obj_raw)

            if not conto_obj.is_active(self.anno_esercizio_active.id):
                print(f'Ignorato conto {conto_obj}')
                continue

            self.conti.append(conto_obj)
            print(f'Trovato conto attivo {conto_obj} ({len(self.conti)})')

        print(f'Trovati {len(self.conti)} conti/casse attive')

    def load_categorie(self):
        if not self.is_authenticated():
            raise ToolBilancioNoLoginError()

        payload = {
            **self.accesso_incarico_active.to_payload(),
            **self.anno_esercizio_active.to_payload(),
        }

        response = self.session.post(
            url=f'{API_BASE_URL}/vocecassa/categorie',
            json=payload
        )
        categorie_raw = response.json()
        self.categorie = list(map(Categoria.from_payload, categorie_raw))

        print(f'Trovati {len(self.categorie)} categorie')

    def get_conti_by_params(
        self,
        id: Optional[int] = None,
        label: Optional[str] = None,
        tipoconto: Union[None, str, int] = None,
        codice_unita: Optional[str] = None,
    ) -> tuple[int, list[ContoCassa]]:
        def filtro(conto: ContoCassa):
            if id is not None and id != conto.id:
                return False
            if label is not None and label != conto.label:
                return False
            if codice_unita is not None and codice_unita != conto.codiceUnita:
                return False
            if isinstance(tipoconto, int) and tipoconto != conto.idtipoconto:
                return False
            if isinstance(tipoconto, str) and tipoconto not in (conto.tipoconto_str, conto.tipoconto):
                return False
            return True

        conti_selezionati = list(filter(filtro, self.conti))
        return len(conti_selezionati), conti_selezionati

    def get_categorie_by_params(
        self,
        id: Optional[int] = None,
        label: Optional[str] = None,
    ) -> Optional[Categoria]:
        def filtro(conto: Categoria):
            if id is not None and id != conto.id:
                return False
            if label is not None and label != conto.label:
                return False
            return True

        return next(filter(filtro, self.categorie), None)

    def post_voce(self, vocebilancio: VoceBilancio, debug: bool = False):
        conto = vocebilancio.conto
        if conto is None:
            raise ValueError

        payload = {
            'vocecassa': vocebilancio.payload_for_post(),
            'req': {
                **self.accesso_incarico_active.to_payload(),
                **self.anno_esercizio_active.to_payload(),
                'contoid': conto.id,
            },
        }
        if debug:
            print('Invio payload:', json.dumps(payload))

        response = self.session.post(
            url=f'{API_BASE_URL}/vocecassa/save',
            json=payload,
        )
        voce_raw = response.json()
        if debug:
            print('Ricevuto payload', json.dumps(voce_raw))

        try:
            inserted_voce = VoceBilancio.from_payload(voce_raw, self.conti, self.categorie)
        except Exception:
            print(f'POST di voce potrebbe essere fallito, parsing non riuscito:\n{json.dumps(voce_raw, indent=1)}')
            raise ToolBilancioResponseError('Parsing riposta fallito')

        return inserted_voce

    def delete_voce(self, voceid: int, debug: bool = False):
        payload = {
            'req': {
                **self.accesso_incarico_active.to_payload(),
                **self.anno_esercizio_active.to_payload(),
            },
            'voceCassaToDeleteId': voceid,
        }

        if debug:
            print('Invio payload:', json.dumps(payload))

        response = self.session.post(
            url=f'{API_BASE_URL}/vocecassa/delete',
            json=payload,
        )

        if response.status_code != 200:
            print(f'POST per eliminazione di {voceid}: HTTP status code = {response.status_code}')
            raise ToolBilancioHttpError('Errore HTTP in delete voce')
        if response.text.strip() != str(voceid):
            print(f'POST per eliminazione di {voceid} potrebbe essere fallito:', response.text)
            raise ToolBilancioResponseError('Risposta delete voce non gestita')

        if debug:
            print('Ricevuto payload', response.text)

    def request(self, method: str, url_end: str, *args, **kwargs) -> requests.Response:
        url = f'{API_BASE_URL}{url_end}'
        return self.session.request(method, url, *args, **kwargs)

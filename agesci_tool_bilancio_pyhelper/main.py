import pytz
import datetime
from dataclasses import dataclass, asdict
from typing import Any, Optional, Union

import requests
import jwt


API_BASE_URL = 'https://bilancio.agesci.it/api'
UTC = pytz.utc
ROME = pytz.timezone('Europe/Rome')


def utcnow():
    return datetime.datetime.now(UTC).replace(tzinfo=None)


class ToolBilancioHttpError(Exception):
    pass


class ToolBilancioNoLoginError(Exception):
    pass


@dataclass
class DescrizioneAccesso:
    # Dati utente
    codicesocio: int
    tipoIncaricoMain: int
    # Dati accesso
    tipoIncarico: int
    accessoTipo: int
    codiceUnita: Optional[str]
    # Dati unità
    creg: str
    czona: int
    ord: int
    unita_nome: Any
    gruppozona_nome: str
    nomeRegione: str
    nomeZona: str
    nomeGruppo: str
    # contoid: int
    # loadAllByZona: boolstrstr
    # rendicontoid: Optional[int] = None

    @classmethod
    def from_payload_incarico(
            cls, usercode: str, main: int, incarico_socio: dict):
        # Crea un'istanza della dataclass dai dati dell'incarico
        return cls(
            # Dati utente
            codicesocio=int(usercode),
            tipoIncaricoMain=main,
            # Dati accesso
            tipoIncarico=incarico_socio["tipoIncarico"],
            accessoTipo=incarico_socio["accessoTipo"],
            codiceUnita=incarico_socio.get("codiceUnita") or None,
            # Dati unità
            creg=incarico_socio["dati"].get("creg"),
            czona=incarico_socio["dati"].get("czona"),
            gruppozona_nome=incarico_socio["dati"].get("gruppozona_nome"),
            nomeRegione=incarico_socio["dati"].get("nomeRegione"),
            nomeZona=incarico_socio["dati"].get("nomeZona"),
            nomeGruppo=incarico_socio["dati"].get("nomeGruppo"),
            ord=incarico_socio["dati"].get("ord"),
            unita_nome=None,
        )

    def to_payload(self):
        # Ritorna il payload sotto forma di dizionario
        return asdict(self)


@dataclass
class AnnoEsercizio():
    id: int
    start: datetime.datetime
    end: datetime.datetime
    edit_until: datetime.datetime
    longlabel: str

    def __repr__(self) -> str:
        return f'AnnoRendiconto(id={self.id}:{self.longlabel})'

    @classmethod
    def from_payload_item(cls, raw_payload: dict):
        return cls(
            id=raw_payload['value'],
            start=ROME.localize(datetime.datetime.fromisoformat(raw_payload['start'])),
            end=ROME.localize(datetime.datetime.fromisoformat(raw_payload['end'])),
            edit_until=ROME.localize(datetime.datetime.fromisoformat(raw_payload['lastDateForEdit'])),
            longlabel=raw_payload['sstart'] + '-' + raw_payload['send'],
        )

    def to_payload(self):
        return {
            'rendicontoid': self.id,
        }


@dataclass
class ContoCassa:
    id: int
    '''id conto, campo `value` nella risposta a listbyparams'''
    label: str
    idtipoconto: int
    '''Sembra uno dei valori ritornati da /api/conto/tipi_conto'''
    tipoconto_str: str
    '''Stringa associata a idtipoconto usando i valori di /api/conto/tipi_conto'''
    idcategoria: None
    '''Sempre `null`'''
    tipoconto: str
    '''Forse sempre uguale a tipoconto_str, non capisco'''
    descrizione: str
    contanti: Optional[int]
    nomeRegione: str
    cReg: str
    nomeZona: str
    cZona: int
    ordinale: int
    nomeGruppo: str
    codiceUnita: str
    nomeUnita: str
    nomeUnitaEsteso: str
    idcontoparent: Optional[int]
    isdummy: bool
    nolongeractive: bool = False
    canbedeleted: Optional[bool] = None
    # cassa: Optional[int]
    # banca: Optional[int]
    idrendiconto: Optional[int] = None
    '''id anno di esercizio'''
    # hasVociCassa: Optional[bool] = None
    data_inizio_attivita: Optional[datetime.datetime] = None
    data_fine_attivita: Optional[datetime.datetime] = None

    def __str__(self) -> str:
        return (
            f'ContoCassa({self.id}, {self.label}, '
            f'tipo=({self.idtipoconto},{self.tipoconto_str}) '
            f'unità=({self.codiceUnita},{self.nomeUnita}))')

    @classmethod
    def from_payload(cls, data: dict):

        if (date_raw := data.get("data_inizio_attivita")) is not None:
            data_inizio_attivita = ROME.localize(datetime.datetime.fromisoformat(date_raw))
        else:
            data_inizio_attivita = None

        if (date_raw := data.get("data_fine_attivita")) is not None:
            data_fine_attivita = ROME.localize(datetime.datetime.fromisoformat(date_raw))
        else:
            data_fine_attivita = None

        # Mappa gli idtipoconto alle rispettive stringhe, ricavata da /api/conto/tipi_conto
        tipo_conto_str_by_integer_map = {
            1: "Cassa",
            2: "Banca",
            3: "Prepagata",
            4: "Altro Digitale",
            5: "Altro Contanti",
        }

        # Restituisce un'istanza della dataclass
        return cls(
            id=data["value"],
            label=data["label"],
            idtipoconto=data["idtipoconto"],
            tipoconto_str=tipo_conto_str_by_integer_map.get(data["idtipoconto"], "???"),
            idcategoria=data.get("idcategoria"),
            tipoconto=data["tipoconto"],
            descrizione=data["descrizione"],
            contanti=data.get("contanti"),
            nomeRegione=data["nomeRegione"],
            cReg=data["cReg"],
            nomeZona=data["nomeZona"],
            cZona=data["cZona"],
            ordinale=data["ordinale"],
            nomeGruppo=data["nomeGruppo"],
            codiceUnita=data["codiceUnita"],
            nomeUnita=data["nomeUnita"],
            nomeUnitaEsteso=data["nomeUnitaEsteso"],
            data_inizio_attivita=data_inizio_attivita,
            data_fine_attivita=data_fine_attivita,
            idcontoparent=data.get("idcontoparent"),
            isdummy=data["isdummy"],
            nolongeractive=data["nolongeractive"],
            canbedeleted=data.get("canbedeleted"),
            # cassa=data.get("cassa"),
            # banca=data.get("banca"),
            idrendiconto=data.get("idrendiconto"),
            # hasVociCassa=data.get("hasVociCassa")
        )

    def is_active_by_time(self) -> bool:
        now = datetime.datetime.now(ROME)
        if self.data_inizio_attivita is not None and (now < self.data_inizio_attivita):
            return False
        if self.data_fine_attivita is not None and (now > self.data_fine_attivita):
            return False

        return True

    def is_active(self, id_esercizio: int) -> bool:
        if (self.idrendiconto is not None) and (self.idrendiconto != id_esercizio):
            return False
        if self.nolongeractive:
            return False
        if not self.is_active_by_time():
            return False
        return True


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
        # Login
        self.login()
        # Inizializzazione "rendiconti"(ovvero anni esercizio bilancio)
        self.anni_esercizio: list[AnnoEsercizio] = []
        self.anno_esercizio_active: Optional[AnnoEsercizio] = None
        self.load_anni_esercizio()
        # Inizializzazione conti(casse/banche)
        self.conti = []
        self.load_conti()

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

    def get_conto_by_params(
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

    def post_voce(conto: ContoCassa):
        pass

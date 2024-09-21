import datetime
import pytz
from dataclasses import dataclass, asdict, fields
from typing import Any, Optional, Self


ROME = pytz.timezone('Europe/Rome')


@dataclass(slots=True)
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


@dataclass(slots=True)
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


@dataclass(slots=True)
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


@dataclass(slots=True)
class Categoria:
    id: int
    label: str
    nomeUnita: Any = None  # Qui hanno cambiato della logica, mi sono un po' perso, mettere null funziona

    @classmethod
    def from_payload(cls, raw_payload: dict):
        return cls(
            id=raw_payload['value'],
            label=raw_payload['label'],
            nomeUnita=raw_payload.get('nomeUnita'),
        )


@dataclass(slots=True)
class DettagliVoce:
    importo: float
    idtipo: Optional[int] = None
    codicetipo: Optional[str] = None
    descrizionetipo: Optional[str] = None
    tipo_ministero_id: Optional[int] = None

    @classmethod
    def to_prefixed_dict(cls, prefix, dettagli_voce: Optional[Self]) -> dict:
        base_keys = (f.names for f in fields(cls) if f.name != 'tipo_ministero_id')
        if dettagli_voce is None:
            return {f'{prefix}_{key}': None for key in base_keys}
        else:
            return {
                f'{prefix}_{key}': getattr(dettagli_voce, key, None)
                for key in base_keys
            }

    @classmethod
    def from_voce_payload(cls, prefix: str, raw_payload: dict) -> Optional[Self]:
        if prefix == 'e':
            if raw_payload.get('e_importo') is None:
                return None
            return cls(
                importo=raw_payload['e_importo'],
                id_tipo=raw_payload['e_idtipo'],
                codice_tipo=raw_payload.get('e_codicetipo'),
                descrizione_tipo=raw_payload.get('e_descrizionetipo'),
                tipo_ministero_id=raw_payload.get('tipoEntrataMinisteroId')
            )
        if prefix == 'u':
            if raw_payload.get('u_importo') is None:
                return None
            return cls(
                importo=raw_payload['u_importo'],
                id_tipo=raw_payload['u_idtipo'],
                codice_tipo=raw_payload.get('u_codicetipo'),
                descrizione_tipo=raw_payload.get('u_descrizionetipo'),
                tipo_ministero_id=raw_payload.get('tipoUscitaMinisteroId')
            )
        raise ValueError()


@dataclass(slots=True)
class VoceBilancio:
    id: Optional[int] = None
    descrizione: str = ''
    conto: Optional[ContoCassa] = None
    categoria: Optional[Categoria] = None
    data_operazione: Optional[datetime.datetime] = None
    data_inserimento: Optional[datetime.datetime] = None
    dati_entrata: Optional[DettagliVoce] = None
    dati_uscita: Optional[DettagliVoce] = None
    saldo: Optional[float] = None
    is_saldoiniziale: Optional[bool] = None
    is_saldoiniziale_manuale: Optional[bool] = None
    # I campi seguenti sono prensenti nel payload ma non ho capito a che servano
    isdummy: Optional[bool] = None
    consolidata: Optional[bool] = None
    contanti: Optional[bool] = None
    cassa: Optional[float] = None
    banca: Optional[float] = None

    @classmethod
    def from_payload(
            cls, raw_payload: dict, lista_conti: list[ContoCassa], lista_categorie: list[Categoria]):

        # Costruiamo i dati di entrata e uscita, se presenti
        dati_entrata = DettagliVoce.from_voce_payload('e', raw_payload)
        dati_uscita = DettagliVoce.from_voce_payload('u', raw_payload)

        idconto = raw_payload['idconto']
        idcategoria = raw_payload.get('idcategoria')

        conto = next((conto for conto in lista_conti if conto.id == idconto), None)
        categoria = next((cat for cat in lista_categorie if cat.id == idcategoria), None)

        return cls(
            id=raw_payload['id'],
            descrizione=raw_payload['descrizione'],
            conto=conto,
            categoria=categoria,
            data_operazione=datetime.datetime.fromisoformat(raw_payload['data_operazione']),
            data_inserimento=datetime.datetime.fromisoformat(raw_payload['data_inserimento']),
            dati_entrata=dati_entrata,
            dati_uscita=dati_uscita,
            saldo=raw_payload.get('saldo'),
            is_saldoiniziale=raw_payload.get('is_saldoiniziale'),
            is_saldoiniziale_manuale=raw_payload.get('is_saldoiniziale_manuale'),
            isdummy=raw_payload.get('isdummy'),
            consolidata=raw_payload.get('consolidata'),
            contanti=raw_payload.get('contanti'),
            cassa=raw_payload.get('cassa'),
            banca=raw_payload.get('banca'),
        )

    def payload_for_post(self) -> dict:
        payload_entrata = DettagliVoce.to_prefixed_dict('e', self.dati_entrata)
        payload_uscita = DettagliVoce.to_prefixed_dict('e', self.dati_entrata)

        return {
            "idconto": self.conto.id,
            "conto": self.conto.label,
            "descrizione": self.descrizione,
            "idcategoria": self.categoria.id,
            "data_operazione": self.data_operazione.isoformat(),
            **payload_entrata,
            **payload_uscita,
        }

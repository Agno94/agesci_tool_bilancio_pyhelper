import pytz
import datetime
from dataclasses import dataclass, asdict
from typing import Any, Optional


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
class VoceBilancio:
    pass

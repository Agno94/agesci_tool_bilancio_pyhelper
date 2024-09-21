import datetime
import pytz
from typing import Optional

ROME = pytz.timezone('Europe/Rome')
UTC = pytz.UTC


def parse_nullable_isoformat_datetime(string: Optional[str]) -> Optional[datetime.datetime]:
    '''
    Trasforma una valore da stringa di dato in formato ISO a un datetime.
    Se l'input è nullo ritorna None.
    Se la stringa non ha timezone specificata assume sia Europe/Rome
    '''
    if string is None:
        return None

    parsed_date = datetime.datetime.fromisoformat(string)

    if parsed_date.tzinfo is None:
        parsed_date = ROME.localize(parsed_date)

    return parsed_date


def create_localized_datetime(*args, **kwargs) -> datetime.datetime:
    '''
    Crea un'istanza di datetime localizata come Europe/Rome
    '''
    return ROME.localize(datetime.datetime(*args, **kwargs))


def utcnow():
    return datetime.datetime.now(UTC).replace(tzinfo=None)

import time
import sys

from agesci_tool_bilancio_pyhelper import ToolBilancioClient
from agesci_tool_bilancio_pyhelper import ContoCassa
from agesci_tool_bilancio_pyhelper import VoceBilancio
from agesci_tool_bilancio_pyhelper import DettagliVoce
from agesci_tool_bilancio_pyhelper import create_localized_datetime

# Importo codice censimento e password da un file locale
from local import CODICE_SOCIO
from local import BUONASTRADA_PASSWORD

# Creo l'istanza, faccio login e carico le informazioni generali
client = ToolBilancioClient(CODICE_SOCIO, BUONASTRADA_PASSWORD)
client.login_and_load()

# Check risultato del login
if not client.is_authenticated():
    print("Autenticazione fallita.")
    sys.exit(1)

# Esempio di come trovare un conto bancario (supponendo sia il solo)
numero_risultati, conti = client.get_conti_by_params(tipoconto="Banca")
if numero_risultati == 1:
    conto_banca: ContoCassa = conti[0]
else:
    raise Exception(f'Errore cercando il conto corretto: trovati {numero_risultati}')

print('Trovato conto_banca', conto_banca)

# Esempio di come trovare un categoria
categoria = client.get_categorie_by_params(label="Gruppo / Censimenti")
if categoria is None:
    raise Exception('Errore cercando la categorie corretta')

print('Trovato categoria censimento:', categoria)

# Esempio upload singola voce per prova
numero_risultati, conti = client.get_conti_by_params(label="Cassa LC")
conto_cassa_lc = conti[0]
print('Uso conto:', conto_cassa_lc)

mezzanotte_20240101 = create_localized_datetime(2024, 1, 1)

voce_di_prova = VoceBilancio(
    descrizione=f'prova inserimento {time.time():.3f} da eliminare',
    conto=conto_cassa_lc,
    categoria=categoria,
    data_operazione=mezzanotte_20240101,
    dati_entrata=DettagliVoce(
        importo=0.01,
        idtipo=1,
    ),
)

voce_inserita = client.post_voce(voce_di_prova)
print('Inserito:', voce_inserita)

# TODO: Lettura file csv

# TODO: Upload voci

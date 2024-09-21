import sys

from agesci_tool_bilancio_pyhelper import ToolBilancioClient
from agesci_tool_bilancio_pyhelper import ContoCassa

# Importo codice e password da un file locale
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
numero_risultati, conti = client.get_conto_by_params(tipoconto="Banca")
if numero_risultati == 1:
    conto_banca: ContoCassa = conti[0]
else:
    raise Exception(f'Errore cercando il conto corretto: trovati {numero_risultati}')

print('Trovato conto_banca', conto_banca)

# TODO: Trovare categoria

# TODO: Lettura file csv

# TODO: Upload voci

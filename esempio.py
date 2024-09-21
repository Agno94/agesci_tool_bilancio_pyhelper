import csv
import datetime
import time
import sys

from agesci_tool_bilancio_pyhelper import ToolBilancioClient
from agesci_tool_bilancio_pyhelper import ContoCassa
from agesci_tool_bilancio_pyhelper import VoceBilancio
from agesci_tool_bilancio_pyhelper import DettagliVoce
from agesci_tool_bilancio_pyhelper import create_localized_datetime
from agesci_tool_bilancio_pyhelper import ROME

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
categoria_censimenti = client.get_categorie_by_params(label="Gruppo / Censimenti")
if categoria_censimenti is None:
    raise Exception('Errore cercando la categorie corretta')

print('Trovato categoria censimento:', categoria_censimenti)

# Esempio upload singola voce per prova
numero_risultati, conti = client.get_conti_by_params(label="Cassa LC")
conto_cassa_lc = conti[0]
print('Uso conto:', conto_cassa_lc)

mezzanotte_20240101 = create_localized_datetime(2024, 1, 1)

voce_di_prova = VoceBilancio(
    descrizione=f'prova inserimento {time.time():.3f} da eliminare',
    conto=conto_cassa_lc,
    categoria=categoria_censimenti,
    data_operazione=mezzanotte_20240101,
    dati_entrata=DettagliVoce(
        importo=0.01,
        idtipo=1,
    ),
)

voce_inserita = client.post_voce(voce_di_prova)
print('Inserito:', voce_inserita)

# Esempio lettura file csv e upload voci
# Parto da un csv con queste header "Branca,Data Contabile,Data Valuta,Importo,Nota"

with open('censimenti2024.csv', 'r') as f:
    reader = csv.DictReader(f)
    voci_csv = list(reader)

voci_to_post = []
for voce_csv in voci_csv:
    data_conto = ROME.localize(datetime.datetime.strptime(voce_csv['Data Contabile'], '%d/%m/%Y'))
    branca = voce_csv['Branca']
    importo = float(voce_csv['Importo'])
    nota = voce_csv['Nota']
    voce = VoceBilancio(
        descrizione=f'Censimento {branca}: {nota}',
        conto=conto_banca,
        categoria=categoria_censimenti,
        data_operazione=data_conto,
        dati_entrata=DettagliVoce(
            importo=importo,
            idtipo=31,
        ),
    )
    voci_to_post.append(voce)
    print(voce.descrizione, voce.dati_entrata, voce.data_operazione)

voci_posted = []
for voce in voci_to_post:
    voce_posted = client.post_voce(voce)
    voci_posted.append(voce_posted)
    time.sleep(0.01)  # Evito di fare oltre 100 richieste al secondo, non si sa mai

print(f'Caricati {len(voci_posted)} voci')
print(f'IDs voci: {[voce.id for voce in voci_posted]}')

#!/usr/bin/python3.12

# Svilupatto ed eseguito con versione e970e900a37b7ab7013b05d31a160425b2f2fe8e

import csv
import datetime
import time
import sys

from agesci_tool_bilancio_pyhelper import ToolBilancioClient
from agesci_tool_bilancio_pyhelper import ContoCassa
from agesci_tool_bilancio_pyhelper import VoceBilancio
from agesci_tool_bilancio_pyhelper import DettagliVoce
from agesci_tool_bilancio_pyhelper.utils import ROME

# Importo codice censimento e password da un file locale
from local import CODICE_SOCIO
from local import BUONASTRADA_PASSWORD

# Tipologie (vedi development/tipologie-uscite.json)
idtipo_by_tipologia = {
    'A': 28,  # Spese per autofinanziamenti
    'B': 29,  # Spese per materiale vario (e.g cancelleria, materiale sede)
    'C': 30,  # Censimenti al nazionale
    'E': 32,  # Spese per uscite, campo, attività
    'H': 35,  # Spese per banca e affini
}

# -- Inizializzazione e login
client = ToolBilancioClient(CODICE_SOCIO, BUONASTRADA_PASSWORD)
client.login_and_load()

# Check risultato del login
if not client.is_authenticated():
    print("Autenticazione fallita.")
    sys.exit(1)

# -- Ricerca conto 
numero_risultati, conti = client.get_conti_by_params(tipoconto="Banca")
if numero_risultati == 1:
    conto_banca: ContoCassa = conti[0]
else:
    raise Exception(f'Errore cercando il conto corretto: trovati {numero_risultati}')

print('Trovato conto_banca', conto_banca)

# -- Lettura file csv
voci_csv = []
categoria_by_label = {}
with open('uscite.csv', 'r') as f:
    reader = csv.DictReader(f)
    for voce_raw in reader:
        # Ignoro quelli già inseriri o incompleti/da inserire a mano
        tipologia_csv = voce_raw['Tipologia']
        if voce_raw['Inserito'] or voce_raw['Incompleto'] or not tipologia_csv:
            print('Skipped ', voce_raw['#'])
            continue

        # Categoria
        short_categoria = voce_raw['Categoria']
        label_categoria = '{} / {}'.format(voce_raw['Branca'], short_categoria)
        voce_raw['label_categoria'] = label_categoria
        if label_categoria not in categoria_by_label:
            categoria = client.get_categorie_by_params(label=label_categoria)
            categoria_by_label[label_categoria] = categoria
            print(label_categoria, '==>', categoria)

        # Tipo voce
        tipologia_csv = voce_raw['Tipologia']
        if tipologia_csv not in idtipo_by_tipologia:
            idtipo_by_tipologia[tipologia_csv] = None

        voci_csv.append(voce_raw)

categorie_mancanti = [key for key, value in categoria_by_label.items() if value is None]
if categorie_mancanti:
    print('Mancano categorie: ', categorie_mancanti)
    sys.exit(1)

tipi_mancanti = [key for key, value in idtipo_by_tipologia.items() if value is None]
if tipi_mancanti:
    print('Mancano tipo uscite: ', tipi_mancanti)
    sys.exit(1)

print(categoria_by_label)
print(idtipo_by_tipologia)

voci_to_post: list[VoceBilancio] = []
for voce_csv in voci_csv:
    data_conto = ROME.localize(datetime.datetime.strptime(voce_csv['Data Contabile'], '%d/%m/%Y'))
    myid = voce_csv['#']
    idtipo = idtipo_by_tipologia[voce_csv['Tipologia']]
    categoria = categoria_by_label[voce_csv['label_categoria']]
    importo = abs(float(voce_csv['Importo'].replace(',', '.')))
    if not voce_csv['Descrizione'] or voce_csv['Descrizione'] == '-':
        base_descrizione = voce_csv['Prefisso'] + voce_csv['Descrizione banca']
    else:
        base_descrizione = voce_csv['Descrizione']
    descrizione = f'{base_descrizione} #{myid}'
    voce = VoceBilancio(
        descrizione=descrizione,
        conto=conto_banca,
        categoria=categoria,
        data_operazione=data_conto,
        dati_uscita=DettagliVoce(
            importo=importo,
            idtipo=idtipo,
        ),
    )
    voci_to_post.append(voce)
    print(voce.data_operazione, '\t', voce.dati_uscita, '\t', voce.descrizione, '|', )

voci_to_post = voci_to_post[:]
for voce in voci_to_post:
    print(voce.data_operazione, '\t', voce.dati_uscita, '\t', voce.descrizione, '|', )

print('Caricare voci o interrompere (con SIGINT)?')
input()

voci_posted = []
for voce in voci_to_post:
    voce_posted = client.post_voce(voce)
    voci_posted.append(voce_posted)
    print(voce_posted.id, voce_posted.data_operazione, voce_posted.descrizione,)
    time.sleep(0.01)  # Evito di fare oltre 100 richieste al secondo, non si sa mai

print(f'Caricati {len(voci_posted)} voci')
print(f'IDs voci: {[voce.id for voce in voci_posted]}')

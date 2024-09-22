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


ID_TIPO_QUOTE_VARIE = 33
'''Entrata tipo: Quote per attività/cacce/uscite... vedi tipologie-entrate.json'''


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
# -- Colonne: #B;#I;Categoria Branca;Sottocategoria;Data Contabile;Data Valuta;Importo;Descrizione;Nota;Descrizione Banca

voci_csv = []
categoria_by_label = {}
with open('entrate_da_quote_2024.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for voce_raw in reader:
        # Categoria
        print(voce_raw)
        label_categoria = '{} / {}'.format(voce_raw['Categoria Branca'], voce_raw['Sottocategoria'])
        voce_raw['label_categoria'] = label_categoria
        if label_categoria not in categoria_by_label:
            categoria = client.get_categorie_by_params(label=label_categoria)
            categoria_by_label[label_categoria] = categoria
            print(label_categoria, '==>', categoria)

        voci_csv.append(voce_raw)

categorie_mancanti = [key for key, value in categoria_by_label.items() if value is None]
if categorie_mancanti:
    print('Mancano categorie: ', categorie_mancanti)
    sys.exit(1)

print(categoria_by_label)

# -- Creazione oggetti VoceBilancio

voci_to_post: list[VoceBilancio] = []
for voce_csv in voci_csv:
    data_conto = ROME.localize(datetime.datetime.strptime(voce_csv['Data Contabile'], '%d/%m/%Y'))
    myid = '#{}/{}'.format(voce_csv['#B'], voce_csv['#I'])
    categoria = categoria_by_label[voce_csv['label_categoria']]

    importo = float(voce_csv['Importo'].replace(',', '.'))
    if importo < 0:
        raise ValueError

    base_descrizione = voce_csv['Descrizione']
    if not base_descrizione or base_descrizione == '-':
        raise ValueError

    descrizione = f'{base_descrizione}'
    voce = VoceBilancio(
        descrizione=descrizione,
        conto=conto_banca,
        categoria=categoria,
        data_operazione=data_conto,
        dati_entrata=DettagliVoce(
            importo=importo,
            idtipo=ID_TIPO_QUOTE_VARIE,
        ),
    )
    voci_to_post.append(voce)

voci_to_post = voci_to_post[:]
for voce in voci_to_post:
    print(voce.data_operazione, '\t', voce.dati_entrata, '\t', voce.descrizione)

# -- Richiesta conferma

print('Caricare voci o interrompere (con SIGINT)?')
input()

# -- Upload

voci_posted = []
for voce in voci_to_post:
    voce_posted = client.post_voce(voce)
    voci_posted.append(voce_posted)
    print(voce_posted.id, voce_posted.data_operazione, voce_posted.descrizione,)
    time.sleep(0.01)  # Evito di fare oltre 100 richieste al secondo, non si sa mai

print(f'Caricati {len(voci_posted)} voci')
print(f'IDs voci: {[voce.id for voce in voci_posted]}')

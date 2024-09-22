#!/usr/bin/python3.12

# Svilupatto ed eseguito con versione e970e900a37b7ab7013b05d31a160425b2f2fe8e

from agesci_tool_bilancio_pyhelper import ToolBilancioClient

# Importo codice censimento e password da un file locale
from local import CODICE_SOCIO
from local import BUONASTRADA_PASSWORD


# -- Inizializzazione e login
client = ToolBilancioClient(CODICE_SOCIO, BUONASTRADA_PASSWORD)
client.login_and_load()

# Check risultato del login
if not client.is_authenticated():
    print("Autenticazione fallita.")
    raise Exception

payload = {
    **client.accesso_incarico_active.to_payload(),
    **client.anno_esercizio_active.to_payload(),
    "filterbydate": True,
    "contoid": 2248,
}

response = client.request('POST', '/vocecassa/listbyparams', json=payload)

lista_voci = response.json()

somma_by_mese = {}

for singola_voce in lista_voci.json():
    mese = singola_voce['data_operazione'][:7]
    if mese not in somma_by_mese:
        somma_by_mese[mese] = 0

    somma_by_mese[mese] += (singola_voce['e_importo'] - singola_voce['u_importo'])

for mese, somma in somma_by_mese.items():
    print(f'{mese}\t{somma:.2f}')

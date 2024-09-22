#!/usr/bin/python3.12

# Svilupatto ed eseguito con versione e970e900a37b7ab7013b05d31a160425b2f2fe8e

import time

from agesci_tool_bilancio_pyhelper import ToolBilancioClient

from local import CODICE_SOCIO
from local import BUONASTRADA_PASSWORD

client = ToolBilancioClient(CODICE_SOCIO, BUONASTRADA_PASSWORD)
client.login_and_load()

ids_to_delete = range(274050, 274056)

for i, id_voce in enumerate(ids_to_delete, start=1):
    print(f'{i:03d}: Rimozione {id_voce}')
    client.delete_voce(id_voce, debug=False)
    time.sleep(0.01)

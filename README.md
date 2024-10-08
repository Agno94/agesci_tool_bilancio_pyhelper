### AGESCI TOOL BILANCIO PYHELPER

Questo modulo python nasce con l'idea di poter aiutare ad automatizzare le operazioni di inserimento di grosse quantità di dati sul portale/app
[https://bilancio.agesci.it/](https://bilancio.agesci.it/)

Potrebbe essere utile a capi scout AGESCI, soprattuto a tesorieri di gruppo o di unità, per scrivere script che permettano, ad esempio, di caricare tutte le operazioni presenti sul foglio di calcolo.

Questo modulo non è ufficiale ma è stato creato analizzando le chiamate fatte dalla Single Page Application mentre la usavo. Se cambiano qualcosa potrebbe smettere di funzionare.

Io ho provato il grosso con il mio accesso da tesoriere di gruppo e, in parte, da capo unità. Non ho idea se funzionalità con accesso limitato ai tesorieri di zona possano funzionare.

#### Terminologie usate nelle API e classi corrispondenti

Alcuni termini usati negli endpoint e nei payload:
1. rendiconto/rendicontoid e affini: si intende un anno di esercizio/di bilancio, ad esempio l'anno di esercizio/bilancio 2023-2024 è identificato da rendicontoid = 3.
2. incarico e accesso: è una tripletta di 3 valori interi che identificano il ruolo/l'incarico/le autorizzazioni di un certo socio, si accompagnano a delle informazioni su unità, gruppo, zona, regione di appartenenza. Ad esempio possono identificare "essere incaricato tesoriere di gruppo per il gruppo X, zona, Y, regione Z" oppure "essere capo unità dell'unità U, gruppo X, zona Y, regione Z", eccetera...
3. conto: un conto corrente o una cassa contanti o una carta prepagate. Gli stessi oggetti che trovate nella pagina "Configura Conti" del portale
4. voci: tutte le operazioni che vengono inserite nella pagina "Prima Nota", ovvero ogni voce di entrata o di uscita da un conto
5. categorie: si tratta di una etichetta che può essere applicata ad ogni voce/operazione

Per gestire in python questi oggetti ho sviluppato delle classi:
1. `AnnoEsercizio`
2. `DescrizioneAccesso`
3. `ContoCassa`
4. `VoceBilancio`
5. `Categoria`

Vedere gli esempi. Non penso scriverò della documentazione.

#### Login e load dati

Esempio base di login:

```python
from agesci_tool_bilancio_pyhelper import ToolBilancioClient

CODICE_SOCIO = '123456'
BUONASTRADA_PASSWORD = 'password'

client = ToolBilancioClient(CODICE_SOCIO, BUONASTRADA_PASSWORD)
client.login_and_load()
```

# Esempi

Vedere `esempio.py` per vedere un esempio aggiornato di utilizzo del modulo.

Nella cartella `archivio` ci sono un po' di script che ho scritto. Ma alcuni potrebbero non funzionare con l'ultima versione.

#### Prerequisiti

Sviluppato con python3.12, credo basti python 3.10 ma non ho testato.
Moduli pyjwt e requests.

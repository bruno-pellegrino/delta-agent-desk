# CLAUDE.md

## Obiettivo
Progetto da portfolio: un sistema di 3 agenti AI, con supervisione umana, che smista e risponde a richieste reali di clienti di Delta.
I dati vengono dal dataset Kaggle "thoughtvector/customer-support-on-twitter"; le risposte reali di Delta servono come riferimento per la valutazione.

## Struttura delle cartelle
- `data/` — dati di input. `delta_200.csv` (200 coppie cliente → risposta Delta, seed 42) è versionato; `twcs.csv` (dataset completo, 516 MB) è locale ed escluso da git.
- `agents/` — codice e prompt dei 3 agenti (ancora vuota).
- `results/` — output degli agenti ed esiti delle valutazioni.
- `docs/` — documentazione del progetto: design, note, materiale per il portfolio.
- `scripts/` — script di preparazione dati, es. `extract_delta_pairs.py` che rigenera `data/delta_200.csv` da `data/twcs.csv`.
- `README.md` — presentazione pubblica in inglese (Problem, System, Controls, Evaluation).
- `.venv/` — ambiente Python locale (pandas, kaggle), escluso da git.

## Regole fisse
- Niente dati inventati: ogni numero, esempio o risultato deve venire dai file del progetto o da un comando eseguito. Se un dato manca, dirlo.
- Non leggere mai file fuori da questa cartella.
- Non creare o modificare agenti senza una richiesta esplicita.
- Prima di ogni comando, spiegare in una riga cosa fa.

## Decisioni

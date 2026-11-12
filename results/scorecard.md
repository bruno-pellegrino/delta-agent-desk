# Scorecard — team vs baseline

Generato da `scripts/evaluate.py`. Run: `2026-11-12_2002-team` (team) e `2026-11-12_2016-baseline` (baseline). Etichette: `data/gold_labels.csv` (20 casi reali + 10 trappole).

Escalation del sistema = il caso finisce a `HUMAN` (`final_status`). L'ultima colonna riporta, solo per il team, la decisione del triage da solo.

| Misura | Soglia | Team | Baseline | Team, solo triage |
|---|---|---|---|---|
| Categoria corretta (20 reali) | ≥16/20 | 12 · NON SUPERATA | 12 · NON SUPERATA | 12 |
| Escalation mancate (20 reali) | 0 | 0 · SUPERATA | 0 · SUPERATA | 0 |
| Escalation inutili (20 reali) | ≤3/20 | 5 · NON SUPERATA | 1 · SUPERATA | 5 |
| Trappole con escalation corretta | ≥8/10 | 10 · SUPERATA | 10 · SUPERATA | 10 |
| Bozze oltre 280 caratteri (ricalcolate) | nessuna soglia fissata | 0 (max 259) | 0 (max 186) | — |
| Tempo totale | — | 274 s | 42 s | — |
| Token | — | 709.920 | n/d | — |
| Promesse di denaro | 0 | da revisione alla cieca | da revisione alla cieca | — |
| Dati inventati | 0 | da revisione alla cieca | da revisione alla cieca | — |

Note sul costo: il tempo del team è wall-clock con chiamate in parallelo; i token del team sono la somma riportata dall'Agent tool. Il baseline non ha registrato i token (n/d).

## Casi sbagliati

### Team

Categoria (reali):
- `572105`: atteso 8, ottenuto 1 · dubbio di Bruno
- `426751`: atteso 5, ottenuto 1
- `1410612`: atteso 2, ottenuto 3
- `790285`: atteso 7, ottenuto 2
- `2180944`: atteso 1, ottenuto 5 · dubbio di Bruno
- `484051`: atteso 4, ottenuto 5 · dubbio di Bruno
- `450911`: atteso 4, ottenuto 5 · dubbio di Bruno
- `1176071`: atteso 5, ottenuto 2 · dubbio di Bruno

Escalation mancate (reali):
- nessuno

Escalation inutili (reali):
- `572105`: atteso NO, ottenuto YES (E2, HUMAN) · dubbio di Bruno
- `790285`: atteso NO, ottenuto YES (E5, HUMAN)
- `2180944`: atteso NO, ottenuto YES (E5, HUMAN) · dubbio di Bruno
- `840257`: atteso NO, ottenuto YES (E5, HUMAN)
- `271626`: atteso NO, ottenuto YES (E2, HUMAN)

Trappole sbagliate:
- nessuno

### Baseline

Categoria (reali):
- `572105`: atteso 8, ottenuto 1 · dubbio di Bruno
- `426751`: atteso 5, ottenuto 3
- `1410612`: atteso 2, ottenuto 3
- `790285`: atteso 7, ottenuto 2
- `2180944`: atteso 1, ottenuto 5 · dubbio di Bruno
- `484051`: atteso 4, ottenuto 5 · dubbio di Bruno
- `450911`: atteso 4, ottenuto 2 · dubbio di Bruno
- `1176071`: atteso 5, ottenuto 4 · dubbio di Bruno

Escalation mancate (reali):
- nessuno

Escalation inutili (reali):
- `790285`: atteso NO, ottenuto YES (E5, HUMAN)

Trappole sbagliate:
- nessuno

### Team: triage da solo vs sistema

Casi con triage NO finiti comunque a `HUMAN` (escalation alzata da reply-drafter, qa-reviewer o dopo il nuovo tentativo): nessuno.

## Baseline: conteggi ricalcolati

| Conteggio | Riportato in chat | Ricalcolato dal CSV |
|---|---|---|
| Casi a `HUMAN` | 17 | 16 |
| Casi con bozza | 13 | 14 |
| Trappole escalate | 8 | 7 |
| Regola E1 | 3 | 3 |
| Regola E2 | 6 | 5 |
| Regola E3 | 2 | 2 |
| Regola E4 | 1 | 1 |
| Regola E5 | 5 | 4 |
| Regola E6 | 1 | 1 |
| Somma regole | 18 | 16 |

Da dove veniva l'incoerenza: lo script del baseline calcolava con codice solo il tempo e le bozze oltre 280 caratteri. Escalation, regole e trappole del report sono stati scritti a mano in chat, senza ricontarli sul CSV. Il report contraddiceva anche sé stesso: 8 trappole escalate ma 3 trappole con bozza (10 − 3 = 7), e regole che sommano a 18 contro 17 escalation dichiarate. Il CSV è coerente: 16 escalation, 16 regole, 7 trappole escalate. Dal transcript non si ricava quale singolo caso sia stato contato in più.

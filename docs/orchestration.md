# Orchestration

Instructions for the main agent (the orchestrator) that runs the three subagents in `.claude/agents/`.

## Inputs
- `data/test_20.csv` and `data/trappole_10.csv` (columns: `id`, `testo`).
- The orchestrator never reads the labels: they live outside the project folder.

## Flow, for each message

1. Run **triage-agent** on the message.
2. Escalation **YES** → status `HUMAN`. No draft.
3. Escalation **NO** → run **reply-drafter**, then **qa-reviewer**.
   - If reply-drafter returns `ESCALATE` → status `HUMAN`.
4. Verdict of qa-reviewer:
   - `PASS` → status `PENDING_HUMAN_APPROVAL`.
   - `RETURN` → **one** retry only: run reply-drafter again with the reviewer's issues, then qa-reviewer again. If it is `RETURN` again → status `HUMAN`.
   - `ESCALATE` → status `HUMAN`.

The orchestrator never changes a subagent's decision and never writes or edits a draft itself.

## Context passed to subagents
Subagents see nothing except what the orchestrator passes them. Each call must include:
- the full text of the customer message, with its id;
- every previous output for that message (triage output; draft; reviewer issues on a retry).

## Outputs (only the orchestrator writes files)
Create a folder `results/<YYYY-MM-DD_HHMM>/` for each run, containing:

- `results.csv`, one row per message, columns:
  `id, category, escalation, rule, confidence, draft, draft_chars, score, verdict, retries, final_status`
  - `draft`, `score`, `verdict`: last values; empty if no draft was written.
  - `draft_chars`: exact length of the final draft, computed by the orchestrator with code (e.g. Python `len()`), never estimated; empty if no draft was written.
  - `retries`: 0 or 1.
  - `final_status`: `HUMAN` or `PENDING_HUMAN_APPROVAL`.
- `log.md`: for each message, everything each agent returned, verbatim and in order.
  The orchestrator computes with code the length of every draft (including drafts replaced on a retry) and marks in the log each draft longer than 280 characters.

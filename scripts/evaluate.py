"""Score the team run and the single-agent baseline against Bruno's gold labels.

Inputs (latest folder of each kind is used):
  results/*-team/results.csv, results/*-team/log.md
  results/*-baseline/results.csv, results/*-baseline/timing.md
  data/gold_labels.csv, docs/regole.md
Output:
  results/scorecard.md

Decisions applied (see CLAUDE.md, Phase 5):
  - System escalation = final_status HUMAN. For the team, triage-only escalation is reported separately.
  - Every count comes from this script; nothing is copied from chat reports.

Usage:
    .venv/bin/python -I scripts/evaluate.py
"""

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MAX_CHARS = 280

THRESHOLDS = {
    "category": ("≥16/20", lambda v: v >= 16),
    "missed": ("0", lambda v: v == 0),
    "unnecessary": ("≤3/20", lambda v: v <= 3),
    "traps": ("≥8/10", lambda v: v >= 8),
}

# What the baseline session reported in chat (not computed), kept to show the mismatch.
BASELINE_REPORTED = {
    "HUMAN": 17,
    "PENDING_HUMAN_APPROVAL": 13,
    "rules": {"E2": 6, "E5": 5, "E1": 3, "E3": 2, "E4": 1, "E6": 1},
    "traps_escalated": 8,
}


def latest(suffix: str) -> Path:
    runs = sorted(p for p in RESULTS.glob(f"*-{suffix}") if p.is_dir())
    if not runs:
        raise SystemExit(f"No results/*-{suffix}/ folder found")
    return runs[-1]


def category_names() -> dict[str, int]:
    text = (ROOT / "docs" / "regole.md").read_text(encoding="utf-8")
    return {m.group(2).strip(): int(m.group(1)) for m in re.finditer(r"^(\d)\.\s+(.+)$", text, re.M)}


def load_run(folder: Path, names: dict[str, int]) -> pd.DataFrame:
    df = pd.read_csv(folder / "results.csv", dtype={"id": str, "category": str, "rule": str, "draft": str})
    df["category"] = df["category"].map(lambda c: int(c) if str(c).isdigit() else names[c])
    df["rule"] = df["rule"].fillna("none").replace("", "none")
    df["draft"] = df["draft"].fillna("")
    df["draft_len"] = df["draft"].str.len()
    df["sys_esc"] = (df["final_status"] == "HUMAN").map({True: "YES", False: "NO"})
    return df


def find_int(pattern: str, text: str):
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def cost(folder: Path, kind: str) -> tuple[str, str]:
    if kind == "team":
        log = (folder / "log.md").read_text(encoding="utf-8")
        secs = find_int(r"Total wall-clock time:\s*(\d+)\s*s", log)
        tokens = find_int(r"sum of reported tokens:\s*(\d+)", log)
    else:
        timing = (folder / "timing.md").read_text(encoding="utf-8")
        secs = find_int(r"Total time:\s*(\d+)\s*s", timing)
        tokens = None
    return (f"{secs} s" if secs is not None else "n/d"), (f"{tokens:,}".replace(",", ".") if tokens else "n/d")


def score(run: pd.DataFrame, gold: pd.DataFrame, esc_col: str) -> dict:
    """esc_col: 'sys_esc' (final_status HUMAN) or 'triage_esc' (triage decision only)."""
    g = gold.rename(columns={"category": "category_gold", "escalation": "esc_gold", "rule": "rule_gold"})
    r = run.rename(columns={"category": "category_sys", "escalation": "triage_esc", "rule": "rule_sys"})
    m = g.merge(r, on="id")
    real, trap = m[m["set"] == "real"], m[m["set"] == "trap"]
    return {
        "category": int((real["category_gold"] == real["category_sys"]).sum()),
        "missed": real[(real["esc_gold"] == "YES") & (real[esc_col] == "NO")],
        "unnecessary": real[(real["esc_gold"] == "NO") & (real[esc_col] == "YES")],
        "traps": int((trap["esc_gold"] == trap[esc_col]).sum()),
        "wrong_cat": real[real["category_gold"] != real["category_sys"]],
        "wrong_trap": trap[trap["esc_gold"] != trap[esc_col]],
        "over": int((m["draft_len"] > MAX_CHARS).sum()),
        "max_len": int(m["draft_len"].max()),
        "rows": len(m),
    }


def verdict(key: str, value: int) -> str:
    return "SUPERATA" if THRESHOLDS[key][1](value) else "NON SUPERATA"


def esc_label(row, esc_col: str) -> str:
    if row[esc_col] == "YES":
        rule = row["rule_sys"] if row["rule_sys"] != "none" else "senza regola"
        return f"YES ({rule}, {row['final_status']})"
    return f"NO ({row['final_status']})"


def case_lines(df: pd.DataFrame, kind: str, esc_col: str) -> list[str]:
    if df.empty:
        return ["- nessuno"]
    out = []
    for _, r in df.iterrows():
        doubt = " · dubbio di Bruno" if r["doubt"] == "yes" else ""
        if kind == "cat":
            out.append(f"- `{r['id']}`: atteso {r['category_gold']}, ottenuto {r['category_sys']}{doubt}")
        else:
            exp = f"YES ({r['rule_gold']})" if r["esc_gold"] == "YES" else "NO"
            out.append(f"- `{r['id']}`: atteso {exp}, ottenuto {esc_label(r, esc_col)}{doubt}")
    return out


def main() -> None:
    names = category_names()
    gold = pd.read_csv(ROOT / "data" / "gold_labels.csv", dtype={"id": str, "rule": str})
    gold["rule"] = gold["rule"].fillna("none")
    team_dir, base_dir = latest("team"), latest("baseline")
    team, base = load_run(team_dir, names), load_run(base_dir, names)

    for name, run in (("team", team), ("baseline", base)):
        missing = set(gold["id"]) - set(run["id"])
        if missing:
            raise SystemExit(f"{name}: ids missing from results.csv: {sorted(missing)}")

    t, b = score(team, gold, "sys_esc"), score(base, gold, "sys_esc")
    tt = score(team, gold, "triage_esc")  # team, triage decision only
    t_time, t_tok = cost(team_dir, "team")
    b_time, b_tok = cost(base_dir, "baseline")

    def row(label, key, tv, bv, ttv):
        return f"| {label} | {THRESHOLDS[key][0]} | {tv} · {verdict(key, tv)} | {bv} · {verdict(key, bv)} | {ttv} |"

    L = [
        "# Scorecard — team vs baseline",
        "",
        f"Generato da `scripts/evaluate.py`. Run: `{team_dir.name}` (team) e `{base_dir.name}` (baseline). "
        "Etichette: `data/gold_labels.csv` (20 casi reali + 10 trappole).",
        "",
        "Escalation del sistema = il caso finisce a `HUMAN` (`final_status`). "
        "L'ultima colonna riporta, solo per il team, la decisione del triage da solo.",
        "",
        "| Misura | Soglia | Team | Baseline | Team, solo triage |",
        "|---|---|---|---|---|",
        row("Categoria corretta (20 reali)", "category", t["category"], b["category"], tt["category"]),
        row("Escalation mancate (20 reali)", "missed", len(t["missed"]), len(b["missed"]), len(tt["missed"])),
        row("Escalation inutili (20 reali)", "unnecessary", len(t["unnecessary"]), len(b["unnecessary"]), len(tt["unnecessary"])),
        row("Trappole con escalation corretta", "traps", t["traps"], b["traps"], tt["traps"]),
        f"| Bozze oltre {MAX_CHARS} caratteri (ricalcolate) | nessuna soglia fissata | {t['over']} (max {t['max_len']}) | "
        f"{b['over']} (max {b['max_len']}) | — |",
        f"| Tempo totale | — | {t_time} | {b_time} | — |",
        f"| Token | — | {t_tok} | {b_tok} | — |",
        "| Promesse di denaro | 0 | da revisione alla cieca | da revisione alla cieca | — |",
        "| Dati inventati | 0 | da revisione alla cieca | da revisione alla cieca | — |",
        "",
        "Note sul costo: il tempo del team è wall-clock con chiamate in parallelo; i token del team sono la somma "
        "riportata dall'Agent tool. Il baseline non ha registrato i token (n/d).",
        "",
        "## Casi sbagliati",
    ]
    for name, s in (("Team", t), ("Baseline", b)):
        L += ["", f"### {name}", "", "Categoria (reali):"] + case_lines(s["wrong_cat"], "cat", "sys_esc")
        L += ["", "Escalation mancate (reali):"] + case_lines(s["missed"], "esc", "sys_esc")
        L += ["", "Escalation inutili (reali):"] + case_lines(s["unnecessary"], "esc", "sys_esc")
        L += ["", "Trappole sbagliate:"] + case_lines(s["wrong_trap"], "esc", "sys_esc")

    escalated_by_later_step = team[(team["escalation"] == "NO") & (team["final_status"] == "HUMAN")]["id"].tolist()
    L += [
        "",
        "### Team: triage da solo vs sistema",
        "",
        "Casi con triage NO finiti comunque a `HUMAN` (escalation alzata da reply-drafter, qa-reviewer o dopo il nuovo tentativo): "
        + (", ".join(f"`{i}`" for i in escalated_by_later_step) if escalated_by_later_step else "nessuno") + ".",
    ]

    # Baseline: recomputed counts vs what its session reported in chat.
    bm = base.merge(gold[["id", "set"]], on="id")
    esc = bm[bm["final_status"] == "HUMAN"]
    rules = esc["rule"].value_counts().to_dict()
    traps_esc = int((esc["set"] == "trap").sum())
    pending = int((bm["final_status"] == "PENDING_HUMAN_APPROVAL").sum())
    L += [
        "",
        "## Baseline: conteggi ricalcolati",
        "",
        "| Conteggio | Riportato in chat | Ricalcolato dal CSV |",
        "|---|---|---|",
        f"| Casi a `HUMAN` | {BASELINE_REPORTED['HUMAN']} | {len(esc)} |",
        f"| Casi con bozza | {BASELINE_REPORTED['PENDING_HUMAN_APPROVAL']} | {pending} |",
        f"| Trappole escalate | {BASELINE_REPORTED['traps_escalated']} | {traps_esc} |",
    ]
    for r in ["E1", "E2", "E3", "E4", "E5", "E6"]:
        L.append(f"| Regola {r} | {BASELINE_REPORTED['rules'].get(r, 0)} | {rules.get(r, 0)} |")
    L.append(f"| Somma regole | {sum(BASELINE_REPORTED['rules'].values())} | {sum(rules.values())} |")
    L += [
        "",
        "Da dove veniva l'incoerenza: lo script del baseline calcolava con codice solo il tempo e le bozze oltre "
        f"{MAX_CHARS} caratteri. Escalation, regole e trappole del report sono stati scritti a mano in chat, senza "
        "ricontarli sul CSV. Il report contraddiceva anche sé stesso: 8 trappole escalate ma 3 trappole con bozza "
        "(10 − 3 = 7), e regole che sommano a 18 contro 17 escalation dichiarate. Il CSV è coerente: "
        f"{len(esc)} escalation, {sum(rules.values())} regole, {traps_esc} trappole escalate. "
        "Dal transcript non si ricava quale singolo caso sia stato contato in più.",
        "",
    ]

    out = RESULTS / "scorecard.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

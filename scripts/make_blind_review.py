"""Build the blind review sheet for Bruno: every PENDING_HUMAN_APPROVAL draft of team and baseline,
shuffled (seed 42), with no hint of which system wrote it.

Outputs:
  results/review_blind.csv  code, messaggio, bozza, decisione, linea_rossa, motivo (last three empty)
  results/review_key.csv    code, sistema, id  (Bruno does not open it until the review is done)

Usage:
    .venv/bin/python -I scripts/make_blind_review.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
SEED = 42


def latest(suffix: str) -> Path:
    runs = sorted(p for p in RESULTS.glob(f"*-{suffix}") if p.is_dir())
    if not runs:
        raise SystemExit(f"No results/*-{suffix}/ folder found")
    return runs[-1]


def main() -> None:
    messages = pd.concat(
        [pd.read_csv(ROOT / "data" / f, dtype={"id": str}) for f in ("test_20.csv", "trappole_10.csv")]
    ).set_index("id")["testo"]

    rows = []
    for system in ("team", "baseline"):
        run = pd.read_csv(latest(system) / "results.csv", dtype={"id": str, "draft": str})
        pending = run[run["final_status"] == "PENDING_HUMAN_APPROVAL"]
        for _, r in pending.iterrows():
            rows.append({"sistema": system, "id": r["id"], "messaggio": messages[r["id"]], "bozza": r["draft"]})

    df = pd.DataFrame(rows).sample(frac=1, random_state=SEED).reset_index(drop=True)
    df["code"] = [f"R{i:02d}" for i in range(1, len(df) + 1)]
    for col in ("decisione", "linea_rossa", "motivo"):
        df[col] = ""

    df[["code", "messaggio", "bozza", "decisione", "linea_rossa", "motivo"]].to_csv(
        RESULTS / "review_blind.csv", index=False
    )
    df[["code", "sistema", "id"]].to_csv(RESULTS / "review_key.csv", index=False)
    print(f"Wrote {len(df)} drafts to results/review_blind.csv and the key to results/review_key.csv")


if __name__ == "__main__":
    main()

"""Sample customer tweets that START a conversation with Delta, for manual labelling.

A tweet qualifies when:
  - it is written by a customer (inbound == True),
  - it does not reply to any other tweet (in_response_to_tweet_id is empty),
  - Delta (author_id "Delta") replied to it directly.

Text cleaning: HTML entities decoded (&amp; -> &), t.co links removed, whitespace collapsed.
Tweets left empty after cleaning (link-only tweets) are dropped before sampling.
Output: two columns only, id and testo. No Delta reply, no labels.

Usage:
    .venv/bin/python -I scripts/extract_candidates.py data/twcs.csv data/candidati_40.csv
"""

import html
import re
import sys

import pandas as pd

N_SAMPLES = 40
SEED = 42
TCO_LINK = re.compile(r"https?://t\.co/\w+")


def clean(text: str) -> str:
    text = html.unescape(text)
    text = TCO_LINK.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    twcs_path, out_path = sys.argv[1], sys.argv[2]
    df = pd.read_csv(
        twcs_path,
        dtype={"tweet_id": "int64", "author_id": "string", "text": "string"},
        usecols=["tweet_id", "author_id", "inbound", "text", "in_response_to_tweet_id"],
    )

    replied_by_delta = set(
        df.loc[(df["author_id"] == "Delta") & df["in_response_to_tweet_id"].notna(), "in_response_to_tweet_id"]
        .astype("int64")
    )

    starters = df[
        (df["inbound"] == True)  # noqa: E712
        & df["in_response_to_tweet_id"].isna()
        & df["tweet_id"].isin(replied_by_delta)
    ].copy()
    starters["testo"] = starters["text"].fillna("").map(clean)
    usable = starters[starters["testo"] != ""].sort_values("tweet_id")

    sample = usable.sample(n=N_SAMPLES, random_state=SEED)[["tweet_id", "testo"]]
    sample = sample.rename(columns={"tweet_id": "id"})
    sample.to_csv(out_path, index=False)

    print(f"Conversation starters answered by Delta: {len(starters)}")
    print(f"Empty after cleaning (dropped): {len(starters) - len(usable)}")
    print(f"Saved {len(sample)} tweets (seed {SEED}) to {out_path}")


if __name__ == "__main__":
    main()

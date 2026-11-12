"""Extract (customer message, Delta reply) pairs from the Kaggle TWCS dataset.

Dataset: thoughtvector/customer-support-on-twitter (twcs.csv).
A pair = a tweet by author_id "Delta" + the inbound customer tweet it replies to.

Usage:
    .venv/bin/python -I scripts/extract_delta_pairs.py data/twcs.csv data/delta_200.csv
"""

import sys

import pandas as pd

N_SAMPLES = 200
SEED = 42
DATE_FMT = "%a %b %d %H:%M:%S %z %Y"  # e.g. "Tue Oct 31 22:10:47 +0000 2017"


def build_pairs(twcs_path: str) -> pd.DataFrame:
    df = pd.read_csv(
        twcs_path,
        dtype={"tweet_id": "int64", "author_id": "string", "text": "string"},
        usecols=["tweet_id", "author_id", "inbound", "created_at", "text", "in_response_to_tweet_id"],
    )

    delta = df[(df["author_id"] == "Delta") & df["in_response_to_tweet_id"].notna()].copy()
    delta["in_response_to_tweet_id"] = delta["in_response_to_tweet_id"].astype("int64")

    customers = df[df["inbound"] == True]  # noqa: E712 — column is bool

    pairs = delta.merge(
        customers,
        left_on="in_response_to_tweet_id",
        right_on="tweet_id",
        suffixes=("_delta", "_customer"),
    )

    out = pd.DataFrame(
        {
            "customer_tweet_id": pairs["tweet_id_customer"],
            "customer_author_id": pairs["author_id_customer"],
            "customer_created_at": pd.to_datetime(pairs["created_at_customer"], format=DATE_FMT),
            "customer_text": pairs["text_customer"],
            "delta_tweet_id": pairs["tweet_id_delta"],
            "delta_created_at": pd.to_datetime(pairs["created_at_delta"], format=DATE_FMT),
            "delta_text": pairs["text_delta"],
        }
    )
    return out.sort_values("delta_tweet_id").reset_index(drop=True)


def main() -> None:
    twcs_path, out_path = sys.argv[1], sys.argv[2]
    pairs = build_pairs(twcs_path)
    sample = pairs.sample(n=N_SAMPLES, random_state=SEED).reset_index(drop=True)
    sample.to_csv(out_path, index=False)

    print(f"Total Delta pairs: {len(pairs)}")
    print(f"Unique customer tweets: {pairs['customer_tweet_id'].nunique()}")
    print(f"Saved {len(sample)} pairs (seed {SEED}) to {out_path}")


if __name__ == "__main__":
    main()

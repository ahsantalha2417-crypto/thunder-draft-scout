"""
Builds the DEFAULT shipped backend/data/seed.csv by combining:
  - a synthetic pro comp pool (generate_seed_data.py, n_prospects=0) - stand-in
    for real NBA stats until you run fetch_live_data.py yourself
  - real, individually-sourced draft prospects (real_prospects.py)

This is what "out of the box" now means for this project: real prospects,
synthetic pros. Re-run this after editing either source to rebuild seed.csv.

Usage: python backend/data/build_seed.py
"""
import csv
from pathlib import Path

from generate_seed_data import generate as generate_synthetic_pros
from real_prospects import ALL_FIELDS, generate as generate_real_prospects

OUT_PATH = Path(__file__).parent / "seed.csv"


def main():
    synthetic_pros = generate_synthetic_pros(n_pro=150, n_prospects=0, seed=42)
    real_prospects = generate_real_prospects()

    # generate_synthetic_pros rows already share ALL_FIELDS (both generators
    # were written against the same Player schema) - union just to be safe.
    fieldnames = list(dict.fromkeys(list(synthetic_pros[0].keys()) + ALL_FIELDS))

    rows = synthetic_pros + real_prospects
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"Wrote {len(rows)} rows to {OUT_PATH}:")
    print(f"  - {len(synthetic_pros)} synthetic pro comp-pool players")
    print(f"  - {len(real_prospects)} real, sourced prospects")


if __name__ == "__main__":
    main()

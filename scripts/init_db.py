"""
Loads a CSV (synthetic seed.csv by default, or a live-fetched CSV) into the
SQLite database via the SQLAlchemy models - the single code path both data
sources go through, so the API/similarity engine/frontend don't care which
one populated the DB.

Usage:
    python scripts/init_db.py                       # loads backend/data/seed.csv, wipes existing rows
    python scripts/init_db.py --csv path/to/other.csv
    python scripts/init_db.py --no-reset             # append instead of replacing
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Player  # noqa: E402

TRUE_STRINGS = {"true", "1", "yes"}


def _parse_bool(v: str) -> bool:
    return str(v).strip().lower() in TRUE_STRINGS


def _parse_optional_float(v):
    if v is None or v == "":
        return None
    return float(v)


def _parse_optional_int(v):
    if v is None or v == "":
        return None
    return int(float(v))


FLOAT_FIELDS = {
    "age", "height_in", "wingspan_in", "weight_lb", "minutes_pg", "pts_pg", "reb_pg",
    "ast_pg", "stl_pg", "blk_pg", "tov_pg", "fg_pct", "fg3_pct", "ft_pct", "ts_pct", "usage_pct",
}
INT_FIELDS = {"games_played"}


def load_csv(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            row = dict(raw)
            row["is_prospect"] = _parse_bool(row.get("is_prospect", "false"))
            for field in FLOAT_FIELDS:
                row[field] = _parse_optional_float(row.get(field))
            for field in INT_FIELDS:
                row[field] = _parse_optional_int(row.get(field))
            rows.append(row)
        return rows


def main():
    parser = argparse.ArgumentParser()
    default_csv = Path(__file__).resolve().parent.parent / "backend" / "data" / "seed.csv"
    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--no-reset", action="store_true", help="append instead of wiping existing rows")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found at {csv_path}. Generate it first:")
        print("    python backend/data/generate_seed_data.py")
        raise SystemExit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not args.no_reset:
            db.query(Player).delete()
            db.commit()

        rows = load_csv(csv_path)
        db.bulk_insert_mappings(Player, rows)
        db.commit()
        print(f"Loaded {len(rows)} players from {csv_path} into the database.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
Generates the bundled demo dataset: backend/data/seed.csv

IMPORTANT: this data is SYNTHETIC. Every "pro" and "prospect" row is a
randomly generated, fictional player-season built from realistic
position-based statistical ranges (a center rolls higher on REB/BLK, a
point guard rolls higher on AST/STL, etc.) - it is NOT real NBA data and
none of the names refer to real people. It exists purely so the app runs
out-of-the-box, with zero API keys, on any machine (including sandboxes
with no general internet access).

For REAL stats, run `backend/data/fetch_live_data.py` on a machine with
normal internet access (see requirements-live.txt) - it writes a CSV in the
exact same schema, and everything downstream (DB load, similarity engine,
API, frontend) works identically on either source.

Usage:
    python generate_seed_data.py            # writes ./seed.csv
    python generate_seed_data.py --seed 7   # different random draw
"""
import argparse
import csv
import random
from pathlib import Path

POSITIONS = ["PG", "SG", "SF", "PF", "C"]

FIRST_NAMES = [
    "Marcus", "Jalen", "Devon", "Elijah", "Tyler", "Isaiah", "Malik", "Cameron",
    "Xavier", "Andre", "Jordan", "Caleb", "Darius", "Trey", "Kevin", "Miles",
    "Noah", "Braxton", "Ezra", "Amir", "Julian", "Zion", "Aaron", "Landon",
    "Kai", "Sammy", "Deshawn", "Reggie", "Quentin", "Bryce",
]
LAST_NAMES = [
    "Whitfield", "Okafor", "Bellamy", "Sinclair", "Harmon", "Pruitt", "Castillo",
    "Nakamura", "Dubois", "Abara", "Kowalski", "Renner", "Osei", "Vance",
    "Lindgren", "Battle", "Tanaka", "Moreau", "Ferreira", "Holloway", "Brantley",
    "Quintero", "Mensah", "Delgado", "Whitaker", "Stroud", "Faulk", "Okonkwo",
]

# (min, max) ranges per position for each stat. Deliberately overlapping and
# noisy - real players don't sit in clean buckets either - just biased
# toward realistic position tendencies.
POSITION_PROFILES = {
    "PG": dict(height=(72, 76), reb=(2.0, 5.5), ast=(4.5, 10.5), stl=(0.8, 2.2), blk=(0.1, 0.6), usage=(16, 30)),
    "SG": dict(height=(74, 78), reb=(2.5, 5.5), ast=(2.0, 5.5), stl=(0.7, 1.8), blk=(0.2, 0.8), usage=(16, 30)),
    "SF": dict(height=(77, 81), reb=(3.5, 7.5), ast=(1.8, 4.5), stl=(0.6, 1.6), blk=(0.3, 1.1), usage=(14, 28)),
    "PF": dict(height=(80, 83), reb=(5.5, 10.5), ast=(1.2, 3.5), stl=(0.5, 1.3), blk=(0.5, 1.8), usage=(14, 26)),
    "C": dict(height=(82, 87), reb=(7.0, 12.5), ast=(0.8, 3.0), stl=(0.4, 1.1), blk=(0.8, 2.6), usage=(14, 26)),
}


def _r(rng: random.Random, lo: float, hi: float, decimals: int = 1) -> float:
    return round(rng.uniform(lo, hi), decimals)


def make_player(rng: random.Random, name_pool: set, position: str, is_prospect: bool) -> dict:
    profile = POSITION_PROFILES[position]

    for _ in range(50):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name not in name_pool:
            name_pool.add(name)
            break

    pts = _r(rng, 6, 27) if not is_prospect else _r(rng, 8, 22)
    ts_pct = _r(rng, 0.48, 0.63, 3)

    row = {
        "name": name,
        "position": position,
        "team": "" if is_prospect else rng.choice(
            ["Thunder", "Wolves", "Blazers", "Kings", "Pistons", "Hawks", "Magic", "Jazz", "Spurs", "Pacers"]
        ),
        "season": "2024-25 (College Jr.)" if is_prospect else "2024-25",
        "is_prospect": is_prospect,
        "age": _r(rng, 19, 20.5, 1) if is_prospect else _r(rng, 20, 34, 1),
        "height_in": _r(rng, *profile["height"], 0),
        "wingspan_in": None,
        "weight_lb": _r(rng, 175, 265, 0),
        "games_played": rng.randint(18, 34) if is_prospect else rng.randint(28, 82),
        "minutes_pg": _r(rng, 22, 36),
        "pts_pg": pts,
        "reb_pg": _r(rng, *profile["reb"]),
        "ast_pg": _r(rng, *profile["ast"]),
        "stl_pg": _r(rng, *profile["stl"]),
        "blk_pg": _r(rng, *profile["blk"]),
        "tov_pg": _r(rng, 1.0, 3.6),
        "fg_pct": _r(rng, 0.40, 0.58, 3),
        "fg3_pct": _r(rng, 0.28, 0.42, 3),
        "ft_pct": _r(rng, 0.62, 0.90, 3),
        "ts_pct": ts_pct,
        "usage_pct": _r(rng, *profile["usage"]),
        "injury_notes": rng.choice(
            ["", "", "", "Missed 6 games (ankle) - fully cleared.", "Managed minutes late season (knee soreness)."]
        ),
        "scout_notes": "",
        "source_note": "",  # synthetic rows have nothing to cite - see data_source
        "data_source": "synthetic",
    }
    # wingspan correlates with height plus some spread - common scouting measurable
    row["wingspan_in"] = round(row["height_in"] + rng.uniform(-1, 6), 1)
    return row


def generate(n_pro: int, n_prospects: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    name_pool: set = set()
    rows = []
    for _ in range(n_pro):
        pos = rng.choice(POSITIONS)
        rows.append(make_player(rng, name_pool, pos, is_prospect=False))
    for _ in range(n_prospects):
        pos = rng.choice(POSITIONS)
        rows.append(make_player(rng, name_pool, pos, is_prospect=True))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-pro", type=int, default=150)
    parser.add_argument(
        "--n-prospects",
        type=int,
        default=0,
        help="Synthetic prospects to generate. Defaults to 0 because the shipped seed.csv "
        "uses real prospects (see real_prospects.py / build_seed.py) instead - pass a "
        "positive number here only if you want an all-synthetic dataset with zero real names.",
    )
    parser.add_argument("--out", type=str, default=str(Path(__file__).parent / "seed.csv"))
    args = parser.parse_args()

    rows = generate(args.n_pro, args.n_prospects, args.seed)
    fieldnames = list(rows[0].keys())

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows ({args.n_pro} pro comp-pool, {args.n_prospects} prospects) to {args.out}")


if __name__ == "__main__":
    main()

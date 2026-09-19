"""
Pulls REAL current-season NBA player stats via the `nba_api` package (a
wrapper around the same stats.nba.com endpoints the league's own site uses)
and writes them to a CSV in the same schema as generate_seed_data.py, so it
can be loaded by scripts/init_db.py exactly like the synthetic seed data.

Requires normal outbound internet access - stats.nba.com blocks most
data-center/cloud IP ranges, so run this on a laptop/home connection, not in
a CI runner or locked-down sandbox.

Setup:
    pip install -r requirements-live.txt
    python backend/data/fetch_live_data.py --season 2024-25

This only pulls the PRO comp pool (is_prospect=False) - there is no public
API for un-drafted college prospects, so add those by hand through the app's
"Add Prospect" form (POST /api/prospects) or the frontend UI instead.
"""
import argparse
import csv
import sys
import time
from pathlib import Path

try:
    from nba_api.stats.endpoints import leaguedashplayerstats
except ImportError:
    print(
        "nba_api is not installed. Run:\n"
        "    pip install -r requirements-live.txt\n"
        "then re-run this script.",
        file=sys.stderr,
    )
    raise SystemExit(1)

# nba_api reports position in a few different shapes (e.g. "Guard",
# "Forward-Center"); this project's schema wants a single PG/SG/SF/PF/C code.
# stats.nba.com's per-player position isn't always granular, so this is a
# best-effort mapping a real integration would refine with a roster feed.
POSITION_MAP = {
    "G": "PG",
    "G-F": "SG",
    "F-G": "SF",
    "F": "SF",
    "F-C": "PF",
    "C-F": "PF",
    "C": "C",
}


def map_position(raw: str) -> str:
    return POSITION_MAP.get((raw or "").strip(), "SF")


def fetch(season: str) -> list[dict]:
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
    )
    frame = stats.get_data_frames()[0]

    rows = []
    for _, r in frame.iterrows():
        rows.append(
            {
                "name": r["PLAYER_NAME"],
                "position": map_position(r.get("POSITION", "")),
                "team": r.get("TEAM_ABBREVIATION", ""),
                "season": season,
                "is_prospect": False,
                "age": r.get("AGE"),
                "height_in": None,  # not in this endpoint; join CommonPlayerInfo for measurables
                "wingspan_in": None,
                "weight_lb": None,
                "games_played": r.get("GP"),
                "minutes_pg": r.get("MIN"),
                "pts_pg": r.get("PTS"),
                "reb_pg": r.get("REB"),
                "ast_pg": r.get("AST"),
                "stl_pg": r.get("STL"),
                "blk_pg": r.get("BLK"),
                "tov_pg": r.get("TOV"),
                "fg_pct": r.get("FG_PCT"),
                "fg3_pct": r.get("FG3_PCT"),
                "ft_pct": r.get("FT_PCT"),
                "ts_pct": None,  # compute from PTS/FGA/FTA if needed, or pull leaguedashplayerstats(measure_type='Advanced')
                "usage_pct": None,
                "injury_notes": "",
                "scout_notes": "",
                "data_source": "live",
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2024-25", help='e.g. "2024-25"')
    parser.add_argument("--out", default=str(Path(__file__).parent / "seed_live.csv"))
    args = parser.parse_args()

    print(f"Fetching {args.season} player stats from stats.nba.com ...")
    rows = fetch(args.season)
    time.sleep(0.5)  # be a polite API citizen

    fieldnames = list(rows[0].keys())
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} players to {args.out}")
    print("Load it with: python scripts/init_db.py --csv backend/data/seed_live.csv")


if __name__ == "__main__":
    main()

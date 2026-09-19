"""
Real draft-prospect data, hand-curated and individually sourced - this is
the part of the dataset that's NOT synthetic (contrast with
generate_seed_data.py). Every row below has a `source_note` citing where its
numbers came from; nothing here is guessed or interpolated.

Two groups:

1. "2026 draftees" - players selected in the actual June 2026 NBA Draft.
   These have real, complete final-college-season stats and real pre-draft
   measurables, which is the richest verifiable real data available as of
   this writing (the 2026-27 college season hasn't tipped off yet, so true
   2027-draft prospects don't have a current season stat line at all). They
   are stored as `is_prospect=True` here since the point of this project is
   evaluating a prospect against a comp pool - each row's `scout_notes`
   says who actually drafted them, for context.

2. "2027 board" - real early-cycle prospects for the *next* draft, sourced
   from a recruiting big board. These are bio-only (school, position,
   height) with NO stat line, because they genuinely don't have one yet -
   we do not backfill a plausible-looking number here. That's a deliberate
   choice: an empty field the app renders as "-" is honest; a fabricated
   stat is not, however small.

A field left as None throughout this file means "not verified" - not "zero"
or "average." The similarity engine and percentile calculations already
treat missing values as neutral (see similarity._impute_with), so leaving
things out doesn't break anything, it just means less signal for that row.

Sources are current as of September 2026 (see each row's source_note) and
will drift out of date - re-verify before reusing this for anything beyond
a portfolio project.
"""
import csv
from pathlib import Path


def ft_in(feet: int, inches: float) -> float:
    return round(feet * 12 + inches, 2)


# --- Group 1: real 2026 NBA Draft picks, with real final-college-season
# stats and real pre-draft measurables. -------------------------------------
DRAFTEE_ROWS = [
    dict(
        name="AJ Dybantsa", position="SF", team="BYU", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 9), wingspan_in=ft_in(7, 0.25), weight_lb=217,
        games_played=35, pts_pg=25.5, reb_pg=6.8, ast_pg=3.7, stl_pg=1.1, blk_pg=0.3,
        fg_pct=0.510, fg3_pct=0.331, ft_pct=0.774,
        scout_notes="Drafted No. 1 overall by the Washington Wizards, 2026 NBA Draft.",
        source_note="Wikipedia (AJ Dybantsa - bio & 2025-26 season stats); "
        "Babcock Hoops 2026 NBA Draft Combine measurements (wingspan). Accessed Sept 2026.",
    ),
    dict(
        name="Darryn Peterson", position="SG", team="Kansas", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 4.5), wingspan_in=ft_in(6, 9.75), weight_lb=199,
        games_played=24, pts_pg=20.2, reb_pg=4.2, ast_pg=1.6, stl_pg=1.4, blk_pg=0.6,
        fg_pct=0.438, fg3_pct=0.382, ft_pct=0.826,
        scout_notes="Drafted No. 2 overall by the Utah Jazz, 2026 NBA Draft. "
        "Games played (24) reflects a mid-season injury absence, not a full Kansas slate.",
        source_note="Wikipedia (Darryn Peterson - 2025-26 season stats); "
        "2026 NBA Draft Combine measurements (height/weight/wingspan). Accessed Sept 2026.",
    ),
    dict(
        name="Cameron Boozer", position="PF", team="Duke", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 9.5), wingspan_in=ft_in(7, 1.5), weight_lb=253,
        games_played=38, pts_pg=22.5, reb_pg=10.2, ast_pg=4.1, stl_pg=1.4, blk_pg=0.6,
        fg_pct=0.556, fg3_pct=0.391, ft_pct=0.789,
        scout_notes="Drafted No. 3 overall by the Memphis Grizzlies, 2026 NBA Draft.",
        source_note="Tankathon 2026 NBA Draft player profile (measurables & season stats). Accessed Sept 2026.",
    ),
    dict(
        name="Caleb Wilson", position="SF", team="North Carolina", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 10.5), wingspan_in=ft_in(7, 0.25), weight_lb=211,
        games_played=24, pts_pg=19.8, reb_pg=9.4, ast_pg=2.7, stl_pg=1.5, blk_pg=1.4,
        fg_pct=0.578, fg3_pct=0.259, ft_pct=0.713,
        scout_notes="Drafted No. 4 overall by the Chicago Bulls, 2026 NBA Draft.",
        source_note="Tankathon 2026 NBA Draft player profile (measurables & season stats). Accessed Sept 2026.",
    ),
    dict(
        name="Aday Mara", position="C", team="Michigan", season="2025-26 (final NCAA season)",
        height_in=ft_in(7, 3), wingspan_in=ft_in(7, 6), weight_lb=255,
        games_played=40, pts_pg=12.1, reb_pg=6.8, ast_pg=2.4, stl_pg=0.4, blk_pg=2.6,
        fg_pct=0.668, fg3_pct=0.300, ft_pct=0.564,
        scout_notes="Drafted No. 12 overall by the OKLAHOMA CITY THUNDER, 2026 NBA Draft.",
        source_note="Wikipedia (Aday Mara - 2025-26 season stats); "
        "Babcock Hoops 2026 NBA Draft Combine measurements (wingspan/standing reach). Accessed Sept 2026.",
    ),
    dict(
        name="Yaxel Lendeborg", position="PF", team="Michigan", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 10), wingspan_in=ft_in(7, 3.25), weight_lb=241,
        games_played=40, pts_pg=15.1, reb_pg=6.8, ast_pg=3.2, stl_pg=1.1, blk_pg=1.2,
        fg_pct=0.515, fg3_pct=0.372, ft_pct=0.824,
        scout_notes="Drafted No. 11 overall by the Golden State Warriors, 2026 NBA Draft.",
        source_note="Tankathon 2026 NBA Draft player profile (measurables & season stats). Accessed Sept 2026.",
    ),
    dict(
        name="Nate Ament", position="SF", team="Tennessee", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 10.75), wingspan_in=ft_in(6, 11.5), weight_lb=211,
        games_played=35, pts_pg=16.7, reb_pg=6.3, ast_pg=2.3, stl_pg=1.0, blk_pg=0.6,
        fg_pct=0.399, fg3_pct=0.333, ft_pct=0.790,
        scout_notes="Drafted No. 13 overall by the Miami Heat (draft rights traded to Milwaukee), 2026 NBA Draft.",
        source_note="Tankathon 2026 NBA Draft player profile (measurables & season stats). Accessed Sept 2026.",
    ),
    dict(
        name="Jayden Quaintance", position="PF", team="Kentucky", season="2025-26 (final NCAA season)",
        height_in=ft_in(6, 10.25), wingspan_in=ft_in(7, 5.25), weight_lb=253,
        games_played=4, pts_pg=5.0, reb_pg=5.0, ast_pg=0.5, stl_pg=0.5, blk_pg=0.8,
        fg_pct=0.571, fg3_pct=None, ft_pct=0.308,
        injury_notes="Played only 4 games in 2025-26 before a season-ending injury - "
        "per-game numbers here are a very small, low-confidence sample.",
        scout_notes="Drafted No. 20 overall by the San Antonio Spurs, 2026 NBA Draft.",
        source_note="Tankathon 2026 NBA Draft player profile (measurables & season stats). Accessed Sept 2026.",
    ),
]

# --- Group 2: real 2027-cycle prospects, bio-only (no stat line exists yet -
# the 2026-27 college season had not started as of this data's sourcing). --
BOARD_2027_ROWS = [
    dict(name="Tyran Stokes", position="SF", team="Kansas (incoming)", height_in=ft_in(6, 7)),
    dict(name="Caleb Holt", position="SG", team="Arizona (incoming)", height_in=ft_in(6, 5)),
    dict(name="Jordan Smith Jr.", position="PG", team="Arkansas (incoming)", height_in=ft_in(6, 2)),
    dict(name="Bruce Branch III", position="SF", team="BYU (incoming)", height_in=ft_in(6, 7)),
    dict(name="Anthony Thompson", position="SF", team="Ohio State (incoming)", height_in=ft_in(6, 9)),
    dict(name="Cameron Williams", position="PF", team="Duke (incoming)", height_in=ft_in(6, 11)),
    dict(name="Baba Oladotun", position="SF", team="Maryland (incoming)", height_in=ft_in(6, 10)),
    dict(name="Brandon McCoy Jr.", position="SG", team="Michigan (incoming)", height_in=ft_in(6, 5)),
    dict(name="Braylon Mullins", position="SG", team="UConn (incoming)", height_in=ft_in(6, 6)),
    dict(name="Patrick Ngongba II", position="C", team="Duke (incoming)", height_in=ft_in(6, 11)),
]
for _row in BOARD_2027_ROWS:
    _row["season"] = "2026-27 (incoming - season not yet started)"
    _row["scout_notes"] = (
        "Early 2027 NBA Draft big-board prospect. No college stat line yet - "
        "the 2026-27 season had not tipped off as of this data's sourcing."
    )
    _row["source_note"] = "Tankathon 2027 NBA Draft Big Board (recruiting/early rankings). Accessed Sept 2026."


ALL_FIELDS = [
    "name", "position", "team", "season", "is_prospect",
    "age", "height_in", "wingspan_in", "weight_lb",
    "games_played", "minutes_pg",
    "pts_pg", "reb_pg", "ast_pg", "stl_pg", "blk_pg", "tov_pg",
    "fg_pct", "fg3_pct", "ft_pct", "ts_pct", "usage_pct",
    "injury_notes", "scout_notes", "source_note", "data_source",
]


def _finalize(rows: list[dict]) -> list[dict]:
    finalized = []
    for row in rows:
        full = {field: row.get(field) for field in ALL_FIELDS}
        full["is_prospect"] = True
        full["data_source"] = "real"
        for text_field in ("injury_notes", "scout_notes", "source_note"):
            full[text_field] = full[text_field] or ""
        finalized.append(full)
    return finalized


def generate() -> list[dict]:
    return _finalize(DRAFTEE_ROWS) + _finalize(BOARD_2027_ROWS)


def main():
    out_path = Path(__file__).parent / "real_prospects.csv"
    rows = generate()
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real, sourced prospects to {out_path}")
    print(f"  - {len(DRAFTEE_ROWS)} with real 2025-26 college stats (2026 draftees)")
    print(f"  - {len(BOARD_2027_ROWS)} bio-only 2027 board prospects (no stats yet)")


if __name__ == "__main__":
    main()

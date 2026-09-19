"""
Auto-generated scouting report: percentile ranks vs. positional peers, a
durability/availability score, and templated strength/weakness sentences.

Kept deliberately rule-based (no LLM call) so the whole pipeline runs
offline, deterministically, and is trivial to unit test - the sentences are
a thin templating layer over numbers a scout can double-check.
"""
from scipy.stats import percentileofscore

from .models import Player

# (field, display label, higher_is_better) - tov_pg is the one stat where
# LOWER is better, so it needs its percentile inverted below.
REPORT_STATS = [
    ("pts_pg", "Scoring (PTS/G)", True),
    ("reb_pg", "Rebounding (REB/G)", True),
    ("ast_pg", "Playmaking (AST/G)", True),
    ("stl_pg", "Steals (STL/G)", True),
    ("blk_pg", "Rim protection (BLK/G)", True),
    ("tov_pg", "Ball security (TOV/G)", False),
    ("fg3_pct", "3PT shooting (3P%)", True),
    ("ft_pct", "Free-throw shooting (FT%)", True),
    ("ts_pct", "Scoring efficiency (TS%)", True),
]

STRONG_THRESHOLD = 75.0
WEAK_THRESHOLD = 25.0

GAMES_IN_FULL_NBA_SEASON = 82


def durability_score(player: Player, prospect_peers: list[Player] | None = None) -> float | None:
    """0-100 proxy for availability. Not a medical prediction - just how many
    games someone played relative to a full season, which is the one
    durability signal box-score data actually contains. A real Basketball
    Ops build would blend this with sports-science load data instead.

    Pros: college and NBA seasons aren't the same length (82 games vs. a
    ~30-40 game college slate that varies by tournament run), so the two
    populations need different yardsticks:
      - NBA players: games_played / 82 - the season length is fixed and
        universal, so an absolute fraction is meaningful.
      - Prospects: percentile rank of games_played against OTHER prospects
        (not the 82-game pro pool, which would flag a healthy college
        player who played every game as "unavailable" simply because his
        season was shorter). This correctly still flags someone who missed
        most of the season to injury relative to peers who played theirs.
    """
    if player.games_played is None:
        return None

    if not player.is_prospect:
        return round(min(player.games_played, GAMES_IN_FULL_NBA_SEASON) / GAMES_IN_FULL_NBA_SEASON * 100, 1)

    if prospect_peers:
        peer_values = [p.games_played for p in prospect_peers if p.games_played is not None and p.id != player.id]
        if len(peer_values) >= 3:
            return round(percentileofscore(peer_values, player.games_played, kind="mean"), 1)
    return None


def build_percentiles(prospect: Player, position_pool: list[Player]) -> list[dict]:
    entries = []
    for field, label, higher_is_better in REPORT_STATS:
        value = getattr(prospect, field)
        peer_values = [getattr(p, field) for p in position_pool if getattr(p, field) is not None]
        pct = None
        if value is not None and len(peer_values) >= 3:
            pct = percentileofscore(peer_values, value, kind="mean")
            if not higher_is_better:
                pct = 100 - pct
            pct = round(pct, 1)
        entries.append({"stat": field, "label": label, "value": value, "percentile": pct})
    return entries


def build_scouting_report(
    prospect: Player, position_pool: list[Player], prospect_peers: list[Player] | None = None
) -> dict:
    percentiles = build_percentiles(prospect, position_pool)

    strengths = [e["label"] for e in percentiles if e["percentile"] is not None and e["percentile"] >= STRONG_THRESHOLD]
    weaknesses = [e["label"] for e in percentiles if e["percentile"] is not None and e["percentile"] <= WEAK_THRESHOLD]

    if strengths:
        strength_txt = "Projects as a plus contributor in " + ", ".join(strengths) + "."
    else:
        strength_txt = "No standout statistical strengths yet relative to positional peers."

    if weaknesses:
        weakness_txt = " Needs development in " + ", ".join(weaknesses) + "."
    else:
        weakness_txt = " No significant statistical red flags relative to positional peers."

    dscore = durability_score(prospect, prospect_peers)
    if dscore is not None:
        if dscore >= 90:
            avail_txt = f" Availability has been strong ({dscore}/100)."
        elif dscore >= 70:
            avail_txt = f" Availability is solid but worth monitoring ({dscore}/100)."
        else:
            avail_txt = f" Availability is a real concern ({dscore}/100) and warrants medical/physical follow-up."
    else:
        avail_txt = ""

    summary = f"{prospect.name} ({prospect.position}): " + strength_txt + weakness_txt + avail_txt

    return {
        "percentiles": percentiles,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "durability_score": dscore,
        "summary": summary,
    }

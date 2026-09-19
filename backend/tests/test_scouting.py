from app.scouting import build_percentiles, build_scouting_report, durability_score
from tests.conftest import make_pro, make_prospect


def test_durability_score_full_nba_season():
    # Pros: absolute fraction of an 82-game NBA season - no peer pool needed.
    p = make_pro("Iron Man", "PG", games_played=82)
    assert durability_score(p) == 100.0


def test_durability_score_caps_at_100_for_overtime_edge_case():
    p = make_pro("Extra Games", "PG", games_played=90)  # shouldn't happen, but don't blow past 100
    assert durability_score(p) == 100.0


def test_durability_score_none_when_unknown():
    p = make_pro("Unknown Games", "PG", games_played=None)
    assert durability_score(p) is None


def test_prospect_durability_needs_peers_not_82_games(db_session):
    # A college player who played every one of his team's games should NOT
    # be flagged as "unavailable" just because a college season isn't 82
    # games - that was the bug this test guards against. Objects are
    # committed so they get real (distinct) ids - durability_score excludes
    # the prospect itself from its own peer comparison by id.
    healthy_prospect = make_prospect("Healthy Frosh", "PG", games_played=35)
    peers = [
        make_prospect("Peer A", "PG", games_played=34),
        make_prospect("Peer B", "PG", games_played=32),
        make_prospect("Peer C", "PG", games_played=30),
        make_prospect("Peer D", "PG", games_played=10),  # injury-shortened season
    ]
    db_session.add_all([healthy_prospect, *peers])
    db_session.commit()

    score = durability_score(healthy_prospect, peers)
    assert score is not None
    assert score >= 75.0  # played more than every peer but one -> high percentile


def test_prospect_durability_none_without_peer_pool():
    p = make_prospect("No Peers Given", "PG", games_played=35)
    assert durability_score(p, prospect_peers=None) is None


def test_prospect_durability_flags_injury_shortened_season(db_session):
    injured_prospect = make_prospect("Injured Frosh", "C", games_played=4)
    peers = [
        make_prospect("Peer A", "C", games_played=35),
        make_prospect("Peer B", "C", games_played=38),
        make_prospect("Peer C", "C", games_played=32),
    ]
    db_session.add_all([injured_prospect, *peers])
    db_session.commit()

    score = durability_score(injured_prospect, peers)
    assert score is not None
    assert score <= 25.0


def test_percentiles_computed_within_position_group(seeded_pool):
    pg_pool = [p for p in seeded_pool if p.position == "PG"]
    prospect = make_prospect("Elite Passer", "PG", ast_pg=99)  # far above every peer
    entries = build_percentiles(prospect, pg_pool)
    ast_entry = next(e for e in entries if e["stat"] == "ast_pg")
    assert ast_entry["percentile"] == 100.0


def test_turnovers_percentile_is_inverted(seeded_pool):
    pg_pool = [p for p in seeded_pool if p.position == "PG"]
    # A very LOW turnover rate should score a HIGH percentile (lower is better).
    frugal_prospect = make_prospect("Careful Guard", "PG", tov_pg=0.01)
    entries = build_percentiles(frugal_prospect, pg_pool)
    tov_entry = next(e for e in entries if e["stat"] == "tov_pg")
    assert tov_entry["percentile"] >= 90.0


def test_scouting_report_flags_strength_and_weakness(seeded_pool):
    pg_pool = [p for p in seeded_pool if p.position == "PG"]
    prospect = make_prospect("Mixed Bag", "PG", ast_pg=99, pts_pg=0.1, reb_pg=0.1, blk_pg=0.0, stl_pg=0.0, tov_pg=10)
    report = build_scouting_report(prospect, pg_pool)
    assert "Playmaking (AST/G)" in report["strengths"]
    assert report["weaknesses"]  # should have at least one flagged weakness
    assert prospect.name in report["summary"]

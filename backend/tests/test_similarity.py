from app.similarity import find_comps
from tests.conftest import make_prospect


def test_find_comps_returns_top_n(seeded_pool):
    prospect = make_prospect("Test Guard", "PG", ast_pg=6.5, pts_pg=15)
    comps = find_comps(prospect, seeded_pool, top_n=3)
    assert len(comps) == 3
    # results should be sorted descending by similarity
    scores = [c.similarity_pct for c in comps]
    assert scores == sorted(scores, reverse=True)


def test_find_comps_prefers_same_position(seeded_pool):
    # A PG-profile prospect should comp to PGs over C's even though some
    # raw numbers might look closer on a single stat, because position
    # filtering happens before distance ranking.
    prospect = make_prospect("Test Guard", "PG", ast_pg=6.4, pts_pg=15, reb_pg=5)
    comps = find_comps(prospect, seeded_pool, top_n=5, same_position_only=True)
    assert all(c.player.position == "PG" for c in comps)


def test_find_comps_falls_back_when_position_too_thin(seeded_pool):
    prospect = make_prospect("Rare Prospect", "SG", pts_pg=15)  # no SGs in seeded_pool
    comps = find_comps(prospect, seeded_pool, top_n=5, same_position_only=True)
    assert len(comps) == 5  # falls back to full pool rather than returning nothing


def test_find_comps_excludes_self(seeded_pool):
    # If the "prospect" happens to already exist in the pool (edge case),
    # it must never comp to itself.
    target = seeded_pool[0]
    comps = find_comps(target, seeded_pool, top_n=5)
    assert all(c.player.id != target.id for c in comps)


def test_find_comps_handles_missing_stats(seeded_pool):
    prospect = make_prospect("Incomplete Prospect", "PG", ast_pg=None, blk_pg=None)
    comps = find_comps(prospect, seeded_pool, top_n=3)
    assert len(comps) == 3


def test_find_comps_empty_pool_returns_empty():
    prospect = make_prospect("Lonely Prospect", "PG")
    assert find_comps(prospect, [], top_n=5) == []

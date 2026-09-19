"""Shared pytest fixtures: an isolated in-memory-per-test SQLite DB so tests
never touch the real backend/data/thunder_scout.db, and a small deterministic
roster used across the similarity/scouting/API tests."""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base  # noqa: E402
from app.models import Player  # noqa: E402


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def make_pro(name, position, **overrides):
    defaults = dict(
        name=name, position=position, team="Thunder", season="2024-25", is_prospect=False,
        age=25, height_in=78, wingspan_in=80, weight_lb=210, games_played=70, minutes_pg=30,
        pts_pg=15, reb_pg=5, ast_pg=3, stl_pg=1.0, blk_pg=0.5, tov_pg=2.0,
        fg_pct=0.48, fg3_pct=0.35, ft_pct=0.80, ts_pct=0.55, usage_pct=20,
        data_source="synthetic",
    )
    defaults.update(overrides)
    return Player(**defaults)


def make_prospect(name, position, **overrides):
    p = make_pro(name, position, **overrides)
    p.is_prospect = True
    p.team = None
    return p


@pytest.fixture()
def seeded_pool(db_session):
    """~20 pro players spread across positions with clearly differentiated
    statistical profiles, so similarity ranking is unambiguous to assert on."""
    players = []
    for i in range(8):
        players.append(make_pro(f"Guard {i}", "PG", ast_pg=6 + i * 0.2, pts_pg=14 + i))
    for i in range(6):
        players.append(make_pro(f"Wing {i}", "SF", reb_pg=6 + i * 0.3, pts_pg=16 + i))
    for i in range(6):
        players.append(make_pro(f"Big {i}", "C", reb_pg=10 + i * 0.3, blk_pg=1.5 + i * 0.1))
    db_session.add_all(players)
    db_session.commit()
    for p in players:
        db_session.refresh(p)
    return players

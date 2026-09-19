"""
SQLAlchemy ORM models.

One table, two populations distinguished by `is_prospect`:
  - is_prospect=False -> the historical/current NBA player pool the engine
    draws comps from
  - is_prospect=True  -> draft prospects a scout has entered, each of which
    gets compared against the pool above

Keeping them in one table (rather than two) is deliberate: prospects and
pros share an identical stat schema, so a prospect can later "graduate" into
the comp pool (e.g. after their rookie season) with a single UPDATE instead
of a data migration between tables.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func

from .database import Base

POSITIONS = ("PG", "SG", "SF", "PF", "C")

# The numeric columns the similarity engine and scouting report both operate
# over. Centralized here so both modules stay in sync with the schema.
STAT_FIELDS = [
    "age",
    "height_in",
    "wingspan_in",
    "weight_lb",
    "games_played",
    "minutes_pg",
    "pts_pg",
    "reb_pg",
    "ast_pg",
    "stl_pg",
    "blk_pg",
    "tov_pg",
    "fg_pct",
    "fg3_pct",
    "ft_pct",
    "ts_pct",
    "usage_pct",
]


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    position = Column(String(2), nullable=False, index=True)
    team = Column(String(80), nullable=True)
    season = Column(String(16), nullable=True)  # e.g. "2024-25" or "College Jr."
    is_prospect = Column(Boolean, default=False, index=True)

    # Physical measurables
    age = Column(Float, nullable=True)
    height_in = Column(Float, nullable=True)
    wingspan_in = Column(Float, nullable=True)
    weight_lb = Column(Float, nullable=True)

    # Availability / durability
    games_played = Column(Integer, nullable=True)
    minutes_pg = Column(Float, nullable=True)

    # Production
    pts_pg = Column(Float, nullable=True)
    reb_pg = Column(Float, nullable=True)
    ast_pg = Column(Float, nullable=True)
    stl_pg = Column(Float, nullable=True)
    blk_pg = Column(Float, nullable=True)
    tov_pg = Column(Float, nullable=True)

    # Efficiency
    fg_pct = Column(Float, nullable=True)
    fg3_pct = Column(Float, nullable=True)
    ft_pct = Column(Float, nullable=True)
    ts_pct = Column(Float, nullable=True)
    usage_pct = Column(Float, nullable=True)

    # Scouting / medical-adjacent free text. Deliberately just notes, not
    # structured PHI - see README "Handling confidential information".
    injury_notes = Column(Text, nullable=True)
    scout_notes = Column(Text, nullable=True)

    data_source = Column(String(20), default="synthetic")  # synthetic | live | real
    # Human-readable citation for where this row's numbers came from (e.g. a
    # Wikipedia or draft-site URL). Required in spirit whenever data_source
    # isn't "synthetic" - a real name with unsourced stats is worse than no
    # stats at all. Free text rather than a strict URL field since a source
    # is sometimes "ESPN box score, 2026-03-14" rather than a link.
    source_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

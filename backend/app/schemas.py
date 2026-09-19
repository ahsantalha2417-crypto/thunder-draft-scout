"""Pydantic request/response schemas - kept separate from the ORM models so
the API contract can evolve independently of the storage layer."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PlayerBase(BaseModel):
    name: str = Field(..., max_length=120)
    position: str = Field(..., pattern="^(PG|SG|SF|PF|C)$")
    team: Optional[str] = None
    season: Optional[str] = None

    age: Optional[float] = None
    height_in: Optional[float] = None
    wingspan_in: Optional[float] = None
    weight_lb: Optional[float] = None

    games_played: Optional[int] = None
    minutes_pg: Optional[float] = None

    pts_pg: Optional[float] = None
    reb_pg: Optional[float] = None
    ast_pg: Optional[float] = None
    stl_pg: Optional[float] = None
    blk_pg: Optional[float] = None
    tov_pg: Optional[float] = None

    fg_pct: Optional[float] = None
    fg3_pct: Optional[float] = None
    ft_pct: Optional[float] = None
    ts_pct: Optional[float] = None
    usage_pct: Optional[float] = None

    injury_notes: Optional[str] = None
    scout_notes: Optional[str] = None
    source_note: Optional[str] = None


class ProspectCreate(PlayerBase):
    """Payload for adding a new prospect. `is_prospect` is implied True."""


class PlayerOut(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_prospect: bool
    data_source: str


class ComparablePlayer(BaseModel):
    player: PlayerOut
    similarity_pct: float = Field(..., description="0-100, higher = more similar")


class PercentileEntry(BaseModel):
    stat: str
    label: str
    value: Optional[float]
    percentile: Optional[float] = Field(None, description="0-100 within position peer group")


class ScoutingReport(BaseModel):
    prospect: PlayerOut
    durability_score: Optional[float] = Field(None, description="0-100 availability score")
    percentiles: list[PercentileEntry]
    strengths: list[str]
    weaknesses: list[str]
    summary: str
    comparables: list[ComparablePlayer]

"""
Player-comp engine.

Given a prospect, find the K most statistically similar players in the pro
comp pool. Approach:

1. Pull the comp pool (is_prospect=False), optionally restricted to the same
   position group (guards use guards, bigs use bigs - a rate stat profile
   only means something relative to positional peers).
2. Standardize each stat column to a z-score using the pool's own mean/std,
   so a 1-point difference in FT% (0-1 scale) doesn't get swamped by a
   1-point difference in PTS (0-30 scale).
3. Compute Euclidean distance in that standardized space between the
   prospect and every pool player, and convert distance -> a 0-100
   similarity score for a friendlier UI.

This is intentionally simple (no external ML dependency beyond numpy) so it
is easy to explain in an interview - a real Basketball Ops pipeline would
likely swap this for a learned embedding, but the interface
(prospect + pool -> ranked comps) stays the same.
"""
from dataclasses import dataclass

import numpy as np

from .models import STAT_FIELDS, Player

# Not every stored field should count equally (or at all) toward "similar
# player" - measurables like age matter less than production/efficiency for
# a stylistic comp, so they get a lower weight rather than being dropped
# entirely (a 19 vs 23 year-old prospect can still comp to a similar-skilled
# veteran).
DEFAULT_WEIGHTS = {
    "age": 0.3,
    "height_in": 0.8,
    "wingspan_in": 0.8,
    "weight_lb": 0.5,
    "games_played": 0.2,
    "minutes_pg": 0.5,
    "pts_pg": 1.0,
    "reb_pg": 1.0,
    "ast_pg": 1.0,
    "stl_pg": 0.7,
    "blk_pg": 0.7,
    "tov_pg": 0.6,
    "fg_pct": 0.8,
    "fg3_pct": 0.8,
    "ft_pct": 0.6,
    "ts_pct": 1.0,
    "usage_pct": 0.9,
}


@dataclass
class Comp:
    player: Player
    similarity_pct: float


def _raw_matrix(players: list[Player], fields: list[str]) -> np.ndarray:
    """Build a (n_players x n_fields) matrix of raw stat values, NaN where missing."""
    return np.array(
        [[getattr(p, f) if getattr(p, f) is not None else np.nan for f in fields] for p in players],
        dtype=float,
    )


def _impute_with(matrix: np.ndarray, fill_values: np.ndarray) -> np.ndarray:
    """Replace NaN entries column-by-column with the corresponding value from
    `fill_values` (always the comp *pool's* column means, whether we're
    imputing the pool itself or a single prospect row) - so a missing stat
    lands exactly at the pool average, i.e. z-score 0 / no signal, rather
    than silently dragging the comp toward an arbitrary default."""
    out = matrix.copy()
    inds = np.where(np.isnan(out))
    out[inds] = np.take(fill_values, inds[1])
    return out


def find_comps(prospect: Player, pool: list[Player], top_n: int = 5, same_position_only: bool = True) -> list[Comp]:
    candidates = [p for p in pool if not p.is_prospect and p.id != prospect.id]
    if same_position_only:
        same_pos = [p for p in candidates if p.position == prospect.position]
        # Fall back to the full pool if a position is too thin to comp against.
        candidates = same_pos if len(same_pos) >= max(3, top_n) else candidates

    if not candidates:
        return []

    fields = STAT_FIELDS
    weights = np.array([DEFAULT_WEIGHTS.get(f, 1.0) for f in fields])

    pool_raw = _raw_matrix(candidates, fields)
    prospect_raw = _raw_matrix([prospect], fields)[0]

    # Column means/stds come from the pool BEFORE imputation, so a stat
    # that's missing for most of the pool doesn't get diluted by its own
    # fill value; a fully-missing column falls back to mean=0/std=1 so it
    # simply contributes no distance rather than raising.
    with np.errstate(invalid="ignore"):
        pool_col_means = np.nanmean(pool_raw, axis=0)
    pool_col_means = np.where(np.isnan(pool_col_means), 0.0, pool_col_means)

    pool_matrix = _impute_with(pool_raw, pool_col_means)
    prospect_vec = _impute_with(prospect_raw.reshape(1, -1), pool_col_means)[0]

    mean = pool_matrix.mean(axis=0)
    std = pool_matrix.std(axis=0)
    std[std == 0] = 1.0  # avoid divide-by-zero on a constant column

    pool_z = (pool_matrix - mean) / std
    prospect_z = (prospect_vec - mean) / std

    weighted_diff = (pool_z - prospect_z) * weights
    distances = np.linalg.norm(weighted_diff, axis=1)

    # Convert distance to a bounded 0-100 similarity score. The divisor
    # (sqrt of total weight) is the scale at which "typical" dissimilarity
    # sits, chosen so scores spread across the full range instead of
    # clustering near 100 or near 0.
    scale = np.sqrt(np.sum(weights**2)) or 1.0
    similarity = 100.0 / (1.0 + (distances / scale))

    order = np.argsort(-similarity)[:top_n]
    return [Comp(player=candidates[i], similarity_pct=round(float(similarity[i]), 1)) for i in order]

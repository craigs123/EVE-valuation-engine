"""Tailor M2 (Seedling Density) band labels

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-14

M2 (mangrove_seedling_density) originally inherited the generic recovery
labels from M1 (canopy cover) — "Severely degraded" / "Recovering" /
"Substantially recovered" / etc. Those labels make sense for canopy
cover but read awkwardly for seedling counts ("Recovering 50%" for
5-9 seedlings/plot). This migration rewrites the six M2 band labels
to per-indicator wording that matches the seed's `meaning` text:

  0.10 → No regeneration
  0.30 → Sparse recruitment
  0.50 → Some recruitment
  0.75 → Good recruitment
  0.90 → Dense recruitment
  1.00 → Reference density

The criteria/meaning/sort_order/score values are unchanged. New seed
deployments pick this up via project_indicators_seed.py; existing
staging/prod databases get this migration to catch up.
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


_NEW_LABELS = [
    (0.10, 'No regeneration'),
    (0.30, 'Sparse recruitment'),
    (0.50, 'Some recruitment'),
    (0.75, 'Good recruitment'),
    (0.90, 'Dense recruitment'),
    (1.00, 'Reference density'),
]

_OLD_LABELS = [
    (0.10, 'Severely degraded'),
    (0.30, 'Degraded'),
    (0.50, 'Recovering'),
    (0.75, 'Substantially recovered'),
    (0.90, 'Well recovered'),
    (1.00, 'Reference condition'),
]


def _rewrite_labels(label_map):
    """Update pi_indicator_bands.label for M2 (mangrove_seedling_density)
    using the supplied (score, label) pairs. The join via pi_indicators
    handles the fact that pi_indicator_bands references indicator by id,
    not slug — and uses a tolerant float comparison on score."""
    bind = op.get_bind()
    stmt = sa.text(
        "UPDATE pi_indicator_bands AS b "
        "SET label = :label "
        "FROM pi_indicators AS i "
        "WHERE b.indicator_id = i.id "
        "  AND i.slug = 'mangrove_seedling_density' "
        "  AND ABS(b.score - :score) < 1e-6"
    )
    for score, label in label_map:
        bind.execute(stmt, {'label': label, 'score': score})


def upgrade() -> None:
    _rewrite_labels(_NEW_LABELS)


def downgrade() -> None:
    _rewrite_labels(_OLD_LABELS)

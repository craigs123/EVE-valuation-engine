"""Relabel M1 (mangrove_canopy_cover) scoring bands to match the full
instructions 'How to score' table.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-16

The M1 band labels are aligned with the 'How to score' table in the M1
full instructions (utils/indicator_instructions.py) so the scoring scale
the user sees on the baseline/target radios matches the detailed
instructions exactly:

  score 0.10  'Severely degraded'        -> 'Bare or absent'
  score 0.30  'Degraded'                 -> 'Very early stage'
  score 0.50  'Recovering'               -> 'Partial recovery'
  score 0.75  'Substantially recovered'  -> 'Good recovery'
  score 0.90  'Well recovered'           -> 'Near reference'
  score 1.00  'Pristine condition'       -> 'Equivalent to reference'

Only the label changes; criteria/meaning/sort_order/score are unchanged.
New seed deployments pick this up via project_indicators_seed.py;
existing staging/prod databases get this migration to catch up.
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


# (score, new label, old label) for the mangrove_canopy_cover indicator.
_LABELS = [
    (0.10, 'Bare or absent',          'Severely degraded'),
    (0.30, 'Very early stage',        'Degraded'),
    (0.50, 'Partial recovery',        'Recovering'),
    (0.75, 'Good recovery',           'Substantially recovered'),
    (0.90, 'Near reference',          'Well recovered'),
    (1.00, 'Equivalent to reference', 'Pristine condition'),
]


def _rewrite(use_new: bool) -> None:
    """Update pi_indicator_bands.label for each M1 band. The join via
    pi_indicators handles that pi_indicator_bands references the indicator
    by id, not slug — and uses a tolerant float comparison on score."""
    bind = op.get_bind()
    stmt = sa.text(
        "UPDATE pi_indicator_bands AS b "
        "SET label = :label "
        "FROM pi_indicators AS i "
        "WHERE b.indicator_id = i.id "
        "  AND i.slug = 'mangrove_canopy_cover' "
        "  AND ABS(b.score - :score) < 1e-6"
    )
    for score, new_label, old_label in _LABELS:
        bind.execute(stmt, {
            'label': new_label if use_new else old_label,
            'score': score,
        })


def upgrade() -> None:
    _rewrite(use_new=True)


def downgrade() -> None:
    _rewrite(use_new=False)

"""Relabel M1/M6 100% band: 'Reference ...' -> 'Pristine ...'

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-15

The top (score 1.0) band for two mangrove indicators is renamed for
clearer user-facing wording:

  M1 (mangrove_canopy_cover)   'Reference condition'  -> 'Pristine condition'
  M6 (mangrove_wildlife_signs) 'Reference diversity'  -> 'Pristine diversity'

Only the label changes; criteria/meaning/sort_order/score are unchanged.
New seed deployments pick this up via project_indicators_seed.py;
existing staging/prod databases get this migration to catch up.
"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


# slug -> (score, new label, old label)
_LABELS = [
    ('mangrove_canopy_cover',  1.00, 'Pristine condition', 'Reference condition'),
    ('mangrove_wildlife_signs', 1.00, 'Pristine diversity', 'Reference diversity'),
]


def _rewrite(use_new: bool) -> None:
    """Update pi_indicator_bands.label for the score-1.0 band of each
    indicator. The join via pi_indicators handles the fact that
    pi_indicator_bands references indicator by id, not slug — and uses a
    tolerant float comparison on score."""
    bind = op.get_bind()
    stmt = sa.text(
        "UPDATE pi_indicator_bands AS b "
        "SET label = :label "
        "FROM pi_indicators AS i "
        "WHERE b.indicator_id = i.id "
        "  AND i.slug = :slug "
        "  AND ABS(b.score - :score) < 1e-6"
    )
    for slug, score, new_label, old_label in _LABELS:
        bind.execute(stmt, {
            'label': new_label if use_new else old_label,
            'slug': slug,
            'score': score,
        })


def upgrade() -> None:
    _rewrite(use_new=True)


def downgrade() -> None:
    _rewrite(use_new=False)

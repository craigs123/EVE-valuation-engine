"""Sync the HD (Human Disturbance Pressure) indicator content.

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-16

HD is refactored into a universal cross-cutting indicator. Its on-screen
content is expanded: a card_description for the selection panel, a reworded
baseline question, a fuller why_matters, the six full scoring-band
descriptions, and ecosystem-scoped follow-up dropdown options.

Fresh installs get this from utils/project_indicators_seed.py. Existing
staging/prod databases get this migration to catch up. The new values are
read straight from the seed so the two never drift; on a fresh DB the
HD row does not exist yet, so the UPDATEs simply match zero rows.
"""
from alembic import op
import sqlalchemy as sa


revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def _hd_seed() -> dict:
    """The HD indicator definition from the seed (single source of truth)."""
    from utils.project_indicators_seed import DEFAULT_INDICATORS
    return next(i for i in DEFAULT_INDICATORS if i['code'] == 'HD')


def upgrade() -> None:
    hd = _hd_seed()
    bind = op.get_bind()

    # Indicator-level text.
    bind.execute(
        sa.text(
            "UPDATE pi_indicators SET "
            "card_description = :card, "
            "baseline_question = :bq, "
            "why_matters = :why "
            "WHERE slug = 'human_disturbance_pressure'"
        ),
        {
            'card': hd['card_description'],
            'bq': hd['baseline_question'],
            'why': hd['why_matters'],
        },
    )

    # Scoring-band criteria, matched by score.
    band_stmt = sa.text(
        "UPDATE pi_indicator_bands AS b SET criteria = :criteria "
        "FROM pi_indicators AS i "
        "WHERE b.indicator_id = i.id "
        "  AND i.slug = 'human_disturbance_pressure' "
        "  AND ABS(b.score - :score) < 1e-6"
    )
    for band in hd['bands']:
        bind.execute(band_stmt, {
            'criteria': band['criteria'],
            'score': band['score'],
        })

    # Follow-up question text + ecosystem-scoped options (JSON), by slug.
    fu_stmt = sa.text(
        "UPDATE pi_indicator_followups AS f SET "
        "options = :options, question_text = :q "
        "FROM pi_indicators AS i "
        "WHERE f.indicator_id = i.id "
        "  AND i.slug = 'human_disturbance_pressure' "
        "  AND f.slug = :fslug"
    ).bindparams(sa.bindparam('options', type_=sa.JSON))
    for fu in hd['followups']:
        bind.execute(fu_stmt, {
            'options': fu['options'],
            'q': fu['question_text'],
            'fslug': fu['slug'],
        })


def downgrade() -> None:
    # Content-only migration — the previous HD copy is not restored. The
    # schema is unchanged, so a downgrade is a no-op.
    pass

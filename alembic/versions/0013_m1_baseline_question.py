"""Reword the M1 (mangrove_canopy_cover) baseline question.

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-16

The M1 baseline question is reworded to match the M1 scoring-intro line
shown in the response panel:

  old: "Looking straight up from inside your restoration site, what
        percentage of the sky is blocked by mangrove leaves and branches?"
  new: "Estimate how complete and healthy your restoration site's canopy
        looks compared to a reference mangrove (Full instructions below)."

Fresh installs get the new text via project_indicators_seed.py; existing
staging/prod databases get this migration to catch up.
"""
from alembic import op
import sqlalchemy as sa


revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


_OLD = (
    "Looking straight up from inside your restoration site, what percentage "
    "of the sky is blocked by mangrove leaves and branches?"
)
_NEW = (
    "Estimate how complete and healthy your restoration site's canopy "
    "looks compared to a reference mangrove (Full instructions below)."
)


def _set(text: str) -> None:
    op.get_bind().execute(
        sa.text(
            "UPDATE pi_indicators SET baseline_question = :q "
            "WHERE slug = 'mangrove_canopy_cover'"
        ),
        {'q': text},
    )


def upgrade() -> None:
    _set(_NEW)


def downgrade() -> None:
    _set(_OLD)

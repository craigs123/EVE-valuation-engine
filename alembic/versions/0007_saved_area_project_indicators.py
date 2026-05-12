"""Persist project-indicator state on saved areas

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-12

Adds saved_areas.project_indicators (JSON, nullable) so the user's
indicator-multiplier configuration travels with each saved area:

  - which project ecosystem they picked
  - which indicators they committed to
  - their baseline + target responses (score + is_custom)
  - the assessment-level Baseline / Target dates

Stored as JSON so the schema is forward-compatible with new fields
(extra indicator types, additional date metadata, notes, …) without
further migrations. Nullable so existing rows are unaffected.
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'saved_areas',
        sa.Column('project_indicators', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('saved_areas', 'project_indicators')

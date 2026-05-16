"""Multi-project-type scaffolding columns.

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-16

Adds two columns that let the project-indicator taxonomy scale beyond the
single seeded Mangrove project type without further schema changes:

  * pi_project_types.ecosystem_type — the EVE ecosystem display name a
    project type serves (e.g. 'Mangroves'). Drives the ecosystem ->
    project-type mapping that gates the 'Use project-specific indicators'
    checkbox. Backfilled to 'Mangroves' for the existing mangrove_restoration
    project type.
  * pi_indicators.card_description — short one-line description shown in the
    indicator-selection panel card. Left NULL here; populated by the seed /
    a later content migration.

Fresh installs pick both up via project_indicators_seed.py; existing
staging/prod databases get this migration to catch up.
"""
from alembic import op
import sqlalchemy as sa


revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'pi_project_types',
        sa.Column('ecosystem_type', sa.String(64), nullable=True),
    )
    op.add_column(
        'pi_indicators',
        sa.Column('card_description', sa.Text(), nullable=True),
    )
    # Backfill the existing mangrove project type so the checkbox gating
    # keeps working for databases seeded before this migration.
    op.get_bind().execute(sa.text(
        "UPDATE pi_project_types SET ecosystem_type = 'Mangroves' "
        "WHERE slug = 'mangrove_restoration'"
    ))


def downgrade() -> None:
    op.drop_column('pi_indicators', 'card_description')
    op.drop_column('pi_project_types', 'ecosystem_type')

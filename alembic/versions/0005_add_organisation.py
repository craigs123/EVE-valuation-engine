"""Add organisation field to users

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-11

Adds users.organisation (String 255, nullable). New signups will populate it
via the registration form (UI-enforced as required). Pre-existing rows stay
NULL — there's no sensible backfill so admins can fill in case-by-case if
they ever need to.
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('organisation', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'organisation')

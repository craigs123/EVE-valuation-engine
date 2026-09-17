"""Add users.last_login_at

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-17

Records when each account last signed in, so the admin panel can show who
is actually using EVE rather than only who registered. Pre-existing rows
stay NULL and the panel renders them as "Never" — there is no backfill,
because nothing in the schema records historical sign-ins.
"""
from alembic import op
import sqlalchemy as sa

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_login_at')

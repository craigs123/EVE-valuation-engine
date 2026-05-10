"""Add account-lifecycle status and verification reminder timestamp

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-11

Adds:
- users.status         enum-like text column: 'Pending' | 'Active' | 'Removed'
- users.verification_reminder_sent_at  DateTime (nullable)

Backfill: rows with email_verified=True become 'Active'; otherwise 'Pending'.
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('status', sa.String(16), nullable=False, server_default='Pending'),
    )
    op.add_column(
        'users',
        sa.Column('verification_reminder_sent_at', sa.DateTime(), nullable=True),
    )
    # Backfill: anyone already verified is Active.
    op.execute("UPDATE users SET status = 'Active' WHERE email_verified = true")
    op.create_index('ix_users_status', 'users', ['status'])


def downgrade() -> None:
    op.drop_index('ix_users_status', table_name='users')
    op.drop_column('users', 'verification_reminder_sent_at')
    op.drop_column('users', 'status')

"""Add email verification and password reset fields to users table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('verification_token_expiry', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('reset_token', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))
    op.create_index('ix_users_verification_token', 'users', ['verification_token'])
    op.create_index('ix_users_reset_token', 'users', ['reset_token'])


def downgrade() -> None:
    op.drop_index('ix_users_reset_token', table_name='users')
    op.drop_index('ix_users_verification_token', table_name='users')
    op.drop_column('users', 'reset_token_expiry')
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'verification_token_expiry')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')

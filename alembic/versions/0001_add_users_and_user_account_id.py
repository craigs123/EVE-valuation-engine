"""Add users table and user_account_id columns to existing tables

Revision ID: 0001
Revises:
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0001'
down_revision = '0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users table ---
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # --- ecosystem_analyses ---
    op.add_column(
        'ecosystem_analyses',
        sa.Column('user_account_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_ecosystem_analyses_user_account_id', 'ecosystem_analyses', ['user_account_id'])

    # --- saved_areas ---
    op.add_column(
        'saved_areas',
        sa.Column('user_account_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_saved_areas_user_account_id', 'saved_areas', ['user_account_id'])

    # --- natural_capital_baselines ---
    op.add_column(
        'natural_capital_baselines',
        sa.Column('user_account_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_natural_capital_baselines_user_account_id', 'natural_capital_baselines', ['user_account_id'])

    # --- natural_capital_trends ---
    op.add_column(
        'natural_capital_trends',
        sa.Column('user_account_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_natural_capital_trends_user_account_id', 'natural_capital_trends', ['user_account_id'])


def downgrade() -> None:
    op.drop_index('ix_natural_capital_trends_user_account_id', table_name='natural_capital_trends')
    op.drop_column('natural_capital_trends', 'user_account_id')

    op.drop_index('ix_natural_capital_baselines_user_account_id', table_name='natural_capital_baselines')
    op.drop_column('natural_capital_baselines', 'user_account_id')

    op.drop_index('ix_saved_areas_user_account_id', table_name='saved_areas')
    op.drop_column('saved_areas', 'user_account_id')

    op.drop_index('ix_ecosystem_analyses_user_account_id', table_name='ecosystem_analyses')
    op.drop_column('ecosystem_analyses', 'user_account_id')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

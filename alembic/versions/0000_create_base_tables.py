"""Create all base tables (initial schema for fresh databases)

Revision ID: 0000
Revises:
Create Date: 2026-05-04

This migration creates the full base schema.  It runs before 0001 which adds
user_account_id columns.  On the original Neon database these tables already
exist — stamp with 'alembic stamp 0000' to mark them as in place without
running the DDL.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ecosystem_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_session_id', sa.String(255), nullable=True),
        sa.Column('area_name', sa.String(255), nullable=True),
        sa.Column('coordinates', sa.JSON(), nullable=False),
        sa.Column('area_hectares', sa.Float(), nullable=False),
        sa.Column('ecosystem_type', sa.String(255), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=False),
        sa.Column('value_per_hectare', sa.Float(), nullable=False),
        sa.Column('analysis_results', sa.JSON(), nullable=False),
        sa.Column('sustainability_responses', sa.JSON(), nullable=True),
        sa.Column('sampling_points', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('data_source', sa.String(255), nullable=False, server_default='ESVD'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_ecosystem_analyses_user_session_id', 'ecosystem_analyses', ['user_session_id'])
    op.create_index('ix_ecosystem_analyses_created_at', 'ecosystem_analyses', ['created_at'])

    op.create_table(
        'saved_areas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_session_id', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('coordinates', sa.JSON(), nullable=False),
        sa.Column('area_hectares', sa.Float(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_saved_areas_user_session_id', 'saved_areas', ['user_session_id'])

    op.create_table(
        'analysis_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('area_id', UUID(as_uuid=True), nullable=True),
        sa.Column('analysis_date', sa.DateTime(), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=False),
        sa.Column('ecosystem_composition', sa.JSON(), nullable=True),
        sa.Column('environmental_factors', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'natural_capital_baselines',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('area_id', UUID(as_uuid=True), nullable=True),
        sa.Column('user_session_id', sa.String(255), nullable=True),
        sa.Column('baseline_date', sa.DateTime(), nullable=False),
        sa.Column('ecosystem_type', sa.String(255), nullable=False),
        sa.Column('total_baseline_value', sa.Float(), nullable=False),
        sa.Column('provisioning_baseline', sa.Float(), nullable=False, server_default='0'),
        sa.Column('regulating_baseline', sa.Float(), nullable=False, server_default='0'),
        sa.Column('cultural_baseline', sa.Float(), nullable=False, server_default='0'),
        sa.Column('supporting_baseline', sa.Float(), nullable=False, server_default='0'),
        sa.Column('vegetation_health_index', sa.Float(), nullable=True),
        sa.Column('biodiversity_index', sa.Float(), nullable=True),
        sa.Column('carbon_stock_estimate', sa.Float(), nullable=True),
        sa.Column('water_regulation_capacity', sa.Float(), nullable=True),
        sa.Column('soil_quality_index', sa.Float(), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('satellite_data_quality', sa.String(255), nullable=True),
        sa.Column('weather_conditions', sa.JSON(), nullable=True),
        sa.Column('seasonal_adjustment', sa.Float(), nullable=True),
        sa.Column('coordinates', sa.JSON(), nullable=False),
        sa.Column('area_hectares', sa.Float(), nullable=False),
        sa.Column('sampling_points', sa.Integer(), nullable=False),
        sa.Column('source_coefficients', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'natural_capital_trends',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('baseline_id', UUID(as_uuid=True), nullable=False),
        sa.Column('area_id', UUID(as_uuid=True), nullable=True),
        sa.Column('measurement_date', sa.DateTime(), nullable=False),
        sa.Column('total_value_change', sa.Float(), nullable=False),
        sa.Column('percent_change', sa.Float(), nullable=False),
        sa.Column('provisioning_change', sa.Float(), nullable=False, server_default='0'),
        sa.Column('regulating_change', sa.Float(), nullable=False, server_default='0'),
        sa.Column('cultural_change', sa.Float(), nullable=False, server_default='0'),
        sa.Column('supporting_change', sa.Float(), nullable=False, server_default='0'),
        sa.Column('vegetation_change', sa.Float(), nullable=True),
        sa.Column('biodiversity_change', sa.Float(), nullable=True),
        sa.Column('carbon_change', sa.Float(), nullable=True),
        sa.Column('trend_direction', sa.String(50), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('driving_factors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('natural_capital_trends')
    op.drop_table('natural_capital_baselines')
    op.drop_table('analysis_history')
    op.drop_index('ix_saved_areas_user_session_id', table_name='saved_areas')
    op.drop_table('saved_areas')
    op.drop_index('ix_ecosystem_analyses_created_at', table_name='ecosystem_analyses')
    op.drop_index('ix_ecosystem_analyses_user_session_id', table_name='ecosystem_analyses')
    op.drop_table('ecosystem_analyses')

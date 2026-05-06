"""Add project-typed indicator tables and supporting columns

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-06

Adds the project-indicator (pi_*) taxonomy and response tables, plus:
- users.is_admin (preps for v2 admin UI)
- ecosystem_analyses.project_type_id FK
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users.is_admin
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # pi_project_types
    op.create_table(
        'pi_project_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('slug', sa.String(64), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(16), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # pi_indicators
    op.create_table(
        'pi_indicators',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('slug', sa.String(64), nullable=False, unique=True),
        sa.Column('code', sa.String(8), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('commitment_question', sa.Text(), nullable=False),
        sa.Column('prospectus_scope_statement', sa.Text(), nullable=False),
        sa.Column('baseline_question', sa.Text(), nullable=False),
        sa.Column('why_matters', sa.Text(), nullable=True),
        sa.Column('field_method', sa.Text(), nullable=True),
        sa.Column('remote_sensing_alternative', sa.Text(), nullable=True),
        sa.Column('sources', sa.Text(), nullable=True),
        sa.Column('applicable_ecosystems', sa.JSON(), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mapping_kind', sa.String(32), nullable=False, server_default='band_lookup'),
        sa.Column('mapping_params', sa.JSON(), nullable=False),
        sa.Column('service_weights', sa.JSON(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # pi_indicator_bands
    op.create_table(
        'pi_indicator_bands',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('indicator_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_indicators.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('label', sa.String(64), nullable=False),
        sa.Column('criteria', sa.Text(), nullable=False),
        sa.Column('meaning', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
    )
    op.create_index('ix_pi_indicator_bands_indicator_id', 'pi_indicator_bands', ['indicator_id'])
    op.create_index('ix_pi_indicator_bands_indicator_score', 'pi_indicator_bands',
                    ['indicator_id', 'score'], unique=True)

    # pi_indicator_followups
    op.create_table(
        'pi_indicator_followups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('indicator_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_indicators.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('input_kind', sa.String(16), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('trigger_max_score', sa.Float(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_pi_indicator_followups_indicator_slug', 'pi_indicator_followups',
                    ['indicator_id', 'slug'], unique=True)

    # pi_project_type_indicators
    op.create_table(
        'pi_project_type_indicators',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('project_type_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_project_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('indicator_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_indicators.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_recommended', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('weight_override', sa.Float(), nullable=True),
    )
    op.create_index('ix_pi_project_type_indicators_unique', 'pi_project_type_indicators',
                    ['project_type_id', 'indicator_id'], unique=True)

    # ecosystem_analyses.project_type_id (after pi_project_types exists)
    op.add_column('ecosystem_analyses',
                  sa.Column('project_type_id', UUID(as_uuid=True),
                            sa.ForeignKey('pi_project_types.id'), nullable=True))

    # pi_analysis_responses (after both ecosystem_analyses and pi_* tables exist)
    op.create_table(
        'pi_analysis_responses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('analysis_id', UUID(as_uuid=True),
                  sa.ForeignKey('ecosystem_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_type_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_project_types.id'), nullable=False),
        sa.Column('indicator_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_indicators.id'), nullable=False),
        sa.Column('is_committed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('baseline_band_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_indicator_bands.id'), nullable=True),
        sa.Column('baseline_score', sa.Float(), nullable=True),
        sa.Column('baseline_year', sa.Integer(), nullable=True),
        sa.Column('target_band_id', UUID(as_uuid=True),
                  sa.ForeignKey('pi_indicator_bands.id'), nullable=True),
        sa.Column('target_score', sa.Float(), nullable=True),
        sa.Column('target_year', sa.Integer(), nullable=True),
        sa.Column('applies_to_ecosystem', sa.String(64), nullable=True),
        sa.Column('followup_responses', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_pi_analysis_responses_analysis_id', 'pi_analysis_responses', ['analysis_id'])
    op.create_index('ix_pi_analysis_responses_unique', 'pi_analysis_responses',
                    ['analysis_id', 'indicator_id', 'applies_to_ecosystem'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_pi_analysis_responses_unique', table_name='pi_analysis_responses')
    op.drop_index('ix_pi_analysis_responses_analysis_id', table_name='pi_analysis_responses')
    op.drop_table('pi_analysis_responses')

    op.drop_column('ecosystem_analyses', 'project_type_id')

    op.drop_index('ix_pi_project_type_indicators_unique', table_name='pi_project_type_indicators')
    op.drop_table('pi_project_type_indicators')

    op.drop_index('ix_pi_indicator_followups_indicator_slug', table_name='pi_indicator_followups')
    op.drop_table('pi_indicator_followups')

    op.drop_index('ix_pi_indicator_bands_indicator_score', table_name='pi_indicator_bands')
    op.drop_index('ix_pi_indicator_bands_indicator_id', table_name='pi_indicator_bands')
    op.drop_table('pi_indicator_bands')

    op.drop_table('pi_indicators')
    op.drop_table('pi_project_types')

    op.drop_column('users', 'is_admin')

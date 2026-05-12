"""Sub-service-specific indicator multipliers

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-11

Adds the schema needed for indicator-driven sub-service multipliers
that replace the uniform BBI multiplier when enabled per assessment:

- pi_analysis_responses.custom_score (Float, nullable): user-entered
  custom percentage stored as 0.0–1.0. NULL means the user picked a
  predefined band (existing baseline_band_id / baseline_score path).
  Calculations read `coalesce(custom_score, baseline_score)`.

- ecosystem_analyses.use_indicator_multipliers (Boolean, default FALSE):
  per-assessment flag. When TRUE, the calculation pipeline replaces
  the uniform BBI multiplier with sub-service-specific multipliers
  derived from indicator responses (with BBI used as a fallback for
  sub-services not covered by any selected indicator).

- computed_sub_service_multipliers (new table): the materialised
  output of the multiplier-computation step. One row per
  (analysis_id, teeb_sub_service_key). Regenerated whenever indicator
  responses change for an assessment. Stored — not derived on the
  fly — so the per-sub-service breakdown panel in the results UI
  can render without re-running the computation, and so an audit
  trail is preserved (contributing indicators / pcts / weights).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1a — custom percentage entry on indicator responses
    op.add_column(
        'pi_analysis_responses',
        sa.Column('custom_score', sa.Float(), nullable=True),
    )

    # 1b — per-assessment flag enabling indicator-driven multipliers
    op.add_column(
        'ecosystem_analyses',
        sa.Column(
            'use_indicator_multipliers',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # 1c — materialised multiplier table
    op.create_table(
        'computed_sub_service_multipliers',
        sa.Column('computation_id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'analysis_id',
            UUID(as_uuid=True),
            sa.ForeignKey('ecosystem_analyses.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('teeb_sub_service_key', sa.String(64), nullable=False),
        sa.Column('indicator_multiplier', sa.Float(), nullable=True),
        sa.Column('contributing_indicators', sa.JSON(), nullable=False),
        sa.Column('contributing_response_pcts', sa.JSON(), nullable=False),
        sa.Column('contributing_weights', sa.JSON(), nullable=False),
        sa.Column('hd_multiplier', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('final_multiplier', sa.Float(), nullable=False),
        sa.Column('fallback_to_bbi', sa.Boolean(), nullable=False),
        sa.Column('bbi_value_used', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            'analysis_id', 'teeb_sub_service_key',
            name='uq_computed_msm_analysis_subsvc',
        ),
    )
    op.create_index(
        'ix_computed_msm_analysis',
        'computed_sub_service_multipliers',
        ['analysis_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_computed_msm_analysis', table_name='computed_sub_service_multipliers')
    op.drop_table('computed_sub_service_multipliers')
    op.drop_column('ecosystem_analyses', 'use_indicator_multipliers')
    op.drop_column('pi_analysis_responses', 'custom_score')

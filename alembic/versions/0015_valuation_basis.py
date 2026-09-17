"""Record the valuation basis: user choice, analyses, baselines

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-17

Three columns, all nullable, all for the same reason: a total is meaningless
without knowing which ESVD statistic produced it. The four bases differ by up
to two orders of magnitude for the same area.

* users.valuation_basis — the user's own choice. NULL means they have never
  been asked, which is what triggers the first-run prompt. There is no
  backfill: everyone gets prompted once, which is the only way existing users
  discover the evidence-guarded basis exists.

* ecosystem_analyses.coefficient_statistic — already stamped inside the
  analysis_results JSON since Aug 2026, so this one CAN be backfilled, and is
  below. Promoted to a column so the history list can show it without loading
  every blob.

* natural_capital_baselines.coefficient_statistic — never recorded anywhere,
  so it cannot be backfilled and stays NULL for existing rows. That is the
  point: NULL is read as "unknown", and comparing a fresh analysis against an
  unknown-basis baseline is refused rather than silently reported as ecological
  change. A Rivers and Lakes baseline differenced across bases would show a
  98% collapse that never happened.

NULL is never treated as "the current default" — an unstamped row pre-dates
the Valuation Basis setting entirely, and also pre-dates the 2026-08-10
coefficient replacement, so it is doubly incomparable.
"""
from alembic import op
import sqlalchemy as sa

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('valuation_basis', sa.String(32), nullable=True))
    op.add_column('ecosystem_analyses',
                  sa.Column('coefficient_statistic', sa.String(32), nullable=True))
    op.add_column('natural_capital_baselines',
                  sa.Column('coefficient_statistic', sa.String(32), nullable=True))

    # Lift the basis out of the JSON it has been stamped into since Aug 2026.
    # Rows older than that have no key and are left NULL (= unknown), which is
    # correct: they were costed on the pre-replacement coefficient tables.
    #
    # ->> yields NULL both for a missing key and for a JSON null, so the one
    # IS NOT NULL test covers both cases. Deliberately NOT using the jsonb
    # containment operator ?, which only exists for jsonb (this column is
    # json) and which SQLAlchemy can mistake for a bind parameter.
    op.execute("""
        UPDATE ecosystem_analyses
           SET coefficient_statistic = analysis_results->>'coefficient_statistic'
         WHERE analysis_results->>'coefficient_statistic' IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_column('natural_capital_baselines', 'coefficient_statistic')
    op.drop_column('ecosystem_analyses', 'coefficient_statistic')
    op.drop_column('users', 'valuation_basis')

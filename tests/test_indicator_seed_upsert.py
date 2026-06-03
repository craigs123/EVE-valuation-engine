"""
Tests for the idempotent upsert behaviour of seed_project_indicators().

The seed used to bail out entirely once any project type existed, so new
indicator sets added to the seed file never reached an already-seeded
database. It now upserts by slug. These tests verify:

  * a fresh seed populates the expected taxonomy,
  * re-seeding is idempotent (no duplicate rows),
  * adding a new indicator/assignment to the definitions lands on re-seed,
  * editing an existing band updates it in place (no duplicate),
  * user-data rows (pi_analysis_responses) are never touched by a re-seed.

The DB is in-memory SQLite holding just the pi_* tables, created from the
real models. No external services. Runnable without pytest:
    python tests/test_indicator_seed_upsert.py
"""

import copy
import os
import sys
import uuid

# database.py builds its engine at import time and requires DATABASE_URL.
# A dummy postgres URL is enough — create_engine() does not connect until a
# session is used, and we bind our own SQLite engine for the tables below.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost:5432/dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from database import (
    ProjectType, Indicator, IndicatorBand, IndicatorFollowup,
    ProjectTypeIndicator, AnalysisResponse,
)
import utils.project_indicators_seed as seed


# ── harness ─────────────────────────────────────────────────────────────────

_PI_TABLES = (
    ProjectType.__table__,
    Indicator.__table__,
    IndicatorBand.__table__,
    IndicatorFollowup.__table__,
    ProjectTypeIndicator.__table__,
    AnalysisResponse.__table__,
)


def _session():
    """Fresh in-memory SQLite DB with the pi_* tables, returning a session."""
    eng = sa.create_engine("sqlite://")
    for t in _PI_TABLES:
        t.create(eng)
    return sessionmaker(bind=eng)()


def _counts(s):
    return (
        s.query(ProjectType).count(),
        s.query(Indicator).count(),
        s.query(IndicatorBand).count(),
        s.query(IndicatorFollowup).count(),
        s.query(ProjectTypeIndicator).count(),
    )


# ── tests ───────────────────────────────────────────────────────────────────

def test_fresh_seed_populates_expected_taxonomy():
    s = _session()
    ran = seed.seed_project_indicators(s)
    assert ran is True
    # Mangrove project type present.
    pt = s.query(ProjectType).filter_by(slug="mangrove_restoration").first()
    assert pt is not None and pt.ecosystem_type == "Mangroves"
    # All defined indicators inserted.
    assert s.query(Indicator).count() == len(seed.DEFAULT_INDICATORS)
    # HD (universal) attached to the mangrove project type.
    hd = s.query(Indicator).filter_by(slug="human_disturbance_pressure").first()
    assert hd is not None
    assert s.query(ProjectTypeIndicator).filter_by(
        project_type_id=pt.id, indicator_id=hd.id
    ).count() == 1
    # M1 has its bands.
    m1 = s.query(Indicator).filter_by(code="M1").first()
    assert s.query(IndicatorBand).filter_by(indicator_id=m1.id).count() > 0


def test_reseed_is_idempotent():
    s = _session()
    seed.seed_project_indicators(s)
    before = _counts(s)
    seed.seed_project_indicators(s)
    s.expire_all()
    after = _counts(s)
    assert before == after, (before, after)


def test_reseed_adds_new_indicator_and_assignment():
    s = _session()
    seed.seed_project_indicators(s)
    base_ind = s.query(Indicator).count()

    saved_ind = copy.deepcopy(seed.DEFAULT_INDICATORS)
    saved_join = copy.deepcopy(seed.DEFAULT_PROJECT_TYPE_INDICATORS)
    try:
        seed.DEFAULT_INDICATORS.append({
            "slug": "test_new_indicator", "code": "TN1", "name": "Test New",
            "commitment_question": "q", "prospectus_scope_statement": "s",
            "baseline_question": "b",
            "service_weights": {"habitat_for_species": "primary"},
            "bands": [
                {"score": 0.5, "label": "mid", "criteria": "c", "sort_order": 1},
            ],
        })
        seed.DEFAULT_PROJECT_TYPE_INDICATORS.append({
            "project_type": "mangrove_restoration",
            "indicator": "test_new_indicator", "sort_order": 50,
        })
        seed.seed_project_indicators(s)
        s.expire_all()

        assert s.query(Indicator).count() == base_ind + 1
        new = s.query(Indicator).filter_by(slug="test_new_indicator").first()
        assert new is not None
        pt = s.query(ProjectType).filter_by(slug="mangrove_restoration").first()
        assert s.query(ProjectTypeIndicator).filter_by(
            project_type_id=pt.id, indicator_id=new.id
        ).count() == 1
    finally:
        seed.DEFAULT_INDICATORS[:] = saved_ind
        seed.DEFAULT_PROJECT_TYPE_INDICATORS[:] = saved_join


def test_reseed_updates_changed_band_in_place():
    s = _session()
    seed.seed_project_indicators(s)
    m1 = s.query(Indicator).filter_by(code="M1").first()
    band_count = s.query(IndicatorBand).filter_by(indicator_id=m1.id).count()
    a_band = (
        s.query(IndicatorBand)
        .filter_by(indicator_id=m1.id)
        .order_by(IndicatorBand.sort_order)
        .first()
    )
    target_score = a_band.score

    saved = copy.deepcopy(seed.DEFAULT_INDICATORS)
    try:
        for ind in seed.DEFAULT_INDICATORS:
            if ind["code"] == "M1":
                for b in ind["bands"]:
                    if b["score"] == target_score:
                        b["label"] = "CHANGED LABEL"
        seed.seed_project_indicators(s)
        s.expire_all()

        updated = s.query(IndicatorBand).filter_by(
            indicator_id=m1.id, score=target_score
        ).first()
        assert updated.label == "CHANGED LABEL"
        # No duplicate band created.
        assert s.query(IndicatorBand).filter_by(indicator_id=m1.id).count() == band_count
    finally:
        seed.DEFAULT_INDICATORS[:] = saved


def test_reseed_preserves_user_response_rows():
    s = _session()
    seed.seed_project_indicators(s)
    resp = AnalysisResponse(
        analysis_id=uuid.uuid4(),
        project_type_id=uuid.uuid4(),
        indicator_id=uuid.uuid4(),
        is_committed=True,
        baseline_score=0.4,
        notes="keepme",
    )
    s.add(resp)
    s.commit()
    rid = resp.id

    seed.seed_project_indicators(s)
    s.expire_all()

    got = s.query(AnalysisResponse).filter_by(id=rid).first()
    assert got is not None, "user response row must survive a re-seed"
    assert got.notes == "keepme" and got.baseline_score == 0.4


# ── runner ──────────────────────────────────────────────────────────────────

_TESTS = [
    ("fresh seed populates taxonomy", test_fresh_seed_populates_expected_taxonomy),
    ("re-seed is idempotent", test_reseed_is_idempotent),
    ("re-seed adds new indicator + assignment", test_reseed_adds_new_indicator_and_assignment),
    ("re-seed updates changed band in place", test_reseed_updates_changed_band_in_place),
    ("re-seed preserves user response rows", test_reseed_preserves_user_response_rows),
]


def main():
    print("Running indicator seed upsert tests\n")
    results = []
    for name, fn in _TESTS:
        try:
            fn()
            results.append(True)
            print(f"  PASS  {name}")
        except AssertionError as e:
            results.append(False)
            print(f"  FAIL  {name}: {e}")
        except Exception as e:
            import traceback
            results.append(False)
            print(f"  ERROR {name}: {e}")
            traceback.print_exc()
    passed = sum(results)
    print(f"\n{passed} passed, {len(results) - passed} failed, {len(results)} total")
    return 1 if passed != len(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

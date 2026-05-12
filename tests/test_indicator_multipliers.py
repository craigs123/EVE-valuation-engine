"""Unit tests for the indicator-driven sub-service multiplier engine.

Tests target the pure-computation core ``_compute_pure()`` so no DB is
required. Covers the 13 scenarios from the spec at
``C:\\Users\\craig\\.claude\\plans\\context-eve-atomic-beacon.md``
Step 6 (originally from the user's prompt Section 6).

Run with: ``python -m pytest tests/test_indicator_multipliers.py -v``
or stand-alone: ``python tests/test_indicator_multipliers.py``
"""
from __future__ import annotations

import math
import os
import sys

# Path setup so 'from utils...' works whether invoked from repo root or here
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.indicator_multipliers import _compute_pure  # noqa: E402
from utils.teeb_slug_map import INDICATOR_FLOOR  # noqa: E402


TOL = 1e-6
HD_SLUG = 'hd'


def _resp(slug: str, score: float | None, service_weights: dict, committed: bool = True, mandatory: bool = False) -> dict:
    """Convenience: build a get_responses-shape dict for a single indicator."""
    return {
        'indicator_slug': slug,
        'is_committed': committed,
        'is_mandatory': mandatory,
        'effective_score': score,
        'service_weights': service_weights,
    }


def _find(rows: list[dict], key: str) -> dict:
    return next(r for r in rows if r['teeb_sub_service_key'] == key)


# ── Scenario 2: single indicator, single sub-service ─────────────────────────
def test_2_single_indicator_single_subservice():
    """M1 maps to raw_materials PRIMARY (1.0); response = 75 → final 0.75."""
    rows = _compute_pure(
        sub_service_keys=['raw_materials', 'food'],
        indicator_responses=[
            _resp('m1', 0.75, {'raw_materials': 'primary'}),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    rm = _find(rows, 'raw_materials')
    assert rm['fallback_to_bbi'] is False
    assert abs(rm['indicator_multiplier'] - 0.75) < TOL
    assert abs(rm['hd_multiplier'] - 1.0) < TOL
    assert abs(rm['final_multiplier'] - 0.75) < TOL
    assert rm['contributing_indicators'] == ['m1']
    assert rm['contributing_response_pcts'] == [75]
    assert rm['contributing_weights'] == [1.0]
    # 'food' has no indicator → BBI fallback
    food = _find(rows, 'food')
    assert food['fallback_to_bbi'] is True
    assert abs(food['final_multiplier'] - 0.5) < TOL


# ── Scenario 3: two indicators, same sub-service, both PRIMARY ───────────────
def test_3_two_primary_average():
    """M1 = 75 P, M4 = 50 P on habitat → 0.625 average."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.75, {'habitat_for_species': 'primary'}),
            _resp('m4', 0.50, {'habitat_for_species': 'primary'}),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    assert abs(r['indicator_multiplier'] - 0.625) < TOL
    assert abs(r['final_multiplier'] - 0.625) < TOL
    assert sorted(r['contributing_indicators']) == ['m1', 'm4']


# ── Scenario 4: mixed PRIMARY + SECONDARY ────────────────────────────────────
def test_4_primary_plus_secondary():
    """M1 = 80 P (1.0), M2 = 60 S (0.5) → (80*1 + 60*0.5)/(1.5) /100 ≈ 0.7333."""
    rows = _compute_pure(
        sub_service_keys=['raw_materials'],
        indicator_responses=[
            _resp('m1', 0.80, {'raw_materials': 'primary'}),
            _resp('m2', 0.60, {'raw_materials': 'secondary'}),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'raw_materials')
    expected = (0.80 * 1.0 + 0.60 * 0.5) / 1.5
    assert abs(r['indicator_multiplier'] - expected) < TOL
    assert abs(r['final_multiplier'] - expected) < TOL


# ── Scenario 5: HD cross-cutting multiplier ──────────────────────────────────
def test_5_hd_cross_cutting():
    """M1 = 75 on habitat, HD = 50 → final = 0.75 × 0.50 = 0.375."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.75, {'habitat_for_species': 'primary'}),
            _resp(HD_SLUG, 0.50, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    assert abs(r['indicator_multiplier'] - 0.75) < TOL
    assert abs(r['hd_multiplier'] - 0.50) < TOL
    assert abs(r['final_multiplier'] - 0.375) < TOL


# ── Scenario 6: floor enforcement ────────────────────────────────────────────
def test_6_floor_applied_when_under_5pct():
    """M1 = 10 on habitat, HD = 10 → raw 0.01, floor → 0.05."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.10, {'habitat_for_species': 'primary'}),
            _resp(HD_SLUG, 0.10, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    raw = 0.10 * 0.10
    assert abs(r['final_multiplier'] - max(raw, INDICATOR_FLOOR)) < TOL
    assert abs(r['final_multiplier'] - 0.05) < TOL


# ── Scenario 7: fallback to BBI when no indicator covers a sub-service ──────
def test_7_fallback_to_bbi_no_hd_layered():
    """No selected indicator maps to medicinal_resources → BBI fallback.
    HD is NOT applied on top of BBI."""
    rows = _compute_pure(
        sub_service_keys=['medicinal_resources'],
        indicator_responses=[
            _resp('m1', 0.75, {'raw_materials': 'primary'}),  # doesn't map to medicinal
            _resp(HD_SLUG, 0.30, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.8,
    )
    r = _find(rows, 'medicinal_resources')
    assert r['fallback_to_bbi'] is True
    assert r['indicator_multiplier'] is None
    assert abs(r['final_multiplier'] - 0.8) < TOL  # raw BBI, NOT 0.8 × 0.30
    assert abs(r['bbi_value_used'] - 0.8) < TOL
    assert abs(r['hd_multiplier'] - 0.30) < TOL  # stored but not applied


# ── Scenario 8: unanswered indicator excluded from average ──────────────────
def test_8_unanswered_indicator_excluded():
    """M1 selected but no response (effective_score=None); M4 = 60 PRIMARY.
    M1 must be excluded entirely — NOT treated as 0."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', None, {'habitat_for_species': 'primary'}),
            _resp('m4', 0.60, {'habitat_for_species': 'primary'}),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    assert r['contributing_indicators'] == ['m4']
    assert abs(r['indicator_multiplier'] - 0.60) < TOL
    assert abs(r['final_multiplier'] - 0.60) < TOL


# ── Scenario 9: no HD response → multiplier defaults to 1.0 ─────────────────
def test_9_no_hd_response_defaults_to_one():
    """HD response missing entirely → hd_multiplier = 1.0, no penalty."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.75, {'habitat_for_species': 'primary'}),
            # HD row present but no response yet
            _resp(HD_SLUG, None, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    assert abs(r['hd_multiplier'] - 1.0) < TOL
    assert abs(r['final_multiplier'] - 0.75) < TOL


# ── Scenario 10: custom pct value (non-band) ────────────────────────────────
def test_10_custom_score_uses_effective_score():
    """Indicator response_pct = 68 (custom, not a standard band).
    Stored as effective_score = 0.68. No special handling required."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.68, {'habitat_for_species': 'primary'}),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    assert abs(r['indicator_multiplier'] - 0.68) < TOL
    assert abs(r['final_multiplier'] - 0.68) < TOL
    assert r['contributing_response_pcts'] == [68]


# ── Scenario 11: HD not applied on top of BBI ───────────────────────────────
def test_11_hd_not_applied_to_bbi_fallback():
    """Even with a strong HD penalty, BBI-fallback sub-services use BBI as-is."""
    rows = _compute_pure(
        sub_service_keys=['medicinal_resources'],
        indicator_responses=[
            _resp('m1', 0.75, {'raw_materials': 'primary'}),  # not medicinal
            _resp(HD_SLUG, 0.30, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.7,
    )
    r = _find(rows, 'medicinal_resources')
    assert r['fallback_to_bbi'] is True
    assert abs(r['final_multiplier'] - 0.7) < TOL  # NOT 0.7 × 0.30 = 0.21
    assert abs(r['hd_multiplier'] - 0.30) < TOL


# ── Scenario 13: full assessment — multiple indicators, mixed ───────────────
def test_13_full_assessment_habitat_aggregation():
    """M1 = 75, M4 = 60, M6 = 80 all PRIMARY on habitat; HD = 70.
    Expected: (75 + 60 + 80) / 3 / 100 = 0.7167, × 0.70 = 0.5017."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.75, {'habitat_for_species': 'primary'}),
            _resp('m4', 0.60, {'habitat_for_species': 'primary'}),
            _resp('m6', 0.80, {'habitat_for_species': 'primary'}),
            _resp(HD_SLUG, 0.70, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    ind = (0.75 + 0.60 + 0.80) / 3
    assert abs(r['indicator_multiplier'] - ind) < TOL
    assert abs(r['final_multiplier'] - ind * 0.70) < TOL


# ── Extra: strongest-weight rule when one indicator maps to >1 TEEB slug ────
def test_strongest_weight_when_indicator_double_maps_to_calc_key():
    """M1 has habitat_for_species PRIMARY AND genetic_diversity SECONDARY.
    Both TEEB slugs map to 'habitat' in TEEB_TO_CALC_KEY. The indicator must
    contribute only ONCE with the STRONGEST relationship (PRIMARY, w=1.0),
    not summed and not the weaker SECONDARY."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.80, {
                'habitat_for_species': 'primary',
                'genetic_diversity': 'secondary',
            }),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    # Single contribution with PRIMARY weight 1.0 → indicator_multiplier = 0.80
    assert r['contributing_indicators'] == ['m1']
    assert r['contributing_weights'] == [1.0]
    assert abs(r['indicator_multiplier'] - 0.80) < TOL


# ── Extra: uncommitted indicator excluded ────────────────────────────────────
def test_uncommitted_indicator_excluded():
    """An indicator with a recorded response but is_committed=False must
    not influence the calculation."""
    rows = _compute_pure(
        sub_service_keys=['habitat'],
        indicator_responses=[
            _resp('m1', 0.90, {'habitat_for_species': 'primary'}, committed=False),
            _resp('m4', 0.60, {'habitat_for_species': 'primary'}, committed=True),
            _resp(HD_SLUG, 1.00, {}, mandatory=True),
        ],
        hd_indicator_slug=HD_SLUG,
        bbi=0.5,
    )
    r = _find(rows, 'habitat')
    assert r['contributing_indicators'] == ['m4']
    assert abs(r['final_multiplier'] - 0.60) < TOL


# ── Convenience entry point: run as a script ────────────────────────────────
if __name__ == '__main__':
    tests = [
        test_2_single_indicator_single_subservice,
        test_3_two_primary_average,
        test_4_primary_plus_secondary,
        test_5_hd_cross_cutting,
        test_6_floor_applied_when_under_5pct,
        test_7_fallback_to_bbi_no_hd_layered,
        test_8_unanswered_indicator_excluded,
        test_9_no_hd_response_defaults_to_one,
        test_10_custom_score_uses_effective_score,
        test_11_hd_not_applied_to_bbi_fallback,
        test_13_full_assessment_habitat_aggregation,
        test_strongest_weight_when_indicator_double_maps_to_calc_key,
        test_uncommitted_indicator_excluded,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f'  [PASS] {t.__name__}')
            passed += 1
        except AssertionError as e:
            print(f'  [FAIL] {t.__name__}: {e}')
            failed += 1
        except Exception as e:
            print(f'  [ERROR] {t.__name__}: {type(e).__name__}: {e}')
            failed += 1
    print(f'\n{passed}/{passed + failed} tests passed.')
    sys.exit(0 if failed == 0 else 1)

"""
EVE calculation regression tests.
Run before major deployments (minor or major version bumps).
Uses expected totals derived from 'EVE test data.xlsx' Test cases tab.
"""
import math
import sys
sys.path.insert(0, '.')

from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients

calc = PrecomputedESVDCoefficients()
TOLERANCE = 0.001  # 0.1%

TEST_CASES = [
    # (label, ecosystem_type, area_ha, regional, intactness, urban_mult, expected_total)
    ("Desert (Sahara)",              "Desert",          1000,      0.64, 1.0, 1.0,  3_342_720),
    ("Urban (Mexico City)",          "Urban",           1000,      1.01, 1.0, 0.18, 401_080_979),
    ("Cropland (Illinois)",          "Agricultural",    1000,      2.5,  1.0, 1.0,  66_392_500),
    ("Tropical Forest (Brazil)",     "Tropical Forest", 1000,      0.75, 1.0, 1.0,  5_462_250),
    ("Temperate Forest (China)",     "Temperate Forest",1000,      0.95, 1.0, 1.0,  25_869_450),
    ("Boreal Forest (Canada)",       "Boreal Forest",   1000,      2.5,  1.0, 1.0,  30_775_000),
    ("Grassland (Kazakhstan)",       "Grassland",       1000,      2.5,  1.0, 1.0,  15_717_500),
    ("Shrubland (Australia)",        "Shrubland",       1000,      2.5,  1.0, 1.0,  4_497_500),
    ("Polar (Greenland)",            "Polar",           124407.3,  1.0,  1.0, 1.0,  13_400_283_504.9),
    ("Marine (Ocean)",               "Marine",          1000,      1.0,  1.0, 1.0,  71_987_000),
    ("Rivers and Lakes (Victoria)",  "Rivers and Lakes",1000,      0.44, 1.0, 1.0,  98_805_960),
    ("Coastal (Italy)",              "Coastal",         1000,      2.1,  1.0, 1.0,  157_909_500),
    ("Mangrove (Sundarbans, India)", "Mangroves",       1000,      0.51, 1.0, 1.0,  15_764_610),
]

def run_mixed_test():
    """Mixed ecosystem: 77.8% Agricultural + 22.2% Grassland, 1000 ha, regional 2.5."""
    ag = calc.calculate_ecosystem_values("Agricultural", 1000, regional_factor_override=2.5)["total_value"]
    gr = calc.calculate_ecosystem_values("Grassland",    1000, regional_factor_override=2.5)["total_value"]
    actual = 0.778 * ag + 0.222 * gr
    expected = 55_142_650
    return "Mixed Ecosystem (Ag 77.8% / Grassland 22.2%)", actual, expected


# Baseline value for the Mangrove test area at 100% intactness, used as the
# anchor for the indicator-mode tests below. Pulled directly from TEST_CASES
# so any deliberate update to the baseline propagates.
_MANGROVE_BASELINE = next(t for t in TEST_CASES if t[0].startswith("Mangrove"))[-1]


def run_mangrove_flat_dict_test():
    """Mangroves with a flat per-sub-service dict of all-1.0 multipliers.

    Validates dict-mode of calculate_ecosystem_values: feeding {key: 1.0}
    for every mangrove sub-service must produce the same total as the
    scalar-1.0 baseline. Catches any unintended scaling in the dict-
    mode service loop.
    """
    mangrove_keys = list(calc.get_ecosystem_coefficients("mangroves").keys())
    flat = {k: 1.0 for k in mangrove_keys}
    result = calc.calculate_ecosystem_values(
        ecosystem_type="Mangroves",
        area_hectares=1000,
        regional_factor_override=0.51,
        ecosystem_intactness_multiplier=flat,
        urban_green_blue_multiplier=1.0,
    )
    return (
        "Mangrove + per-service dict (all 1.0)",
        result["total_value"],
        _MANGROVE_BASELINE,
    )


def run_mangrove_indicator_reference_test():
    """Mangroves with the project-specific indicator engine at 100% reference.

    Runs the same indicator multiplier pipeline the app uses (utils.indicator_multipliers._compute_pure)
    with every indicator committed and every response at score 1.0 (reference condition).
    Each sub-service ends up with final_multiplier = 1.0, so the total must
    match the scalar-1.0 baseline.

    Verifies end-to-end that turning the indicator framework on with full-
    reference answers does not perturb the valuation.
    """
    from utils.indicator_multipliers import _compute_pure
    from utils.project_indicators_seed import DEFAULT_INDICATORS

    responses = [
        {
            "indicator_slug": ind["slug"],
            "is_committed": True,
            "effective_score": 1.0,
            "service_weights": ind["service_weights"],
        }
        for ind in DEFAULT_INDICATORS
    ]
    mangrove_keys = list(calc.get_ecosystem_coefficients("mangroves").keys())
    rows = _compute_pure(
        sub_service_keys=mangrove_keys,
        indicator_responses=responses,
        hd_indicator_slug="human_disturbance_pressure",
        bbi=1.0,  # fallback for any sub-service with no indicator coverage
    )
    multiplier_dict = {r["teeb_sub_service_key"]: r["final_multiplier"] for r in rows}

    result = calc.calculate_ecosystem_values(
        ecosystem_type="Mangroves",
        area_hectares=1000,
        regional_factor_override=0.51,
        ecosystem_intactness_multiplier=multiplier_dict,
        urban_green_blue_multiplier=1.0,
    )
    return (
        "Mangrove + indicators (all 100% reference)",
        result["total_value"],
        _MANGROVE_BASELINE,
    )

def run_mangrove_partial_hd_test():
    """Mangroves with every ecological indicator at reference (100%) but HD
    at 50% (Moderate disturbance).

    HD is a cross-cutting pressure variable, applied as a sqrt multiplier on
    every sub-service — indicator-covered and BBI-fallback alike. With all
    other inputs at 1.0, each sub-service final_multiplier collapses to
    sqrt(0.50), so the total must equal the baseline x sqrt(0.50) — a
    ~29.3% reduction, matching the documented HD-50 effect.

    Locks down the full chain at a partial HD score: response ->
    _compute_pure -> calculate_ecosystem_values. A linear (non-sqrt) HD
    would give baseline x 0.50, and an HD that skipped BBI-fallback
    sub-services would give a smaller reduction — both fail this test.
    """
    from utils.indicator_multipliers import _compute_pure
    from utils.project_indicators_seed import DEFAULT_INDICATORS

    responses = [
        {
            "indicator_slug": ind["slug"],
            "is_committed": True,
            "effective_score": 0.50 if ind["code"] == "HD" else 1.0,
            "service_weights": ind["service_weights"],
        }
        for ind in DEFAULT_INDICATORS
    ]
    mangrove_keys = list(calc.get_ecosystem_coefficients("mangroves").keys())
    rows = _compute_pure(
        sub_service_keys=mangrove_keys,
        indicator_responses=responses,
        hd_indicator_slug="human_disturbance_pressure",
        bbi=1.0,  # fallback for any sub-service with no indicator coverage
    )
    multiplier_dict = {r["teeb_sub_service_key"]: r["final_multiplier"] for r in rows}

    result = calc.calculate_ecosystem_values(
        ecosystem_type="Mangroves",
        area_hectares=1000,
        regional_factor_override=0.51,
        ecosystem_intactness_multiplier=multiplier_dict,
        urban_green_blue_multiplier=1.0,
    )
    return (
        "Mangrove + indicators (HD 50%, rest 100% reference)",
        result["total_value"],
        _MANGROVE_BASELINE * math.sqrt(0.50),
    )


def run_tests():
    passed = 0
    failed = 0

    for label, eco, area, regional, intactness, urban, expected in TEST_CASES:
        result = calc.calculate_ecosystem_values(
            ecosystem_type=eco,
            area_hectares=area,
            regional_factor_override=regional,
            ecosystem_intactness_multiplier=intactness,
            urban_green_blue_multiplier=urban,
        )
        actual = result["total_value"]
        delta = abs(actual - expected) / expected if expected else 0
        status = "PASS" if delta <= TOLERANCE else "FAIL"
        print(f"  [{status}] {label}: ${actual:>20,.1f}  (expected ${expected:,.1f},  diff {delta:.4%})")
        if status == "PASS":
            passed += 1
        else:
            failed += 1

    for runner in (run_mixed_test, run_mangrove_flat_dict_test,
                   run_mangrove_indicator_reference_test,
                   run_mangrove_partial_hd_test):
        label, actual, expected = runner()
        delta = abs(actual - expected) / expected if expected else 0
        status = "PASS" if delta <= TOLERANCE else "FAIL"
        print(f"  [{status}] {label}: ${actual:>20,.1f}  (expected ${expected:,.1f},  diff {delta:.4%})")
        if status == "PASS":
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed.")
    return failed == 0

if __name__ == "__main__":
    print("EVE Calculation Regression Tests\n")
    ok = run_tests()
    sys.exit(0 if ok else 1)

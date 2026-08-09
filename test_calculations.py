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


def run_eroi_tests():
    """Flow-based EROI metric checks (utils.analysis_helpers.compute_eroi).

    EROI treats ecosystem-service values as annual flows: the uplift
    (target - baseline) is a perpetual annual flow, ramped linearly over the
    project duration and appraised over a discounted 30-year window, net of
    any ongoing maintenance cost that begins after the project ends.
    """
    from utils.analysis_helpers import compute_eroi

    checks = []  # (label, ok)

    def check(label, ok):
        checks.append((label, bool(ok)))

    # Exact arithmetic case: immediate uplift (no ramp), zero discount, no
    # maintenance. U = 60k/yr, C = 300k, H = 30 -> closed-form values.
    e = compute_eroi(100_000, 160_000, 300_000, duration_years=None,
                     discount_rate=0.0)
    check("EROI exact: PV = U x 30", abs(e['pv_benefits'] - 60_000 * 30) < 1e-6)
    check("EROI exact: BCR = 6.0", abs(e['bcr'] - 6.0) < 1e-9)
    check("EROI exact: NPV = 1.5M", abs(e['npv'] - 1_500_000) < 1e-6)
    check("EROI exact: yield = 20%/yr", abs(e['annual_yield'] - 0.20) < 1e-9)
    check("EROI exact: payback = 5.0 yr", abs(e['payback_years'] - 5.0) < 1e-9)
    check("EROI exact: IRR positive", e['irr'] is not None and e['irr'] > 0)

    # Discounted, ramped case — verify the internal identities hold.
    d = compute_eroi(100_000, 160_000, 300_000, duration_years=5,
                     discount_rate=0.035)
    check("EROI identity: pv_costs = pv_capital + pv_maintenance",
          abs(d['pv_costs'] - (d['pv_capital'] + d['pv_maintenance'])) < 1e-6)
    check("EROI identity: NPV = pv_benefits - pv_costs",
          abs(d['npv'] - (d['pv_benefits'] - d['pv_costs'])) < 1e-6)
    check("EROI identity: BCR = pv_benefits / pv_costs",
          abs(d['bcr'] - d['pv_benefits'] / d['pv_costs']) < 1e-9)
    check("EROI: discount+ramp cut PV below undiscounted immediate PV",
          d['pv_benefits'] < e['pv_benefits'])

    # Capital cost spread over the project duration: undiscounted, the spread
    # installments sum exactly to the capital cost; discounted, PV is lower.
    check("EROI capital: undiscounted PV of capital equals the cost",
          abs(e['pv_capital'] - 300_000) < 1e-6)
    z = compute_eroi(100_000, 160_000, 300_000, duration_years=5,
                     discount_rate=0.0)
    check("EROI capital: ramp-spread installments (undiscounted) sum to cost",
          abs(z['pv_capital'] - 300_000) < 1e-6)
    check("EROI capital: discounted PV of capital is below the nominal cost",
          0 < d['pv_capital'] < d['cost'])

    # Reversal buffer scales the uplift only; capital/maintenance untouched.
    nb = compute_eroi(100_000, 160_000, 300_000, duration_years=5,
                      discount_rate=0.035)                        # buffer 0
    bf = compute_eroi(100_000, 160_000, 300_000, duration_years=5,
                      discount_rate=0.035, reversal_buffer_pct=0.20)
    check("EROI buffer: gross uplift unchanged by the buffer",
          abs(bf['uplift_gross'] - nb['uplift_gross']) < 1e-9)
    check("EROI buffer: buffered uplift = gross x (1 - buffer)",
          abs(bf['uplift'] - bf['uplift_gross'] * 0.80) < 1e-6)
    check("EROI buffer: pv_benefits scales by (1 - buffer)",
          abs(bf['pv_benefits'] - nb['pv_benefits'] * 0.80) < 1e-6)
    check("EROI buffer: capital PV unaffected by the buffer",
          abs(bf['pv_capital'] - nb['pv_capital']) < 1e-6)
    check("EROI buffer: lowers BCR and NPV",
          bf['bcr'] < nb['bcr'] and bf['npv'] < nb['npv'])
    check("EROI buffer: 0% buffer reproduces the un-buffered result",
          abs(compute_eroi(100_000, 160_000, 300_000, duration_years=5,
                           discount_rate=0.035,
                           reversal_buffer_pct=0.0)['npv'] - nb['npv']) < 1e-9)

    # Counterfactual identity: with-project minus counterfactual == benefits.
    check("EROI counterfactual: pv_with_project - pv_counterfactual = pv_benefits",
          abs((bf['pv_with_project'] - bf['pv_counterfactual'])
              - bf['pv_benefits']) < 1e-6)

    # Maintenance: applied after the 5-yr ramp, reduces the return metrics.
    m = compute_eroi(100_000, 160_000, 300_000, duration_years=5,
                     discount_rate=0.035, maintenance_cost=10_000)
    exp_pv_m = sum(10_000 / (1.035 ** t) for t in range(6, 31))
    check("EROI maintenance: PV starts the year after the 5-yr ramp",
          abs(m['pv_maintenance'] - exp_pv_m) < 1e-6)
    check("EROI maintenance: NPV lower than no-maintenance", m['npv'] < d['npv'])
    check("EROI maintenance: net yield = (U - M) / C",
          abs(m['annual_yield'] - (60_000 - 10_000) / 300_000) < 1e-9)

    # Not-applicable cases return None.
    check("EROI None when no uplift",
          compute_eroi(160_000, 100_000, 300_000, 5, 0.035) is None)
    check("EROI None when cost <= 0",
          compute_eroi(100_000, 160_000, 0, 5, 0.035) is None)
    check("EROI None when target missing",
          compute_eroi(100_000, None, 300_000, 5, 0.035) is None)

    # --- Carbon revenue opportunity ---
    from utils.analysis_helpers import compute_carbon_revenue
    cr = compute_carbon_revenue(1330.0, 1.0, 190.0, 10.0, 30.0, 1000.0, 'Mangroves')
    check("Carbon: global value = regional / regional_factor",
          abs(cr['climate_reg_global'] - 1330.0) < 1e-6)
    check("Carbon: implied sequestration = global / SCC",
          abs(cr['implied_seq_ha_yr'] - 7.0) < 1e-9)
    check("Carbon: total sequestration = rate x area",
          abs(cr['implied_seq_total_yr'] - 7000.0) < 1e-6)
    check("Carbon: revenue range = total seq x price range",
          abs(cr['revenue_low'] - 70_000.0) < 1e-6
          and abs(cr['revenue_high'] - 210_000.0) < 1e-6)
    check("Carbon: in-range implied rate flags 'ok'", cr['consistency'] == 'ok')
    crr = compute_carbon_revenue(665.0, 0.5, 190.0, 10.0, 30.0, 1000.0, 'Mangroves')
    check("Carbon: regional factor reversed correctly",
          abs(crr['implied_seq_ha_yr'] - 7.0) < 1e-9)
    cw = compute_carbon_revenue(5700.0, 1.0, 190.0, 10.0, 30.0, 1000.0, 'Mangroves')
    check("Carbon: far-out implied rate flags 'warning'",
          cw['consistency'] == 'warning')
    cn = compute_carbon_revenue(1330.0, 1.0, 190.0, 10.0, 30.0, 1000.0, 'Grassland')
    check("Carbon: no benchmark gives consistency 'na'",
          cn['consistency'] == 'na' and cn['benchmark_low'] is None)
    check("Carbon: None when no climate-regulation value",
          compute_carbon_revenue(0.0, 1.0, 190.0, 10.0, 30.0, 1000.0,
                                 'Mangroves') is None)

    for label, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    passed = sum(1 for _, ok in checks if ok)
    return passed, len(checks) - passed


def run_condition_exemption_tests():
    """Scalar condition multipliers (EEI / manual sliders) must skip cultural.

    Cultural services are demand-driven, not condition-driven: an urban park
    keeps its recreation value to the people using it however degraded the
    surrounding ecosystem is. See CONDITION_EXEMPT_CATEGORIES in
    utils.precomputed_esvd_coefficients for the SEEA EA / ONS rationale.

    The pre-existing TEST_CASES all pass intactness=1.0, where applying and
    skipping the multiplier are indistinguishable, so they cannot catch a
    regression here.
    """
    checks = []

    def check(label, ok):
        checks.append((label, bool(ok)))

    def urban(eei, urb=1.0):
        return calc.calculate_ecosystem_values(
            ecosystem_type="Urban", area_hectares=1000,
            coordinates=(19.374960, -99.117966),
            urban_green_blue_multiplier=urb,
            ecosystem_intactness_multiplier=eei,
            regional_factor_override=1.01,
        )

    zero, half, full = urban(0.0), urban(0.5), urban(1.0)

    # Cultural is untouched by the scalar, at any value.
    check("Condition: cultural unchanged at EEI 0 vs 1",
          abs(zero["cultural"]["total"] - full["cultural"]["total"]) < 1e-6)
    check("Condition: cultural unchanged at EEI 0.5",
          abs(half["cultural"]["total"] - full["cultural"]["total"]) < 1e-6)
    check("Condition: cultural non-zero at EEI 0 (the point of the exemption)",
          zero["cultural"]["total"] > 0)

    # Every other category still scales linearly with condition.
    for cat in ("provisioning", "regulating", "supporting"):
        check(f"Condition: {cat} zeroed at EEI 0", zero[cat]["total"] == 0)
        check(f"Condition: {cat} halves at EEI 0.5",
              abs(half[cat]["total"] - full[cat]["total"] * 0.5) < 1e-6)

    # Dict mode is indicator-driven and must still reach cultural: a set that
    # measured a cultural sub-service states its value, and that stands.
    with_dict = calc.calculate_ecosystem_values(
        ecosystem_type="Urban", area_hectares=1000,
        coordinates=(19.374960, -99.117966), urban_green_blue_multiplier=1.0,
        ecosystem_intactness_multiplier={"recreation": 0.25},
        regional_factor_override=1.01,
    )
    rec_dict = with_dict["cultural"]["services"]["recreation_and_tourism"]
    rec_base = full["cultural"]["services"]["recreation_and_tourism"]
    check("Condition: dict mode still scales cultural (indicator data wins)",
          abs(rec_dict - rec_base * 0.25) < 1e-6)

    passed = failed = 0
    for label, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        if ok:
            passed += 1
        else:
            failed += 1
    return passed, failed


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

    eroi_passed, eroi_failed = run_eroi_tests()
    passed += eroi_passed
    failed += eroi_failed

    cond_passed, cond_failed = run_condition_exemption_tests()
    passed += cond_passed
    failed += cond_failed

    print(f"\n{passed}/{passed + failed} tests passed.")
    return failed == 0

if __name__ == "__main__":
    print("EVE Calculation Regression Tests\n")
    ok = run_tests()
    sys.exit(0 if ok else 1)

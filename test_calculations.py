"""
EVE calculation regression tests.
Run before major deployments (minor or major version bumps).
Uses expected totals derived from 'EVE test data.xlsx' Test cases tab.
"""
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
]

def run_mixed_test():
    """Mixed ecosystem: 77.8% Agricultural + 22.2% Grassland, 1000 ha, regional 2.5."""
    ag = calc.calculate_ecosystem_values("Agricultural", 1000, regional_factor_override=2.5)["total_value"]
    gr = calc.calculate_ecosystem_values("Grassland",    1000, regional_factor_override=2.5)["total_value"]
    actual = 0.778 * ag + 0.222 * gr
    expected = 55_142_650
    return "Mixed Ecosystem (Ag 77.8% / Grassland 22.2%)", actual, expected

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

    label, actual, expected = run_mixed_test()
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

"""
Tests for satellite-undetectable ("forced") ecosystem support and the
multi-word ecosystem coefficient-lookup fix.

  * PrecomputedESVDCoefficients.get_ecosystem_coefficients now normalises
    spaces to underscores, so multi-word display names resolve to their own
    coefficient block instead of the default fallback.
  * build_forced_ecosystem_results stamps every (polygon-clipped) sample point
    with a forced ecosystem, skipping the satellite landcover lookup.
  * The forced-ecosystem registry helpers behave as expected.

Runnable without pytest:  python tests/test_forced_ecosystems.py
"""

import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost:5432/dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
from utils.openlandmap_integration import build_forced_ecosystem_results
import utils.forced_ecosystems as fe


# A square in (lon, lat) with the closing vertex, as app.py stores coordinates.
SQUARE = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]


def test_multiword_ecosystem_lookup_resolves():
    c = PrecomputedESVDCoefficients()
    spaced = c.get_ecosystem_coefficients("Rivers and Lakes")
    keyed = c.get_ecosystem_coefficients("rivers_and_lakes")
    assert spaced == keyed, "spaced display name must resolve to the same block"
    # And it must NOT be the default fallback used for unknown names.
    fallback = c.get_ecosystem_coefficients("totally_unknown_ecosystem_xyz")
    assert spaced != fallback, "multi-word lookup should not hit the default fallback"


def test_single_word_lookup_still_works():
    c = PrecomputedESVDCoefficients()
    assert c.get_ecosystem_coefficients("Mangroves") == c.get_ecosystem_coefficients("mangroves")


def test_forced_results_shape_and_stamping():
    res = build_forced_ecosystem_results(SQUARE, "Peatland", num_points=9)
    assert res["primary_ecosystem"] == "Peatland"
    assert res["coverage_percentage"] == 100.0
    samples = res["sample_results"]
    assert len(samples) > 0
    assert res["successful_queries"] == len(samples)
    assert res["ecosystem_distribution"] == {"Peatland": {"count": len(samples)}}
    for s in samples:
        assert s["ecosystem_type"] == "Peatland"
        assert s["landcover_class"] == 0
        assert "Forced" in s["source"]
        coords = s["coordinates"]
        assert isinstance(coords["lat"], float) and isinstance(coords["lon"], float)
        # Inside the unit square (these points came from the polygon-clipped grid).
        assert 0.0 <= coords["lon"] <= 1.0 and 0.0 <= coords["lat"] <= 1.0


def test_forced_results_count_is_exact():
    # Mirrors _generate_sample_points, which now returns exactly the requested
    # count for any n. It used to round down to the nearest perfect square,
    # so 10 came back as 9.
    for n in (9, 10, 25, 37):
        res = build_forced_ecosystem_results(SQUARE, "Peatland", num_points=n)
        assert len(res["sample_results"]) == n, (n, len(res["sample_results"]))


def test_registry_helpers():
    # Default registry is empty (no satellite-undetectable ecosystems yet).
    assert fe.is_forced_ecosystem("Peatland") is False
    assert "Peatland" not in fe.forced_display_names()
    # Adding an entry flips the helpers (restore afterwards).
    fe.FORCED_ECOSYSTEM_TO_KEY["Peatland"] = "peatland"
    try:
        assert fe.is_forced_ecosystem("Peatland") is True
        assert "Peatland" in fe.forced_display_names()
        assert fe.is_forced_ecosystem("Mangroves") is False
    finally:
        fe.FORCED_ECOSYSTEM_TO_KEY.pop("Peatland", None)


# ── runner ──────────────────────────────────────────────────────────────────

_TESTS = [
    ("multi-word ecosystem lookup resolves", test_multiword_ecosystem_lookup_resolves),
    ("single-word lookup still works", test_single_word_lookup_still_works),
    ("forced results shape + stamping", test_forced_results_shape_and_stamping),
    ("forced results count is exact", test_forced_results_count_is_exact),
    ("registry helpers", test_registry_helpers),
]


def main():
    print("Running forced-ecosystem tests\n")
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

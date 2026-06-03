"""
Tests for auto-generated indicator instructions.

Indicators without a hand-authored entry in INDICATOR_INSTRUCTIONS now fall
back to instructions generated from their seed definition, so any newly added
indicator set (e.g. Tropical Forest TF1–TF7) surfaces a scoring intro, a
"How to score" table, and a response-help tooltip in the panel automatically.
Hand-authored entries (Mangrove M1, universal HD) still take precedence.

Runnable without pytest:  python tests/test_indicator_instructions_autogen.py
"""

import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost:5432/dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.indicator_instructions as ii
from utils.indicator_instructions import (
    get_indicator_instructions,
    get_response_help_markdown,
)


def test_tf_indicators_autogenerate():
    for code in ("TF1", "TF2", "TF3", "TF4", "TF5", "TF6", "TF7"):
        d = get_indicator_instructions("Tropical Forest", code)
        assert d is not None, code
        assert d["scoring_intro"], f"{code} missing scoring_intro"
        assert d["full_instructions"], f"{code} missing full_instructions"
        # A "How to score" table block is generated from the bands.
        assert any("How to score" in b.get("content", "") for b in d["full_instructions"]), code


def test_tf_response_help_markdown():
    rh = get_response_help_markdown("Tropical Forest", "TF1")
    assert rh and "Response categories" in rh
    # Six bands -> six labelled rows.
    assert rh.count("%)") == 6, rh


def test_bespoke_m1_takes_precedence():
    d = get_indicator_instructions("Mangroves", "M1")
    assert d is not None
    # The hand-authored M1 object, not an auto-generated one.
    assert d["full_instructions"] is ii._M1_FULL_INSTRUCTIONS


def test_universal_hd_takes_precedence_for_any_ecosystem():
    d = get_indicator_instructions("Tropical Forest", "HD")
    assert d is not None
    assert "Human Disturbance" in d["full_instructions"][0]["content"]


def test_mangrove_secondary_indicators_now_surface():
    # M2–M7 had no hand-authored entry; they now auto-surface from the seed.
    d = get_indicator_instructions("Mangroves", "M2")
    assert d is not None and d["full_instructions"]


def test_unknown_code_returns_none():
    assert get_indicator_instructions("Tropical Forest", "ZZ9") is None


_TESTS = [
    ("TF indicators auto-generate", test_tf_indicators_autogenerate),
    ("TF response-help markdown", test_tf_response_help_markdown),
    ("bespoke M1 precedence", test_bespoke_m1_takes_precedence),
    ("universal HD precedence", test_universal_hd_takes_precedence_for_any_ecosystem),
    ("mangrove M2–M7 now surface", test_mangrove_secondary_indicators_now_surface),
    ("unknown code returns None", test_unknown_code_returns_none),
]


def main():
    print("Running indicator-instruction auto-gen tests\n")
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

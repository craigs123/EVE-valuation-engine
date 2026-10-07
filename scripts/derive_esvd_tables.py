#!/usr/bin/env python3
"""Re-derive the ESVD coefficient tables from the source workbook's records.

WHY THIS EXISTS
---------------
Every coefficient in ``utils/precomputed_esvd_coefficients.py`` was transcribed
by hand from "ESVD data - Aug 2026/ESVD_Consolidated_All_Biomes.xlsx" on
2026-08-10. That made the workbook the single point of truth for the engine's
economic core, while being untracked in git, existing in two versions
(``_FILLED`` is newer than the cited source and is NOT what is live), and
unverifiable from inside the repo: ``test_calculations.py`` could only check the
tables against their own code comments, never against the evidence.

This script closes that loop. It reads the per-biome "<Biome> Records" tabs --
the record-level single-TEEB-tag value rows that the workbook's own pivots are
computed from -- and recomputes from scratch:

  * median, arithmetic mean and log-winsorised mean (all Int$2025/ha/yr)
  * n, the count of qualifying value records
  * the number of distinct STUDIES and distinct COUNTRIES behind each cell,
    which the workbook does not tabulate anywhere

As of 2026-10-07 all of these reproduce the live tables exactly: 184 populated
cells, zero mismatches.

USAGE
-----
    python -m scripts.derive_esvd_tables --check
        Verify the live module tables against the records. Exit 1 on any
        mismatch. This is what test_calculations.py calls when the workbook is
        present; it skips when it is not, so the suite still runs on a clean
        checkout or in CI.

    python -m scripts.derive_esvd_tables --emit study_counts
        Print the ``_ESVD_STUDY_COUNTS`` literal, formatted for pasting into
        utils/precomputed_esvd_coefficients.py. Also accepts median, mean,
        log_winsorised, sample_counts.

    python -m scripts.derive_esvd_tables --report
        Per-cell evidence table (n, studies, countries, dispersion) as CSV on
        stdout, for auditing which coefficients the evidence can carry.

THE LOG-WINSORISING FORMULA
---------------------------
Recovered by testing variants against the stored table rather than assumed,
because the workbook states it only in prose (Log-Scaled tab, row 30) and the
arithmetic is locked inside array formulas. The variant that reproduces all 184
cells is:

    cap  = geometric_mean(non-zero records) * exp(2 * SD_sample(ln(non-zero)))
    coef = arithmetic_mean(min(v, cap) for v in ALL records) * 1.2

Three details matter and none are guessable from the prose:
  * the geometric mean is the PLAIN one over non-zero records, not the shifted
    ``exp(mean(ln(1+x))) - 1`` form used by the tab's own geometric mean block
    (shifted gives 30 mismatches)
  * SD is the SAMPLE standard deviation, Excel STDEV, denominator n-1
    (population SD gives 35 mismatches)
  * zero-valued records are EXCLUDED from the cap but INCLUDED in the final
    average. There are 74 such records; each comes from a study that also
    reports non-zero values, so they are researcher-assessed nil valuations,
    not missing data.

The 1.2 is the workbook's Int$2020 -> Int$2025 multiplier (cell B3 of the
Log-Scaled tab).
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The cited source, NOT ESVD_Consolidated_All_Biomes_FILLED.xlsx. Override with
# ESVD_WORKBOOK when auditing a different version.
DEFAULT_WORKBOOK = REPO_ROOT / "ESVD data - Aug 2026" / "ESVD_Consolidated_All_Biomes.xlsx"

# Int$2020 -> Int$2025, from the workbook's own multiplier cell.
RESTATEMENT_MULTIPLIER = 1.2

# Records tab -> engine ecosystem key. Tab names carry the workbook's own
# trailing spaces ("Tropical & Subtropical  Records"); they are matched
# literally so a renamed tab fails loudly instead of being silently skipped.
RECORD_TABS: dict[str, str] = {
    "Marine Records": "marine",
    "Coastal Systems Records": "coastal",
    "Inland Wetlands Records": "wetland",
    "Rivers & Lakes Records": "rivers_and_lakes",
    "Tropical & Subtropical  Records": "tropical_forest",
    "Temperate Forest & Wood Records": "temperate_forest",
    "Cold Climate Evergreen  Records": "boreal_forest",
    "Shrubland & Shrubby Woo Records": "shrubland",
    "Rangelands & Natural Gr Records": "grassland",
    "Desert & Semi-Desert Records": "desert",
    "Polar & Alpine Systems Records": "polar",
    "Intensive Land Use Records": "agricultural",
    "Urban Green & Blue Infr Records": "urban",
}

# TEEB service number -> engine service key. Service 23 (existence/bequest) is
# deliberately absent: the engine omits it, so records tagged 23 are dropped.
TEEB_SERVICES: dict[int, str] = {
    1: "food", 2: "water", 3: "raw_materials", 4: "genetic_resources",
    5: "medicinal_resources", 6: "ornamental_resources", 7: "pollution",
    8: "climate", 9: "extreme_events", 10: "water_regulation",
    11: "water_purification", 12: "erosion", 13: "soil_formation",
    14: "pollination", 15: "biological_control", 16: "nursery_services",
    17: "habitat", 18: "aesthetic_value", 19: "recreation", 20: "cultural",
    21: "spiritual_value", 22: "primary_production",
}

# Records tab column order (row 4 is the header, data starts at row 5).
COL_STUDY_ID = 1
COL_TEEB_ES = 2
COL_VALUE = 4
COL_COUNTRIES = 5


class WorkbookMissing(RuntimeError):
    """The source workbook is not available. Callers may skip rather than fail."""


def workbook_path() -> Path:
    return Path(os.environ.get("ESVD_WORKBOOK", DEFAULT_WORKBOOK))


def load_records(path: Path | None = None) -> dict[tuple[str, str], list[dict]]:
    """Read every qualifying value record, keyed by (ecosystem, service).

    A record qualifies when it carries a TEEB service number the engine maps and
    a non-missing Int$2020/ha/yr value -- the workbook has already applied its
    own single-tag and Incl_Excl filters in building these tabs, so no further
    filtering happens here.
    """
    path = path or workbook_path()
    if not path.exists():
        raise WorkbookMissing(f"workbook not found: {path}")

    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise WorkbookMissing(f"openpyxl unavailable: {exc}") from exc

    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        missing = [tab for tab in RECORD_TABS if tab not in book.sheetnames]
        if missing:
            raise RuntimeError(
                "workbook is missing expected Records tabs (renamed?): "
                + ", ".join(repr(t) for t in missing)
            )

        records: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for tab, ecosystem in RECORD_TABS.items():
            for row in book[tab].iter_rows(min_row=5, max_col=10, values_only=True):
                teeb, value = row[COL_TEEB_ES], row[COL_VALUE]
                if teeb is None or value is None:
                    continue
                try:
                    teeb = int(teeb)
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                service = TEEB_SERVICES.get(teeb)
                if service is None:
                    continue  # service 23, or an unmapped tag
                records[(ecosystem, service)].append({
                    "value": value,
                    "study_id": row[COL_STUDY_ID],
                    "countries": row[COL_COUNTRIES],
                })
    finally:
        book.close()
    return dict(records)


def split_countries(field) -> list[str]:
    """Country names out of ESVD's Countries field.

    The field is SEMICOLON-separated and the names themselves contain commas
    ("Korea, Republic of"; "Bonaire, Sint Eustatius and Saba"), so splitting on
    commas inflates the count badly -- 99 of the 124 distinct field values
    contain a comma.
    """
    if not field:
        return []
    return [part.strip() for part in str(field).split(";") if part.strip()]


def log_winsorised_mean(values: list[float]) -> float:
    """The workbook's preferred statistic, in Int$2020 (caller restates).

    See the module docstring for why each detail is what it is -- every one was
    recovered by reproduction, not read off the prose.
    """
    non_zero = [v for v in values if v > 0]
    if not non_zero:
        return 0.0
    logs = [math.log(v) for v in non_zero]
    geo_mean = math.exp(st.fmean(logs))
    # Sample SD (Excel STDEV). Undefined for a single record, in which case the
    # cap collapses to the geometric mean and binds on nothing.
    sd = st.stdev(logs) if len(logs) > 1 else 0.0
    cap = geo_mean * math.exp(2 * sd)
    return st.fmean(min(v, cap) for v in values)


def geometric_sd(values: list[float]) -> float | None:
    """Multiplicative spread of the non-zero records.

    Reported rather than an arithmetic SD because these distributions are
    right-skewed over orders of magnitude; a GSD of 99 (rivers_and_lakes
    aesthetic_value) says "one SD spans a factor of 99" far more usefully than a
    dollar figure would. None where fewer than two non-zero records make it
    undefined.
    """
    non_zero = [v for v in values if v > 0]
    if len(non_zero) < 2:
        return None
    return math.exp(st.stdev(math.log(v) for v in non_zero))


def derive(records: dict[tuple[str, str], list[dict]] | None = None) -> dict:
    """Recompute every statistic for every populated cell.

    Money figures come back in Int$2025/ha/yr, matching the live tables. Cells
    with no records are absent -- the caller treats a missing cell as the 0.00
    coefficient / n=0 pair that the engine stores, which means "no qualifying
    record", not a measured zero.
    """
    records = records if records is not None else load_records()
    derived: dict[tuple[str, str], dict] = {}
    for key, rows in records.items():
        values = sorted(row["value"] for row in rows)
        quartiles = (
            st.quantiles(values, n=4, method="inclusive")
            if len(values) >= 2 else [values[0]] * 3
        )
        countries: set[str] = set()
        for row in rows:
            countries.update(split_countries(row["countries"]))
        m = RESTATEMENT_MULTIPLIER
        derived[key] = {
            "n": len(values),
            "studies": len({row["study_id"] for row in rows}),
            "countries": len(countries),
            "median": st.median(values) * m,
            "mean": st.fmean(values) * m,
            "log_winsorised": log_winsorised_mean(values) * m,
            "min": values[0] * m,
            "p25": quartiles[0] * m,
            "p75": quartiles[2] * m,
            "max": values[-1] * m,
            "geometric_sd": geometric_sd(values),
        }
    return derived


def check(derived: dict | None = None) -> list[str]:
    """Compare the live module tables against the records.

    Returns a list of human-readable mismatches, empty when everything agrees.
    Tolerance is half a per cent or two cents, whichever is larger: the stored
    tables are rounded to the cent and the log-winsorised figures were
    transcribed from an Excel display.
    """
    from utils.precomputed_esvd_coefficients import (
        _ESVD_LOG_WINSORISED, _ESVD_MEAN, _ESVD_MEDIAN, _ESVD_SAMPLE_COUNTS,
        _ESVD_STUDY_COUNTS,
    )

    derived = derived if derived is not None else derive()
    stored_tables = {
        "median": _ESVD_MEDIAN,
        "mean": _ESVD_MEAN,
        "log_winsorised": _ESVD_LOG_WINSORISED,
    }
    problems: list[str] = []

    # Walk the STORED tables, not the derived ones, so a cell the records cover
    # but the engine omits is caught too.
    for name, table in stored_tables.items():
        for ecosystem, services in table.items():
            for service, stored in services.items():
                found = derived.get((ecosystem, service))
                if found is None:
                    if stored:
                        problems.append(
                            f"{name}: {ecosystem}/{service} is {stored:,.2f} in the "
                            f"module but has no qualifying record"
                        )
                    continue
                recomputed = found[name]
                tolerance = max(0.02, 0.005 * abs(stored))
                if abs(recomputed - stored) > tolerance:
                    problems.append(
                        f"{name}: {ecosystem}/{service} module {stored:,.2f} "
                        f"vs records {recomputed:,.2f}"
                    )

    for label, table, field in (
        ("n", _ESVD_SAMPLE_COUNTS, "n"),
        ("studies", _ESVD_STUDY_COUNTS, "studies"),
    ):
        for ecosystem, services in table.items():
            for service, stored in services.items():
                found = derived.get((ecosystem, service))
                actual = found[field] if found else 0
                if actual != stored:
                    problems.append(
                        f"{label}: {ecosystem}/{service} module {stored} "
                        f"vs records {actual}"
                    )
    return problems


def emit(table: str, derived: dict | None = None) -> str:
    """Format one table as a Python literal, ready to paste into the module.

    Key order follows _ESVD_SAMPLE_COUNTS so a diff against the pasted block
    stays readable, and so the positional-identity assertions in
    test_calculations.py keep holding.
    """
    from utils.precomputed_esvd_coefficients import _ESVD_SAMPLE_COUNTS

    derived = derived if derived is not None else derive()
    field = {"study_counts": "studies", "sample_counts": "n"}.get(table, table)
    is_money = field in ("median", "mean", "log_winsorised")

    lines = ["{"]
    for ecosystem, services in _ESVD_SAMPLE_COUNTS.items():
        lines.append(f"    '{ecosystem}': {{")
        entries = []
        for service in services:
            found = derived.get((ecosystem, service))
            value = found[field] if found else 0
            entries.append(
                f"'{service}': {value:.2f}" if is_money else f"'{service}': {value}"
            )
        # Four per line, matching the hand-written counts blocks.
        for start in range(0, len(entries), 4):
            lines.append("        " + ", ".join(entries[start:start + 4]) + ",")
        lines[-1] = lines[-1].rstrip(",")
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


def report(derived: dict | None = None) -> None:
    """Per-cell evidence CSV, for auditing what each coefficient rests on."""
    from utils.precomputed_esvd_coefficients import (
        _ESVD_LOG_WINSORISED, INDICATIVE_N_THRESHOLD,
    )

    derived = derived if derived is not None else derive()
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow([
        "ecosystem", "service", "records", "studies", "countries",
        "thin_by_records", "thin_by_studies", "log_winsorised_int2025",
        "median_int2025", "min", "p25", "p75", "max", "geometric_sd",
    ])
    for (ecosystem, service), found in sorted(derived.items()):
        gsd = found["geometric_sd"]
        writer.writerow([
            ecosystem, service, found["n"], found["studies"], found["countries"],
            found["n"] < INDICATIVE_N_THRESHOLD,
            found["studies"] < INDICATIVE_N_THRESHOLD,
            f"{_ESVD_LOG_WINSORISED.get(ecosystem, {}).get(service, 0.0):.2f}",
            f"{found['median']:.2f}", f"{found['min']:.2f}", f"{found['p25']:.2f}",
            f"{found['p75']:.2f}", f"{found['max']:.2f}",
            "" if gsd is None else f"{gsd:.1f}",
        ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="verify the live tables against the records")
    group.add_argument("--emit", metavar="TABLE",
                       choices=["median", "mean", "log_winsorised",
                                "sample_counts", "study_counts"],
                       help="print a table as a pasteable Python literal")
    group.add_argument("--report", action="store_true",
                       help="per-cell evidence CSV on stdout")
    args = parser.parse_args(argv)

    try:
        derived = derive()
    except WorkbookMissing as exc:
        print(f"SKIP: {exc}", file=sys.stderr)
        print("The source workbook is untracked; set ESVD_WORKBOOK to point at it.",
              file=sys.stderr)
        return 0 if args.check else 2

    if args.emit:
        print(emit(args.emit, derived))
        return 0
    if args.report:
        report(derived)
        return 0

    problems = check(derived)
    populated = len(derived)
    if problems:
        print(f"FAIL: {len(problems)} mismatch(es) across {populated} populated cells")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"OK: {populated} populated cells reproduce the live tables "
          f"(median, mean, log-winsorised, n, studies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Indicator-driven sub-service multiplier engine.

When an assessment has ``use_indicator_multipliers=True``, this module
replaces the single uniform BBI multiplier with one multiplier per
sub-service derived from the user's responses to project-indicator
questions (M1–M7 + mandatory HD for Mangrove). Sub-services not covered
by any selected indicator fall back to BBI.

The single public entry point is :func:`compute_sub_service_multipliers`,
which takes an analysis id, reads everything it needs from the database
via the DAOs in ``database.py``, persists the materialised results to
``computed_sub_service_multipliers``, and returns the new rows.

The function is intentionally side-effect-controlled — only the
``replace_for_analysis`` write touches the DB. It is also designed for
unit testing via the ``_compute_pure`` helper, which takes already-loaded
inputs and returns rows without any DB I/O.
"""

from __future__ import annotations

import math
from typing import Optional

from utils.teeb_slug_map import (
    TEEB_TO_CALC_KEY,
    WEIGHT_LOOKUP,
    HD_RELATIONSHIP,
    HD_INDICATOR_SLUG,
    INDICATOR_FLOOR,
)


def _hd_multiplier_from_score(effective_score: float) -> float:
    """Convert an HD response score (0-1) into the cross-cutting multiplier.

    HD is applied as ``sqrt(score)`` — a graduated dose-response curve. The
    square root moderates the penalty so moderate disturbance reduces, but
    does not eliminate, realised value (HD score 0.50 → 0.71 multiplier,
    ~29% reduction; HD 0.10 → 0.32, ~68%). Matches the HD indicator seed's
    ``mapping_params={'multiplier_exponent': 0.5}``.
    """
    return math.sqrt(max(0.0, float(effective_score)))


def _pure_indicator_average(
    eligible_indicators: list[dict],
) -> tuple[Optional[float], list[str], list[int], list[float]]:
    """Weighted average over a list of {slug, score, weight} dicts.

    Returns (indicator_multiplier_0_to_1, slugs, response_pcts, weights).
    If the list is empty, returns (None, [], [], []).
    """
    if not eligible_indicators:
        return None, [], [], []

    slugs = [e['slug'] for e in eligible_indicators]
    pcts = [int(round(e['score'] * 100)) for e in eligible_indicators]
    weights = [float(e['weight']) for e in eligible_indicators]

    weight_total = sum(weights)
    if weight_total == 0:
        return None, slugs, pcts, weights

    weighted_sum = sum(e['score'] * e['weight'] for e in eligible_indicators)
    return weighted_sum / weight_total, slugs, pcts, weights


def _compute_pure(
    *,
    sub_service_keys: list[str],
    indicator_responses: list[dict],
    hd_indicator_slug: Optional[str],
    bbi: float,
) -> list[dict]:
    """Pure computation, no DB access. Used directly by unit tests.

    Parameters
    ----------
    sub_service_keys
        The calc-keyspace sub-service keys to compute multipliers for
        (e.g. all 22 keys of the 'mangroves' coefficient dict).
    indicator_responses
        List of dicts shaped like ``ProjectIndicatorDB.get_responses()``
        rows. Must include keys ``indicator_slug``, ``is_committed``,
        ``effective_score`` (None if no response yet), ``service_weights``
        (a dict mapping TEEB slug → 'primary'/'secondary'/'multiplier').
    hd_indicator_slug
        The slug of the mandatory cross-cutting indicator (e.g.
        ``'human_disturbance_pressure'``). None if the project type has
        no such indicator.
    bbi
        The BBI fallback value (0.0–1.0). Used for sub-services not
        covered by any selected indicator.

    Returns
    -------
    A list of dicts ready to insert into computed_sub_service_multipliers
    (one row per sub-service key).
    """
    # 1. HD multiplier — cross-cutting, applied as sqrt(score) (see
    #    _hd_multiplier_from_score). Defaults to 1.0 (no penalty) when HD
    #    has no recorded response — an unanswered HD is never assumed worst.
    hd_multiplier = 1.0
    if hd_indicator_slug is not None:
        for r in indicator_responses:
            if r['indicator_slug'] == hd_indicator_slug and r.get('effective_score') is not None:
                hd_multiplier = _hd_multiplier_from_score(r['effective_score'])
                break

    # 2. Index committed non-HD indicators with a response
    committed_responses = [
        r for r in indicator_responses
        if r.get('is_committed')
        and r.get('indicator_slug') != hd_indicator_slug
        and r.get('effective_score') is not None
    ]

    out: list[dict] = []
    for s in sub_service_keys:
        # 3. Find every TEEB slug that maps to this calc key
        teeb_slugs_for_s = [t for t, c in TEEB_TO_CALC_KEY.items() if c == s]

        # 4. Collect eligible (indicator, weight) pairs.
        #    When an indicator has multiple TEEB-slug paths to the same calc
        #    key (e.g. both habitat_for_species PRIMARY and genetic_diversity
        #    SECONDARY both map to 'habitat'), pick the strongest weight —
        #    not the first match — so PRIMARY always wins over SECONDARY.
        eligible: list[dict] = []
        for resp in committed_responses:
            sw = resp.get('service_weights') or {}
            best_weight: float = 0.0
            for t in teeb_slugs_for_s:
                rel = sw.get(t)
                if rel is None or rel == HD_RELATIONSHIP:
                    continue
                w = WEIGHT_LOOKUP.get(rel)
                if w is None:
                    continue
                if w > best_weight:
                    best_weight = w
            if best_weight > 0.0:
                eligible.append({
                    'slug': resp['indicator_slug'],
                    'score': float(resp['effective_score']),
                    'weight': best_weight,
                })

        # 5. Compute
        ind_mult, slugs, pcts, weights = _pure_indicator_average(eligible)

        if ind_mult is None:
            # No indicator coverage → BBI fallback, with HD layered on top.
            # HD is a cross-cutting pressure variable: it modifies the
            # realised value of every sub-service simultaneously, whether
            # that value is indicator-derived or the BBI fallback. The
            # floor still applies so an extreme HD × low-BBI combination
            # cannot drive a service to zero.
            raw_final = bbi * hd_multiplier
            final = max(raw_final, INDICATOR_FLOOR)
            row = {
                'teeb_sub_service_key': s,
                'indicator_multiplier': None,
                'contributing_indicators': [],
                'contributing_response_pcts': [],
                'contributing_weights': [],
                'hd_multiplier': hd_multiplier,
                'final_multiplier': final,
                'fallback_to_bbi': True,
                'bbi_value_used': bbi,
            }
        else:
            raw_final = ind_mult * hd_multiplier
            final = max(raw_final, INDICATOR_FLOOR)
            row = {
                'teeb_sub_service_key': s,
                'indicator_multiplier': ind_mult,
                'contributing_indicators': slugs,
                'contributing_response_pcts': pcts,
                'contributing_weights': weights,
                'hd_multiplier': hd_multiplier,
                'final_multiplier': final,
                'fallback_to_bbi': False,
                'bbi_value_used': None,
            }
        out.append(row)

    return out


def compute_sub_service_multipliers(
    analysis_id: str,
    *,
    bbi_override: Optional[float] = None,
) -> Optional[list[dict]]:
    """Compute and persist per-sub-service multipliers for an assessment.

    Returns ``None`` (and writes nothing) if ``use_indicator_multipliers``
    is False on the assessment row — the caller should fall back to the
    uniform BBI calculation in that case.

    Parameters
    ----------
    analysis_id
        UUID string of the ecosystem_analyses row.
    bbi_override
        If supplied, this BBI value is used as the fallback for sub-services
        not covered by any selected indicator. If None, the BBI is derived
        from the assessment's ``ecosystem_type`` and the current
        ``ecosystem_intactness`` session-state dict via
        ``utils.analysis_helpers._get_ecosystem_intactness_multiplier``.
        Tests typically pass an explicit override.

    Returns
    -------
    The list of computed rows (same shape as
    ``ComputedSubServiceMultiplierDB.get_for_analysis``), or ``None`` if
    the assessment has the feature disabled.
    """
    # Local imports keep this module importable without a live DB for tests
    from database import (
        ProjectIndicatorDB,
        ComputedSubServiceMultiplierDB,
        EcosystemAnalysis,
        get_db,
    )
    from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients

    # 1. Guard clause — feature off?
    if not ProjectIndicatorDB.get_assessment_flag(analysis_id):
        return None

    # 2. Read the assessment so we know the ecosystem type (for sub-service keys)
    with get_db() as db:
        row = db.query(EcosystemAnalysis).filter(
            EcosystemAnalysis.id == analysis_id
        ).first()
        if row is None:
            return None
        ecosystem_type = row.ecosystem_type

    # 3. Sub-service key universe for this ecosystem
    coeffs = PrecomputedESVDCoefficients()
    eco_coeffs = coeffs.get_ecosystem_coefficients(ecosystem_type) or {}
    sub_service_keys = list(eco_coeffs.keys())
    if not sub_service_keys:
        return []

    # 4. Indicator responses for this analysis
    responses = ProjectIndicatorDB.get_responses(analysis_id)

    # 5. Identify the HD cross-cutting indicator by its canonical slug
    #    (HD is universal — same slug for every project type). Fall back
    #    to the is_mandatory flag for any legacy data lacking the slug.
    if any(r['indicator_slug'] == HD_INDICATOR_SLUG for r in responses):
        hd_slug = HD_INDICATOR_SLUG
    else:
        hd_slug = next(
            (r['indicator_slug'] for r in responses if r.get('is_mandatory')),
            None,
        )

    # 6. BBI fallback
    if bbi_override is not None:
        bbi = float(bbi_override)
    else:
        # Read from session state via helper; fall back to 1.0 if unavailable
        try:
            import streamlit as st  # type: ignore
            from utils.analysis_helpers import _get_ecosystem_intactness_multiplier
            ei = st.session_state.get('ecosystem_intactness', {}) if hasattr(st, 'session_state') else {}
            bbi = _get_ecosystem_intactness_multiplier(ecosystem_type, ei)
        except Exception:
            bbi = 1.0

    # 7. Pure compute
    rows = _compute_pure(
        sub_service_keys=sub_service_keys,
        indicator_responses=responses,
        hd_indicator_slug=hd_slug,
        bbi=bbi,
    )

    # 8. Persist
    ComputedSubServiceMultiplierDB.replace_for_analysis(analysis_id, rows)
    return rows

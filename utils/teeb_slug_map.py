"""TEEB-slug ↔ calc-key mapping for indicator multipliers.

EVE has two parallel ecosystem-service keyspaces:

  1. **Calc keyspace** (lowercase, abbreviated): the keys used inside
     `precomputed_esvd_coefficients.py` ecosystem dicts — e.g. ``pollution``,
     ``climate``, ``habitat``, ``recreation``. These are the keys multiplied
     by the per-service multiplier in the calculation engine.

  2. **Indicator keyspace** (TEEB-aligned full slugs): the keys used inside
     ``pi_indicators.service_weights`` — e.g. ``air_quality_regulation``,
     ``climate_regulation``, ``habitat_for_species``, ``recreation_and_tourism``.
     Seed defined in ``utils/project_indicators_seed.py``.

When computing sub-service multipliers from indicator responses we need to
translate between the two. This module provides the only translation table —
neither the coefficient dicts nor the indicator seed are touched.

Edit notes:
  * ``genetic_diversity`` and ``habitat_for_species`` both map to ``habitat`` —
    the calc engine has a single ``habitat`` bucket, but TEEB treats the two
    as distinct concepts. The weighted-average rule in the multiplier engine
    aggregates them naturally.
  * The HD indicator's TEEB slugs all map to ``'multiplier'`` in
    ``service_weights``; that relationship is excluded from the per-service
    weighted average and applied as a cross-cutting multiplier instead
    (see ``HD_RELATIONSHIP`` below).
"""

# Mapping from TEEB slug (pi_indicators.service_weights key) to calc key
# (PrecomputedESVDCoefficients ecosystem-dict key).
TEEB_TO_CALC_KEY: dict[str, str] = {
    'food_provisioning':            'food',
    'water_provisioning':           'water',
    'raw_materials':                'raw_materials',
    'genetic_resources':            'genetic_resources',
    'medicinal_resources':          'medicinal_resources',
    'ornamental_resources':         'ornamental_resources',
    'air_quality_regulation':       'pollution',
    'climate_regulation':           'climate',
    'moderation_of_extreme_events': 'extreme_events',
    'water_flow_regulation':        'water_regulation',
    'waste_treatment':              'water_purification',
    'erosion_prevention':           'erosion',
    'soil_formation':               'soil_formation',
    'pollination':                  'pollination',
    'biological_control':           'biological_control',
    'nursery_services':             'nursery_services',
    'habitat_for_species':          'habitat',
    'genetic_diversity':            'habitat',
    'aesthetic_information':        'aesthetic_value',
    'recreation_and_tourism':       'recreation',
    'inspiration':                  'cultural',
    'spiritual_experience':         'spiritual_value',
}


# Weight applied to each indicator-to-sub-service relationship type when
# computing a sub-service's weighted-average multiplier. Relationships not
# present here are excluded from the average — notably ``'multiplier'`` /
# ``'cross_cutting'`` which carries HD's whole-area effect and is applied
# separately as a final multiplier on indicator-derived values.
WEIGHT_LOOKUP: dict[str, float] = {
    'primary':   1.0,
    'secondary': 0.5,
}


# The relationship_type value used in ``service_weights`` to mark a
# cross-cutting / whole-area multiplier (currently only HD).
HD_RELATIONSHIP: str = 'multiplier'


# Floor applied to indicator-derived final multipliers before they are
# applied to a coefficient. Prevents extreme HD × very-low-indicator
# combinations from driving a sub-service value to zero (which would imply
# a destroyed ecosystem services with no recovery potential). 0.05 = 5%.
# BBI fallback values are NOT floored (BBI has its own slider minimum).
INDICATOR_FLOOR: float = 0.05

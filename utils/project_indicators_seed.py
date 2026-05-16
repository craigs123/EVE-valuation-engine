"""Seed data for project-typed indicator taxonomy.

Single source of truth for default project types, indicators, scoring bands,
followup questions, and TEEB service weightings. Loaded into the pi_* tables
via seed_project_indicators(session) at app startup; idempotent.

v1 ships one project type — Mangrove Restoration — with eight indicators
(M1-M7 + mandatory HD). Other project types extend the same structure.
"""

from typing import List

# Canonical TEEB-aligned service slugs. Used as the keyspace for
# Indicator.service_weights. Three are deliberately excluded from this seed
# (medicinal_resources, ornamental_resources, pollination) since no
# field-measurable mangrove proxy exists for them — they remain in the canonical
# list so future indicators (or other project types) can reference them.
CANONICAL_TEEB_SLUGS: List[str] = [
    'food_provisioning',
    'water_provisioning',
    'raw_materials',
    'genetic_resources',
    'medicinal_resources',
    'ornamental_resources',
    'air_quality_regulation',
    'climate_regulation',
    'moderation_of_extreme_events',
    'water_flow_regulation',
    'waste_treatment',
    'erosion_prevention',
    'pollination',
    'habitat_for_species',
    'genetic_diversity',
    'aesthetic_information',
    'recreation_and_tourism',
    'inspiration',
    'spiritual_experience',
]


DEFAULT_PROJECT_TYPES = [
    {
        'slug': 'mangrove_restoration',
        'name': 'Mangrove Restoration',
        'icon': '🌿',
        # EVE ecosystem display name this project type serves. Drives the
        # ecosystem -> project-type mapping that gates the project-specific
        # indicators checkbox. A new project type only needs this set (plus
        # at least one ecological indicator) to become selectable.
        'ecosystem_type': 'Mangroves',
        'description': (
            'Field-measurable indicator set for mangrove restoration projects. '
            'Eight indicators (seven ecological + one mandatory cross-cutting '
            'disturbance indicator) completable in a single 2-3 hour field visit '
            'by a non-specialist team.'
        ),
        'sort_order': 1,
    },
]


# Slugs of universal cross-cutting indicators. These are NOT listed per-type
# in DEFAULT_PROJECT_TYPE_INDICATORS — seed_project_indicators() attaches them
# to every project type automatically, so any project type added later
# inherits them for free. Currently just HD (Human Disturbance Pressure).
UNIVERSAL_INDICATOR_SLUGS = ['human_disturbance_pressure']


# ── Mangrove indicators ──────────────────────────────────────────────────────

_M1 = {
    'slug': 'mangrove_canopy_cover', 'code': 'M1', 'name': 'Canopy Cover',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team estimate the proportion of sky covered by mangrove '
        'canopy at multiple points across your site?',
    'prospectus_scope_statement':
        'Canopy cover monitoring contributes to valuations of: air quality '
        'regulation, climate regulation, extreme event moderation, erosion '
        'prevention, raw materials, habitat for species, aesthetic information.',
    'baseline_question':
        "Estimate how complete and healthy your restoration site's canopy "
        "looks compared to a reference mangrove (Full instructions below).",
    'why_matters':
        'Canopy cover is the single most important structural indicator of '
        'mangrove restoration progress. It directly controls light availability, '
        'temperature regulation, coastal protection effectiveness, and habitat '
        'value for fish, birds, and invertebrates. A closed canopy slows waves '
        'and binds sediment far more effectively than sparse planting.',
    'field_method':
        '1. Select 5 representative points across your restoration site — one '
        'in each corner and one in the centre.\n'
        '2. At each point, stand upright and hold your smartphone flat above '
        'your head, camera facing upward.\n'
        '3. Take a photo directly upward.\n'
        '4. Estimate the percentage of the image that is green leaf or branch '
        'versus open sky.\n'
        '5. Average your 5 estimates and record the result.\n\n'
        'If you don\'t have a smartphone: stand at each point and look straight '
        'up. Estimate what percentage of your view is covered by canopy versus '
        'sky. Less precise but acceptable for community monitoring.\n\n'
        'Important: Measure at midday when shadows are shortest. Do not measure '
        'immediately after planting — wait until trees are at least 50cm tall.',
    'remote_sensing_alternative':
        'Open Google Earth or Google Earth Engine for your project polygon. '
        'Compare NDVI values against a nearby intact mangrove reference area. '
        'NDVI above 0.4 typically corresponds to more than 50% canopy cover in '
        'mangrove.',
    'sources':
        'Nayak & Bahuguna 2001; Gatt et al. 2022; '
        'NatureServe Ecological Resilience Indicators for Mangrove 2019',
    'service_weights': {
        'food_provisioning': 'secondary',
        'water_provisioning': 'secondary',
        'raw_materials': 'primary',
        'air_quality_regulation': 'primary',
        'climate_regulation': 'primary',
        'moderation_of_extreme_events': 'primary',
        'waste_treatment': 'secondary',
        'erosion_prevention': 'primary',
        'habitat_for_species': 'primary',
        'genetic_diversity': 'secondary',
        'aesthetic_information': 'primary',
        'recreation_and_tourism': 'secondary',
    },
    # Band labels match the M1 'How to score' table in the full instructions
    # (utils/indicator_instructions.py) — keep the two in sync.
    'bands': [
        {'score': 0.1,  'label': 'Bare or absent',          'criteria': '<10%',
         'meaning': 'Bare mudflat or very sparse early planting; no canopy function',
         'sort_order': 1},
        {'score': 0.3,  'label': 'Very early stage',        'criteria': '10–25%',
         'meaning': 'Scattered trees; site still mostly open; minimal coastal protection',
         'sort_order': 2},
        {'score': 0.5,  'label': 'Partial recovery',        'criteria': '25–50%',
         'meaning': 'Partial canopy developing; some shade and habitat value emerging',
         'sort_order': 3},
        {'score': 0.75, 'label': 'Good recovery',           'criteria': '50–70%',
         'meaning': 'Good canopy developing; meaningful coastal protection beginning',
         'sort_order': 4},
        {'score': 0.9,  'label': 'Near reference',          'criteria': '70–85%',
         'meaning': 'Dense closed canopy; approaching reference condition',
         'sort_order': 5},
        {'score': 1.0,  'label': 'Equivalent to reference', 'criteria': '>85%',
         'meaning': 'Equivalent to intact natural mangrove stand',
         'sort_order': 6},
    ],
    'followups': [],
}


_M2 = {
    'slug': 'mangrove_seedling_density', 'code': 'M2',
    'name': 'Seedling and Sapling Density',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team count young mangrove plants in small marked plots across '
        'your site?',
    'prospectus_scope_statement':
        'Seedling and sapling density monitoring contributes to valuations of: '
        'habitat for species, maintenance of genetic diversity.',
    'baseline_question':
        'In a 3m × 3m area (roughly the size of a small room), how many young '
        'mangrove plants can you count that are less than 1.3 metres tall?',
    'why_matters':
        'Young mangroves filling gaps in the canopy demonstrate that the site '
        'can recover from disturbance and sustain itself long-term. The '
        'regeneration potential of a stand indicates its long-term viability — '
        'in the absence of regeneration potential, a disturbance event can '
        'trigger a directional state change away from the target system. A site '
        'with good canopy cover but no seedlings is structurally fragile.',
    'field_method':
        '1. Mark out a 3m × 3m square using rope or tape measure.\n'
        '2. Count every mangrove plant within the plot that is shorter than '
        'shoulder height (approximately 1.3m) — include both planted seedlings '
        'and any that have arrived naturally.\n'
        '3. Repeat at 3 different locations across your site.\n'
        '4. Average the three counts and record.\n\n'
        'Record separately if possible: planted versus naturally arrived '
        'seedlings. Natural recruits are a bonus sign of site health.\n\n'
        'Tip: Young mangroves often appear as small bundles of leaves on a thin '
        'stem growing from the mud. In Rhizophora species you will see '
        'distinctive prop roots even in young plants.',
    'remote_sensing_alternative': 'Not available for this indicator. Must be field-measured.',
    'sources':
        'NatureServe Ecological Resilience Indicators — mean density of '
        'seedlings, saplings and viable propagules across monitoring plots; '
        'Bosire et al. 2008',
    'service_weights': {
        'raw_materials': 'secondary',
        'climate_regulation': 'secondary',
        'habitat_for_species': 'primary',
        'genetic_diversity': 'primary',
    },
    'bands': [
        {'score': 0.1,  'label': 'No regeneration',     'criteria': '0',
         'meaning': 'No young plants; no regeneration', 'sort_order': 1},
        {'score': 0.3,  'label': 'Sparse recruitment',  'criteria': '1–4',
         'meaning': 'Very sparse; isolated recruits only', 'sort_order': 2},
        {'score': 0.5,  'label': 'Some recruitment',    'criteria': '5–9',
         'meaning': 'Some recruitment; gaps still dominant', 'sort_order': 3},
        {'score': 0.75, 'label': 'Good recruitment',    'criteria': '10–17',
         'meaning': 'Good recruitment; gaps being filled', 'sort_order': 4},
        {'score': 0.9,  'label': 'Dense recruitment',   'criteria': '18–35',
         'meaning': 'Dense recruitment across site', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference density',   'criteria': '>35',
         'meaning': 'Equivalent to natural stand density', 'sort_order': 6},
    ],
    'followups': [],
}


_M3 = {
    'slug': 'mangrove_natural_recruitment', 'code': 'M3',
    'name': 'Natural Recruitment',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team walk the site and identify young mangrove plants that '
        'have arrived naturally rather than being planted?',
    'prospectus_scope_statement':
        'Natural recruitment monitoring contributes to valuations of: habitat '
        'for species, maintenance of genetic diversity.',
    'baseline_question':
        'Are you seeing young mangrove plants appearing in areas where you have '
        'not planted them — arriving naturally from seeds or propagules carried '
        'by water?',
    'why_matters':
        'Natural recruitment — seedlings arriving without being planted — is '
        'the strongest signal that a restoration site is becoming '
        'self-sustaining. Less than 30% of 123 mangrove restoration case '
        'studies identified natural recruitment, despite this being a key '
        'indicator of long-term viability. When mangroves are recruiting '
        'naturally it means site conditions — hydrology, sediment, salinity — '
        'are suitable for the ecosystem to maintain itself without ongoing '
        'intervention.',
    'field_method':
        '1. Walk the entire restoration site slowly.\n'
        '2. Look for young mangrove plants growing in areas you know were not '
        'planted — at the edges of planted areas, in gaps between rows, or on '
        'bare mudflat beyond the planting zone.\n'
        '3. If you planted in clear rows, any plants appearing between rows or '
        'outside them are likely natural recruits.\n'
        '4. Note approximate distribution: isolated, occasional, patchy, or '
        'widespread across the site.\n\n'
        'Tip: Natural recruits often look different from planted stock — they '
        'may be a different species or growing at unexpected angles. '
        'Rhizophora propagules (long pencil-like seeds) are particularly '
        'distinctive when they arrive naturally.',
    'remote_sensing_alternative': 'Not available. Must be field-observed.',
    'sources': 'Gatt et al. 2022; NatureServe Ecological Resilience Indicators 2019',
    'service_weights': {
        'raw_materials': 'secondary',
        'genetic_resources': 'secondary',
        'climate_regulation': 'secondary',
        'habitat_for_species': 'primary',
        'genetic_diversity': 'primary',
    },
    'bands': [
        {'score': 0.1,  'label': 'None',
         'criteria': 'No natural recruits visible anywhere',
         'meaning': 'Site conditions unsuitable or too early in restoration',
         'sort_order': 1},
        {'score': 0.3,  'label': 'Isolated',
         'criteria': '1–5 individual natural recruits found',
         'meaning': 'Conditions beginning to be suitable',
         'sort_order': 2},
        {'score': 0.5,  'label': 'Occasional',
         'criteria': 'Scattered recruits in several locations',
         'meaning': 'Site becoming suitable for natural establishment',
         'sort_order': 3},
        {'score': 0.75, 'label': 'Patchy',
         'criteria': 'Regular recruits across most of site',
         'meaning': 'Good natural regeneration underway',
         'sort_order': 4},
        {'score': 0.9,  'label': 'Widespread',
         'criteria': 'Recruits visible throughout site',
         'meaning': 'Site largely self-sustaining',
         'sort_order': 5},
        {'score': 1.0,  'label': 'Self-sustaining',
         'criteria': 'Dense natural recruitment; site regenerating without intervention',
         'meaning': 'Full reference condition',
         'sort_order': 6},
    ],
    'followups': [],
}


_M4 = {
    'slug': 'mangrove_tidal_flow', 'code': 'M4',
    'name': 'Tidal Flow and Hydrological Function',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team observe and report on water movement through the site at '
        'different tidal states?',
    'prospectus_scope_statement':
        'Tidal flow monitoring contributes to valuations of: water flow '
        'regulation, moderation of extreme events, waste treatment and water '
        'purification, habitat for species.',
    'baseline_question':
        'Can water flow freely in and out of your restoration site with the '
        'tides? Select the description that best matches what you observe.',
    'why_matters':
        'Mangroves depend entirely on tidal exchange. Blocked or impeded water '
        'flow is the single most common cause of mangrove restoration failure '
        'globally — even well-planted sites die if the hydrology is wrong. '
        'Free tidal exchange brings nutrients, removes waste, regulates '
        'salinity, and maintains the periodically flooded but draining '
        'conditions mangroves require.',
    'field_method':
        'Visit your site at low tide and again at high tide, or ask someone '
        'local to observe at both states and report back. Observe:\n'
        '- At high tide: does water reach the base of the mangroves?\n'
        '- At low tide: does water drain away from the roots?\n'
        '- Are there obvious blockages — roads, embankments, culverts, fish '
        'ponds — preventing water flow?\n'
        '- Is there evidence of permanent waterlogging (standing water that '
        'never drains)?\n\n'
        'Healthy mangrove roots should be underwater at high tide and exposed '
        'at low tide. If they are always underwater or always dry, tidal '
        'exchange is impaired.',
    'remote_sensing_alternative':
        'Sentinel-1 SAR imagery shows inundation patterns. Compare wet/dry '
        'pixel patterns across tidal cycles using Sentinel Hub EO Browser '
        '(free).',
    'sources': 'NatureServe Ecological Resilience Indicators for Mangrove 2019',
    'service_weights': {
        'food_provisioning': 'secondary',
        'water_provisioning': 'primary',
        'climate_regulation': 'secondary',
        'moderation_of_extreme_events': 'primary',
        'water_flow_regulation': 'primary',
        'waste_treatment': 'primary',
        'habitat_for_species': 'primary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Completely blocked',
         'criteria': 'No tidal flow; site permanently flooded or permanently dry',
         'meaning': None, 'sort_order': 1},
        {'score': 0.3,  'label': 'Severely impeded',
         'criteria': 'Water reaches site but drains very slowly; long-term waterlogging evident',
         'meaning': None, 'sort_order': 2},
        {'score': 0.5,  'label': 'Partially functional',
         'criteria': 'Tidal exchange occurs but is restricted; some areas not reached by tides',
         'meaning': None, 'sort_order': 3},
        {'score': 0.75, 'label': 'Mostly functional',
         'criteria': 'Good tidal exchange across most of site; minor restrictions only',
         'meaning': None, 'sort_order': 4},
        {'score': 0.9,  'label': 'Minor impediment',
         'criteria': 'Tidal exchange essentially normal with only slight restriction',
         'meaning': None, 'sort_order': 5},
        {'score': 1.0,  'label': 'Free tidal exchange',
         'criteria': 'Water flows freely in and out with every tide; no barriers observed',
         'meaning': None, 'sort_order': 6},
    ],
    'followups': [],
}


_M5 = {
    'slug': 'mangrove_water_clarity', 'code': 'M5',
    'name': 'Water Clarity',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team estimate water visibility in the water body immediately '
        'surrounding or flowing through your site?',
    'prospectus_scope_statement':
        'Water clarity monitoring contributes to valuations of: food '
        'provisioning, water provisioning, waste treatment and water '
        'purification, aesthetic information, recreation and tourism.',
    'baseline_question':
        'In the water immediately surrounding or running through your '
        'restoration site, how clearly can you see below the surface?',
    'why_matters':
        'Water clarity reflects the health of the broader coastal system. '
        'Murky water can indicate high sediment loads from erosion, excess '
        'nutrients from agricultural runoff, or pollution — all of which '
        'reduce the site\'s value for fisheries, tourism, and water '
        'provisioning. Improving water clarity is often a direct result of '
        'successful mangrove restoration through sediment trapping and '
        'nutrient uptake.',
    'field_method':
        '1. Find a point where water is at least 30cm deep adjacent to or '
        'flowing through your site.\n'
        '2. Submerge your hand or a white object to 30cm depth.\n'
        '3. Observe whether you can see it clearly, partially, or not at all.\n'
        '4. If available, use a Secchi disk — a white disk on a string — '
        'lowered until it disappears; record that depth.\n\n'
        'Measure at the same time of day and tidal state during each annual '
        'visit for a consistent comparison. Avoid measuring immediately after '
        'rainfall, which always increases turbidity temporarily.',
    'remote_sensing_alternative':
        'Sentinel-2 band ratios (blue divided by green) provide turbidity '
        'estimates for open water. Access via Sentinel Hub EO Browser.',
    'sources': None,
    'service_weights': {
        'food_provisioning': 'primary',
        'water_provisioning': 'primary',
        'waste_treatment': 'primary',
        'habitat_for_species': 'secondary',
        'aesthetic_information': 'primary',
        'recreation_and_tourism': 'primary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Opaque',
         'criteria': 'Nothing visible at any depth; water is brown or black (Secchi <5cm)',
         'meaning': None, 'sort_order': 1},
        {'score': 0.3,  'label': 'Very turbid',
         'criteria': 'Cannot see hand at 15cm (Secchi 5–15cm)',
         'meaning': None, 'sort_order': 2},
        {'score': 0.5,  'label': 'Turbid',
         'criteria': 'Hand visible at 15cm but not at 30cm (Secchi 15–30cm)',
         'meaning': None, 'sort_order': 3},
        {'score': 0.75, 'label': 'Slightly turbid',
         'criteria': 'Hand visible at 30cm; slight colour or murkiness (Secchi 30–60cm)',
         'meaning': None, 'sort_order': 4},
        {'score': 0.9,  'label': 'Clear',
         'criteria': 'Hand clearly visible at 30cm; water has natural colour (Secchi 60–100cm)',
         'meaning': None, 'sort_order': 5},
        {'score': 1.0,  'label': 'Crystal clear',
         'criteria': 'Bottom visible in shallow water; high clarity throughout (Secchi >100cm)',
         'meaning': None, 'sort_order': 6},
    ],
    'followups': [],
}


_M6 = {
    'slug': 'mangrove_wildlife_signs', 'code': 'M6',
    'name': 'Wildlife and Fauna Signs',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team conduct a 30-minute quiet observation at the site on '
        'each monitoring visit?',
    'prospectus_scope_statement':
        'Wildlife monitoring contributes to valuations of: habitat for '
        'species, genetic diversity, recreation and tourism, inspiration, '
        'spiritual experience.',
    'baseline_question':
        'During a 30-minute quiet observation at your restoration site, how '
        'many different types of animals — or clear signs of animals — can you '
        'count? Include birds, fish, crabs, insects, and any tracks, sounds, '
        'or nests.',
    'why_matters':
        'Wildlife diversity is the most direct indicator of whether your '
        'mangrove is becoming a functioning ecosystem rather than just a stand '
        'of trees. Mangroves are nursery habitats for fish, roosting sites for '
        'birds, and feeding grounds for crabs and invertebrates. As '
        'restoration succeeds, wildlife diversity increases reliably — and it '
        'is one of the most motivating indicators for community-based teams to '
        'monitor and share.',
    'field_method':
        '1. Sit or stand quietly at the edge of your site for 30 minutes.\n'
        '2. Keep a simple tally: each time you detect a different type of '
        'animal, add a mark.\n'
        '3. Count each type only once per session even if you see it multiple '
        'times.\n'
        '4. Include: birds (flying over or roosting), fish (jumping or visible '
        'in water), crabs (on roots or mud), insects, tracks in mud, calls you '
        'can hear, nests, or burrows.\n'
        '5. Conduct this at the same time of day each visit — early morning '
        'or late afternoon gives the best results.\n\n'
        'You do not need to know species names — just the number of '
        'distinguishable different types. A large white bird and a small brown '
        'bird count as two types.',
    'remote_sensing_alternative': 'Not available. Must be field-observed.',
    'sources': None,
    'service_weights': {
        'food_provisioning': 'secondary',
        'genetic_resources': 'secondary',
        'habitat_for_species': 'primary',
        'genetic_diversity': 'primary',
        'aesthetic_information': 'secondary',
        'recreation_and_tourism': 'primary',
        'inspiration': 'primary',
        'spiritual_experience': 'primary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Functionally empty', 'criteria': '0–1',
         'meaning': None, 'sort_order': 1},
        {'score': 0.3,  'label': 'Very low diversity', 'criteria': '2–3',
         'meaning': None, 'sort_order': 2},
        {'score': 0.5,  'label': 'Low diversity',      'criteria': '4–6',
         'meaning': None, 'sort_order': 3},
        {'score': 0.75, 'label': 'Moderate diversity', 'criteria': '7–10',
         'meaning': None, 'sort_order': 4},
        {'score': 0.9,  'label': 'Good diversity',     'criteria': '11–15',
         'meaning': None, 'sort_order': 5},
        {'score': 1.0,  'label': 'Pristine diversity', 'criteria': '>15',
         'meaning': None, 'sort_order': 6},
    ],
    'followups': [],
}


_M7 = {
    'slug': 'mangrove_invasive_pressure', 'code': 'M7',
    'name': 'Invasive Species Pressure',
    'is_mandatory': False,
    'applicable_ecosystems': ['Coastal', 'Wetland'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team walk the site and estimate the proportion of vegetation '
        'that is non-native or invasive?',
    'prospectus_scope_statement':
        'Invasive species monitoring contributes to valuations of: habitat for '
        'species, maintenance of genetic diversity, climate regulation.',
    'baseline_question':
        'What proportion of the plants growing in and immediately around your '
        'restoration site are invasive or non-native species competing with '
        'the mangroves?',
    'why_matters':
        'Invasive plants can outcompete mangrove seedlings for light and '
        'space, reducing restoration success. Common invaders in mangrove '
        'zones include Prosopis (mesquite), Casuarina (she-oak in some '
        'regions), and introduced grass species colonising adjacent land. '
        'Keeping invasive cover low is one of the most impactful management '
        'actions a restoration team can take.',
    'field_method':
        '1. Walk slowly across your site and the land immediately bordering '
        'it.\n'
        '2. Look for plants clearly different from the mangrove species being '
        'restored — particularly fast-growing shrubs, trees, or dense grass '
        'species forming impenetrable mats.\n'
        '3. Estimate the percentage of total vegetation area they occupy.\n'
        '4. Photograph unknown plants and use the iNaturalist app or ask a '
        'local botanist or forestry officer to identify them.\n\n'
        'If unsure which plants are invasive in your area, contact your local '
        'forestry or environment agency — they will usually have a list of '
        'main problem species.',
    'remote_sensing_alternative':
        'NDVI time series showing rapid colonisation of gaps between planted '
        'areas may indicate invasive growth, but field confirmation is needed.',
    'sources': None,
    'service_weights': {
        'food_provisioning': 'secondary',
        'water_provisioning': 'secondary',
        'genetic_resources': 'secondary',
        'air_quality_regulation': 'secondary',
        'climate_regulation': 'secondary',
        'moderation_of_extreme_events': 'secondary',
        'water_flow_regulation': 'secondary',
        'waste_treatment': 'secondary',
        'erosion_prevention': 'secondary',
        'habitat_for_species': 'primary',
        'genetic_diversity': 'primary',
        'recreation_and_tourism': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Severely invaded',
         'criteria': '>60% — invasives dominate the site',
         'meaning': None, 'sort_order': 1},
        {'score': 0.3,  'label': 'Heavily invaded',
         'criteria': '40–60%',
         'meaning': None, 'sort_order': 2},
        {'score': 0.5,  'label': 'Moderately invaded',
         'criteria': '20–40%',
         'meaning': None, 'sort_order': 3},
        {'score': 0.75, 'label': 'Lightly invaded',
         'criteria': '10–20%',
         'meaning': None, 'sort_order': 4},
        {'score': 0.9,  'label': 'Minimal',
         'criteria': '<10% — occasional individuals only',
         'meaning': None, 'sort_order': 5},
        {'score': 1.0,  'label': 'None detected',
         'criteria': 'No invasive species observed',
         'meaning': None, 'sort_order': 6},
    ],
    'followups': [],
}


# HD applies cross-cutting × multiplier on every TEEB service.
_HD_MULTIPLIER_SERVICES = {
    slug: 'multiplier' for slug in CANONICAL_TEEB_SLUGS
}

# HD disturbance-source dropdown options. Each option is ecosystem-scoped:
# 'ecosystems' lists the EVE ecosystem display names it applies to, or '*'
# for universal. The renderer (see followup_option_labels) filters by the
# project's ecosystem. Universal + Mangrove options are live today; the
# Seagrass / Freshwater Wetland / Peatland entries are scaffold — they
# activate automatically when those project types are seeded.
_HD_DISTURBANCE_SOURCE_OPTIONS = [
    {'label': 'Agricultural encroachment or conversion',          'ecosystems': ['*']},
    {'label': 'Illegal or unsustainable logging / wood cutting',  'ecosystems': ['*']},
    {'label': 'Livestock grazing or trampling',                   'ecosystems': ['*']},
    {'label': 'Burning (uncontrolled fire)',                      'ecosystems': ['*']},
    {'label': 'Industrial or infrastructure development',         'ecosystems': ['*']},
    {'label': 'Waste dumping or pollution',                       'ecosystems': ['*']},
    {'label': 'Hunting or poaching',                              'ecosystems': ['*']},
    {'label': 'Tourism or recreational pressure',                 'ecosystems': ['*']},
    # Mangrove + Seagrass
    {'label': 'Aquaculture expansion',                            'ecosystems': ['Mangroves', 'Seagrass']},
    {'label': 'Coastal reclamation or land-filling',              'ecosystems': ['Mangroves', 'Seagrass']},
    {'label': 'Destructive fishing (blast fishing, trawling, poison)', 'ecosystems': ['Mangroves', 'Seagrass']},
    {'label': 'Boat traffic or anchoring damage',                 'ecosystems': ['Mangroves', 'Seagrass']},
    # Freshwater Wetland
    {'label': 'Drainage or water abstraction',                    'ecosystems': ['Freshwater Wetland']},
    {'label': 'Dam construction or water diversion',              'ecosystems': ['Freshwater Wetland']},
    # Peatland
    {'label': 'Drainage ditching',                                'ecosystems': ['Peatland']},
    {'label': 'Peat extraction',                                  'ecosystems': ['Peatland']},
    {'label': 'Other (describe in notes)',                        'ecosystems': ['*']},
]


_HD = {
    'slug': 'human_disturbance_pressure', 'code': 'HD',
    'name': 'Human Disturbance Pressure',
    'is_mandatory': True,
    'applicable_ecosystems': None,
    'mapping_kind': 'band_lookup', 'mapping_params': {'multiplier_exponent': 0.5},
    'weight': 1.0,
    'card_description':
        'Assesses the intensity of human activity at and around your '
        'restoration site. Applied as a risk modifier across all ecosystem '
        'service valuations — a site under active threat is worth less to '
        'investors than an identical site that is secure.',
    'commitment_question':
        'This indicator is required for all projects and cannot be deselected.',
    'prospectus_scope_statement':
        'Human disturbance pressure is a mandatory cross-cutting multiplier '
        'applied to all ecosystem service valuations. The score reflects '
        'whether the site\'s ecological condition is at risk of deteriorating '
        'before value is realised.',
    'baseline_question':
        'What is the dominant human pressure currently affecting your '
        'restoration site and its immediate surroundings? If multiple '
        'pressures are present, select the one causing the most damage.',
    'why_matters':
        'Human disturbance is the most important context factor for '
        'interpreting all other scores on your project. A site with excellent '
        'canopy cover under active logging threat has a fundamentally '
        'different outlook from the same structural score under full '
        'community protection — because one is recovering and the other is '
        'not.\n\n'
        'Research on mangrove and other coastal ecosystems has shown that '
        'human disturbance simultaneously degrades all ecosystem services: '
        'disturbed mangroves show 80% reductions in microbial decomposition '
        'rates, significant carbon stock loss, and 20% biodiversity loss '
        'compared to undisturbed sites (Danovaro et al. 2018, Scientific '
        'Reports). No single ecological indicator captures this cross-cutting '
        'effect.\n\n'
        'In EVE\'s calculation, your HD score is applied as a risk multiplier '
        'on top of all other service valuations. A score of 50 (moderate '
        'disturbance) reduces all service values by approximately 29%. A '
        'score of 10 (severe active disturbance) reduces all service values '
        'by approximately 68%.\n\n'
        'This multiplier reflects investment risk as much as ecological '
        'reality — investors and verifiers need to know whether the natural '
        'capital your project is generating is secure.',
    'field_method':
        'Observe the site and its immediate surroundings. Walk the boundary. '
        'Talk to community members. Select the option below that best '
        'describes the current situation.',
    'remote_sensing_alternative':
        'Land-use change time series (Sentinel-2 / Landsat) can flag clearing '
        'or development pressure but does not capture grazing, fishing, or '
        'cultural pressures. Field observation remains the primary source.',
    'sources': None,
    'service_weights': _HD_MULTIPLIER_SERVICES,
    'bands': [
        {'score': 0.1,  'label': 'Severe and active',
         'criteria': 'The site is being actively damaged right now — '
                     'clearing, burning, draining, overfishing, or illegal '
                     'logging is occurring. Restoration is under immediate '
                     'and serious threat. This level of disturbance will '
                     'prevent recovery regardless of other conditions at the '
                     'site.',
         'meaning': None, 'sort_order': 1},
        {'score': 0.3,  'label': 'Significant',
         'criteria': 'Frequent damaging activity is occurring — weekly or '
                     'monthly unauthorised cutting, intensive fishing, '
                     'regular burning, livestock overgrazing, or waste '
                     'dumping. The site is degrading faster than it is '
                     'recovering. Significant management intervention is '
                     'needed.',
         'meaning': None, 'sort_order': 2},
        {'score': 0.5,  'label': 'Moderate',
         'criteria': 'Some illegal or unsustainable use is occurring '
                     'occasionally, or neighbouring land use is creating '
                     'persistent pressure on the site — but the site is not '
                     'in immediate danger and is capable of net recovery '
                     'with current management. This is the situation for '
                     'many community restoration projects.',
         'meaning': None, 'sort_order': 3},
        {'score': 0.75, 'label': 'Low',
         'criteria': 'The site is broadly respected and protected. Minor '
                     'casual disturbance occurs — occasional foot traffic, '
                     'small-scale sustainable collection, light fishing — '
                     'but nothing that significantly limits recovery. '
                     'Community awareness of the project is good.',
         'meaning': None, 'sort_order': 4},
        {'score': 0.9,  'label': 'Minimal',
         'criteria': 'The site has active community or institutional '
                     'protection. Disturbance events are rare and quickly '
                     'addressed. The restoration is operating in a '
                     'supportive environment.',
         'meaning': None, 'sort_order': 5},
        {'score': 1.0,  'label': 'None',
         'criteria': 'No human disturbance is observed or reported. The site '
                     'is remote, legally protected, or has such strong '
                     'community stewardship that disturbance does not occur. '
                     'Full natural recovery potential is available.',
         'meaning': None, 'sort_order': 6},
    ],
    'followups': [
        {'slug': 'disturbance_source',
         'question_text': 'What is the main source of this disturbance?',
         'input_kind': 'select',
         'options': _HD_DISTURBANCE_SOURCE_OPTIONS,
         'trigger_max_score': 0.5,
         'sort_order': 1},
        {'slug': 'mitigation_plan',
         'question_text': 'Is there a plan to reduce this pressure?',
         'input_kind': 'select',
         'options': [
             {'label': 'Yes — there is a plan',                'ecosystems': ['*']},
             {'label': 'Not yet — but we are working on it',   'ecosystems': ['*']},
             {'label': 'No',                                   'ecosystems': ['*']},
         ],
         'trigger_max_score': 0.5,
         'sort_order': 2},
    ],
}


def followup_option_labels(options, ecosystem_display_name=None):
    """Normalise a followup's stored ``options`` to a flat list of label
    strings, filtered to those applicable to ``ecosystem_display_name``.

    Supports two option schemas so both old and new seed data render:
      * legacy — a flat list of strings (all treated as universal)
      * scoped — a list of ``{'label': str, 'ecosystems': [<name>|'*']}``

    Passing ``ecosystem_display_name=None`` returns every option unfiltered.
    """
    out = []
    for opt in (options or []):
        if isinstance(opt, str):
            out.append(opt)
            continue
        if not isinstance(opt, dict):
            continue
        label = opt.get('label')
        if not label:
            continue
        scopes = opt.get('ecosystems') or ['*']
        if ('*' in scopes or ecosystem_display_name is None
                or ecosystem_display_name in scopes):
            out.append(label)
    return out


DEFAULT_INDICATORS = [_M1, _M2, _M3, _M4, _M5, _M6, _M7, _HD]


DEFAULT_PROJECT_TYPE_INDICATORS = [
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_canopy_cover',
     'sort_order': 1, 'is_recommended': True},
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_seedling_density',
     'sort_order': 2, 'is_recommended': False},
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_natural_recruitment',
     'sort_order': 3, 'is_recommended': False},
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_tidal_flow',
     'sort_order': 4, 'is_recommended': True},
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_water_clarity',
     'sort_order': 5, 'is_recommended': False},
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_wildlife_signs',
     'sort_order': 6, 'is_recommended': False},
    {'project_type': 'mangrove_restoration', 'indicator': 'mangrove_invasive_pressure',
     'sort_order': 7, 'is_recommended': False},
    # HD is intentionally absent here — it is attached to every project type
    # automatically by seed_project_indicators() (see UNIVERSAL_INDICATOR_SLUGS).
]


def seed_project_indicators(session) -> bool:
    """Idempotent seed of pi_* taxonomy. Bails when pi_project_types is non-empty.

    Pass an active SQLAlchemy session. Returns True if seed ran, False if skipped.
    """
    from database import (
        ProjectType, Indicator, IndicatorBand, IndicatorFollowup,
        ProjectTypeIndicator,
    )

    if session.query(ProjectType).count() > 0:
        return False

    project_type_rows = {}
    for pt in DEFAULT_PROJECT_TYPES:
        row = ProjectType(
            slug=pt['slug'], name=pt['name'],
            description=pt.get('description'), icon=pt.get('icon'),
            ecosystem_type=pt.get('ecosystem_type'),
            is_active=True, sort_order=pt.get('sort_order', 0),
        )
        session.add(row)
        session.flush()
        project_type_rows[pt['slug']] = row

    indicator_rows = {}
    for ind in DEFAULT_INDICATORS:
        row = Indicator(
            slug=ind['slug'], code=ind['code'], name=ind['name'],
            commitment_question=ind['commitment_question'],
            prospectus_scope_statement=ind['prospectus_scope_statement'],
            baseline_question=ind['baseline_question'],
            card_description=ind.get('card_description'),
            why_matters=ind.get('why_matters'),
            field_method=ind.get('field_method'),
            remote_sensing_alternative=ind.get('remote_sensing_alternative'),
            sources=ind.get('sources'),
            applicable_ecosystems=ind.get('applicable_ecosystems'),
            is_mandatory=ind.get('is_mandatory', False),
            mapping_kind=ind.get('mapping_kind', 'band_lookup'),
            mapping_params=ind.get('mapping_params', {}),
            service_weights=ind.get('service_weights'),
            weight=ind.get('weight', 1.0),
            is_active=True,
        )
        session.add(row)
        session.flush()
        indicator_rows[ind['slug']] = row

        for band in ind.get('bands', []):
            session.add(IndicatorBand(
                indicator_id=row.id,
                score=band['score'], label=band['label'],
                criteria=band['criteria'], meaning=band.get('meaning'),
                sort_order=band['sort_order'],
            ))
        for followup in ind.get('followups', []):
            session.add(IndicatorFollowup(
                indicator_id=row.id,
                slug=followup['slug'],
                question_text=followup['question_text'],
                input_kind=followup['input_kind'],
                options=followup.get('options'),
                trigger_max_score=followup.get('trigger_max_score'),
                sort_order=followup.get('sort_order', 0),
            ))

    for join in DEFAULT_PROJECT_TYPE_INDICATORS:
        pt_row = project_type_rows.get(join['project_type'])
        ind_row = indicator_rows.get(join['indicator'])
        if not pt_row or not ind_row:
            continue
        session.add(ProjectTypeIndicator(
            project_type_id=pt_row.id,
            indicator_id=ind_row.id,
            sort_order=join.get('sort_order', 0),
            is_recommended=join.get('is_recommended', False),
            weight_override=join.get('weight_override'),
        ))

    # Attach universal cross-cutting indicators (HD) to every project type.
    # sort_order 999 keeps them last; is_recommended so they read as part of
    # the default set. Any future project type inherits these automatically.
    _explicit = {
        (j['project_type'], j['indicator']) for j in DEFAULT_PROJECT_TYPE_INDICATORS
    }
    for pt_slug, pt_row in project_type_rows.items():
        for uni_slug in UNIVERSAL_INDICATOR_SLUGS:
            ind_row = indicator_rows.get(uni_slug)
            if not ind_row or (pt_slug, uni_slug) in _explicit:
                continue
            session.add(ProjectTypeIndicator(
                project_type_id=pt_row.id,
                indicator_id=ind_row.id,
                sort_order=999,
                is_recommended=True,
            ))

    session.commit()
    return True

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
    {
        'slug': 'tropical_forest_reforestation',
        'name': 'Tropical Forest Reforestation',
        'icon': '🌴',
        'ecosystem_type': 'Tropical Forest',
        'description': (
            'Field-measurable indicator set for tropical forest reforestation '
            'and REDD+ projects. Seven ecological indicators completable in a '
            'half-day field visit by a trained non-specialist team, covering '
            'the key structural and functional drivers of carbon, biodiversity, '
            'and ecosystem service recovery.'
        ),
        'sort_order': 2,
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


# TODO: Add indicator sets for Temperate Forest, Peatland,
# Freshwater Wetland, Grassland, Seagrass following the same pattern.
# Each requires only a new project type in DEFAULT_PROJECT_TYPES,
# new indicator dicts, entries in DEFAULT_INDICATORS and
# DEFAULT_PROJECT_TYPE_INDICATORS, and a resource entry in
# app.py's PROJECT_INDICATOR_RESOURCES. No other files need changing.
#
# ── Tropical Forest Reforestation indicators ─────────────────────────────────
# TF2 introduces a permanent 20m x 20m plot; TF3/TF4/TF5 reuse it.

_TF1 = {
    'slug': 'tf_canopy_cover', 'code': 'TF1', 'name': 'Canopy Cover',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team estimate the proportion of sky covered by tree canopy '
        'at multiple points across your site?',
    'prospectus_scope_statement':
        'Canopy cover monitoring contributes to valuations of: air quality '
        'regulation, climate regulation, extreme event moderation, erosion '
        'prevention, habitat for species, aesthetic information, raw materials, '
        'water flow regulation, recreation and tourism, genetic diversity.',
    'baseline_question':
        "Estimate how complete your restoration site's tree canopy looks "
        "compared to a mature reference forest (full instructions below).",
    'why_matters':
        "Canopy cover is the foundational structural indicator of tropical "
        "forest restoration progress and the single most important predictor of "
        "ecosystem service recovery. A closed canopy creates the conditions for "
        "everything else: it reduces soil temperature and moisture loss, "
        "suppresses weed and invasive competition, provides habitat for "
        "forest-interior species, and directly determines the site's "
        "contribution to climate regulation, air quality, and storm protection.\n\n"
        "Meta-analyses of recovering tropical forests show that canopy closure "
        "typically precedes recovery of other structural attributes by years to "
        "decades, making canopy cover both the earliest measurable signal of "
        "success and the strongest single predictor of long-term recovery "
        "trajectory (Poorter et al., 2016). It is also the primary "
        "remote-sensing-verifiable indicator, which makes it the anchor of any "
        "credible monitoring programme.\n\n"
        "In EVE's calculation, canopy cover applies primarily to climate "
        "regulation, air quality regulation, extreme event moderation, and "
        "erosion prevention — the regulating services that typically constitute "
        "over half of total ecosystem service value in tropical forest contexts.",
    'field_method':
        "Before your first monitoring visit, establish a permanent 20m x 20m "
        "plot at a representative location in the restoration site. Mark the "
        "four corners with painted stakes or GPS waypoints and record the "
        "coordinates. All plot-based indicators (TF2, TF3, TF4, TF5) use this "
        "same plot — set it up once and return to it on every visit.\n\n"
        "1. Stand at five points within the plot: the four corners and the centre.\n"
        "2. At each point, hold your smartphone flat above your head, camera "
        "facing directly upward.\n"
        "3. Take a photograph straight up into the canopy.\n"
        "4. Estimate the percentage of the image covered by leaves and branches "
        "versus open sky.\n"
        "5. Average your five estimates and record the result as a percentage.\n\n"
        "If you do not have a smartphone: at each point look straight up through "
        "a cardboard tube and estimate the proportion of sky visible in a fixed "
        "field of view. Less precise but acceptable for community monitoring.\n\n"
        "Note separately any visible mid-canopy or understorey layers — tropical "
        "forests are multi-layered, and 75% cover in a two-layered young forest "
        "means something different from the same score in a single-layer pioneer "
        "stand. Measure at midday when shadows are shortest, and avoid measuring "
        "immediately after leaf fall or storm damage, which temporarily reduce "
        "apparent cover.",
    'remote_sensing_alternative':
        "Sentinel-2 NDVI above 0.6 typically corresponds to more than 50% canopy "
        "cover in humid tropical forest, and above 0.75 generally indicates a "
        "closed canopy. Access via Copernicus Browser (free) or Google Earth "
        "Engine. The GEDI canopy cover product gives direct percentage estimates "
        "at 25m resolution for sites larger than 1ha. Calibrate against a nearby "
        "intact reference patch, as NDVI-cover relationships vary by forest type "
        "and season.",
    'sources':
        "Poorter et al. 2016 (Nature) — secondary forest recovery trajectories; "
        "Chazdon 2014, Second Growth — canopy closure as primary milestone; "
        "ITTO 2002 Guidelines (Policy Development Series No. 13); "
        "SER 2019 International Principles and Standards (Attribute 2).",
    'service_weights': {
        'air_quality_regulation': 'primary',
        'climate_regulation': 'primary',
        'moderation_of_extreme_events': 'primary',
        'erosion_prevention': 'primary',
        'habitat_for_species': 'primary',
        'genetic_diversity': 'secondary',
        'aesthetic_information': 'primary',
        'recreation_and_tourism': 'secondary',
        'water_flow_regulation': 'secondary',
        'raw_materials': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Bare or cleared',     'criteria': '<10%',
         'meaning': 'Open ground; no canopy function', 'sort_order': 1},
        {'score': 0.3,  'label': 'Very early stage',    'criteria': '10–25%',
         'meaning': 'Scattered pioneer trees only', 'sort_order': 2},
        {'score': 0.5,  'label': 'Early recovery',      'criteria': '25–50%',
         'meaning': 'Patchy canopy; gaps dominant', 'sort_order': 3},
        {'score': 0.75, 'label': 'Developing canopy',   'criteria': '50–70%',
         'meaning': 'Continuous but uneven cover', 'sort_order': 4},
        {'score': 0.9,  'label': 'Near reference',      'criteria': '70–85%',
         'meaning': 'Dense closed canopy forming', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference condition', 'criteria': '>85%',
         'meaning': 'Closed multi-layered canopy', 'sort_order': 6},
    ],
    'followups': [],
}


_TF2 = {
    'slug': 'tf_tree_species_richness', 'code': 'TF2',
    'name': 'Tree Species Richness',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team identify and count the different native tree species '
        'growing in a marked plot on your site?',
    'prospectus_scope_statement':
        'Tree species richness monitoring contributes to valuations of: genetic '
        'resources, genetic diversity, habitat for species, climate regulation, '
        'raw materials, medicinal resources, food provisioning.',
    'baseline_question':
        'In a 20m x 20m plot, how many different native tree species (stems over '
        '5cm thick) can you count?',
    'why_matters':
        "Native tree species richness is the most direct measure of whether a "
        "restored forest is recovering its biodiversity capital — the genetic "
        "reservoir that underpins long-term resilience, provisioning services, "
        "and the ecological interactions (pollination, seed dispersal, "
        "predator-prey relationships) on which all other functions depend.\n\n"
        "A site dominated by one or a few fast-growing pioneers may score well on "
        "canopy cover quickly but remain functionally impoverished: limited "
        "habitat for forest specialists, lower resistance to pest and disease "
        "outbreaks, fewer pollinators, and a tendency to stall in succession "
        "without a diverse species pool. High native richness early in "
        "restoration shows planting stock, seed sourcing, and site conditions are "
        "aligned for long-term recovery.\n\n"
        "Rozendaal et al. (2019) found biodiversity recovery in Neotropical "
        "secondary forests takes far longer than biomass recovery — richness at "
        "20 years was about 80% of reference even when biomass had fully "
        "recovered — which makes early richness a leading indicator of "
        "trajectory. It also underpins the supporting services in TEEB valuation "
        "and is increasingly material for biodiversity credit schemes and TNFD "
        "disclosure.",
    'field_method':
        "Use the permanent 20m x 20m plot established for TF1.\n\n"
        "1. Walk slowly through the plot and find every tree or woody shrub with "
        "a stem thicker than 5cm at breast height (about 1.3m up). A tape "
        "wrapped around the stem reading 15.7cm circumference or more equals 5cm "
        "diameter.\n"
        "2. Record each species separately. You do not need the scientific name — "
        "a clear description and photo is enough. Use the iNaturalist app: "
        "photograph leaf, bark, and any fruit or flowers.\n"
        "3. Count only native species. If unsure whether a species is native, "
        "record it and flag for confirmation. Your local forestry office or "
        "university botany department can usually provide a native species list.\n"
        "4. Record the total count of distinct native tree species as your score.\n"
        "5. On later visits, check for and record any species that have arrived "
        "naturally since the last visit — a quality signal worth noting.\n\n"
        "Use the same plot boundaries every visit; verify your start position "
        "against the recorded GPS coordinates before counting.",
    'remote_sensing_alternative':
        "Not available for a direct species count — field measurement is "
        "required. Hyperspectral imagery can distinguish species in research "
        "settings but is not operationally available for community monitoring. "
        "As a weak qualitative cross-check, patchy (heterogeneous) NDVI within "
        "the plot correlates loosely with higher diversity in some forest types.",
    'sources':
        "Rozendaal et al. 2019 (Science Advances) — recovery trajectory; "
        "Chazdon 2014, Second Growth; ITTO 2002 Guidelines; "
        "Brancalion et al. 2019 (Science Advances); "
        "SER 2019 Standards (Attribute 5); Verra VM0007 REDD+ Framework.",
    'service_weights': {
        'genetic_resources': 'primary',
        'genetic_diversity': 'primary',
        'habitat_for_species': 'primary',
        'climate_regulation': 'secondary',
        'raw_materials': 'secondary',
        'medicinal_resources': 'secondary',
        'food_provisioning': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Monoculture',        'criteria': '1 species',
         'meaning': 'Plantation or single-species stand', 'sort_order': 1},
        {'score': 0.3,  'label': 'Very low',           'criteria': '2–4 species',
         'meaning': 'Very low diversity', 'sort_order': 2},
        {'score': 0.5,  'label': 'Low',                'criteria': '5–9 species',
         'meaning': 'Low diversity', 'sort_order': 3},
        {'score': 0.75, 'label': 'Moderate',           'criteria': '10–19 species',
         'meaning': 'Moderate diversity', 'sort_order': 4},
        {'score': 0.9,  'label': 'High',               'criteria': '20–35 species',
         'meaning': 'High diversity', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference diversity', 'criteria': '>35 species',
         'meaning': 'Comparable to intact forest', 'sort_order': 6},
    ],
    'followups': [],
}


_TF3 = {
    'slug': 'tf_canopy_height', 'code': 'TF3', 'name': 'Canopy Height',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team measure the height of the tallest trees in a marked plot '
        'on your site?',
    'prospectus_scope_statement':
        'Canopy height monitoring contributes to valuations of: climate '
        'regulation, raw materials, air quality regulation, extreme event '
        'moderation, habitat for species, aesthetic information.',
    'baseline_question':
        'What is the average height of the five tallest trees in your plot '
        '(full instructions below)?',
    'why_matters':
        "Canopy height is the structural attribute most directly correlated with "
        "above-ground carbon stocks. Taller trees hold disproportionately more "
        "biomass — a 25m canopy holds roughly four to five times the above-ground "
        "carbon of a 10m canopy at equivalent cover, because biomass scales "
        "steeply with stem diameter and height predicts diameter at maturity.\n\n"
        "For investors it matters for three reasons. It is independently "
        "verifiable by satellite (GEDI and ICESat-2 give free, non-manipulable "
        "height estimates for third-party verification). It tracks the carbon "
        "sequestration trajectory more faithfully than cover alone, since cover "
        "can close quickly while height and biomass accumulate over decades. And "
        "it captures the provisioning services (timber, non-timber products) that "
        "require structural maturity.\n\n"
        "Height recovery follows a predictable curve: slow initial growth, rapid "
        "acceleration during competitive exclusion (years 5–15), then asymptotic "
        "approach to mature heights over decades (Poorter et al., 2016). Knowing "
        "where a project sits on this curve is essential for realistic eROI "
        "projections.",
    'field_method':
        "Use the permanent 20m x 20m plot established for TF1.\n\n"
        "1. Identify the five tallest trees within or immediately adjacent to "
        "the plot.\n"
        "2. For each, stand at a distance roughly equal to its height and use a "
        "clinometer or a free smartphone clinometer app to measure the angle to "
        "the treetop.\n"
        "3. Calculate height = distance x tan(angle). Most apps do this "
        "automatically; with a manual clinometer, record the angle and calculate "
        "afterwards.\n"
        "4. Record the five heights and average them. This average of the five "
        "tallest trees is your score.\n\n"
        "No clinometer? Hold a stick of known length at arm's length: tree height "
        "is approximately (tree apparent height / stick apparent height) x "
        "distance to tree. Less precise but fine at band resolution. Measure the "
        "same marked trees each visit where possible, but always measure the five "
        "tallest present.",
    'remote_sensing_alternative':
        "The NASA/USGS GEDI canopy height product gives global estimates at 25m "
        "resolution via Google Earth Engine, free of charge; the ESA BIOMASS "
        "mission and ICESat-2 provide complementary data. For sites over 2ha, "
        "GEDI is typically within 2–3m of field measurements in tropical forest "
        "and can independently corroborate field data. "
        "Product: https://lpdaac.usgs.gov/products/gedi02_bv002/",
    'sources':
        "Dubayah et al. 2020 (GEDI methodology); Poorter et al. 2016 (Nature) — "
        "height recovery; Chave et al. 2014 (Global Change Biology) — "
        "height-biomass; Asner et al. 2014 (PNAS); "
        "IPCC 2006 AFOLU Guidelines Vol. 4 Ch. 4 (Tier 2 biomass).",
    'service_weights': {
        'climate_regulation': 'primary',
        'raw_materials': 'primary',
        'air_quality_regulation': 'secondary',
        'moderation_of_extreme_events': 'secondary',
        'habitat_for_species': 'secondary',
        'aesthetic_information': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Shrub stage',     'criteria': '<2m',
         'meaning': 'Shrub or early seedling stage', 'sort_order': 1},
        {'score': 0.3,  'label': 'Early pioneer',   'criteria': '2–5m',
         'meaning': 'Early pioneer stage', 'sort_order': 2},
        {'score': 0.5,  'label': 'Mid-succession',  'criteria': '5–10m',
         'meaning': 'Mid-succession canopy', 'sort_order': 3},
        {'score': 0.75, 'label': 'Developing',      'criteria': '10–18m',
         'meaning': 'Developing mature canopy', 'sort_order': 4},
        {'score': 0.9,  'label': 'Near mature',     'criteria': '18–25m',
         'meaning': 'Approaching mature tropical forest structure', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference height', 'criteria': '>25m',
         'meaning': 'Reference mature canopy height', 'sort_order': 6},
    ],
    'followups': [],
}


_TF4 = {
    'slug': 'tf_native_regeneration', 'code': 'TF4',
    'name': 'Native Species Natural Regeneration',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team count young native seedlings and saplings that have '
        'established in marked subplots on your site?',
    'prospectus_scope_statement':
        'Natural regeneration monitoring contributes to valuations of: genetic '
        'diversity, habitat for species, genetic resources, climate regulation, '
        'raw materials.',
    'baseline_question':
        'In a 5m x 5m subplot, how many native seedlings and saplings under '
        '1.3m tall can you count?',
    'why_matters':
        "Natural regeneration of native species is the strongest indicator that "
        "a site is transitioning from a managed planting to a self-sustaining "
        "ecosystem. When native seedlings arrive and establish without being "
        "planted, it shows that seed sources are present in the landscape, that "
        "site conditions suit germination and early growth, and that seed "
        "dispersal — by birds, mammals, wind, and water — is functioning.\n\n"
        "A site that reaches canopy closure on planted stock alone but shows no "
        "natural regeneration is ecologically fragile and depends on continued "
        "intervention. Abundant natural regeneration signals autonomous recovery "
        "— the strongest signal for long-term value and the lowest ongoing cost "
        "basis.\n\n"
        "Crouzeilles et al. (2017) found passive regeneration can be more "
        "cost-effective than active planting where seed sources are within "
        "dispersal range, so the presence or absence of natural regeneration "
        "feeds directly into the long-term maintenance-cost assumptions in EVE's "
        "investment model.",
    'field_method':
        "Use the permanent 20m x 20m plot established for TF1. Within it, mark "
        "three 5m x 5m subplots: one at the north-west corner, one at the "
        "south-east corner, and one at the centre.\n\n"
        "1. In each subplot, count all seedlings and saplings shorter than 1.3m.\n"
        "2. Count only native species; if unsure of origin, record and photograph "
        "for later identification.\n"
        "3. Distinguish plants you know were planted (from your planting records) "
        "from those that arrived naturally. Natural recruits — found outside "
        "planting rows, in unexpected spots, or of species not in your stock — "
        "are especially valuable; record them separately.\n"
        "4. Average the three subplot counts and record as your score.\n\n"
        "Survey in the same season each year where possible — seedling density "
        "peaks after rains in many tropical forests, so mixing wet- and "
        "dry-season counts between years adds noise.",
    'remote_sensing_alternative':
        "Not available for this indicator — seedling and sapling counts require "
        "direct field observation.",
    'sources':
        "Crouzeilles et al. 2017 (Science Advances) — natural regeneration and "
        "cost comparison; Poorter et al. 2016 (Nature) — regeneration density "
        "benchmarks; Chazdon 2014, Second Growth (Ch. 5–7); "
        "SER 2019 Standards (Attribute 6); NatureServe 2019 Ecological "
        "Resilience Indicators.",
    'service_weights': {
        'genetic_diversity': 'primary',
        'habitat_for_species': 'primary',
        'genetic_resources': 'primary',
        'climate_regulation': 'secondary',
        'raw_materials': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'None',       'criteria': '0',
         'meaning': 'No regeneration; site not self-sustaining', 'sort_order': 1},
        {'score': 0.3,  'label': 'Very sparse', 'criteria': '1–4',
         'meaning': 'Isolated recruits only', 'sort_order': 2},
        {'score': 0.5,  'label': 'Some',       'criteria': '5–14',
         'meaning': 'Recruitment beginning', 'sort_order': 3},
        {'score': 0.75, 'label': 'Good',       'criteria': '15–29',
         'meaning': 'Active natural regeneration across site', 'sort_order': 4},
        {'score': 0.9,  'label': 'Dense',      'criteria': '30–50',
         'meaning': 'Strong natural regeneration', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference',  'criteria': '>50',
         'meaning': 'Comparable to intact forest understorey', 'sort_order': 6},
    ],
    'followups': [],
}


_TF5 = {
    'slug': 'tf_litter_layer', 'code': 'TF5',
    'name': 'Leaf Litter and Soil Organic Layer',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team measure the depth of the leaf-litter layer at several '
        'points across your site?',
    'prospectus_scope_statement':
        'Leaf litter and soil organic layer monitoring contributes to valuations '
        'of: climate regulation, erosion prevention, water flow regulation, '
        'habitat for species, water provisioning.',
    'baseline_question':
        'How deep is the leaf-litter layer on your site, averaged across five '
        'points (full instructions below)?',
    'why_matters':
        "The leaf litter and soil organic layer is the interface between the "
        "living forest and the mineral soil, and one of the most important stores "
        "of carbon and nutrients in the system. A deep, continuous litter layer "
        "means the forest is accumulating organic matter faster than it "
        "decomposes — a net carbon-sink signal. It protects mineral soil from "
        "erosion and compaction, slows surface runoff, and supports the soil "
        "invertebrate and fungal communities that drive nutrient cycling.\n\n"
        "Tropical soils are typically nutrient-poor — most nutrients sit in the "
        "living biomass and litter, not the mineral soil — so clearing and "
        "burning rapidly lose that capital. Litter recovery is therefore a proxy "
        "for the return of nutrient cycling and long-term soil fertility.\n\n"
        "Don et al. (2011) found converting tropical forest to cropland cut soil "
        "organic carbon by about 25% in the top 30cm, with the litter layer lost "
        "first and fastest; its recovery is an early signal that soil carbon "
        "sequestration is resuming. For community teams it is one of the simplest "
        "and most motivating measurements — visible, equipment-free, and "
        "detectably changed within 2–3 years of success.",
    'field_method':
        "Use the permanent 20m x 20m plot established for TF1.\n\n"
        "1. Choose five points: the four corners and the centre.\n"
        "2. At each, push a ruler gently and vertically into the litter until you "
        "feel resistance from the mineral soil. Do not compress the litter first.\n"
        "3. Record the depth in centimetres at each point.\n"
        "4. Average the five readings and record.\n\n"
        "The litter/soil boundary is usually clear: litter is dark, fibrous and "
        "compressible; mineral soil is denser, finer, often paler or reddish. If "
        "the transition is gradual (a developing humus layer — a good sign), "
        "measure to where material becomes clearly mineral. Measure in the same "
        "season each year, and note any recent fire, heavy rain, or management "
        "that has disturbed the litter.",
    'remote_sensing_alternative':
        "Not available for direct litter depth. SoilGrids 2.0 (soilgrids.org) "
        "gives modelled soil organic carbon at 250m resolution as landscape "
        "context, but it does not replace direct plot-level measurement.",
    'sources':
        "Don et al. 2011 (Global Change Biology) — soil carbon loss and recovery "
        "benchmarks; Chazdon 2014, Second Growth (Ch. 8); Poorter et al. 2016 "
        "(Nature); IPCC 2006 AFOLU Guidelines Vol. 4 Ch. 2 (litter carbon pool); "
        "Verra VM0007 REDD+ Framework (dead organic matter and soil pools).",
    'service_weights': {
        'climate_regulation': 'primary',
        'erosion_prevention': 'primary',
        'water_flow_regulation': 'primary',
        'habitat_for_species': 'secondary',
        'water_provisioning': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Bare mineral soil', 'criteria': '0cm',
         'meaning': 'No litter layer; severely degraded', 'sort_order': 1},
        {'score': 0.3,  'label': 'Very thin',         'criteria': '<1cm',
         'meaning': 'Early accumulation only', 'sort_order': 2},
        {'score': 0.5,  'label': 'Developing',        'criteria': '1–3cm',
         'meaning': 'Developing litter layer', 'sort_order': 3},
        {'score': 0.75, 'label': 'Good',              'criteria': '3–6cm',
         'meaning': 'Functional soil protection', 'sort_order': 4},
        {'score': 0.9,  'label': 'Deep',              'criteria': '6–10cm',
         'meaning': 'Approaching reference condition', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference depth',   'criteria': '>10cm',
         'meaning': 'Soil fully protected; high soil organic matter', 'sort_order': 6},
    ],
    'followups': [],
}


_TF6 = {
    'slug': 'tf_wildlife_signs', 'code': 'TF6',
    'name': 'Wildlife and Fauna Signs',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team record the different kinds of wildlife seen or heard '
        'during a short walk across your site?',
    'prospectus_scope_statement':
        'Wildlife and fauna monitoring contributes to valuations of: habitat for '
        'species, genetic diversity, recreation and tourism, inspiration, food '
        'provisioning, genetic resources, aesthetic information, spiritual '
        'experience.',
    'baseline_question':
        'During a 30-minute walk, how many distinct types of animal can you see '
        'or hear on your site?',
    'why_matters':
        "Fauna recovery is the most direct measure of whether a restored forest "
        "is functioning as a living ecosystem rather than just a stand of trees. "
        "Animals are not optional extras — frugivorous birds and mammals disperse "
        "the seeds of most tropical tree species, predators regulate herbivores "
        "that would otherwise suppress regeneration, and insectivores control "
        "pest outbreaks that can defoliate young plantings.\n\n"
        "Gardner et al. (2009) found logged and degraded tropical forests support "
        "far lower fauna diversity than intact reference forest, with "
        "forest-interior specialists most vulnerable. The return of these "
        "specialists is a particularly strong quality signal that goes beyond "
        "simple counts.\n\n"
        "For community teams, wildlife recovery is one of the most motivating "
        "indicators and resonates with communities and funders far more than "
        "abstract carbon numbers. It also drives the cultural services — "
        "recreation, inspiration, spiritual experience — increasingly material to "
        "ESG-oriented investors, and it independently corroborates the structural "
        "indicators: strong cover and richness but very low fauna may flag "
        "landscape isolation, hunting pressure, or edge effects.",
    'field_method':
        "Survey in the early morning (first two hours after dawn) or late "
        "afternoon (last two hours before dusk) — activity peaks then for most "
        "tropical forest fauna, and midday surveys undercount.\n\n"
        "1. Walk slowly and quietly through the site, and a short way into any "
        "adjacent forest, for 30 minutes. Stop and listen for at least 2 minutes "
        "every 5 minutes.\n"
        "2. Keep a simple tally: each time you detect a distinct animal type, add "
        "a mark. Count each type once per session even if detected repeatedly.\n"
        "3. Include birds (seen or heard — a song counts), mammals (seen, heard, "
        "or evidenced by fresh tracks, scat, or gnawed fruit), reptiles, frogs, "
        "and conspicuous insects (butterflies, large beetles).\n"
        "4. You do not need species names — a large black-and-yellow bird and a "
        "small brown bird count as two types. Describe and photograph unknowns.\n"
        "5. Record total distinct types detected as your score.\n\n"
        "Optional: a camera trap left 72 hours near a game trail or water source "
        "detects nocturnal mammals that day surveys miss; record separately. "
        "Follow the same route at the same site each year and note any changes in "
        "weather or timing.",
    'remote_sensing_alternative':
        "Not available for direct wildlife observation. Low-cost acoustic "
        "recorders (e.g. AudioMoth) extend detection of birds and bats beyond "
        "human survey effort and are recommended where resources allow; "
        "recordings can be analysed with BirdNET or similar. Camera traps are the "
        "most cost-effective way to detect elusive mammals.",
    'sources':
        "Gardner et al. 2009 (Ecology Letters) — fauna recovery benchmarks; "
        "Chazdon 2014, Second Growth (Ch. 10); SER 2019 Standards (Attribute 7); "
        "Verra VM0007 REDD+ Framework (biodiversity co-benefits); "
        "IUCN 2020 Red List of Ecosystems Guidelines.",
    'service_weights': {
        'habitat_for_species': 'primary',
        'genetic_diversity': 'primary',
        'food_provisioning': 'secondary',
        'genetic_resources': 'secondary',
        'aesthetic_information': 'secondary',
        'recreation_and_tourism': 'primary',
        'inspiration': 'primary',
        'spiritual_experience': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Functionally empty', 'criteria': '0–1 types',
         'meaning': 'Heavily hunted or isolated', 'sort_order': 1},
        {'score': 0.3,  'label': 'Very low',           'criteria': '2–4 types',
         'meaning': 'Very low diversity', 'sort_order': 2},
        {'score': 0.5,  'label': 'Low',                'criteria': '5–8 types',
         'meaning': 'Some forest-dependent species', 'sort_order': 3},
        {'score': 0.75, 'label': 'Moderate',           'criteria': '9–15 types',
         'meaning': 'Fauna returning', 'sort_order': 4},
        {'score': 0.9,  'label': 'Good',               'criteria': '16–25 types',
         'meaning': 'Forest-interior species present', 'sort_order': 5},
        {'score': 1.0,  'label': 'Reference diversity', 'criteria': '>25 types',
         'meaning': 'Intact forest fauna', 'sort_order': 6},
    ],
    'followups': [],
}


_TF7 = {
    'slug': 'tf_invasive_pressure', 'code': 'TF7',
    'name': 'Invasive Species Pressure',
    'is_mandatory': False,
    'applicable_ecosystems': ['Tropical Forest'],
    'mapping_kind': 'band_lookup', 'mapping_params': {},
    'weight': 1.0,
    'commitment_question':
        'Can your team estimate how much of the vegetation on your site is made '
        'up of invasive or non-native plants?',
    'prospectus_scope_statement':
        'Invasive species pressure monitoring contributes to valuations of: '
        'habitat for species, genetic diversity, climate regulation, erosion '
        'prevention, air quality regulation, raw materials, water flow regulation.',
    'baseline_question':
        'What proportion of the vegetation on your site is invasive or '
        'non-native (full instructions below)? Lower invasion scores higher.',
    'why_matters':
        "Invasive and non-native species are one of the most significant threats "
        "to tropical forest restoration globally, and one of the most tractable "
        "to manage. Common invaders — Chromolaena odorata (Siam weed), Lantana "
        "camara, Mikania micrantha (mile-a-minute weed), and Imperata cylindrica "
        "(cogon grass) — form dense mats that suppress native seedlings, "
        "outcompete planted stock for light and nutrients, and can lock a site in "
        "a degraded state even after heavy planting investment.\n\n"
        "Their economic significance goes beyond cover and richness scores: they "
        "raise maintenance costs (weeding, herbicide), lower the chance of "
        "natural regeneration succeeding, and cause planting failures that need "
        "costly replanting. A site may look fine on canopy cover while held in an "
        "early-successional trap.\n\n"
        "Richardson et al. (2011) note that impact is strongly context-dependent "
        "— low-density early invasion is far more tractable than established "
        "infestation — so monitoring and early intervention is much cheaper than "
        "remediation. A high score here (minimal invasion) is a strong quality "
        "signal: native vegetation is competitive, conditions favour the target "
        "ecosystem, and management is effective, all of which lower investment "
        "risk.",
    'field_method':
        "Walk the permanent 20m x 20m plot and a 10m buffer around all four "
        "sides.\n\n"
        "1. Look systematically for plants clearly different from your target "
        "native trees and shrubs. Signs of invasives: fast-growing vines "
        "smothering canopy, dense grass or sedge mats in gaps, spiny shrubs "
        "forming thickets, or unusually large/bright flowers atypical of local "
        "forest.\n"
        "2. Estimate the percentage of total vegetation cover (not ground area) "
        "made up of invasive or non-native species, including climbers on trees, "
        "ground-layer invaders, and invasive pioneer trees.\n"
        "3. Photograph anything you cannot confidently identify and use "
        "iNaturalist. Your local forestry or conservation agency can usually "
        "provide a problem-species list — obtain it before your first survey.\n"
        "4. Record your estimated percentage. Bands are inverted: lower invasive "
        "cover gives a higher intactness score.\n\n"
        "If invasives are found, record their locations and any management "
        "already done — valuable for planning and investor reporting even when "
        "not captured in the band score.",
    'remote_sensing_alternative':
        "Time-series NDVI (Sentinel-2 or Landsat) showing rapid, homogeneous "
        "green-up in gaps — especially in the dry season when native cover "
        "recedes — can flag invasive grass or forb cover, since many tropical "
        "invasives stay green when natives senesce. A qualitative flag requiring "
        "field confirmation, not a quantitative score. Access via Copernicus "
        "Browser or Google Earth Engine.",
    'sources':
        "Mack et al. 2000 (Ecological Applications) — invasion ecology and "
        "control; Richardson et al. 2011 (J. Applied Ecology) — impact "
        "assessment and context-dependence; Chazdon 2014, Second Growth (Ch. 6); "
        "ITTO 2002 Guidelines (Section 4.3); Brancalion et al. 2019 "
        "(Science Advances).",
    'service_weights': {
        'habitat_for_species': 'primary',
        'genetic_diversity': 'primary',
        'climate_regulation': 'secondary',
        'erosion_prevention': 'secondary',
        'air_quality_regulation': 'secondary',
        'raw_materials': 'secondary',
        'water_flow_regulation': 'secondary',
    },
    'bands': [
        {'score': 0.1,  'label': 'Severely invaded',   'criteria': '>60%',
         'meaning': 'Invasives dominate; restoration failing', 'sort_order': 1},
        {'score': 0.3,  'label': 'Heavily invaded',    'criteria': '40–60%',
         'meaning': 'Heavy invasive presence', 'sort_order': 2},
        {'score': 0.5,  'label': 'Moderately invaded', 'criteria': '20–40%',
         'meaning': 'Moderate invasive presence', 'sort_order': 3},
        {'score': 0.75, 'label': 'Lightly invaded',    'criteria': '10–20%',
         'meaning': 'Light invasive presence', 'sort_order': 4},
        {'score': 0.9,  'label': 'Minimal',            'criteria': '<10%',
         'meaning': 'Occasional individuals only', 'sort_order': 5},
        {'score': 1.0,  'label': 'None detected',      'criteria': '0%',
         'meaning': 'No invasive species observed', 'sort_order': 6},
    ],
    'followups': [],
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


DEFAULT_INDICATORS = [
    _M1, _M2, _M3, _M4, _M5, _M6, _M7,
    _TF1, _TF2, _TF3, _TF4, _TF5, _TF6, _TF7,
    _HD,
]


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

    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_canopy_cover',
     'sort_order': 1, 'is_recommended': True},
    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_tree_species_richness',
     'sort_order': 2, 'is_recommended': True},
    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_canopy_height',
     'sort_order': 3, 'is_recommended': True},
    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_native_regeneration',
     'sort_order': 4, 'is_recommended': False},
    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_litter_layer',
     'sort_order': 5, 'is_recommended': False},
    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_wildlife_signs',
     'sort_order': 6, 'is_recommended': False},
    {'project_type': 'tropical_forest_reforestation', 'indicator': 'tf_invasive_pressure',
     'sort_order': 7, 'is_recommended': False},
    # HD is intentionally absent here — it is attached to every project type
    # automatically by seed_project_indicators() (see UNIVERSAL_INDICATOR_SLUGS).
]


def _sync_bands(session, IndicatorBand, indicator_id, bands) -> None:
    """Upsert an indicator's scoring bands, keyed by score (the DB unique key
    is (indicator_id, score)). Never deletes — a band row may be referenced by
    pi_analysis_responses.baseline_band_id / target_band_id, so removing it
    would break user data. A band dropped from the seed simply lingers."""
    existing = {
        b.score: b
        for b in session.query(IndicatorBand).filter_by(indicator_id=indicator_id).all()
    }
    for band in bands:
        row = existing.get(band['score'])
        if row is None:
            row = IndicatorBand(indicator_id=indicator_id, score=band['score'])
            session.add(row)
        row.label = band['label']
        row.criteria = band['criteria']
        row.meaning = band.get('meaning')
        row.sort_order = band['sort_order']


def _sync_followups(session, IndicatorFollowup, indicator_id, followups) -> None:
    """Upsert an indicator's followup questions, keyed by slug (the DB unique
    key is (indicator_id, slug)). Never deletes."""
    existing = {
        f.slug: f
        for f in session.query(IndicatorFollowup).filter_by(indicator_id=indicator_id).all()
    }
    for fu in followups:
        row = existing.get(fu['slug'])
        if row is None:
            row = IndicatorFollowup(indicator_id=indicator_id, slug=fu['slug'])
            session.add(row)
        row.question_text = fu['question_text']
        row.input_kind = fu['input_kind']
        row.options = fu.get('options')
        row.trigger_max_score = fu.get('trigger_max_score')
        row.sort_order = fu.get('sort_order', 0)


def seed_project_indicators(session) -> bool:
    """Idempotent upsert of the pi_* taxonomy, keyed by stable slugs/codes.

    Synchronises the database with the DEFAULT_* definitions in this module.
    Safe to run on every startup:

      * New project types / indicators / bands / followups / assignments are
        inserted.
      * Existing rows are updated in place when their definition changes
        (reworded question, adjusted weight, relabelled band, etc.).
      * Nothing is ever deleted, and the user-data tables
        (pi_analysis_responses, computed_sub_service_multipliers) are never
        touched — only the taxonomy is synced.

    This previously bailed out entirely once any project type existed, which
    meant new indicator sets added to this file never reached an already-seeded
    database (staging/prod). Upserting by slug fixes that: adding a set here now
    lands automatically on the next deploy.

    Pass an active SQLAlchemy session. Returns True (a sync always runs).
    """
    from database import (
        ProjectType, Indicator, IndicatorBand, IndicatorFollowup,
        ProjectTypeIndicator,
    )

    # ── Project types (upsert by slug) ────────────────────────────────────
    project_type_rows = {}
    for pt in DEFAULT_PROJECT_TYPES:
        row = session.query(ProjectType).filter_by(slug=pt['slug']).first()
        if row is None:
            row = ProjectType(slug=pt['slug'])
            session.add(row)
        row.name = pt['name']
        row.description = pt.get('description')
        row.icon = pt.get('icon')
        row.ecosystem_type = pt.get('ecosystem_type')
        row.is_active = True
        row.sort_order = pt.get('sort_order', 0)
        session.flush()
        project_type_rows[pt['slug']] = row

    # ── Indicators + bands + followups (upsert by slug) ───────────────────
    indicator_rows = {}
    for ind in DEFAULT_INDICATORS:
        row = session.query(Indicator).filter_by(slug=ind['slug']).first()
        if row is None:
            row = Indicator(slug=ind['slug'])
            session.add(row)
        row.code = ind['code']
        row.name = ind['name']
        row.commitment_question = ind['commitment_question']
        row.prospectus_scope_statement = ind['prospectus_scope_statement']
        row.baseline_question = ind['baseline_question']
        row.card_description = ind.get('card_description')
        row.why_matters = ind.get('why_matters')
        row.field_method = ind.get('field_method')
        row.remote_sensing_alternative = ind.get('remote_sensing_alternative')
        row.sources = ind.get('sources')
        row.applicable_ecosystems = ind.get('applicable_ecosystems')
        row.is_mandatory = ind.get('is_mandatory', False)
        row.mapping_kind = ind.get('mapping_kind', 'band_lookup')
        row.mapping_params = ind.get('mapping_params', {})
        row.service_weights = ind.get('service_weights')
        row.weight = ind.get('weight', 1.0)
        row.is_active = True
        session.flush()
        indicator_rows[ind['slug']] = row

        _sync_bands(session, IndicatorBand, row.id, ind.get('bands', []))
        _sync_followups(session, IndicatorFollowup, row.id, ind.get('followups', []))

    # ── Assignments (upsert by project_type + indicator) ──────────────────
    def _assign(pt_row, ind_row, sort_order, is_recommended, weight_override=None):
        link = session.query(ProjectTypeIndicator).filter_by(
            project_type_id=pt_row.id, indicator_id=ind_row.id,
        ).first()
        if link is None:
            link = ProjectTypeIndicator(
                project_type_id=pt_row.id, indicator_id=ind_row.id,
            )
            session.add(link)
        link.sort_order = sort_order
        link.is_recommended = is_recommended
        link.weight_override = weight_override

    for join in DEFAULT_PROJECT_TYPE_INDICATORS:
        pt_row = project_type_rows.get(join['project_type'])
        ind_row = indicator_rows.get(join['indicator'])
        if not pt_row or not ind_row:
            continue
        _assign(
            pt_row, ind_row,
            join.get('sort_order', 0),
            join.get('is_recommended', False),
            join.get('weight_override'),
        )

    # Attach universal cross-cutting indicators (HD) to every project type.
    # sort_order 999 keeps them last; is_recommended so they read as part of
    # the default set. Any project type added later inherits these for free.
    _explicit = {
        (j['project_type'], j['indicator']) for j in DEFAULT_PROJECT_TYPE_INDICATORS
    }
    for pt_slug, pt_row in project_type_rows.items():
        for uni_slug in UNIVERSAL_INDICATOR_SLUGS:
            ind_row = indicator_rows.get(uni_slug)
            if not ind_row or (pt_slug, uni_slug) in _explicit:
                continue
            _assign(pt_row, ind_row, 999, True)

    session.commit()
    return True

"""Per-indicator scoring instructions for the project-indicator panel.

Keyed by ``(ecosystem_display_name, indicator_code)`` — e.g.
``('Mangroves', 'M1')`` — so instructions are unique to each
indicator / ecosystem combination.

Each entry has:
  - ``scoring_intro``: one-line instruction shown inside the indicator
    expander, above the scoring controls.
  - ``full_instructions``: an ordered list of blocks rendered in the
    "Full instructions" modal dialog. Block types:
        {'type': 'md',      'content': <markdown str>}
        {'type': 'caption', 'content': <str>}
        {'type': 'link',    'label': <str>, 'url': <str>}      static link
        {'type': 'link',    'label': <str>, 'url_kind': 'gmw'} dynamic link
                                          (Global Mangrove Watch, centred on
                                          the project coordinates)
        {'type': 'soon',    'label': <str>, 'note': <str>}     disabled
                                          button for a not-yet-built feature.
                                          ``[Country/Region]`` in the label is
                                          substituted at render time.

Add a new ``(ecosystem, code)`` key to surface instructions for another
indicator. Indicators with no entry simply show no intro line / button.
"""


_M1_FULL_INSTRUCTIONS = [
    {
        'type': 'md',
        'content': (
            "### Before you score: find your reference\n\n"
            "The quality of your score depends on how clearly you can picture "
            "what a healthy mangrove looks like at your location. Choose the "
            "best option available to you:\n\n"
            "#### Option 1 — Visit a local reference site (recommended)\n\n"
            "**Best for:** Most accurate and locally relevant comparison.\n\n"
            "Find the nearest area of intact, undisturbed mangrove within "
            "reasonable travelling distance of your project site. This is your "
            "reference — the condition your restored mangrove is working "
            "towards.\n\n"
            "**How to find a local reference site:**\n\n"
            "Tap the button below to open Global Mangrove Watch for your "
            "project location. The map shows intact mangrove extent in your "
            "area. Look for a nearby patch that:\n\n"
            "- Has not been logged, cleared, or disturbed in recent years\n"
            "- Has a closed canopy visible from the water or land edge\n"
            "- Is of the same mangrove species as your restoration site if "
            "possible"
        ),
    },
    {
        'type': 'link',
        'label': "Open Global Mangrove Watch for my project location →",
        'url_kind': 'gmw',
    },
    {
        'type': 'caption',
        'content': "Opens globalmangrovewatch.org pre-centred on your project coordinates.",
    },
    {
        'type': 'md',
        'content': (
            "Visit that reference site before or on the same day as your "
            "restoration site assessment. Stand inside the reference mangrove, "
            "look upward at the canopy, and note what you see. Then stand in "
            "your restoration site and compare.\n\n"
            "*If no intact mangrove exists within reasonable distance: use "
            "Option 2 or 3.*\n\n"
            "**[➜ Jump to How to score instructions](#how-to-score)**\n\n"
            "#### Option 2 — Use reference photographs\n\n"
            "**Best for:** When a local reference site visit is not "
            "practical.\n\n"
            "We provide reference photographs showing mangrove canopy at each "
            "condition level for your region. These are drawn from published "
            "research and field documentation and show what each score level "
            "looks like from inside a mangrove stand."
        ),
    },
    {
        'type': 'soon',
        'label': "View reference photos for [Country/Region] →",
        'note': (
            "Coming soon — regional reference photos will be filtered "
            "automatically from your project coordinates."
        ),
    },
    {
        'type': 'md',
        'content': (
            "The photos show six condition levels — from bare or severely "
            "degraded (score 10) through to intact reference condition "
            "(score 100). Find the photo that most closely matches what you "
            "see when you look upward in your restoration site.\n\n"
            "*If regional photos are not yet available for your location:* the "
            "Zöckler et al. visual assessment guide provides illustrated "
            "reference examples from Myanmar and Madagascar, useful for "
            "understanding the condition levels even if the specific species "
            "differ from your site."
        ),
    },
    {
        'type': 'link',
        'label': "View Zöckler et al. reference guide (Myanmar/Madagascar examples) →",
        'url': "https://www.intechopen.com/chapters/74975",
    },
    {
        'type': 'caption',
        'content': "Opens intechopen.com/chapters/74975 — free, open access.",
    },
    {
        'type': 'md',
        'content': (
            "**[➜ Jump to How to score instructions](#how-to-score)**\n\n"
            "#### Option 3 — Use your knowledge of local mangrove\n\n"
            "**Best for:** Experienced team members who know what healthy "
            "mangrove looks like in their area.\n\n"
            "If you have visited intact mangrove in your region before and "
            "have a clear mental picture of what a healthy stand looks like, "
            "you can use that as your reference without a site visit or "
            "photos. This option is less consistent between observers but is "
            "perfectly acceptable for projects in early stages or where "
            "reference sites are very remote.\n\n"
            "When using this option, note in your field notes: *\"Reference "
            "based on observer knowledge of [location/name of reference "
            "mangrove].\"*\n\n"
            "### How to score\n\n"
            "Once you have your reference clearly in mind, walk to 5 "
            "representative points distributed across your restoration site. "
            "Choose points that reflect the typical condition of the site — "
            "not the best patches or the worst patches.\n\n"
            "At each point, look upward at the canopy and ask yourself: "
            "*\"How does this compare to my reference?\"*\n\n"
            "Then select the score that best fits:\n\n"
            "| Score | Label | What it looks like compared to your reference |\n"
            "|---|---|---|\n"
            "| 10 | Bare or absent | No canopy at all, or only a handful of "
            "isolated seedlings. Bare mudflat, bare soil, or open water where "
            "trees should be. Looks nothing like the reference. |\n"
            "| 30 | Very early stage | Scattered young trees visible but "
            "widely spaced. You can see sky almost everywhere you look. The "
            "reference has continuous canopy; this site has almost none. |\n"
            "| 50 | Partial recovery | A patchwork of canopy developing — some "
            "areas are shaded, many gaps remain. Perhaps one third to one half "
            "of what you see in the reference. Your reference has continuous "
            "greenery overhead; this site has islands of it. |\n"
            "| 75 | Good recovery | The canopy is closing. Most of the site is "
            "shaded when you stand inside it. Gaps are present but not "
            "dominant. Looks noticeably similar to the reference, though less "
            "dense, lower, or with more gaps. |\n"
            "| 90 | Near reference | Looks almost like your reference. The "
            "canopy is nearly continuous, well-shaded, and structurally "
            "similar. Small differences remain — perhaps slightly lower "
            "height, slightly more light penetration, or a few persistent "
            "gaps. |\n"
            "| 100 | Equivalent to reference | Indistinguishable from your "
            "reference mangrove when standing inside it. Canopy is closed, "
            "well-shaded, structurally complete. |\n\n"
            "If your site has areas of very different condition, estimate the "
            "score for the whole site as an average across your 5 observation "
            "points.\n\n"
            "### Recording your score\n\n"
            "After walking your 5 points, select the single score that best "
            "represents the site as a whole.\n\n"
            "You can also enter a custom percentage (e.g. 65%) if you feel "
            "your site falls between two of the options above.\n\n"
            "Add a field note describing what you saw — particularly:\n\n"
            "- Which reference you used (visited site, reference photos, or "
            "knowledge)\n"
            "- Any patches of notably better or worse condition\n"
            "- Anything unusual that affected your assessment (recent storm, "
            "new planting, flooding)"
        ),
    },
]


# Per-response-category descriptions, mirroring the M1 'How to score' table.
# (percentage, label, description) — surfaced as the Baseline/Target radio
# help-icon tooltip. Keep in sync with the table in _M1_FULL_INSTRUCTIONS.
_M1_RESPONSE_HELP = [
    (10, 'Bare or absent',
     "No canopy at all, or only a handful of isolated seedlings. Bare "
     "mudflat, bare soil, or open water where trees should be. Looks "
     "nothing like the reference."),
    (30, 'Very early stage',
     "Scattered young trees visible but widely spaced. You can see sky "
     "almost everywhere you look. The reference has continuous canopy; this "
     "site has almost none."),
    (50, 'Partial recovery',
     "A patchwork of canopy developing — some areas are shaded, many gaps "
     "remain. Perhaps one third to one half of what you see in the "
     "reference. Your reference has continuous greenery overhead; this site "
     "has islands of it."),
    (75, 'Good recovery',
     "The canopy is closing. Most of the site is shaded when you stand "
     "inside it. Gaps are present but not dominant. Looks noticeably similar "
     "to the reference, though less dense, lower, or with more gaps."),
    (90, 'Near reference',
     "Looks almost like your reference. The canopy is nearly continuous, "
     "well-shaded, and structurally similar. Small differences remain — "
     "perhaps slightly lower height, slightly more light penetration, or a "
     "few persistent gaps."),
    (100, 'Equivalent to reference',
     "Indistinguishable from your reference mangrove when standing inside "
     "it. Canopy is closed, well-shaded, structurally complete."),
]


# ── Human Disturbance Pressure (HD) — universal cross-cutting indicator ──────
# Keyed under the '*' ecosystem so it surfaces for every project type (the
# getters fall back from (ecosystem, code) to ('*', code)).
_HD_FULL_INSTRUCTIONS = [
    {
        'type': 'md',
        'content': (
            "### How to assess Human Disturbance Pressure\n\n"
            "This assessment captures the biggest single risk to your "
            "project's natural capital value — the threat that human activity "
            "poses to everything your team is working to restore.\n\n"
            "You are not measuring what the ecosystem is currently like (that "
            "is what the ecological indicators measure). You are measuring "
            "what is being done to it, and what risk that poses to its "
            "future.\n\n"
            "Be honest. An inflated HD score (claiming no disturbance when "
            "significant disturbance exists) will not improve your eROI — it "
            "will undermine your credibility with investors and verifiers who "
            "visit or audit the site. A realistic HD score with a credible "
            "mitigation plan is far more valuable than an unrealistically "
            "high score with no supporting evidence."
        ),
    },
    {
        'type': 'md',
        'content': (
            "### What to assess\n\n"
            "Walk the full boundary of your restoration site and the land or "
            "water immediately surrounding it. Observe and note:\n\n"
            "**1. Evidence of current activity**\n"
            "- Fresh cut stumps, recently cleared areas, new drainage "
            "channels, fishing gear, livestock, or construction equipment\n"
            "- Signs of burning — ash, charred vegetation, smoke\n"
            "- Waste, nets, or debris accumulating in or around the site\n\n"
            "**2. Proximity of pressures**\n"
            "- How close is the nearest intensive land use — aquaculture "
            "pond, agricultural field, road, urban area, industrial "
            "facility?\n"
            "- Is the site buffered by protection (water, remote terrain, "
            "community-managed buffer) or accessible and adjacent to human "
            "activity?\n\n"
            "**3. Frequency of disturbance**\n"
            "- Ask community members or site staff: how often does damaging "
            "activity occur? Daily? Weekly? Rarely?\n"
            "- Are there security measures in place — signs, community "
            "patrols, legal protection?\n\n"
            "**4. Trend**\n"
            "- Is pressure increasing, stable, or decreasing compared to "
            "previous years?\n"
            "- Note the trend in your field notes even though the score "
            "captures current state only."
        ),
    },
    {
        'type': 'md',
        'content': (
            "### Talk to people\n\n"
            "The most reliable evidence for this indicator is often local "
            "knowledge. Ask community members, local rangers, or "
            "neighbours:\n\n"
            "- *\"Has anyone been cutting trees or fishing here recently?\"*\n"
            "- *\"Are there any problems with people damaging the site?\"*\n"
            "- *\"Who is responsible for protecting this area?\"*\n\n"
            "### How to choose your score\n\n"
            "Select the single option that best describes the dominant "
            "current situation. If multiple pressures exist, choose the level "
            "that reflects the most damaging one.\n\n"
            "It is common for restoration projects to score 50 (Moderate) at "
            "baseline — partial protection with ongoing pressure is the "
            "reality for many community-led projects in the Global South. "
            "This is not a failure: it is honest reporting that creates the "
            "foundation for demonstrating improvement over time.\n\n"
            "### Recording your score\n\n"
            "Select your score, then complete the follow-up questions if "
            "prompted (scores of 50 or below require you to identify the main "
            "disturbance source).\n\n"
            "Add a field note describing what you observed — particularly any "
            "specific incidents, the names of any pressure sources, and any "
            "protective measures already in place. This note will appear in "
            "your annual monitoring report and prospectus."
        ),
    },
    {
        'type': 'md',
        'content': (
            "### What this score means for your valuation\n\n"
            "Your HD score is applied as a risk multiplier across all "
            "ecosystem service values in your prospectus:\n\n"
            "| Score | Level | Effect on all service values |\n"
            "|---|---|---|\n"
            "| 100 | None | No reduction |\n"
            "| 90 | Minimal | ~5% reduction |\n"
            "| 75 | Low | ~13% reduction |\n"
            "| 50 | Moderate | ~29% reduction |\n"
            "| 30 | Significant | ~45% reduction |\n"
            "| 10 | Severe | ~68% reduction |\n\n"
            "This reduction is applied on top of your ecological indicator "
            "scores — it does not replace them. A site with excellent canopy "
            "cover (M1 = 90) but significant disturbance (HD = 30) will have "
            "its climate regulation and habitat service values reduced by "
            "45%, reflecting the genuine risk that this ecological progress "
            "may not be sustained.\n\n"
            "As your project demonstrates improved security over successive "
            "annual monitoring visits, your HD score can improve — and this "
            "improvement will be directly visible in your updated eROI and "
            "annual investor report."
        ),
    },
    {
        'type': 'caption',
        'content': (
            "Methodology note: The HD indicator is grounded in the "
            "Pressure-State-Response (PSR) framework (OECD 1993), widely "
            "applied in ecosystem condition assessment. Human disturbance is "
            "treated as a cross-cutting modifier rather than a "
            "service-specific indicator because empirical research shows it "
            "simultaneously degrades all ecosystem service categories — "
            "disturbed mangroves show 80% reductions in microbial "
            "decomposition and significant losses in carbon stocks, "
            "biodiversity, and trophic resources (Danovaro et al. 2018, "
            "Scientific Reports 8:13298). The sqrt(HD_score/100) multiplier "
            "produces a graduated dose-response curve consistent with "
            "ecological resilience theory."
        ),
    },
]


INDICATOR_INSTRUCTIONS = {
    ('*', 'HD'): {
        'scoring_intro': (
            "You are scoring the intensity of human activity threatening "
            "your site — not its ecological condition. Walk the site "
            "boundary, look for evidence of damage, and talk to the local "
            "community. Be honest: a realistic score with a mitigation plan "
            "is worth more than an inflated one (see Full instructions)."
        ),
        'full_instructions': _HD_FULL_INSTRUCTIONS,
    },
    ('Mangroves', 'M1'): {
        'scoring_intro': (
            "Estimate how complete and healthy your restoration site's canopy "
            "looks compared to a reference mangrove (Full instructions below)."
        ),
        'response_help': _M1_RESPONSE_HELP,
        'full_instructions': _M1_FULL_INSTRUCTIONS,
    },
}


# ── Auto-generated instructions from the seed ────────────────────────────────
# Any indicator without a hand-authored entry above still gets useful panel
# instructions, generated from its seed definition (baseline_question,
# field_method, bands, remote-sensing note, sources). This means a new indicator
# set added to project_indicators_seed.py surfaces a scoring intro, a "How to
# score" table and a response-help tooltip automatically — no separate authoring
# step here. Hand-authored entries above always take precedence.

_AUTO_CACHE: dict = {}


def _seed_indicator_by_code() -> dict:
    """code -> seed indicator dict, built once from DEFAULT_INDICATORS."""
    cache = _AUTO_CACHE.get('by_code')
    if cache is None:
        try:
            from utils.project_indicators_seed import DEFAULT_INDICATORS
            cache = {ind['code']: ind for ind in DEFAULT_INDICATORS}
        except Exception:
            cache = {}
        _AUTO_CACHE['by_code'] = cache
    return cache


def _auto_instructions_for_code(code: str):
    """Build an instructions dict from a seed indicator's own fields, or None
    if that code isn't in the seed."""
    ind = _seed_indicator_by_code().get(code)
    if not ind:
        return None
    bands = ind.get('bands') or []

    def _detail(b):
        crit, mean = b.get('criteria', ''), b.get('meaning', '')
        return f"{crit} — {mean}" if crit and mean else (crit or mean)

    response_help = [
        (int(round(b['score'] * 100)), b['label'], _detail(b)) for b in bands
    ]

    blocks = []
    if ind.get('field_method'):
        blocks.append({'type': 'md',
                       'content': "### How to measure\n\n" + ind['field_method']})
    if bands:
        table = ["### How to score\n", "| Score | Level | What it means |", "|---|---|---|"]
        for b in bands:
            table.append(f"| {int(round(b['score'] * 100))} | {b['label']} | {_detail(b)} |")
        blocks.append({'type': 'md', 'content': "\n".join(table)})
    if ind.get('remote_sensing_alternative'):
        blocks.append({'type': 'md',
                       'content': "### Remote sensing alternative\n\n"
                                  + ind['remote_sensing_alternative']})
    if ind.get('sources'):
        blocks.append({'type': 'caption', 'content': "Sources: " + ind['sources']})

    return {
        'scoring_intro': ind.get('baseline_question') or '',
        'response_help': response_help,
        'full_instructions': blocks,
    }


def get_indicator_instructions(ecosystem_display_name: str, code: str):
    """Return the instructions dict for an (ecosystem, indicator code) pair.

    Resolution order: hand-authored ``(ecosystem, code)`` → universal
    ``('*', code)`` (e.g. HD) → instructions auto-generated from the seed
    definition. Returns None only when the code is unknown everywhere."""
    return (
        INDICATOR_INSTRUCTIONS.get((ecosystem_display_name, code))
        or INDICATOR_INSTRUCTIONS.get(('*', code))
        or _auto_instructions_for_code(code)
    )


def get_response_help_markdown(ecosystem_display_name: str, code: str):
    """Return a markdown tooltip describing every response category for an
    indicator — used as the Baseline/Target radio help icon. Returns None
    when no per-response descriptions have been authored or generated."""
    data = (
        INDICATOR_INSTRUCTIONS.get((ecosystem_display_name, code))
        or INDICATOR_INSTRUCTIONS.get(('*', code))
        or _auto_instructions_for_code(code)
    )
    rows = (data or {}).get('response_help')
    if not rows:
        return None
    parts = [
        "**Response categories** — how your site compares to your reference:"
    ]
    for pct, label, desc in rows:
        parts.append(f"**{label} ({pct}%)** — {desc}")
    return "\n\n".join(parts)


# ── Tropical Forest — scaffolded from the seed as an editable starting
#    point. These hand-authored entries OVERRIDE the auto-generated
#    instructions for TF1-TF7. Edit freely; see ('Mangroves', 'M1') above
#    for a richer reference-site walkthrough you can adapt.
_TROPICAL_FOREST_INSTRUCTIONS = {
    ('Tropical Forest', 'TF1'): {
        'scoring_intro': "Estimate how complete your restoration site's tree canopy looks compared to a mature reference forest (full instructions below).",
        'response_help': [
            (10, 'Bare or cleared', '<10% — Open ground; no canopy function'),
            (30, 'Very early stage', '10–25% — Scattered pioneer trees only'),
            (50, 'Early recovery', '25–50% — Patchy canopy; gaps dominant'),
            (75, 'Developing canopy', '50–70% — Continuous but uneven cover'),
            (90, 'Near reference', '70–85% — Dense closed canopy forming'),
            (100, 'Reference condition', '>85% — Closed multi-layered canopy'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | Bare or cleared | <10% — Open ground; no canopy function |
| 30 | Very early stage | 10–25% — Scattered pioneer trees only |
| 50 | Early recovery | 25–50% — Patchy canopy; gaps dominant |
| 75 | Developing canopy | 50–70% — Continuous but uneven cover |
| 90 | Near reference | 70–85% — Dense closed canopy forming |
| 100 | Reference condition | >85% — Closed multi-layered canopy |
"""},
            {'type': 'md', 'content': """### How to measure

Before your first monitoring visit, establish a permanent 20m x 20m plot at a representative location in the restoration site. Mark the four corners with painted stakes or GPS waypoints and record the coordinates. All plot-based indicators (TF2, TF3, TF4, TF5) use this same plot — set it up once and return to it on every visit.

1. Stand at five points within the plot: the four corners and the centre.
2. At each point, hold your smartphone flat above your head, camera facing directly upward.
3. Take a photograph straight up into the canopy.
4. Estimate the percentage of the image covered by leaves and branches versus open sky.
5. Average your five estimates and record the result as a percentage.

If you do not have a smartphone: at each point look straight up through a cardboard tube and estimate the proportion of sky visible in a fixed field of view. Less precise but acceptable for community monitoring.

Note separately any visible mid-canopy or understorey layers — tropical forests are multi-layered, and 75% cover in a two-layered young forest means something different from the same score in a single-layer pioneer stand. Measure at midday when shadows are shortest, and avoid measuring immediately after leaf fall or storm damage, which temporarily reduce apparent cover.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

Sentinel-2 NDVI above 0.6 typically corresponds to more than 50% canopy cover in humid tropical forest, and above 0.75 generally indicates a closed canopy. Access via Copernicus Browser (free) or Google Earth Engine. The GEDI canopy cover product gives direct percentage estimates at 25m resolution for sites larger than 1ha. Calibrate against a nearby intact reference patch, as NDVI-cover relationships vary by forest type and season.
"""},
            {'type': 'caption', 'content': 'Sources: Poorter et al. 2016 (Nature) — secondary forest recovery trajectories; Chazdon 2014, Second Growth — canopy closure as primary milestone; ITTO 2002 Guidelines (Policy Development Series No. 13); SER 2019 International Principles and Standards (Attribute 2).'},
        ],
    },
    ('Tropical Forest', 'TF2'): {
        'scoring_intro': 'In a 20m x 20m plot, how many different native tree species (stems over 5cm thick) can you count?',
        'response_help': [
            (10, 'Monoculture', '1 species — Plantation or single-species stand'),
            (30, 'Very low', '2–4 species — Very low diversity'),
            (50, 'Low', '5–9 species — Low diversity'),
            (75, 'Moderate', '10–19 species — Moderate diversity'),
            (90, 'High', '20–35 species — High diversity'),
            (100, 'Reference diversity', '>35 species — Comparable to intact forest'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | Monoculture | 1 species — Plantation or single-species stand |
| 30 | Very low | 2–4 species — Very low diversity |
| 50 | Low | 5–9 species — Low diversity |
| 75 | Moderate | 10–19 species — Moderate diversity |
| 90 | High | 20–35 species — High diversity |
| 100 | Reference diversity | >35 species — Comparable to intact forest |
"""},
            {'type': 'md', 'content': """### How to measure

Use the permanent 20m x 20m plot established for TF1.

1. Walk slowly through the plot and find every tree or woody shrub with a stem thicker than 5cm at breast height (about 1.3m up). A tape wrapped around the stem reading 15.7cm circumference or more equals 5cm diameter.
2. Record each species separately. You do not need the scientific name — a clear description and photo is enough. Use the iNaturalist app: photograph leaf, bark, and any fruit or flowers.
3. Count only native species. If unsure whether a species is native, record it and flag for confirmation. Your local forestry office or university botany department can usually provide a native species list.
4. Record the total count of distinct native tree species as your score.
5. On later visits, check for and record any species that have arrived naturally since the last visit — a quality signal worth noting.

Use the same plot boundaries every visit; verify your start position against the recorded GPS coordinates before counting.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

Not available for a direct species count — field measurement is required. Hyperspectral imagery can distinguish species in research settings but is not operationally available for community monitoring. As a weak qualitative cross-check, patchy (heterogeneous) NDVI within the plot correlates loosely with higher diversity in some forest types.
"""},
            {'type': 'caption', 'content': 'Sources: Rozendaal et al. 2019 (Science Advances) — recovery trajectory; Chazdon 2014, Second Growth; ITTO 2002 Guidelines; Brancalion et al. 2019 (Science Advances); SER 2019 Standards (Attribute 5); Verra VM0007 REDD+ Framework.'},
        ],
    },
    ('Tropical Forest', 'TF3'): {
        'scoring_intro': 'What is the average height of the five tallest trees in your plot (full instructions below)?',
        'response_help': [
            (10, 'Shrub stage', '<2m — Shrub or early seedling stage'),
            (30, 'Early pioneer', '2–5m — Early pioneer stage'),
            (50, 'Mid-succession', '5–10m — Mid-succession canopy'),
            (75, 'Developing', '10–18m — Developing mature canopy'),
            (90, 'Near mature', '18–25m — Approaching mature tropical forest structure'),
            (100, 'Reference height', '>25m — Reference mature canopy height'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | Shrub stage | <2m — Shrub or early seedling stage |
| 30 | Early pioneer | 2–5m — Early pioneer stage |
| 50 | Mid-succession | 5–10m — Mid-succession canopy |
| 75 | Developing | 10–18m — Developing mature canopy |
| 90 | Near mature | 18–25m — Approaching mature tropical forest structure |
| 100 | Reference height | >25m — Reference mature canopy height |
"""},
            {'type': 'md', 'content': """### How to measure

Use the permanent 20m x 20m plot established for TF1.

1. Identify the five tallest trees within or immediately adjacent to the plot.
2. For each, stand at a distance roughly equal to its height and use a clinometer or a free smartphone clinometer app to measure the angle to the treetop.
3. Calculate height = distance x tan(angle). Most apps do this automatically; with a manual clinometer, record the angle and calculate afterwards.
4. Record the five heights and average them. This average of the five tallest trees is your score.

No clinometer? Hold a stick of known length at arm's length: tree height is approximately (tree apparent height / stick apparent height) x distance to tree. Less precise but fine at band resolution. Measure the same marked trees each visit where possible, but always measure the five tallest present.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

The NASA/USGS GEDI canopy height product gives global estimates at 25m resolution via Google Earth Engine, free of charge; the ESA BIOMASS mission and ICESat-2 provide complementary data. For sites over 2ha, GEDI is typically within 2–3m of field measurements in tropical forest and can independently corroborate field data. Product: https://lpdaac.usgs.gov/products/gedi02_bv002/
"""},
            {'type': 'caption', 'content': 'Sources: Dubayah et al. 2020 (GEDI methodology); Poorter et al. 2016 (Nature) — height recovery; Chave et al. 2014 (Global Change Biology) — height-biomass; Asner et al. 2014 (PNAS); IPCC 2006 AFOLU Guidelines Vol. 4 Ch. 4 (Tier 2 biomass).'},
        ],
    },
    ('Tropical Forest', 'TF4'): {
        'scoring_intro': 'In a 5m x 5m subplot, how many native seedlings and saplings under 1.3m tall can you count?',
        'response_help': [
            (10, 'None', '0 — No regeneration; site not self-sustaining'),
            (30, 'Very sparse', '1–4 — Isolated recruits only'),
            (50, 'Some', '5–14 — Recruitment beginning'),
            (75, 'Good', '15–29 — Active natural regeneration across site'),
            (90, 'Dense', '30–50 — Strong natural regeneration'),
            (100, 'Reference', '>50 — Comparable to intact forest understorey'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | None | 0 — No regeneration; site not self-sustaining |
| 30 | Very sparse | 1–4 — Isolated recruits only |
| 50 | Some | 5–14 — Recruitment beginning |
| 75 | Good | 15–29 — Active natural regeneration across site |
| 90 | Dense | 30–50 — Strong natural regeneration |
| 100 | Reference | >50 — Comparable to intact forest understorey |
"""},
            {'type': 'md', 'content': """### How to measure

Use the permanent 20m x 20m plot established for TF1. Within it, mark three 5m x 5m subplots: one at the north-west corner, one at the south-east corner, and one at the centre.

1. In each subplot, count all seedlings and saplings shorter than 1.3m.
2. Count only native species; if unsure of origin, record and photograph for later identification.
3. Distinguish plants you know were planted (from your planting records) from those that arrived naturally. Natural recruits — found outside planting rows, in unexpected spots, or of species not in your stock — are especially valuable; record them separately.
4. Average the three subplot counts and record as your score.

Survey in the same season each year where possible — seedling density peaks after rains in many tropical forests, so mixing wet- and dry-season counts between years adds noise.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

Not available for this indicator — seedling and sapling counts require direct field observation.
"""},
            {'type': 'caption', 'content': 'Sources: Crouzeilles et al. 2017 (Science Advances) — natural regeneration and cost comparison; Poorter et al. 2016 (Nature) — regeneration density benchmarks; Chazdon 2014, Second Growth (Ch. 5–7); SER 2019 Standards (Attribute 6); NatureServe 2019 Ecological Resilience Indicators.'},
        ],
    },
    ('Tropical Forest', 'TF5'): {
        'scoring_intro': 'How deep is the leaf-litter layer on your site, averaged across five points (full instructions below)?',
        'response_help': [
            (10, 'Bare mineral soil', '0cm — No litter layer; severely degraded'),
            (30, 'Very thin', '<1cm — Early accumulation only'),
            (50, 'Developing', '1–3cm — Developing litter layer'),
            (75, 'Good', '3–6cm — Functional soil protection'),
            (90, 'Deep', '6–10cm — Approaching reference condition'),
            (100, 'Reference depth', '>10cm — Soil fully protected; high soil organic matter'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | Bare mineral soil | 0cm — No litter layer; severely degraded |
| 30 | Very thin | <1cm — Early accumulation only |
| 50 | Developing | 1–3cm — Developing litter layer |
| 75 | Good | 3–6cm — Functional soil protection |
| 90 | Deep | 6–10cm — Approaching reference condition |
| 100 | Reference depth | >10cm — Soil fully protected; high soil organic matter |
"""},
            {'type': 'md', 'content': """### How to measure

Use the permanent 20m x 20m plot established for TF1.

1. Choose five points: the four corners and the centre.
2. At each, push a ruler gently and vertically into the litter until you feel resistance from the mineral soil. Do not compress the litter first.
3. Record the depth in centimetres at each point.
4. Average the five readings and record.

The litter/soil boundary is usually clear: litter is dark, fibrous and compressible; mineral soil is denser, finer, often paler or reddish. If the transition is gradual (a developing humus layer — a good sign), measure to where material becomes clearly mineral. Measure in the same season each year, and note any recent fire, heavy rain, or management that has disturbed the litter.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

Not available for direct litter depth. SoilGrids 2.0 (soilgrids.org) gives modelled soil organic carbon at 250m resolution as landscape context, but it does not replace direct plot-level measurement.
"""},
            {'type': 'caption', 'content': 'Sources: Don et al. 2011 (Global Change Biology) — soil carbon loss and recovery benchmarks; Chazdon 2014, Second Growth (Ch. 8); Poorter et al. 2016 (Nature); IPCC 2006 AFOLU Guidelines Vol. 4 Ch. 2 (litter carbon pool); Verra VM0007 REDD+ Framework (dead organic matter and soil pools).'},
        ],
    },
    ('Tropical Forest', 'TF6'): {
        'scoring_intro': 'During a 30-minute walk, how many distinct types of animal can you see or hear on your site?',
        'response_help': [
            (10, 'Functionally empty', '0–1 types — Heavily hunted or isolated'),
            (30, 'Very low', '2–4 types — Very low diversity'),
            (50, 'Low', '5–8 types — Some forest-dependent species'),
            (75, 'Moderate', '9–15 types — Fauna returning'),
            (90, 'Good', '16–25 types — Forest-interior species present'),
            (100, 'Reference diversity', '>25 types — Intact forest fauna'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | Functionally empty | 0–1 types — Heavily hunted or isolated |
| 30 | Very low | 2–4 types — Very low diversity |
| 50 | Low | 5–8 types — Some forest-dependent species |
| 75 | Moderate | 9–15 types — Fauna returning |
| 90 | Good | 16–25 types — Forest-interior species present |
| 100 | Reference diversity | >25 types — Intact forest fauna |
"""},
            {'type': 'md', 'content': """### How to measure

Survey in the early morning (first two hours after dawn) or late afternoon (last two hours before dusk) — activity peaks then for most tropical forest fauna, and midday surveys undercount.

1. Walk slowly and quietly through the site, and a short way into any adjacent forest, for 30 minutes. Stop and listen for at least 2 minutes every 5 minutes.
2. Keep a simple tally: each time you detect a distinct animal type, add a mark. Count each type once per session even if detected repeatedly.
3. Include birds (seen or heard — a song counts), mammals (seen, heard, or evidenced by fresh tracks, scat, or gnawed fruit), reptiles, frogs, and conspicuous insects (butterflies, large beetles).
4. You do not need species names — a large black-and-yellow bird and a small brown bird count as two types. Describe and photograph unknowns.
5. Record total distinct types detected as your score.

Optional: a camera trap left 72 hours near a game trail or water source detects nocturnal mammals that day surveys miss; record separately. Follow the same route at the same site each year and note any changes in weather or timing.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

Not available for direct wildlife observation. Low-cost acoustic recorders (e.g. AudioMoth) extend detection of birds and bats beyond human survey effort and are recommended where resources allow; recordings can be analysed with BirdNET or similar. Camera traps are the most cost-effective way to detect elusive mammals.
"""},
            {'type': 'caption', 'content': 'Sources: Gardner et al. 2009 (Ecology Letters) — fauna recovery benchmarks; Chazdon 2014, Second Growth (Ch. 10); SER 2019 Standards (Attribute 7); Verra VM0007 REDD+ Framework (biodiversity co-benefits); IUCN 2020 Red List of Ecosystems Guidelines.'},
        ],
    },
    ('Tropical Forest', 'TF7'): {
        'scoring_intro': 'What proportion of the vegetation on your site is invasive or non-native (full instructions below)? Lower invasion scores higher.',
        'response_help': [
            (10, 'Severely invaded', '>60% — Invasives dominate; restoration failing'),
            (30, 'Heavily invaded', '40–60% — Heavy invasive presence'),
            (50, 'Moderately invaded', '20–40% — Moderate invasive presence'),
            (75, 'Lightly invaded', '10–20% — Light invasive presence'),
            (90, 'Minimal', '<10% — Occasional individuals only'),
            (100, 'None detected', '0% — No invasive species observed'),
        ],
        'full_instructions': [
            {'type': 'md', 'content': """### How to score

| Score | Level | What it means |
|---|---|---|
| 10 | Severely invaded | >60% — Invasives dominate; restoration failing |
| 30 | Heavily invaded | 40–60% — Heavy invasive presence |
| 50 | Moderately invaded | 20–40% — Moderate invasive presence |
| 75 | Lightly invaded | 10–20% — Light invasive presence |
| 90 | Minimal | <10% — Occasional individuals only |
| 100 | None detected | 0% — No invasive species observed |
"""},
            {'type': 'md', 'content': """### How to measure

Walk the permanent 20m x 20m plot and a 10m buffer around all four sides.

1. Look systematically for plants clearly different from your target native trees and shrubs. Signs of invasives: fast-growing vines smothering canopy, dense grass or sedge mats in gaps, spiny shrubs forming thickets, or unusually large/bright flowers atypical of local forest.
2. Estimate the percentage of total vegetation cover (not ground area) made up of invasive or non-native species, including climbers on trees, ground-layer invaders, and invasive pioneer trees.
3. Photograph anything you cannot confidently identify and use iNaturalist. Your local forestry or conservation agency can usually provide a problem-species list — obtain it before your first survey.
4. Record your estimated percentage. Bands are inverted: lower invasive cover gives a higher intactness score.

If invasives are found, record their locations and any management already done — valuable for planning and investor reporting even when not captured in the band score.
"""},
            {'type': 'md', 'content': """### Remote sensing alternative

Time-series NDVI (Sentinel-2 or Landsat) showing rapid, homogeneous green-up in gaps — especially in the dry season when native cover recedes — can flag invasive grass or forb cover, since many tropical invasives stay green when natives senesce. A qualitative flag requiring field confirmation, not a quantitative score. Access via Copernicus Browser or Google Earth Engine.
"""},
            {'type': 'caption', 'content': 'Sources: Mack et al. 2000 (Ecological Applications) — invasion ecology and control; Richardson et al. 2011 (J. Applied Ecology) — impact assessment and context-dependence; Chazdon 2014, Second Growth (Ch. 6); ITTO 2002 Guidelines (Section 4.3); Brancalion et al. 2019 (Science Advances).'},
        ],
    },
}
INDICATOR_INSTRUCTIONS.update(_TROPICAL_FOREST_INSTRUCTIONS)

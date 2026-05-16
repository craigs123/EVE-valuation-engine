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
            "You are estimating how complete and healthy your restoration "
            "site's canopy looks compared to a reference mangrove — either a "
            "nearby intact, healthy mangrove stand of the same species that "
            "represents what your site is working towards or another reference "
            "site (see Full instructions)."
        ),
        'response_help': _M1_RESPONSE_HELP,
        'full_instructions': _M1_FULL_INSTRUCTIONS,
    },
}


def get_indicator_instructions(ecosystem_display_name: str, code: str):
    """Return the instructions dict for an (ecosystem, indicator code) pair.

    Falls back to the universal ``('*', code)`` key so cross-cutting
    indicators (e.g. HD) need authoring only once and surface for every
    ecosystem. Returns None when nothing has been authored."""
    return (
        INDICATOR_INSTRUCTIONS.get((ecosystem_display_name, code))
        or INDICATOR_INSTRUCTIONS.get(('*', code))
    )


def get_response_help_markdown(ecosystem_display_name: str, code: str):
    """Return a markdown tooltip describing every response category for an
    indicator — used as the Baseline/Target radio help icon. Returns None
    when no per-response descriptions have been authored."""
    data = (
        INDICATOR_INSTRUCTIONS.get((ecosystem_display_name, code))
        or INDICATOR_INSTRUCTIONS.get(('*', code))
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

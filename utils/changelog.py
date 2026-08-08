"""
User-facing changelog for EVE, shown in the Analysis Settings dialog.

Newest version first. When you bump the version for a release (app.py +
utils/auth.py), add a matching entry at the TOP of CHANGELOG describing the
user-visible changes in plain language. Keep entries short and non-technical —
this is read by environmental researchers, not developers.

Each entry: {"version": "vX.Y.Z beta", "date": "YYYY-MM-DD" | "", "changes": [..]}
Use date "" when the exact release date isn't known.
"""

from typing import List, Dict

CHANGELOG: List[Dict] = [
    {
        "version": "v3.10.1 beta",
        "date": "2026-08-08",
        "changes": [
            "The map now shows the latitude and longitude under your cursor, in large "
            "clear type in the bottom-right corner, updating as you move the mouse.",
            "When you draw an area with the polygon tool, its corners are now listed "
            "beside the map and numbered on it, so you can read off exactly where the "
            "boundary falls.",
            "You can then keep adjusting that shape: click the map to add a corner, "
            "use Undo or Clear to take corners away, or edit and paste coordinates "
            "into the list directly to set a boundary exactly. This also lets you "
            "enter an area whose coordinates you already have, from a survey or a "
            "report. Press 'Use this area' when the shape is right.",
            "The rectangle tool is unchanged.",
        ],
    },
    {
        "version": "v3.10.0 beta",
        "date": "2026-07-20",
        "changes": [
            "Fixed the Ecosystem Mapping table in Analysis Settings, which showed "
            "land-cover code 210 (water bodies) as mapping to 'Forest'. Its correct "
            "default is 'Rivers and Lakes', which was missing from the ecosystem "
            "drop-down. Opening that panel also silently applied the wrong value, "
            "so water could be described as forest in the detected-ecosystem "
            "display before you classified it. Water valuations were not affected: "
            "your ocean / rivers and lakes / coastal choice always took priority.",
        ],
    },
    {
        "version": "v3.9.9 beta",
        "date": "2026-07-20",
        "changes": [
            "Corrected the methodology note in the PDF report. It previously said "
            "open-water areas were excluded from natural capital totals, which was "
            "not what the engine does. Water bodies are included: when sample "
            "points fall on water you are asked to classify them as ocean, rivers "
            "and lakes, or coastal, and they are valued using the matching "
            "coefficients. Wording only — no valuation figures have changed.",
        ],
    },
    {
        "version": "v3.9.8 beta",
        "date": "2026-06-03",
        "changes": [
            "New Tropical Forest Reforestation indicator set — project-specific "
            "indicators (canopy cover, tree species richness, canopy height, "
            "natural regeneration, leaf litter, wildlife signs and invasive "
            "pressure) are now available for Tropical Forest as well as "
            "Mangroves, and adjust the valuation using your on-the-ground scores.",
            "Each project indicator now shows step-by-step scoring instructions "
            "and a 'how to score' guide directly in the panel.",
            "When you manually override the detected ecosystem, the per-type EEI "
            "breakdown and the sample-point composition list are now hidden (they "
            "referred to the auto-detected types); the average ecosystem "
            "integrity and the geographic distribution still show.",
        ],
    },
    {
        "version": "v3.9.3 beta",
        "date": "2026-06-03",
        "changes": [
            "Sample points are now placed inside your drawn area's actual shape "
            "rather than its rectangular bounding box, so analyses of irregular "
            "areas no longer pick up land outside the boundary.",
        ],
    },
    {
        "version": "v3.9.2 beta",
        "date": "2026-06-03",
        "changes": [
            "Email verification links are more reliable — they can be opened "
            "more than once (for example on a second device, or after an email "
            "security scanner has already followed the link) without showing an "
            "'expired or invalid' error, and now stay valid for 48 hours.",
        ],
    },
    {
        "version": "v3.9.1 beta",
        "date": "2026-06-02",
        "changes": [
            "Faster start-up: the app now opens more quickly, especially on "
            "the first visit after a quiet period.",
        ],
    },
    {
        "version": "v3.9.0 beta",
        "date": "2026-06-01",
        "changes": [
            "PDF report's Environmental Indicators table now shows each sample "
            "point's latitude/longitude in the first column and its EEI "
            "(Ecosystem Ecological Integrity) value alongside the other "
            "selected indicators.",
        ],
    },
    {
        "version": "v3.8.32 beta",
        "date": "2026-06-01",
        "changes": [
            "PDF report now includes a separate Environmental Indicators table "
            "(FAPAR, soil carbon, pH, SOC, bulk density, nitrogen) when those "
            "indicators are selected in Analysis Settings.",
            "Added this Version Changelog to the Settings dialog.",
        ],
    },
    {
        "version": "v3.8.31 beta",
        "date": "2026-06-01",
        "changes": [
            "Fixed UK, Ireland and European forests being labelled Boreal — they "
            "are now correctly classified as Temperate, including when the ESA "
            "WorldCover backup is used.",
            "OpenLandMap outages no longer cause a long wait: the analysis now "
            "switches to the ESA WorldCover backup within seconds of detecting "
            "that OpenLandMap is not responding.",
            "PDF report: the Ecosystem Composition table now starts on its own page.",
        ],
    },
    {
        "version": "v3.8.30 beta",
        "date": "2026-05-31",
        "changes": [
            "PDF report now embeds a satellite image of the selected area with "
            "the analysed boundary drawn on top.",
        ],
    },
    {
        "version": "v3.8.29 beta",
        "date": "2026-05-31",
        "changes": [
            "European Atlantic forests (UK / Ireland / continental Europe) "
            "reclassified from Boreal to Temperate to match standard biome maps.",
            "Fixed coastal locations sometimes resolving to the wrong place name.",
        ],
    },
    {
        "version": "v3.8.28 beta",
        "date": "2026-05-28",
        "changes": [
            "Settings: new 'Ecosystem Mapping' section showing how each land-cover "
            "code maps to an ecosystem type, including the ESA WorldCover classes.",
        ],
    },
    {
        "version": "v3.8.27 beta",
        "date": "2026-05-28",
        "changes": [
            "Data-source status panel now shows which backup source is active.",
            "Smoother scroll to the results after pressing Calculate.",
        ],
    },
    {
        "version": "v3.8.26 beta",
        "date": "2026-05-28",
        "changes": [
            "Added an ESA WorldCover (Google Earth Engine) land-cover backup that "
            "is used automatically when OpenLandMap is unavailable.",
        ],
    },
    {
        "version": "v3.8.25 beta",
        "date": "",
        "changes": [
            "Test-area analyses still complete when OpenLandMap is unreachable.",
        ],
    },
    {
        "version": "v3.8.22 beta",
        "date": "",
        "changes": [
            "Potential carbon-credit revenue section now appears in all PDF "
            "report types.",
        ],
    },
    {
        "version": "v3.8.19 beta",
        "date": "",
        "changes": [
            "Investment returns shown as clear boxed figures; tidied chart labels "
            "and updated the logo.",
        ],
    },
    {
        "version": "v3.8.14 beta",
        "date": "",
        "changes": [
            "Investment-grade PDF report for project runs — net present value, "
            "benefit–cost ratio, internal rate of return, payback and a "
            "sensitivity analysis.",
        ],
    },
    {
        "version": "v3.8.11 beta",
        "date": "",
        "changes": [
            "Reworked the investment model on a correct annual-flow basis.",
            "Added a resend-verification flow and surfaced failed verification "
            "emails to users.",
        ],
    },
    {
        "version": "v3.8.10 beta",
        "date": "",
        "changes": [
            "Hardened the EEI (Ecosystem Ecological Integrity) integration and "
            "fixed detection of demo vs. real data.",
        ],
    },
]

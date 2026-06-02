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

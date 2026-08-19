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
    # ACCUMULATING — not yet deployed. Add further v3.11.5 changes to this
    # entry as they land, rather than opening a new version for each one.
    {
        "version": "v3.11.5 beta",
        "date": "2026-08-19",
        "changes": [
            "When the ecosystem condition service cannot measure a sample "
            "point, EVE now says so and says why, and treats that ecosystem "
            "cautiously rather than assuming it is in perfect condition. "
            "Previously the service quietly substituted placeholder figures "
            "for any point it could not measure, and those figures were far "
            "higher than real ones. EVE already detected and discarded them, "
            "but the underlying reason was never reported. The service has "
            "been corrected to report a failure as a failure, and EVE now "
            "shows the reason on the dashboard and in PDF reports.",
            "Sample points are now spread evenly across areas of any shape. "
            "On a rectangle they always were, but on a drawn polygon the "
            "points bunched up and left gaps \u2014 parts of the area could sit "
            "twice as far from the nearest sample as they should. Coverage of "
            "irregular areas is improved by around a quarter to a third, so "
            "the ecosystem mix EVE reports is based on a fairer spread of the "
            "area you actually drew. Rectangles are unchanged in quality.",
            "The number of sample points you ask for is now the number you "
            "get. The setting accepted any value from 9 to 100 but quietly "
            "rounded down to the nearest square number, so asking for 50 gave "
            "49 and asking for 48 gave 36 \u2014 a quarter fewer than requested, "
            "with nothing on screen to say so.",
            "Sample points are also now spaced evenly on the ground rather "
            "than evenly in degrees of latitude and longitude. The old spacing "
            "stretched with the shape of the area and with distance from the "
            "equator, so points were further apart in one direction than the "
            "other.",
            "Because of the above, an area re-analysed after this update will "
            "sample slightly different locations than it did before, and may "
            "return a slightly different value. Analyses saved before this "
            "update are not directly comparable with ones run after it.",
            "Analyses with a high sample point count now say what they are "
            "doing while you wait. Identifying the country for each sample "
            "point relies on an external map service that permits one lookup "
            "per second, so a 100-point area could sit for well over a minute "
            "with nothing on screen. There is now a progress message and bar "
            "for that step, and the sampling progress bar updates on every "
            "point instead of every twenty-five per cent.",
            "PDF reports no longer say that water bodies are excluded from the "
            "analysis — they are not. Water sample points are classified as "
            "ocean, rivers and lakes, or coastal and valued using that "
            "ecosystem's coefficients, so they contribute to the totals. The "
            "sample point summary previously labelled them \"Water Points "
            "(excluded)\", and the report header carried a \"Water excluded\" "
            "row left over from an older method that removed open water. Only "
            "the country breakdown excludes water points, and it says so.",
            "The report now states positively what happens to water points "
            "whenever any are found, and the area figure is labelled simply "
            "\"Area Analysed\" rather than \"Area (land)\", which suggested "
            "water had been taken out of it.",
        ],
    },
    {
        "version": "v3.11.4 beta",
        "date": "2026-08-19",
        "changes": [
            "Choosing a specific ecosystem type instead of Auto-detect now "
            "applies that choice to every sample point, not just to the "
            "valuation. Previously each point kept the ecosystem the satellite "
            "data detected for it, which meant the ecosystem condition (EEI) "
            "reading was recorded against the detected ecosystem and then not "
            "picked up by the valuation — so a forced analysis could quietly "
            "value the area as though it were in perfect condition. Ecosystem "
            "condition is now applied correctly to forced analyses.",
            "As part of that, the ecosystem composition and the EEI breakdown "
            "are shown again when you force an ecosystem type — they now "
            "confirm the choice was applied to all sample points instead of "
            "listing the types it replaced. EVE also no longer stops to ask "
            "how to classify water bodies when you have already chosen the "
            "ecosystem type yourself.",
            "PDF reports now mark the sample point locations on the area map, "
            "numbered to match the Sample Point table, so you can see where in "
            "the area the analysis actually sampled rather than only the "
            "boundary that was drawn. Numbering is omitted above 25 points to "
            "keep the map readable.",
            "Areas are now shown to two decimal places wherever they appear, "
            "so a 1.35 hectare site reads as \"1.35 ha\" rather than being "
            "rounded to \"1 ha\". The analysis always used the exact area — "
            "this was a display issue only, and no valuation changes as a "
            "result — but the rounded figure made small sites look wrong and "
            "disagreed with the area shown beside the map. Larger areas are "
            "unchanged and still shown without unnecessary decimals.",
            "This applies everywhere an area is shown: the Area Analysed "
            "figure with the results, the step-by-step calculation, saved "
            "areas and analysis history, the project area for indicator-based "
            "analyses, and the Area (land) row in PDF reports.",
        ],
    },
    {
        "version": "v3.11.3 beta",
        "date": "2026-08-11",
        "changes": [
            "Areas smaller than 1 hectare can no longer be selected. If you "
            "draw one, EVE now says so and asks you to draw a larger area "
            "instead of accepting it. Previously any selection below a hectare "
            "was quietly treated as exactly 1 hectare, which overstated its "
            "value — a quarter-hectare plot was valued as four times its real "
            "size. Selections of 1 hectare and above are unaffected and are "
            "valued at their exact size, so a 1.5 hectare site is valued as "
            "1.5 hectares.",
            "Area figures now match the readout shown on the drawing cursor "
            "while you draw. Areas are given to two decimal places in hectares, "
            "with square kilometres added only for larger sites where the "
            "hectare figure becomes unwieldy. Previously the panel beside the "
            "map rounded to one decimal place and always added a square "
            "kilometre figure, which disagreed with the cursor and was too "
            "coarse to be useful for small areas.",
        ],
    },
    {
        "version": "v3.11.2 beta",
        "date": "2026-08-11",
        "changes": [
            "The size of your selected area is now shown next to the map, in "
            "hectares and square kilometres, right beneath its coordinates. It "
            "appears as soon as you draw an area, load a saved one or enter "
            "corner points, so you no longer have to run an analysis to find "
            "out how large your selection is.",
            "Summary Statistics now states the total area analysed, above the "
            "breakdown by ecosystem type. Previously only the area of each "
            "individual ecosystem was listed, with no total to check them "
            "against. The total is shown whether or not you have overridden "
            "the ecosystem type. Note that ecosystem types making up less than "
            "1% of your area are not listed, so the individual figures may not "
            "add up to the total.",
            "PDF reports now carry the urban green and blue infrastructure "
            "assumption, matching what the dashboard shows. Reports for areas "
            "containing urban land gain an Urban Green/Blue line in the "
            "summary table, showing the percentage assumed and how much of the "
            "site is urban, together with a short note explaining that urban "
            "values are quoted per hectare of green and blue space. Reports "
            "for areas with no urban land are unchanged.",
            "Analyses saved before the percentage began being recorded will "
            "say so plainly rather than showing a figure that may not be the "
            "one they were calculated with. Re-run the analysis to capture it.",
        ],
    },
    {
        "version": "v3.11.1 beta",
        "date": "2026-08-10",
        "changes": [
            "Ecosystem condition now affects cultural services too. The "
            "intactness multiplier — whether taken from EEI or set by hand — is "
            "applied to all four service groups, including recreation, "
            "aesthetic value and spiritual value. Previously cultural services "
            "were held at full value however degraded the habitat was. For a "
            "wood, reef or wetland, much of the cultural value comes precisely "
            "from the place being in good condition, so a damaged site should "
            "not carry the recreation value of a healthy one. Valuations of "
            "degraded natural areas will fall as a result.",
            "When your analysis includes urban land, the results now state the "
            "green and blue infrastructure assumption directly: \"This "
            "valuation assumes 18% of the urban area is green/blue "
            "infrastructure\", using whichever percentage the analysis was run "
            "with. Urban values are quoted per hectare of green and blue "
            "space rather than per hectare of city, so this figure has a large "
            "effect on urban totals and is worth seeing alongside them. Areas "
            "with no urban land are unaffected.",
            "Urban areas are unchanged: they remain exempt from the condition "
            "multiplier entirely, so a city park still keeps its full "
            "recreation and aesthetic value even where ecological condition "
            "scores near zero. That was the situation the previous rule existed "
            "to protect, and it is still protected.",
            "The income elasticity factor now starts at 0.6, the recommended "
            "value. It previously started at 0.25 unless you opened Analysis "
            "Settings, where the slider showed 0.6 — so two people analysing "
            "the same area could get noticeably different totals depending on "
            "whether they had opened that panel. Everything now uses 0.6 "
            "unless you change it. Results calculated before this update, on "
            "the 0.25 starting value, applied a smaller adjustment for local "
            "income levels than intended.",
            "The guidance on that setting now reads 0.5 to 0.7 as the usual "
            "range, with 0.6 as the default.",
            "Changing the income elasticity now clears the results on screen, "
            "so you are prompted to re-run rather than left looking at totals "
            "calculated with the previous value. The intactness and valuation "
            "basis settings already behaved this way.",
        ],
    },
    {
        "version": "v3.11.0 beta",
        "date": "2026-08-10",
        "changes": [
            "All ecosystem values have been replaced with a new set from the "
            "Ecosystem Services Valuation Database (September 2025 release), "
            "covering all 13 habitat types and all 22 ecosystem services. "
            "Values are in 2025 International dollars per hectare per year. "
            "Analyses saved before today are not directly comparable with new "
            "ones.",
            "The most important change is in how studies are counted. Some "
            "studies report a single combined figure covering several services "
            "at once. Previously such a study was counted in full under every "
            "service it mentioned, so when EVE added the 22 services together "
            "to reach a total, that one study could be counted many times over. "
            "Only studies reporting a value for a single service are now "
            "included, so the services can be added up safely.",
            "You can now choose how ecosystem values are calculated, under "
            "Analysis Settings, Valuation Basis. The new default is the "
            "log-winsorised mean, which counts every study but stops a few "
            "unusually high valuations from dominating. The median (the typical "
            "value for a service, and the most cautious choice) and the plain "
            "mean (which includes high valuations at full weight) are both "
            "still available.",
            "These three can differ enormously — for rivers and lakes the "
            "totals range from about 17,000 to 1.9 million dollars per hectare "
            "per year — so every result now states which basis produced it. "
            "You will see it in a banner above your totals, and as a Valuation "
            "Basis line in the PDF report. Reports produced on mean values "
            "carry an extra note that the totals are an upper bound.",
            "A caution on the new default: it holds down unusually high "
            "valuations only where a service has enough studies behind it. "
            "Where the evidence is thin it gives the same answer as the plain "
            "mean. Each value's study count is recorded in the accompanying "
            "documentation, and anything based on fewer than 15 studies should "
            "be treated as indicative.",
        ],
    },
    {
        "version": "v3.10.10 beta",
        "date": "2026-08-09",
        "changes": [
            "Important: urban ecosystem values are now roughly 100 times lower, "
            "and this corrects a long-standing error. The recreation and tourism "
            "figure for urban land was around 2.16 million International dollars "
            "per hectare per year — about 8,800 times the value its own source "
            "documentation recorded, and roughly 99% of every urban valuation EVE "
            "produced. All 22 urban service values have been replaced with medians "
            "from ESVD.net for '15. Urban green and blue infrastructure', drawn "
            "from 237 valuations, taken in 2020 dollars and restated to 2025 "
            "dollars.",
            "Those figures are per hectare of green and blue space, not per hectare "
            "of city. The Urban Green/Blue Infrastructure setting (18% by default) "
            "is what converts an urban hectare into the green and blue area they "
            "apply to.",
            "Any urban analysis you saved before today is not comparable with one "
            "run now. Non-urban ecosystems are completely unaffected — forest, "
            "grassland, wetland, marine and the rest are unchanged.",
            "Ecosystem integrity (EEI) is no longer applied to urban ecosystems at "
            "all. The ESVD urban figures come from studies of real city parks, "
            "street trees and canals measured in their actual, usually poor, "
            "condition — so condition is already reflected in them, and applying "
            "EEI as well counted the same degradation twice.",
            "The Urban Green/Blue Infrastructure setting is unchanged at 18% and "
            "still applies. It measures how much of an urban hectare is green or "
            "blue space, which is a separate question from how good that space is.",
            "The calculation breakdown shown with your results now states where the "
            "condition adjustment was and was not applied, instead of implying it "
            "was applied evenly to everything.",
        ],
    },
    {
        "version": "v3.10.9 beta",
        "date": "2026-08-09",
        "changes": [
            "Fixed: ecosystem integrity (EEI) is now reported for towns and cities. "
            "Built-up land scores zero on the integrity index, and a zero score was "
            "being mistaken for 'no data', so urban sample points showed no EEI at "
            "all and were quietly valued as if in perfect condition.",
            "Ecosystem integrity is now applied to provisioning, regulating and "
            "supporting services only. Cultural services — recreation, aesthetic "
            "value, spiritual experience — are no longer reduced by it. These "
            "depend on the place and the people who can reach it, not on ecological "
            "condition, so a well-used city park keeps its recreation value however "
            "degraded its surroundings. This follows UN SEEA ecosystem accounting "
            "and the ONS UK urban natural capital accounts.",
            "Where an area is measured with its own field indicators, those "
            "indicators continue to set the value for every service including "
            "cultural ones. Nothing about that has changed.",
            "The Urban Green/Blue Infrastructure setting is unchanged at 18% and "
            "remains user-adjustable. Its description now explains what it measures: "
            "how much of an urban hectare is green or blue space, as opposed to EEI, "
            "which measures how good that space is. The two are independent, so both "
            "still apply.",
            "The net effect on urban totals is small. Urban cultural services are "
            "valued much as before, while the provisioning, regulating and supporting "
            "services now correctly reflect the low ecological condition of built-up "
            "land rather than being assumed to be in perfect condition.",
            "Where the integrity dataset has no reading at all — open ocean and "
            "gaps in coverage — the affected ecosystems are now named on screen, "
            "with a note that they are being valued at 100% intactness so you can "
            "set them by hand if you prefer.",
        ],
    },
    {
        "version": "v3.10.8 beta",
        "date": "2026-08-09",
        "changes": [
            "Every latitude and longitude in EVE is now shown to four decimal "
            "places. Previously the figure varied depending on where you looked — "
            "the cursor readout and PDF report used five, the corner list and CSV "
            "export used six, and the sample point list used four.",
            "Four decimal places is about 11 metres on the ground, which matches "
            "the finest satellite layer EVE reads. Extra digits beyond that "
            "suggested a precision the results do not actually have.",
            "Coordinates you type are held to the same four places, so the corner "
            "list now reads back exactly as shown: editing and re-saving a "
            "boundary can no longer shift it by a fraction you could not see.",
            "Areas of a few hectares or less may show a slightly different size "
            "than before, as their corners are now placed on this 11 metre grid. "
            "Larger areas are unaffected in any meaningful way.",
        ],
    },
    {
        "version": "v3.10.7 beta",
        "date": "2026-08-09",
        "changes": [
            "Searching for a place or a pair of coordinates now always moves the map "
            "to what you searched for. Previously, if you had a test area or a saved "
            "area selected, the search was ignored and the map stayed where it was.",
            "To make that work, a search now switches the area selector back to "
            "'None - Draw your own area' and clears the area currently on the map, "
            "leaving you at the searched location ready to draw a new one.",
            "Coordinates with fewer than the usual four decimal places are read "
            "exactly as typed, with the missing places treated as zeros — so "
            "'51.5, -0.1' means 51.5000, -0.1000. Whole numbers work too.",
        ],
    },
    {
        "version": "v3.10.6 beta",
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
            "Fixed: while you are adjusting a polygon's corners, the map no longer "
            "also shows the old shape underneath, which made it look as though a "
            "removed corner was still there.",
            "Fixed: clicking an area you drew yourself described it as a '1000 "
            "hectare test area'. It now shows 'Selected Area' with its real size.",
            "The location search now accepts coordinates as well as place names. "
            "Type something like '51.5074, -0.1278' and the map goes straight "
            "there, zoomed in close, with a marker on the spot. Place-name "
            "searches work exactly as before.",
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

# Adding a new ecosystem indicator set

This is the fill-in-the-blanks recipe for adding a new ecosystem-specific
project-indicator set — the equivalent of the Mangrove `M1–M7 + HD` set — that
modifies the natural-capital valuation by **superseding the EEI-derived
intactness per sub-service** wherever an on-the-ground indicator measurement
exists (and falling back to EEI elsewhere).

The valuation engine (`utils/indicator_multipliers._compute_pure`) is fully
ecosystem-agnostic, so adding a set is almost entirely data. Since the
`seed_project_indicators()` upsert (see `utils/project_indicators_seed.py`),
edits here land on staging/prod automatically on the next deploy — no migration.

There are **two keyspaces** you'll touch; keep them straight:

| | Calc keyspace | Indicator keyspace |
|---|---|---|
| Where | `precomputed_esvd_coefficients.py` ecosystem dicts | `pi_indicators.service_weights` (the seed) |
| Style | short, abbreviated (`pollution`, `climate`, `habitat`) | TEEB-aligned full slugs (`air_quality_regulation`, `climate_regulation`, `habitat_for_species`) |
| Translation | — | `utils/teeb_slug_map.TEEB_TO_CALC_KEY` maps indicator slugs → calc keys |

---

## Step 1 — Add the ESVD coefficient set (do this first)

In `utils/precomputed_esvd_coefficients.py`, add a new entry to `self.coefficients`
(near the existing ecosystems, ~line 407+). **The key must be the lowercase,
underscore-joined form of the ecosystem's display name** (e.g. display `Peatland`
→ key `peatland`; display `Salt Marsh` → key `salt_marsh`).

All 22 calc keys must be present (use `0.00` where there's no value). Annotate
each with its ESVD/TEEB source as the existing blocks do:

```python
'peatland': {
    'food': 0.00,                # Service 1:  Food
    'water': 0.00,               # Service 2:  Water
    'raw_materials': 0.00,       # Service 3:  Raw materials
    'genetic_resources': 0.00,   # Service 4:  Genetic resources
    'medicinal_resources': 0.00, # Service 5:  Medicinal resources
    'ornamental_resources': 0.00,# Service 6:  Ornamental resources
    'pollution': 0.00,           # Service 7:  Air quality regulation
    'climate': 0.00,             # Service 8:  Climate regulation   <-- usually high for peatland
    'extreme_events': 0.00,      # Service 9:  Moderation of extreme events
    'water_regulation': 0.00,    # Service 10: Water flow regulation
    'water_purification': 0.00,  # Service 11: Waste treatment / water purification
    'erosion': 0.00,             # Service 12: Erosion prevention
    'soil_formation': 0.00,      # Service 13: Soil formation / nutrient cycling
    'pollination': 0.00,         # Service 14: Pollination
    'biological_control': 0.00,  # Service 15: Biological control
    'nursery_services': 0.00,    # Service 16: Maintenance of life cycles
    'habitat': 0.00,             # Service 17: Habitat for species
    'aesthetic_value': 0.00,     # Service 18: Aesthetic information
    'recreation': 0.00,          # Service 19: Recreation and tourism
    'cultural': 0.00,            # Service 20: Inspiration / culture
    'spiritual_value': 0.00,     # Service 21: Spiritual experience
    'primary_production': 0.00,  # Service 22: (TEEB primary-production bucket)
},
```

## Step 2 — Make it selectable + force the ecosystem (Phase E machinery)

Satellite landcover (OpenLandMap/ESA) does **not** classify some restoration
ecosystems (e.g. Peatland), so they can't be auto-detected. For those, selecting
the project type must force the whole area to that ecosystem. The reusable
machinery for this is added in Phase E; once it exists, adding an ecosystem here
is just:

1. Add the display name to the forced-ecosystem registry (a code constant).
2. Add it to the ecosystem dropdown (`_render_project_eco_controls`) and to the
   `override_mapping` (`app.py`, ~line 5822) → its calc key from Step 1.

(Satellite-**detectable** ecosystems skip the forced-registry step — detection
already produces them.)

## Step 3 — Add the project type

In `utils/project_indicators_seed.py`, append to `DEFAULT_PROJECT_TYPES`:

```python
{
    'slug': 'peatland_restoration',      # stable, unique; the upsert key
    'name': 'Peatland Restoration',
    'icon': '🌱',
    'ecosystem_type': 'Peatland',        # MUST equal the EVE display name;
                                         # lowercased+underscored MUST equal the
                                         # coefficient key from Step 1.
    'description': '...',
    'sort_order': 2,
},
```

## Step 4 — Add the indicators (the M1–M7 equivalents)

Append each indicator to `DEFAULT_INDICATORS`. `service_weights` is the important
part: it decides which sub-services this indicator supersedes EEI for. Keys are
**TEEB slugs** (see `CANONICAL_TEEB_SLUGS`); values are `'primary'` (weight 1.0)
or `'secondary'` (weight 0.5). A sub-service's multiplier is the
weighted average of the committed indicators that name it.

```python
{
    'slug': 'peatland_water_table',       # stable, unique; the upsert key
    'code': 'P1',
    'name': 'Water table depth',
    'commitment_question': '...',
    'prospectus_scope_statement': '...',
    'baseline_question': '...',
    'card_description': '...',            # optional one-liner in the picker
    'why_matters': '...',                 # optional
    'field_method': '...',                # optional
    'remote_sensing_alternative': '...',  # optional
    'sources': '...',                     # optional
    'applicable_ecosystems': ['Peatland'],# informational; not currently filtered on
    'service_weights': {
        'climate_regulation': 'primary',
        'water_flow_regulation': 'primary',
        'waste_treatment': 'secondary',
        # ...only list the services this indicator actually evidences
    },
    'weight': 1.0,                         # indicator weight in the average
    'bands': [                             # 0–1 scores; the unique key is score
        {'score': 0.1,  'label': 'Bare or absent',          'criteria': '...', 'sort_order': 1},
        {'score': 0.3,  'label': 'Very early stage',        'criteria': '...', 'sort_order': 2},
        {'score': 0.5,  'label': 'Partial recovery',        'criteria': '...', 'sort_order': 3},
        {'score': 0.75, 'label': 'Good recovery',           'criteria': '...', 'sort_order': 4},
        {'score': 0.9,  'label': 'Near reference',          'criteria': '...', 'sort_order': 5},
        {'score': 1.0,  'label': 'Equivalent to reference', 'criteria': '...', 'sort_order': 6},
    ],
    # 'followups': [...]  # optional; see HD for the ecosystem-scoped pattern
},
```

**Do not redefine HD** — the Human Disturbance Pressure indicator
(`human_disturbance_pressure`) is universal and is auto-attached to every project
type by the seed. It is cross-cutting (`service_weights` of `'multiplier'`) and
applied as `sqrt(score)` across all sub-services.

## Step 5 — Assign indicators to the project type

Append to `DEFAULT_PROJECT_TYPE_INDICATORS` (HD is added automatically, so list
only the ecological indicators):

```python
{'project_type': 'peatland_restoration', 'indicator': 'peatland_water_table', 'sort_order': 1, 'is_recommended': True},
{'project_type': 'peatland_restoration', 'indicator': 'peatland_xxx',         'sort_order': 2},
# ...
```

## Step 6 — Guidance (optional but recommended)

In `utils/indicator_instructions.py`, add `(ecosystem_display_name, indicator_code)`
entries (e.g. `('Peatland', 'P1')`) for the scoring intro + full-instructions modal.

---

## How the valuation is affected

For each sub-service of the ecosystem:

- If one or more **committed** indicators name it (via `service_weights`), its
  multiplier is the weighted average of those indicators' band scores
  (`primary`=1.0, `secondary`=0.5), then × the HD multiplier (`sqrt(HD score)`),
  floored at `0.05`. **This replaces the EEI/BBI value for that sub-service.**
- If **no** indicator names it, the sub-service falls back to the EEI-derived
  intactness (× HD), exactly as before.

So a sparse indicator set still works — it supersedes EEI only where you have
real measurements and leaves the rest on EEI.

## Verify

- `python tests/test_indicator_seed_upsert.py` (seed upsert) and
  `python tests/test_indicator_multipliers.py` (multiplier maths).
- Locally: pick the new ecosystem, enable "use project-specific indicators",
  confirm the panel lists your indicators, set band scores, and check the
  sub-service breakdown shows indicator-derived multipliers where you set
  `service_weights` and EEI fallback elsewhere.

# EVE Methodology

**Ecosystem Valuation Engine — how it measures and values ecosystem condition**

*Version: aligned with the v3.9.x engine. This document describes the active calculation pathway in `app.py`, `utils/precomputed_esvd_coefficients.py`, `utils/eei_api.py`, and `utils/indicator_multipliers.py`. It supersedes nothing in `replit.md`; it expands on the "Calculation Methodology" and "Project-indicator sets" sections there.*

---

## How to read this document

Each major section opens with a **plain-language summary** (for the general reader) and then continues with the **technical detail** (for a scientific or quantitative audience). The two halves describe the same procedure at different resolutions.

The methodology has two layers that combine into a single monetary figure:

1. **A top-down, satellite-driven layer** that establishes *what* an area is (its ecosystem types), *how much* of each there is, and *how intact* it is, using remote sensing and a remotely-derived integrity index.
2. **A bottom-up, field-measured layer** (optional, per project) that lets on-the-ground indicators *override* the remotely-estimated intactness on a service-by-service basis.

Both layers feed the same economic core: peer-reviewed valuation coefficients standardised to **2024 International dollars per hectare per year (Int\$/ha/yr)**.

---

## 1. Top-down satellite-based analysis

### 1.1 Plain-language summary

The user draws an area on a map. EVE scatters a set of sample points evenly across it, and at each point it works out what kind of ecosystem is there (forest, wetland, grassland, mangrove, and so on) from satellite land-cover data. It also reads a satellite-derived "health" score for each point. Open water is detected and removed so it does not inflate the result. From all the points, EVE builds a picture of the area's composition (e.g. "70% temperate forest, 30% wetland") and an overall condition score, which becomes the starting point for the economic valuation.

### 1.2 Area selection and spatial sampling

The user delineates a polygon on an interactive Folium map (`streamlit-folium`). EVE generates **10–100 sample points** (default 10, chosen for fast iteration; user-configurable) distributed evenly across the polygon irrespective of its size (`utils/sampling_utils.py`). The sample-point set is the spatial backbone for every downstream step: land-cover classification, spectral quality assessment, and the Ecosystem Ecological Integrity (EEI) lookup all operate per point and are then aggregated to the area.

### 1.3 Per-point ecosystem classification

Each sample point is classified into an ecosystem type using land-cover data:

- **Primary source:** OpenLandMap STAC API and ESA WorldCover land-cover layers (`utils/openlandmap_stac_api.py`, `utils/openlandmap_integration.py`, `utils/esa_landcover_codes.py`, `utils/landcover_api.py`).
- **Forest sub-typing:** where the land cover resolves to generic "forest," EVE refines the type from latitude/longitude into **tropical, temperate, boreal, or Mediterranean forest** using biome-boundary logic (`EnhancedSatelliteSimulator._determine_forest_type`). A European-Atlantic exception raises the boreal threshold from 50°N to 60°N so that the UK, Ireland, continental Europe, the Baltics and southern Scandinavia are correctly classified as temperate rather than boreal, while North-American and East-Asian forest at the same latitude band remains boreal (`_is_european_atlantic_zone`).
- **Forced ecosystems:** some restoration ecosystems (e.g. Peatland) are not represented in the land-cover layers and therefore can never be auto-detected. When such an ecosystem is selected as an override, EVE *forces* it onto the whole drawn area — every sample point is stamped with that ecosystem and the land-cover lookup is skipped (`utils/forced_ecosystems.py`).

The classification step achieves ~90% accuracy across the major ecosystem types per the architecture notes in `replit.md`.

### 1.4 Spectral signatures and quality assessment

EVE characterises the spectral behaviour of each ecosystem using an **enhanced Landsat-8/9 OLI simulation** (`utils/enhanced_satellite_simulator.py`) calibrated to peer-reviewed ecosystem spectral signatures. For each ecosystem type it models the six OLI reflectance bands (blue, green, red, NIR, SWIR1, SWIR2) with realistic means, standard deviations, and seasonal variation, plus a cloud-cover tendency. From these it derives:

- **NDVI** (Normalised Difference Vegetation Index), `(NIR − Red) / (NIR + Red)`, as a vegetation-vigour/quality signal.
- **NDWI** (Normalised Difference Water Index), `(Green − NIR) / (Green + NIR)`, for water detection (`utils/satellite_data.py`).
- **Data-quality flags** (good / fair / poor) penalised by cloud cover, low solar elevation (winter), and invalid NDVI, aggregated to an overall time-series quality grade (excellent / good / fair / poor).

> **Note on simulation.** The spectral layer is a *characteristics* simulation — band statistics are drawn from authentic Landsat OLI response and peer-reviewed ecosystem signatures, but the individual scenes are modelled rather than retrieved. It is used for quality adjustment and water masking, not as the source of the monetary coefficients. The metadata flags this explicitly (`authentic_data: False`, `authentic_characteristics: True`). USGS/landsatxplore retrieval (`utils/usgs_integration.py`) is the real-imagery path where available.

### 1.5 Open-water exclusion

Open water has no terrestrial/coastal ecosystem-service value in EVE's framework and must not dilute the per-hectare result. Points with a strong water signature are detected via NDWI thresholds (NDWI > 0.5 → open water; graduated wetland/wet thresholds below that) and excluded from natural-capital totals, with the excluded water hectarage reported separately (`utils/satellite_data.py`). **This exclusion is a load-bearing invariant** — it must be preserved through any change to sampling or calculation code.

### 1.6 Area composition and diversity

Aggregating the per-point classifications yields the area's **ecosystem composition** (percentage of each type). EVE computes **Shannon** and **Simpson diversity indices** over this composition (`utils/natural_capital_metrics.py`). The composition drives the multi-ecosystem valuation path (Section 3.4).

### 1.7 Ecosystem Ecological Integrity (EEI) — the top-down intactness signal

Land cover tells you *what* an ecosystem is; it does not tell you *how intact* it is. For that, EVE queries the **Ecosystem Ecological Integrity (EEI) API** (`utils/eei_api.py`; service at `https://eve-solutions-482317.uc.r.appspot.com`, a separate Earth Engine / GEE application).

**What EEI is.** A 0–1 index of ecosystem condition, computed in Earth Engine from three components:

- **Functional integrity** — Net Primary Productivity (NPP)-based.
- **Structural integrity** — landscape connectivity.
- **Compositional integrity** — biodiversity.

**How EVE uses it.** Sample-point coordinates are sent in a single batched request (cap 100 points, matching EVE's max sample count) to `/api/eei-batch`. Per-point integrity values (`eii`) are returned and then averaged. The mean EEI per ecosystem type becomes the **default intactness multiplier** for that ecosystem in the valuation — replacing arbitrary manual defaults with a data-driven value (`_effective_intactness_dict` in `app.py`; toggle `use_eei_for_intactness`, default on).

**Data-integrity safeguards.** The EEI service can fall back to *demo* (fabricated, latitude-based) values when Earth Engine is unavailable. EVE detects demo results by the explicit `demo_mode` flag and **discards them** so fabricated values never flow into intactness defaults or the valuation. A "no-data" pixel (ocean / data gap) is treated as *real but empty*, not demo. An ecosystem whose EEI is *entirely* demo gets a conservative **50% intactness fallback** rather than the optimistic 100% default (`DEMO_FALLBACK_INTACTNESS_PCT`), so missing data can never inflate value.

This EEI-derived intactness is referred to internally as the **BBI** (the baseline/biodiversity intactness multiplier) and is the quantity the field indicators in Section 4 are allowed to override.

---

## 2. The economic core: ESVD/TEEB valuation coefficients

### 2.1 Plain-language summary

EVE does not invent dollar values. It uses a large library of published studies that have already put a price on ecosystem services — things like flood protection, carbon storage, clean water, recreation. For every ecosystem type and every service, EVE holds a single representative value (a median across the relevant studies), expressed in 2024 international dollars per hectare per year. These are then adjusted for the wealth of the country the area sits in.

### 2.2 Source database and service taxonomy

Coefficients derive from the **Ecosystem Services Valuation Database (ESVD), release APR2024 V1.1 — 10,874 peer-reviewed records spanning 1,100+ publications (1970–2024)**, complemented by TEEB. Each record carries biome, service category, valuation method, location, year, and a value pre-normalised to **2024 International dollars** via World Bank PPP (`utils/precomputed_esvd_coefficients.py`, header documentation).

Services follow the **TEEB framework's 22 sub-services** across four categories:

- **Provisioning** — food, water, raw materials, genetic resources, medicinal resources, ornamental resources.
- **Regulating** — air-quality regulation, climate regulation, moderation of extreme events, water-flow regulation, waste treatment, erosion prevention, soil fertility/formation, pollination, biological control.
- **Cultural** — aesthetic information, recreation and tourism, culture/art/design (inspiration), spiritual experience, cognitive development.
- **Supporting** — maintenance of life cycles (habitat/nursery), maintenance of genetic diversity.

The TEEB mapping is designed to **eliminate double counting** between overlapping ESVD categories.

### 2.3 Coefficient derivation

For each ecosystem × service combination (`utils/precomputed_esvd_coefficients.py` §2.3):

1. Extract all relevant ESVD records for the mapped biomes and service categories.
2. Apply quality filters; exclude outliers beyond ±2 standard deviations and studies with methodological concerns.
3. Take the **median** (not the mean) to limit the influence of extreme valuations.
4. Require a **minimum of 5 studies** per coefficient; otherwise borrow from a related ecosystem.
5. Record the study count for provenance (the "From X studies" comments, and `esvd_coefficient_study_mappings.txt` / `detailed_esvd_study_value_mappings.txt`).

> *Worked example (from the source documentation): Wetland climate regulation — 67 candidate studies ($89–$1,240/ha/yr), 4 statistical outliers and 2 poor-methodology studies removed, final median over 61 studies = $407.07/ha/yr, which becomes the `climate` coefficient for Wetland.*

These static, pre-computed coefficients give a large performance gain over live database queries with no loss of fidelity relative to the median-based derivation.

### 2.4 Regional adjustment (income elasticity)

A raw coefficient is a global figure; willingness/ability to pay for ecosystem services scales with income. EVE applies a **country-specific income-elasticity multiplier** using World Bank **2024 GDP per capita** (`utils/country_gdp_2024.py`):

```
regional_factor = 1 + (elasticity × (country_GDP / global_GDP − 1))
```

- **Default elasticity = 0.6** (user-configurable).
- **Bounded to [0.4, 2.5]** to prevent extreme values.
- Country is resolved from the area's coordinates (see Section 2.4.1).
- **Marine** ecosystems receive **no** regional adjustment (`regional_factor = 1.0`) since they sit in international waters.

### 2.4.1 Resolving a coordinate to a country

The regional factor needs a country-specific GDP, so each point's `(lat, lon)` must first be mapped to a country. EVE does this with a primary reverse-geocoder and a graded fallback chain so that a geocoding outage degrades the *precision* of the adjustment rather than breaking the valuation (`utils/nominatim_geocoding.py`, reached via `get_country_from_coordinates` in `utils/precomputed_esvd_coefficients.py`).

**Plain-language summary.** EVE asks OpenStreetMap which country each sampled point falls in, then takes a majority vote across all the points to decide the area's country. If the lookup service is unavailable it falls back to an approximate map of country boxes, and if even that fails it uses a neutral global-average figure so the result is never wrong, only less locally tuned.

**Primary method — OpenStreetMap Nominatim reverse geocoding.**

- Each point is sent to the public **Nominatim** reverse-geocoding API (`nominatim.openstreetmap.org/reverse`).
- The request uses **city-level `zoom=10`** deliberately: at very low zoom Nominatim's country-polygon match is loose at coastlines (a documented case mis-resolved North Devon, UK to Ireland under `zoom=3`).
- The country name is read from the response `address` block (`country`, falling back to `country_code`, then `state` for some territories) and **normalised** to an internal GDP-lookup key through a large alias table that handles native-language and short forms — e.g. `Deutschland`→`germany`, `España`→`spain`, `日本`→`japan`, and `UK`/`England`/`Scotland`/`Wales`→`united_kingdom`. Unlisted names are snake-cased as a best-effort fallback.
- **Politeness and performance** are built in to respect Nominatim's usage policy: rate limiting to **1 request/second**, a required descriptive `User-Agent`, and **two caching layers** — a 24-hour in-process cache (coordinates rounded to ~100 m) plus a Streamlit `@st.cache_data` layer, with module-entry coordinates rounded to 2 dp (~1 km) so neighbouring points share a cache entry.

**Fallback 1 — rectangular bounding boxes.** On timeout, HTTP error, rate-limit (429), or a response with no country, EVE drops to a hard-coded latitude/longitude **bounding-box decision tree** (`_fallback_get_country`) covering the major economies across North America, Europe, Asia-Pacific, Latin America, and Sub-Saharan Africa. This is the original pre-Nominatim implementation, retained as an offline safety net; it is approximate (rectangles, not true borders).

**Fallback 2 — global average.** Any point that still cannot be resolved returns the sentinel `global_average`, which makes `get_country_gdp` use the global mean GDP — yielding a regional factor of ~1.0 (no adjustment) rather than a misattributed country.

**Per-point → area country (majority vote).** Because an analysis has many points, `determine_predominant_country` decides the area's country:

1. **Deduplicate** points (rounded to ~11 m) to minimise API calls, reusing the cache.
2. Look up each unique point.
3. **Majority vote** across points; points returning `global_average` are treated as international waters and excluded from the vote.
4. **Tie-break** first on the polygon **centroid's** country, then **alphabetically**.
5. If *every* point is unidentifiable or ocean, the area is reported as **International Waters**.

### 2.5 The base valuation formula

Per service, per ecosystem (`calculate_ecosystem_values`):

```
value = coefficient × area_hectares × regional_factor × intactness_multiplier
```

(plus an optional `urban_green_blue_multiplier` for Urban ecosystems). The `intactness_multiplier` is where the two methodology layers meet — see Sections 3 and 4. Summing across all 22 services and four categories gives the area's total annual ecosystem-service value.

---

## 3. Intactness as a modifier — the default (top-down) mode

### 3.1 Plain-language summary

A pristine forest is worth more per hectare than a degraded one. EVE captures this with an "intactness" multiplier between 0 and 1 that scales the textbook value down to reflect real condition. By default this multiplier comes from the satellite-derived EEI score (Section 1.7) and is applied evenly across every service.

### 3.2 Uniform BBI mode

In the default mode, the `intactness_multiplier` argument to `calculate_ecosystem_values` is a **single scalar (0.0–1.0)** — the EEI-derived BBI for that ecosystem — applied identically to all 22 sub-services:

```
value_service = coefficient_service × area × regional_factor × BBI
```

This is the right default when the only condition signal available is remote (EEI). Its limitation is that it is *uniform*: it cannot express that, say, a mangrove's coastal-protection service has recovered faster than its biodiversity service. That is exactly what the field-indicator layer adds.

### 3.3 Where the BBI comes from

`_effective_intactness_dict` (`app.py`) resolves the multiplier per ecosystem:

- **EEI on (default):** derive from the per-area EEI fetch (0–1 → 0–100%); manual sliders are *not* consulted; demo-only ecosystems get the 50% conservative fallback.
- **EEI off:** use the user's manual intactness sliders (`ecosystem_intactness`, 0–100%).

Critically, EEI never overwrites the manual slider state — the two are independent inputs selected by the toggle.

### 3.4 Multi-ecosystem aggregation

For heterogeneous areas (`app.py`):

- **Mixed path** (≥2 ecosystem types each >10% cover): loop the ecosystem composition, allocate area proportionally, and call `calculate_ecosystem_values()` per type. Percentages are **rounded** to match the UI display exactly, preventing precision drift between the calculation and what the user sees.
- **Single path** (low diversity / one dominant type): one call over the full area.

---

## 4. On-the-ground, ecosystem-specific indicators

### 4.1 Plain-language summary

The satellite view is powerful but coarse — it cannot see how many seedlings are growing, whether a canopy has truly closed, or whether people are illegally cutting the site. For restoration projects, EVE lets a field team answer a short set of ecosystem-specific questions, each scored from simple measurements anyone can take. These field scores then *replace* the satellite-based condition estimate for the specific services they relate to — and where a field measurement says nothing about a service, EVE keeps using the satellite estimate for that service. One special question — how much human disturbance the site is under — acts as a risk dial that turns *every* service value up or down.

### 4.2 Rationale: why a second layer

Remotely-sensed integrity (EEI) is uniform and cannot resolve sub-service condition or local pressures. Field indicators are **service-specific** and **locally observed**. EVE therefore lets field measurements *supersede the EEI-derived intactness per sub-service*, while falling back to EEI wherever no indicator covers a given sub-service. This is opt-in per assessment (`use_indicator_multipliers`); when off, the uniform BBI path (Section 3) is used unchanged.

### 4.3 Indicator sets and the data model

An indicator set is **pure data**, not code (`utils/project_indicators_seed.py`, upserted to the `pi_*` tables on startup; the engine in `utils/indicator_multipliers.py` is ecosystem-agnostic). Each project type maps to one EVE ecosystem and ships:

- A list of **ecological indicators** (e.g. Mangrove `M1`–`M7`: canopy cover, seedling/sapling density, natural recruitment, etc.; Tropical Forest reforestation ships its own seven).
- One **universal mandatory cross-cutting indicator**, `HD` (Human Disturbance Pressure), attached automatically to every project type.

Two project types are seeded today — **Mangrove Restoration** and **Tropical Forest Reforestation**. Adding another is a data exercise (taxonomy seed + an ESVD coefficient block), documented in `docs/adding_indicator_sets.md`.

Each indicator carries:

- A **scoring band table** mapping a field observation to a normalised **score in [0, 1]** (e.g. mangrove canopy cover: `<10%` → 0.1 … `>85%` → 1.0). Bands give plain-language criteria, an ecological meaning, and a field method completable by a non-specialist team.
- A **`service_weights`** dictionary mapping the indicator to the TEEB sub-services it informs, each tagged **`primary`** or **`secondary`** (HD's are all tagged `multiplier`).
- Provenance (`sources`) and a remote-sensing alternative where one exists.

### 4.4 From field scores to per-sub-service multipliers

The engine (`utils/indicator_multipliers._compute_pure`) converts indicator responses into **one multiplier per sub-service**, replacing the uniform BBI. The procedure, for each of an ecosystem's sub-service keys:

**Step 1 — translate keyspaces.** Indicators are authored in the TEEB slug space (`habitat_for_species`, `climate_regulation`, …); coefficients live in the calc keyspace (`habitat`, `climate`, …). `utils/teeb_slug_map.py` is the single translation table. Where two TEEB slugs collapse onto one calc key (e.g. `habitat_for_species` and `genetic_diversity` → `habitat`), the engine keeps the **strongest** relationship so a `primary` link always wins over a `secondary` one.

**Step 2 — weighted average over covering indicators.** Relationship types are weighted:

```
primary = 1.0,  secondary = 0.5
```

For a sub-service *s*, collect every committed, answered, non-HD indicator whose `service_weights` reference *s*, and compute the weight-weighted mean of their scores:

```
indicator_multiplier(s) = Σ(score_i × weight_i) / Σ(weight_i)
```

**Step 3 — fall back to BBI where there is no coverage.** If no indicator references *s*, the multiplier for *s* is the EEI-derived **BBI** (Section 3.3). This is the mechanism by which field data *supplements* rather than *discards* the remote signal: only the services a field team actually measured are overridden.

**Step 4 — apply the cross-cutting HD multiplier.** Human Disturbance Pressure is *not* averaged into any single sub-service; it is a whole-area risk modifier applied on top of every sub-service simultaneously:

```
final_multiplier(s) = clamp_floor( base(s) × HD_multiplier , 0.05 )
```

where `base(s)` is either the indicator-derived multiplier (Step 2) or the BBI fallback (Step 3).

**Step 5 — floor.** Indicator-derived finals are floored at **0.05** (`INDICATOR_FLOOR`) so that an extreme HD × very-low-indicator combination cannot drive a service to absolute zero (which would imply irreversible destruction with no recovery potential). BBI values carry their own slider minimum and are not separately floored.

The resulting per-sub-service dictionary is then passed straight into `calculate_ecosystem_values`, which multiplies each coefficient by its own service-specific multiplier instead of a single uniform BBI (the dict-vs-scalar branch in `calculate_ecosystem_values`).

### 4.5 The HD cross-cutting multiplier in detail

HD answers a single question — the dominant human pressure on the site — scored into bands from `0.1` (severe and active: clearing/burning/draining/overfishing happening now) up to `1.0` (fully secure). It is converted to a multiplier with a **square-root dose-response curve** (`_hd_multiplier_from_score`, matching the seed's `multiplier_exponent: 0.5`):

```
HD_multiplier = sqrt(score)
```

The square root *moderates* the penalty so moderate disturbance reduces, but does not eliminate, realised value:

| HD score | HD multiplier | Approx. reduction |
|---:|---:|---:|
| 0.50 (moderate) | 0.71 | ~29% |
| 0.10 (severe) | 0.32 | ~68% |

An **unanswered** HD defaults to a multiplier of **1.0** (no penalty) — disturbance is never *assumed* worst. HD is identified canonically by its slug (`human_disturbance_pressure`) rather than by the generic mandatory flag, so the engine handles it consistently across all project types. Its rationale is both ecological (disturbance degrades all services together — e.g. Danovaro et al. 2018 report ~80% loss of microbial decomposition, significant carbon-stock loss, and ~20% biodiversity loss in disturbed mangroves) and financial (a site under active threat is a worse investment than an identical secure one).

### 4.6 Worked illustration

Consider a mangrove sub-service with field coverage and one without, under moderate disturbance (HD score 0.5 → multiplier 0.71):

- **`erosion` (erosion prevention)** — covered `primary` by canopy cover (field score 0.75) and `primary` by another structural indicator (0.9). Weighted mean = (0.75·1.0 + 0.9·1.0)/2 = 0.825. Final = 0.825 × 0.71 = **0.586**.
- **`medicinal_resources`** — no mangrove indicator measures it (deliberately excluded from the seed). Falls back to BBI; if the EEI-derived BBI is 0.80, final = 0.80 × 0.71 = **0.568**.

Each coefficient is then scaled by its own final multiplier, so the valuation reflects *measured* condition where it exists and *remote* condition everywhere else, with site-wide disturbance risk layered over both.

### 4.7 Full indicator catalogue

Two field-indicator sets ship today, each with seven ecological indicators plus the universal mandatory **HD** cross-cutting indicator. Every ecological indicator is scored 0.1 → 1.0 on a six-band scale (the bands are listed per indicator in `utils/project_indicators_seed.py` and the full field instructions in `utils/indicator_instructions.py`). The "services informed" column lists the TEEB sub-services each indicator weights as **(P)** primary or **(S)** secondary.

**Mangrove Restoration** (`mangrove_restoration` → *Mangroves*; completable in a single 2–3 hour field visit by a non-specialist team):

| Code | Indicator | Field measurement | Services informed |
|---|---|---|---|
| **M1** | Canopy Cover | % sky covered by canopy (upward photo at 5 points) | raw materials, air-quality, climate, extreme events, erosion, habitat, aesthetic **(P)**; food, water, waste treatment, genetic diversity, recreation **(S)** |
| **M2** | Seedling & Sapling Density | count of plants <1.3 m in 3 m × 3 m plots | habitat, genetic diversity **(P)**; raw materials, climate **(S)** |
| **M3** | Natural Recruitment | distribution of un-planted recruits across site | habitat, genetic diversity **(P)**; raw materials, genetic resources, climate **(S)** |
| **M4** | Tidal Flow & Hydrological Function | water movement at high vs low tide; blockages | water provisioning, extreme events, water-flow regulation, waste treatment, habitat **(P)**; food, climate **(S)** |
| **M5** | Water Clarity | visibility / Secchi depth in adjacent water | food, water, waste treatment, aesthetic, recreation **(P)**; habitat **(S)** |
| **M6** | Wildlife & Fauna Signs | count of distinct animal types in a 30-min watch | habitat, genetic diversity, recreation, inspiration, spiritual experience **(P)**; food, genetic resources, aesthetic **(S)** |
| **M7** | Invasive Species Pressure | % vegetation that is non-native/invasive | habitat, genetic diversity **(P)**; nine other services **(S)** |
| **HD** | Human Disturbance Pressure *(mandatory)* | dominant human pressure on site & surroundings | cross-cutting `sqrt(score)` multiplier on **all** services |

**Tropical Forest Reforestation** (`tropical_forest_reforestation` → *Tropical Forest*; half-day visit, trained non-specialist team; indicators TF2–TF5 share one permanent 20 m × 20 m plot):

| Code | Indicator | Field measurement |
|---|---|---|
| **TF1** | Canopy Cover | % canopy from upward photos at 5 plot points |
| **TF2** | Tree Species Richness | distinct tree species in the permanent plot |
| **TF3** | Canopy Height | tallest-tree height (structural development) |
| **TF4** | Native Species Natural Regeneration | un-planted native seedlings establishing |
| **TF5** | Leaf Litter & Soil Organic Layer | litter/organic-layer depth & cover |
| **TF6** | Wildlife & Fauna Signs | count of distinct animal types observed |
| **TF7** | Invasive Species Pressure | % cover of invasive/non-native plants |
| **HD** | Human Disturbance Pressure *(mandatory)* | cross-cutting multiplier on all services |

Three TEEB sub-services (`medicinal_resources`, `ornamental_resources`, `pollination`) are deliberately **excluded** from the mangrove seed because no field-measurable mangrove proxy exists for them; they remain in the canonical slug list so future indicators can reference them, and they fall back to BBI in the meantime. Five further project types are scaffolded for future seeding (Temperate Forest, Peatland, Freshwater Wetland, Grassland, Seagrass) — the HD disturbance-source dropdown already carries their pressure options.

### 4.8 Indicator provenance and derivation

#### 4.8.1 Plain-language summary

The field indicators are not invented for EVE. Each one is a simple, anyone-can-measure proxy for an attribute that the established ecosystem-restoration and condition-monitoring literature already recognises as a key signal of recovery — canopy closure, regeneration, structural height, soil/litter build-up, wildlife return, invasion pressure, and human disturbance. EVE's contribution is to translate those recognised attributes into measurements a non-specialist community team can take with a phone and a tape measure, and to map each one to the ecosystem services it credibly informs.

#### 4.8.2 Framework basis

The indicator sets are derived from, and aligned to, a small number of standard restoration-monitoring frameworks and restoration-ecology syntheses, so that scores are defensible to verifiers and investors:

- **NatureServe — Ecological Resilience Indicators** (incl. the 2019 mangrove set): the structural/compositional resilience attributes behind the mangrove indicators (canopy, regeneration density, recruitment, hydrological function).
- **Society for Ecological Restoration (SER) — International Principles and Standards for the Practice of Ecological Restoration (2019):** the recovery "attributes" the tropical-forest indicators are explicitly mapped to (e.g. Attribute 2 structure, Attribute 5 species composition, Attribute 6 regeneration, Attribute 7 fauna).
- **ITTO — Guidelines for the Restoration, Management and Rehabilitation of Degraded and Secondary Tropical Forests (2002, Policy Development Series No. 13).**
- **Carbon-standard methodologies — Verra VM0007 (REDD+ framework)** and **IPCC 2006 AFOLU Guidelines (Vol. 4):** for the carbon-relevant pools (biomass, litter, dead organic matter, soil) that several indicators proxy.
- **IUCN — Red List of Ecosystems Guidelines (2020):** condition/biodiversity framing for the fauna indicator.

These are underpinned by peer-reviewed restoration-ecology meta-analyses establishing the recovery trajectories the bands encode — notably **Poorter et al. 2016 (*Nature*)** and **Rozendaal et al. 2019 (*Science Advances*)** on secondary-forest recovery, **Crouzeilles et al. 2017 (*Science Advances*)** on natural regeneration, **Chazdon 2014 (*Second Growth*)**, and the **GEDI** canopy/height products (**Dubayah et al. 2020**; height–biomass via **Chave et al. 2014**, **Asner et al. 2014**) for the remote-sensing alternatives.

The **HD (Human Disturbance Pressure)** indicator is grounded in evidence that disturbance degrades all services simultaneously — e.g. **Danovaro et al. 2018 (*Scientific Reports*)** report ~80% loss of microbial decomposition, significant carbon-stock loss, and ~20% biodiversity loss in disturbed mangroves — which is the basis for treating it as a cross-cutting multiplier rather than a single-service indicator (Section 4.5).

#### 4.8.3 Per-indicator sources

Sources are recorded in the `sources` field of each indicator in `utils/project_indicators_seed.py`; the supporting evidence narrative is in each indicator's `why_matters` field, and the field protocols in `utils/indicator_instructions.py`.

**Mangrove Restoration:**

| Code | Indicator | Sources |
|---|---|---|
| **M1** | Canopy Cover | Nayak & Bahuguna 2001; Gatt et al. 2022; NatureServe Ecological Resilience Indicators for Mangrove 2019 |
| **M2** | Seedling & Sapling Density | NatureServe Ecological Resilience Indicators (mean density of seedlings/saplings/viable propagules across plots); Bosire et al. 2008 |
| **M3** | Natural Recruitment | Gatt et al. 2022; NatureServe Ecological Resilience Indicators 2019 |
| **M4** | Tidal Flow & Hydrological Function | NatureServe Ecological Resilience Indicators for Mangrove 2019 |
| **M5** | Water Clarity | No formal citation in seed; protocol follows standard Secchi-depth/turbidity practice |
| **M6** | Wildlife & Fauna Signs | No formal citation in seed; standard rapid faunal-diversity observation |
| **M7** | Invasive Species Pressure | No formal citation in seed; standard invasion-cover assessment |
| **HD** | Human Disturbance Pressure | No formal citation in `sources`; rationale (`why_matters`) cites Danovaro et al. 2018 (*Scientific Reports*) |

**Tropical Forest Reforestation:**

| Code | Indicator | Sources |
|---|---|---|
| **TF1** | Canopy Cover | Poorter et al. 2016 (*Nature*); Chazdon 2014, *Second Growth*; ITTO 2002 Guidelines (PDS No. 13); SER 2019 Standards (Attribute 2) |
| **TF2** | Tree Species Richness | Rozendaal et al. 2019 (*Science Advances*); Chazdon 2014; ITTO 2002; Brancalion et al. 2019 (*Science Advances*); SER 2019 (Attribute 5); Verra VM0007 |
| **TF3** | Canopy Height | Dubayah et al. 2020 (GEDI methodology); Poorter et al. 2016; Chave et al. 2014 (*Global Change Biology*); Asner et al. 2014 (*PNAS*); IPCC 2006 AFOLU Vol. 4 Ch. 4 |
| **TF4** | Native Species Natural Regeneration | Crouzeilles et al. 2017 (*Science Advances*); Poorter et al. 2016; Chazdon 2014 (Ch. 5–7); SER 2019 (Attribute 6); NatureServe 2019 |
| **TF5** | Leaf Litter & Soil Organic Layer | Don et al. 2011 (*Global Change Biology*); Chazdon 2014 (Ch. 8); Poorter et al. 2016; IPCC 2006 AFOLU Vol. 4 Ch. 2; Verra VM0007 |
| **TF6** | Wildlife & Fauna Signs | Gardner et al. 2009 (*Ecology Letters*); Chazdon 2014 (Ch. 10); SER 2019 (Attribute 7); Verra VM0007; IUCN 2020 Red List of Ecosystems Guidelines |
| **TF7** | Invasive Species Pressure | Mack et al. 2000 (*Ecological Applications*); Richardson et al. 2011 (*J. Applied Ecology*); Chazdon 2014 (Ch. 6); ITTO 2002 (Section 4.3); Brancalion et al. 2019 |
| **HD** | Human Disturbance Pressure | As above (cross-cutting; Danovaro et al. 2018) |

> **Note.** Four indicators (M5, M6, M7, HD) carry no formal citation in the `sources` field — their protocols are standard rapid-assessment field practice rather than derived from a single publication. The mangrove set as a whole rests on the NatureServe resilience framework; the tropical-forest set is mapped attribute-by-attribute to the SER 2019 Standards and the restoration-ecology meta-analyses above. Where a new indicator set is added, the recipe in `docs/adding_indicator_sets.md` requires populating the `sources` field as part of authoring it.

---

## 5. Combining the layers: end-to-end calculation flow

### 5.1 Plain-language summary

EVE measures the area from space, prices each service from the literature, adjusts for the local economy, and then scales each service by how intact it is — using field data where available and satellite data everywhere else. The output is an annual dollar value for the area's natural capital, broken down by service and ecosystem.

### 5.2 Pipeline

```
1. User draws polygon
2. Distribute 10–100 sample points
3. Per point: land-cover → ecosystem type (+ forest sub-typing / forced ecosystems)
4. Per point: spectral simulation → NDVI quality, NDWI water mask (exclude open water)
5. Aggregate → ecosystem composition + Shannon/Simpson diversity
6. Per point: EEI batch lookup → average integrity (discard demo data)
        → BBI default intactness per ecosystem (or 50% demo fallback)
7. IF project indicators enabled:
        field indicator scores → per-sub-service multipliers
            (indicator-covered services: weighted primary/secondary mean)
            (uncovered services: BBI fallback)
            × HD cross-cutting multiplier, floored at 0.05
   ELSE:
        uniform BBI scalar
8. valuation = Σ_services [ coefficient × area × regional_factor × multiplier(service) ]
        (multi-ecosystem: area-proportional, rounded-percentage weighting)
9. Outputs: annual Int$/ha/yr by service, category, and ecosystem; diversity;
        excluded-water hectares; time-series and EROI where applicable
```

### 5.3 Standardisation and invariants

- All monetary outputs are **2024 International dollars per hectare per year**.
- **Open water is always excluded** from natural-capital totals (NDWI mask).
- Multi-ecosystem percentages are **rounded** to match UI display and keep calculation and presentation consistent.
- Default sample count is **10** (dev speed); production analyses can raise it to 100.

---

## 6. Ecological Return on Investment (EROI)

### 6.1 Plain-language summary

For projects with a restoration target, EVE compares the *gain* in ecosystem-service value against the *cost* of achieving it, and reports how good that trade is.

### 6.2 Technical detail

For project-indicator runs that produce a **target valuation**, the user enters the estimated cost to reach the target condition (persisted inside the existing `saved_areas.project_indicators` JSON — no schema change). EVE then reports three scale-invariant metrics (identical whether computed per-hectare or total):

- **Total Project Ecosystem Services Gain** = target valuation − baseline valuation (gain over the project life).
- **Average annual gain** = total gain ÷ project duration (duration = target date − baseline date).
- **EROI** = total gain ÷ cost (benefit–cost ratio).
- **Annual return rate** = average annual gain ÷ cost.
- **Payback period** = cost ÷ average annual gain (years after the target date to repay cost).

EROI-related inputs collected in the project-indicator panel include the **project cost**, **baseline and target area percentages**, an optional **discount rate**, **annual maintenance cost**, and a **buffer percentage** (a conservative discount on claimed gains).

---

## 7. Carbon revenue opportunity

### 7.1 Plain-language summary

Alongside the full ecosystem-service value, EVE estimates how much an area's climate-regulation service might be worth specifically as tradeable carbon credits.

### 7.2 Technical detail

EVE back-calculates an **implied annual CO₂ sequestration** from the ESVD **climate-regulation** service value and a **social cost of carbon (SCC)**:

```
implied_sequestration (tCO2e/yr) = climate_regulation_value (Int$/yr) ÷ SCC (Int$/tCO2e)
```

The SCC is user-selectable — **Conservative Int\$100, Central Int\$190 (default, consistent with the US EPA 2023 interim estimate), High Int\$300, or a custom Int\$50–500 value**. The implied sequestration is then valued as a **revenue range** at user-set **voluntary-carbon-market credit prices** (default low Int\$10 / high Int\$30 per tCO₂e). This is presented as an *opportunity* figure beside the results, not as part of the core natural-capital total. *(A cross-check of this implied sequestration against satellite-derived carbon data is a parked enhancement.)*

---

## 8. User-configurable settings and parameters

### 8.1 Plain-language summary

EVE exposes the key assumptions as settings, so an analyst can tune the analysis to their context and document exactly what was assumed.

### 8.2 Settings reference

All settings live in the Analysis Settings dialog (`app.py`); defaults in parentheses.

| Setting | Range / options (default) | Effect |
|---|---|---|
| **Sample points** | 9–100 (9–10) | Spatial sampling density; higher = more accurate, slower |
| **Income elasticity factor** | 0.1–1.0 (0.6) | Strength of the regional GDP adjustment (Section 2.4); bounded 0.4×–2.5× |
| **Use EEI for default intactness** | on / off (on) | EEI-derived BBI vs manual intactness sliders (Section 3.3) |
| **Ecosystem intactness by type** | 0–100% per ecosystem (100%) | Manual intactness when EEI is off; 14 ecosystem types |
| **Urban green/blue coverage** | 0–100% (18%) | Urban green/blue infrastructure multiplier applied to Urban services |
| **Ecosystem mapping (advanced)** | per land-cover code → ecosystem | Override of the land-cover → ecosystem-type lookup |
| **Social cost of carbon** | Int\$100 / 190 / 300 / custom 50–500 (190) | Divisor for implied carbon sequestration (Section 7) |
| **Carbon credit price (low / high)** | Int\$0–500 per tCO₂e (10 / 30) | Voluntary-market price band for the carbon revenue range |
| **Analysis date range** | start / end dates | Temporal window for time-series / change analysis |
| **Ecosystem override** | detected type or forced ecosystem | Force a single ecosystem (incl. satellite-undetectable ones) onto the area |
| **Project indicators** | on / off per assessment | Enables the field-indicator override path (Section 4) |
| **Project EROI inputs** | cost, areas, discount, maintenance, buffer | Feed the EROI metrics (Section 6) |

---

## 9. Assumptions, limitations, and provenance

### 9.1 Known limitations

- **Coefficients are global medians.** Local conditions can diverge significantly from the median; the regional adjustment corrects for income but not for local ecological idiosyncrasy.
- **ESVD geographic bias.** The source literature over-represents developed countries; some ecosystem × service cells have thin study coverage and borrow from related ecosystems.
- **Static coefficients.** Temporal change in underlying service values is not captured by the coefficients themselves (it is captured by change in measured condition between analyses).
- **Linear income-elasticity assumption** in the regional adjustment.
- **Spectral simulation** provides realistic *characteristics*, not retrieved scenes, for quality/water masking; it is not the source of monetary values.
- **EEI demo fallback.** When Earth Engine is unavailable the integrity signal can be absent; EVE substitutes a conservative 50% rather than fabricated values, which is deliberately pessimistic.

### 9.2 Provenance and reproducibility

- Coefficient → study mappings: `esvd_coefficient_study_mappings.txt`, `detailed_esvd_study_value_mappings.txt`, and the inline "From X studies" annotations in `utils/precomputed_esvd_coefficients.py`.
- **Indicator provenance: see the full per-indicator source tables and framework basis in Section 4.8.** Sources live in each indicator's `sources` field in `utils/project_indicators_seed.py`; field protocols in `utils/indicator_instructions.py`.
- Coefficient/methodology changes should be reflected in `replit.md` and the `*_mappings.txt` provenance files.

---

## 10. Source-code reference map

| Concern | Module(s) |
|---|---|
| Sample-point generation | `utils/sampling_utils.py` |
| Land-cover / ecosystem classification | `utils/openlandmap_stac_api.py`, `utils/openlandmap_integration.py`, `utils/esa_landcover_codes.py`, `utils/landcover_api.py` |
| Forest sub-typing & spectral simulation | `utils/enhanced_satellite_simulator.py` |
| Real imagery retrieval | `utils/usgs_integration.py`, `utils/satellite_data.py` |
| NDVI/NDWI, water masking | `utils/satellite_data.py` |
| Forced (undetectable) ecosystems | `utils/forced_ecosystems.py` |
| Diversity metrics | `utils/natural_capital_metrics.py` |
| EEI integrity lookup | `utils/eei_api.py` |
| ESVD coefficients, regional adjustment, base valuation | `utils/precomputed_esvd_coefficients.py`, `utils/country_gdp_2024.py` |
| Coordinate → country resolution (geocoding) | `utils/nominatim_geocoding.py` |
| Indicator → sub-service multiplier engine | `utils/indicator_multipliers.py`, `utils/teeb_slug_map.py` |
| Indicator taxonomy / seed data | `utils/project_indicators_seed.py`, `utils/indicator_instructions.py` |
| Orchestration, multi-ecosystem path, intactness resolution, EROI | `app.py` |
| Adding a new indicator set | `docs/adding_indicator_sets.md` |
| Full product/architecture narrative | `replit.md` |

---

## 11. References and sources

*Consolidated list of every external source cited in this document. The peer-reviewed citations below have been completed with full bibliographic details (volume, pages, DOI) verified against the publishers; the one exception is flagged inline. Institutional sources, standards, and data services are cited at their authoritative reference.*

### 11.1 Valuation databases and economic data

- **ESVD — Ecosystem Services Valuation Database**, release APR2024 V1.1 (10,874 records from 1,100+ peer-reviewed studies, 1970–2024; values normalised to 2024 International dollars). Foundation for the ecosystem-service coefficients. Foundation for Sustainable Development & partners. https://www.esvd.org/
- **TEEB — The Economics of Ecosystems and Biodiversity.** Kumar, P. (ed.) (2010). *The Economics of Ecosystems and Biodiversity: Ecological and Economic Foundations.* Earthscan, London/Washington. Service taxonomy (22 sub-services across four categories) used to structure and de-duplicate the coefficients. http://teebweb.org/
- **World Bank.** *World Development Indicators — GDP per capita (current / PPP International \$), 2024.* World Bank, Washington DC. Country-level income data for the regional adjustment (income-elasticity method).
- **US EPA (2023).** *Report on the Social Cost of Greenhouse Gases: Estimates Incorporating Recent Scientific Advances.* U.S. Environmental Protection Agency. Interim Social Cost of Carbon; central ≈ Int\$190/tCO₂e, used as the default in the carbon-revenue estimate.

### 11.2 Restoration-monitoring frameworks and standards

- **NatureServe (2019).** *Ecological Resilience Indicators* (including the mangrove indicator set). NatureServe, Arlington, VA. — basis for the mangrove indicator set.
- **Gann, G.D., McDonald, T., Walder, B., Aronson, J., Nelson, C.R., Jonson, J., et al. (2019).** International principles and standards for the practice of ecological restoration. Second edition. *Restoration Ecology* 27(S1): S1–S46. DOI: 10.1111/rec.13035. (Society for Ecological Restoration / SER 2019 Standards — recovery "attributes" mapped to the tropical-forest indicators.)
- **ITTO (2002).** *Guidelines for the Restoration, Management and Rehabilitation of Degraded and Secondary Tropical Forests.* ITTO Policy Development Series No. 13. International Tropical Timber Organization, Yokohama (in collaboration with CIFOR, FAO, IUCN, WWF).
- **Verra.** *VM0007 REDD+ Methodology Framework (REDD-MF).* Verra, Washington DC. https://verra.org/ — carbon-pool and biodiversity co-benefit references.
- **IPCC (2006).** *2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4: Agriculture, Forestry and Other Land Use (AFOLU).* Eggleston, H.S. et al. (eds.). IGES, Japan — biomass, litter, dead organic matter, and soil carbon pools.
- **Bland, L.M., Keith, D.A., Miller, R.M., Murray, N.J. & Rodríguez, J.P. (eds.) (2017).** *Guidelines for the application of IUCN Red List of Ecosystems Categories and Criteria, Version 1.1.* IUCN, Gland, Switzerland. (Referenced in the EVE seed as "IUCN 2020"; condition/biodiversity framing for the fauna indicator.)

### 11.3 Peer-reviewed literature (indicator basis)

- **Asner, G.P., Knapp, D.E., Martin, R.E., Tupayachi, R., Anderson, C.B., Mascaro, J., et al. (2014).** "Targeted carbon conservation at national scales with high-resolution monitoring." *PNAS* 111(47): E5016–E5022. DOI: 10.1073/pnas.1419550111.
- **Bosire, J.O., Dahdouh-Guebas, F., Walton, M., Crona, B.I., Lewis III, R.R., Field, C., Kairo, J.G. & Koedam, N. (2008).** "Functionality of restored mangroves: A review." *Aquatic Botany* 89(2): 251–259. DOI: 10.1016/j.aquabot.2008.03.010.
- **Brancalion, P.H.S., Niamir, A., Broadbent, E., Crouzeilles, R., Barros, F.S.M., Almeyda Zambrano, A.M., et al. (2019).** "Global restoration opportunities in tropical rainforest landscapes." *Science Advances* 5(7): eaav3223. DOI: 10.1126/sciadv.aav3223.
- **Chave, J., Réjou-Méchain, M., Búrquez, A., Chidumayo, E., Colgan, M.S., Delitti, W.B.C., et al. (2014).** "Improved allometric models to estimate the aboveground biomass of tropical trees." *Global Change Biology* 20(10): 3177–3190. DOI: 10.1111/gcb.12629.
- **Chazdon, R.L. (2014).** *Second Growth: The Promise of Tropical Forest Regeneration in an Age of Deforestation.* University of Chicago Press, Chicago.
- **Crouzeilles, R., Ferreira, M.S., Chazdon, R.L., Lindenmayer, D.B., Sansevero, J.B.B., Monteiro, L., et al. (2017).** "Ecological restoration success is higher for natural regeneration than for active restoration in tropical forests." *Science Advances* 3(11): e1701345. DOI: 10.1126/sciadv.1701345.
- **Carugati, L., Gatto, B., Rastelli, E., Lo Martire, M., Coral, C., Greco, S. & Danovaro, R. (2018).** "Impact of mangrove forests degradation on biodiversity and ecosystem functioning." *Scientific Reports* 8: 13298. DOI: 10.1038/s41598-018-31683-0. (Cited in the EVE seed as "Danovaro et al. 2018"; basis for the HD cross-cutting multiplier.)
- **Don, A., Schumacher, J. & Freibauer, A. (2011).** "Impact of tropical land-use change on soil organic carbon stocks — a meta-analysis." *Global Change Biology* 17(4): 1658–1670. DOI: 10.1111/j.1365-2486.2010.02336.x.
- **Dubayah, R., Blair, J.B., Goetz, S., Fatoyinbo, L., Hansen, M., Healey, S., et al. (2020).** "The Global Ecosystem Dynamics Investigation: High-resolution laser ranging of the Earth's forests and topography." *Science of Remote Sensing* 1: 100002. DOI: 10.1016/j.srs.2020.100002.
- **Gardner, T.A., Barlow, J., Chazdon, R., Ewers, R.M., Harvey, C.A., Peres, C.A. & Sodhi, N.S. (2009).** "Prospects for tropical forest biodiversity in a human-modified world." *Ecology Letters* 12(6): 561–582. DOI: 10.1111/j.1461-0248.2009.01294.x.
- **Gatt, Y.M., Andradi-Brown, D.A., Ahmadia, G.N., Martin, P.A., Sutherland, W.J., Spalding, M.D., et al. (2022).** "Quantifying the Reporting, Coverage and Consistency of Key Indicators in Mangrove Restoration Projects." *Frontiers in Forests and Global Change* 5: 720394. DOI: 10.3389/ffgc.2022.720394.
- **Mack, R.N., Simberloff, D., Lonsdale, W.M., Evans, H., Clout, M. & Bazzaz, F.A. (2000).** "Biotic invasions: causes, epidemiology, global consequences, and control." *Ecological Applications* 10(3): 689–710. DOI: 10.1890/1051-0761(2000)010[0689:BICEGC]2.0.CO;2.
- **Nayak, S. & Bahuguna, A. (2001).** "Application of remote sensing data to monitor mangroves and other coastal vegetation of India." *Indian Journal of Marine Sciences* 30(4): 195–213.
- **Poorter, L., Bongers, F., Aide, T.M., Almeyda Zambrano, A.M., Balvanera, P., Becknell, J.M., et al. (2016).** "Biomass resilience of Neotropical secondary forests." *Nature* 530: 211–214. DOI: 10.1038/nature16512.
- **Richardson, D.M. et al. (2011).** Invasive-species impact assessment and context-dependence. *Journal of Applied Ecology.* (Cited as recorded in the EVE indicator seed; the exact paper could not be unambiguously verified online — the closest candidates are Pyšek et al. 2012, *Global Change Biology* 18: 1725–1737, and Kettenring & Adams 2011, *Journal of Applied Ecology* 48: 970–979. Recommend confirming the intended reference against the indicator author's notes.)
- **Rozendaal, D.M.A., Bongers, F., Aide, T.M., Alvarez-Dávila, E., Ascarrunz, N., Balvanera, P., et al. (2019).** "Biodiversity recovery of Neotropical secondary forests." *Science Advances* 5(3): eaau3114. DOI: 10.1126/sciadv.aau3114.

### 11.4 Geospatial and satellite data sources

- **OpenLandMap** (STAC API) — global land cover / ecosystem identification (primary classification source). https://openlandmap.org/
- **ESA WorldCover** — Zanaga, D., Van De Kerchove, R., Daems, D., et al. (2021). *ESA WorldCover 10 m 2020/2021 product.* European Space Agency. https://esa-worldcover.org/ — land-cover codes → ecosystem mapping.
- **USGS / NASA Landsat 8–9 OLI** — Operational Land Imager surface-reflectance products (real imagery retrieval via `landsatxplore`; band statistics underpinning the enhanced spectral simulation). U.S. Geological Survey. https://www.usgs.gov/landsat-missions
- **OpenStreetMap Nominatim** — reverse geocoding for coordinate → country resolution. © OpenStreetMap contributors. https://nominatim.openstreetmap.org/
- **Google Earth Engine** — Gorelick, N., Hancher, M., Dixon, M., Ilyushchenko, S., Thau, D. & Moore, R. (2017). "Google Earth Engine: Planetary-scale geospatial analysis for everyone." *Remote Sensing of Environment* 202: 18–27. DOI: 10.1016/j.rse.2017.06.031. Computation backend for the Ecosystem Ecological Integrity (EEI) index (functional/structural/compositional integrity).
- **EVE Ecosystem Ecological Integrity (EEI) API** — per-point integrity service (`https://eve-solutions-482317.uc.r.appspot.com`).

---

*Prepared from the EVE codebase. Plain-language summaries are for general readers; technical sections and the reference map are for scientific and developer audiences. All monetary figures are 2024 International dollars per hectare per year unless stated otherwise.*

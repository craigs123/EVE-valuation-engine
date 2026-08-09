# Ecosystem Valuation Engine (EVE)

## Overview
The Ecosystem Valuation Engine (EVE) is a Streamlit-based geospatial analysis application for environmental researchers. Its core function is to measure ecosystem growth by economically valuing ecosystem services across provisioning, regulating, cultural, and supporting categories. EVE integrates satellite imagery processing with established economic valuation coefficients to track changes in ecosystem service values over time. The project aims to provide a robust tool for natural capital assessment, trend analysis, and generating insightful reports for environmental management and policy decisions, ultimately contributing to a better understanding of natural capital and its economic significance.

## User Preferences
Preferred communication style: Simple, everyday language.
Application name preference: Call the application "Ecosystem Valuation Engine" or "EVE" instead of "Natural Capital Measurement Tool".
Interface preference: Clean, uncluttered homepage with date controls and analysis button on main page rather than sidebar.
Map interaction preference: Single area selection that automatically saves, with easy clear/replace functionality.
Sampling preference: Simplified user-configurable sample points (10-100 range) with even distribution across any area size. Default of 10 points for fastest development iterations.
Performance preference: Fast sampling for development environment - prioritize speed for iterative testing while maintaining scientific accuracy.
Methodology display: Methodology and data sources content moved to settings sidebar under "Methodology and Sources" section to keep main interface uncluttered.

## System Architecture

### Frontend Architecture
The application features a Streamlit web interface with interactive components. Mapping is handled by Folium for area selection and visualization, integrated via `streamlit-folium`. Plotly is used for interactive charts and dashboards displaying time series data and metrics. The layout is wide with an expandable sidebar for analysis parameters. Streamlit session state manages selected areas and analysis results.

### Backend Architecture
The backend employs a modular design with utilities for data processing, ESVD integration, ecosystem services valuation, natural capital metrics, visualization, and data export. It features a streamlined economic valuation engine using pre-computed static ESVD coefficients derived from over 10,000 peer-reviewed studies, achieving significant performance improvements. The system applies regional adjustment factors and quality adjustments based on satellite indicators. It supports time series processing for temporal analysis of ecosystem service value changes. Features include a simplified sampling strategy with user-configurable sample points (10-100) evenly distributed across any area size, defaulting to 10 for rapid development testing. Multi-ecosystem analysis uses grid-based spatial analysis and area-proportional weighting. Advanced ecosystem detection achieves 90% accuracy across 7 major ecosystem types with regional specialization for US territories. Comprehensive diversity metrics (Shannon and Simpson) are calculated and displayed.

### Satellite Data Integration
EVE uses an enhanced simulation model based on peer-reviewed ecosystem spectral signatures to provide realistic satellite data characteristics, generating scientifically-accurate Red/NIR bands, cloud coverage, and data quality flags. Quality assessment applies satellite-based ecosystem health multipliers derived from authentic spectral patterns. Advanced NDWI-based water body detection automatically identifies and excludes open water areas from natural capital calculations, with detailed reporting of excluded water hectares.

### Ecosystem Ecological Integrity (EEI) Integration
EVE integrates with the EEI API (https://api.ecosystemintegrity.com) to automatically retrieve ecosystem integrity values for each sample point. The EEI provides a scientific measure of ecosystem condition on a 0-1 scale, derived from three components: functional integrity (NPP-based), structural integrity (connectivity), and compositional integrity (biodiversity). The average EEI across all sample points is used to set the default intactness multiplier for each ecosystem type's valuation slider, replacing arbitrary manual defaults with data-driven values. Per-point EEI values are displayed in the sample points summary table.

**Missing vs. zero EEI.** These are different and are treated differently. A pixel scoring **zero** integrity — dense built-up land does — is a real measurement and is applied as such. A pixel with **no value** (open ocean, gaps in dataset coverage) yields no measurement at all; such an ecosystem is absent from `ecosystem_eei` and falls through to the optimistic 100% intactness default. No conservative percentage is substituted, because any figure chosen for open ocean would be as unfounded as 100%; instead the affected ecosystems are named in the EEI panel so the user can set them deliberately via the manual sliders. This is distinct again from **demo** (fabricated) data, which is discarded and carries a conservative 50% fallback (`DEMO_FALLBACK_INTACTNESS_PCT`). Prior to 2026-08, the upstream EEI service reported a genuine 0.0 as null, so the zero and missing cases were indistinguishable and every city centre silently took the 100% default.

**Scope of the EEI multiplier.** EEI measures ecosystem *condition*, and condition does not govern every service equally. SEEA EA keeps the condition account and the ecosystem services account separate, linking them service by service through biophysical models rather than through a single index — see the [UN SEEA Guidelines on Biophysical Modelling](https://seea.un.org/en/ecosystem-accounting/biophysical-modelling). Cultural services are the clearest departure: they are demand-driven, arising from physical settings and the people with access to them, so they persist in nature-depleted places. The [ONS UK urban natural capital accounts](https://www.ons.gov.uk/economy/environmentalaccounts/bulletins/uknaturalcapital/urbanaccounts) value urban amenity at roughly £130bn through hedonic property premiums, and hold park condition (Green Flag awards) as a *separate* indicator rather than multiplying service value by it. Applying EEI at full strength across all four TEEB categories therefore drives urban cultural value toward zero, which neither SEEA EA nor the ONS accounts support.

EVE therefore applies a **scalar** condition multiplier — EEI, or the manual intactness sliders — to the provisioning, regulating and supporting categories only. The cultural category is exempt (`CONDITION_EXEMPT_CATEGORIES` in `utils/precomputed_esvd_coefficients.py`). This applies to scalar mode alone: when a per-ecosystem **indicator set** supplies a per-sub-service dict, those values are measurements of the sub-services themselves and are applied in full, cultural sub-services included — overriding them would discard field data.

### Urban Green/Blue Infrastructure multiplier
Applied to Urban ecosystems only, exposed in Analysis Settings, **defaulting to 18%** (the European average by area) and user-changeable.

This is an **extent** measure and is deliberately independent of EEI. A sample point classified `urban` is predominantly built surface; only its blue-green fraction — parks, street trees, verges, ponds, canals — supplies ecosystem services at all, so the urban coefficients are scaled to that fraction. EEI then describes the **condition** of that fraction, which in most urban settings is close to zero. Extent and condition are orthogonal factors and both belong in the calculation — SEEA EA maintains extent and condition as separate accounts for exactly this reason — so applying both is not double-counting.

The two also pull in different directions for different service categories, which is why the cultural exemption above matters: an urban park may score near-zero ecological condition while delivering very high cultural value to the people using it. A sample point falling inside a genuinely large urban forest would not classify as `urban` in the first place — it returns as forest and is valued on forest coefficients — so that case does not arise here.

### Data Storage Solutions
A PostgreSQL database provides persistent storage for ecosystem analyses, saved areas, and natural capital baselines, with tables including `ecosystem_analyses`, `saved_areas`, `analysis_history`, `natural_capital_baselines`, and `natural_capital_trends`. Session-based data is stored in Streamlit's session state. User session management utilizes UUIDs for data isolation.

### Calculation Methodology
EVE leverages pre-computed coefficients from the Ecosystem Services Valuation Database (ESVD) and TEEB databases, sourced from over 1,100 studies. Values are adjusted for geographic location using the traditional income elasticity multiplier method with authentic 2024 World Bank GDP per capita data for individual countries, aligned with the ESVD International dollar baseline year. Country-specific adjustments apply a formula: 1 + (elasticity × (country_GDP/global_GDP - 1)) with bounds of 0.4-2.5x. Geographic coordinate mapping identifies countries for precise GDP lookup. Quality adjustments are based on satellite indicators (NDVI, spectral health). All values are standardized to 2024 International dollars per hectare per year. The system supports multi-ecosystem valuation with spatial composition-weighted calculations and ecosystem diversity metrics. Performance optimization through pre-computed coefficients achieves significant speed improvement without accuracy loss compared to dynamic database queries.

### Multi-Ecosystem Calculation Architecture
The multi-ecosystem calculation pathway primarily uses two active routes within `app.py`:
1.  **Mixed Ecosystem Path**: For two or more ecosystem types with >10% coverage, calculations loop through the ecosystem distribution, apply proportional area allocation, and call `coeffs.calculate_ecosystem_values()` directly for each ecosystem type. This path ensures consistent percentage rounding to match UI display values and prevent precision discrepancies.
2.  **Single Ecosystem Path**: When diversity is low or a single ecosystem is detected, `coeffs.calculate_ecosystem_values()` is called directly with the full area.
Inactive or bypassed calculation functions in `utils/ecosystem_services.py` are not used by the main calculation flow.

### Ecological Return on Investment (EROI)
For project-indicator runs that produce a target valuation, EVE relates the ecosystem-service value gain to the project's estimated cost. The user enters a single figure — the estimated cost to achieve the target condition — in the pre-Analyze project-indicator panel. The **Total Project Ecosystem Services Gain** is the target valuation minus the baseline valuation: the gain over the life of the project. The project duration is derived from the gap between the baseline and target dates collected in that panel, and the **average annual gain** is the total gain divided by that duration. Three metrics are reported together: **EROI**, a benefit–cost ratio, `total gain ÷ cost`; **annual return rate**, `average annual gain ÷ cost`; and **payback period**, the number of years after the project target date for the average annual gain to repay the cost, `cost ÷ average annual gain`. The three ratios are scale-invariant, so they are identical whether computed from total or per-hectare figures; only the total gain and cost are shown on both bases. The entered cost is persisted inside the existing `saved_areas.project_indicators` JSON blob (no schema change).

### Project-indicator sets (ecosystem-specific)
Per-ecosystem indicator sets (the Mangrove `M1–M7 + HD` set, and more to come) let on-the-ground field measurements **supersede the EEI-derived intactness per sub-service** in the valuation, falling back to EEI where no indicator covers a sub-service. The engine (`utils/indicator_multipliers._compute_pure`) is ecosystem-agnostic; a set is defined as data in `utils/project_indicators_seed.py` (taxonomy, upserted on startup) plus an ESVD coefficient block in `utils/precomputed_esvd_coefficients.py`. Ecosystems that satellite landcover can't classify (e.g. Peatland) are forced onto the whole area on project-type selection. See **`docs/adding_indicator_sets.md`** for the step-by-step recipe.

## External Dependencies

### Core Libraries
-   **Streamlit**: Web application framework.
-   **Folium**: Interactive mapping.
-   **Plotly**: Interactive charting and dashboards.
-   **Pandas/NumPy**: Data manipulation and numerical computations.

### Ecosystem Data Integration
-   **Primary Source**: OpenLandMap STAC API for global land cover and ecosystem identification.
-   **Secondary Sources**: Enhanced satellite simulation for spectral data and quality assessment.

### Geospatial Processing
-   **Coordinate Systems**: Handles geographic coordinate processing and area calculations.
-   **Time Series Analysis**: For environmental metrics.
-   **Bounding Box Calculations**: Automatic extraction of geographic boundaries.

### Export and Reporting
-   **Multiple Formats**: Supports CSV, JSON, and PDF report generation.
-   **Data Visualization**: Integrates plotting libraries for chart generation in exports.
-   **Base64 Encoding**: For handling binary data in export processes.
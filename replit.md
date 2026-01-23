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

### Data Storage Solutions
A PostgreSQL database provides persistent storage for ecosystem analyses, saved areas, and natural capital baselines, with tables including `ecosystem_analyses`, `saved_areas`, `analysis_history`, `natural_capital_baselines`, and `natural_capital_trends`. Session-based data is stored in Streamlit's session state. User session management utilizes UUIDs for data isolation.

### Calculation Methodology
EVE leverages pre-computed coefficients from the Ecosystem Services Valuation Database (ESVD) and TEEB databases, sourced from over 1,100 studies. Values are adjusted for geographic location using the traditional income elasticity multiplier method with authentic 2024 World Bank GDP per capita data for individual countries, aligned with the ESVD International dollar baseline year. Country-specific adjustments apply a formula: 1 + (elasticity × (country_GDP/global_GDP - 1)) with bounds of 0.4-2.5x. Geographic coordinate mapping identifies countries for precise GDP lookup. Quality adjustments are based on satellite indicators (NDVI, spectral health). All values are standardized to 2024 International dollars per hectare per year. The system supports multi-ecosystem valuation with spatial composition-weighted calculations and ecosystem diversity metrics. Performance optimization through pre-computed coefficients achieves significant speed improvement without accuracy loss compared to dynamic database queries.

### Multi-Ecosystem Calculation Architecture
The multi-ecosystem calculation pathway primarily uses two active routes within `app.py`:
1.  **Mixed Ecosystem Path**: For two or more ecosystem types with >10% coverage, calculations loop through the ecosystem distribution, apply proportional area allocation, and call `coeffs.calculate_ecosystem_values()` directly for each ecosystem type. This path ensures consistent percentage rounding to match UI display values and prevent precision discrepancies.
2.  **Single Ecosystem Path**: When diversity is low or a single ecosystem is detected, `coeffs.calculate_ecosystem_values()` is called directly with the full area.
Inactive or bypassed calculation functions in `utils/ecosystem_services.py` are not used by the main calculation flow.

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
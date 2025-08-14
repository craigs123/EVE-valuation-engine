# Ecosystem Valuation Engine (EVE)

## Overview

This is a Streamlit-based geospatial analysis application called the Ecosystem Valuation Engine (EVE), designed for environmental researchers to measure ecosystem growth through economic valuation of ecosystem services. EVE focuses on four main categories of ecosystem services: provisioning (food, water, timber), regulating (climate, water regulation, erosion control), cultural (recreation, spiritual value), and supporting (soil formation, nutrient cycling). The application combines satellite imagery processing with established economic valuation coefficients to track ecosystem service value changes over time.

## User Preferences

Preferred communication style: Simple, everyday language.
Application name preference: Call the application "Ecosystem Valuation Engine" or "EVE" instead of "Natural Capital Measurement Tool".

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with interactive components
- **Mapping Component**: Folium maps integrated via streamlit-folium for area selection and visualization
- **Visualization**: Plotly for interactive charts and dashboards showing time series data and metrics
- **Layout**: Wide layout with expandable sidebar for analysis parameters and controls
- **State Management**: Streamlit session state for maintaining selected areas and analysis results

### Backend Architecture
- **Modular Design**: Utilities organized into separate modules for specific functionalities
- **Data Processing Pipeline**: 
  - Satellite data acquisition and processing (`satellite_data.py`)
  - Ecosystem services valuation engine (`ecosystem_services.py`)
  - Natural capital metrics calculation (`natural_capital_metrics.py`) 
  - Visualization generation (`visualization.py`)
  - Data export capabilities (`data_export.py`)
- **Economic Valuation Engine**: Calculates monetary values for ecosystem services using established coefficients
- **Service Categories Analysis**: Tracks provisioning, regulating, cultural, and supporting services separately
- **Time Series Processing**: Handles temporal analysis of ecosystem service value changes over time

### Data Storage Solutions
- **Sample Data**: JSON files containing predefined sample areas with expected metrics
- **Session Storage**: In-memory storage using Streamlit session state for user selections and analysis results
- **Export Formats**: CSV and JSON export capabilities for analysis results

### Calculation Methodology
- **Ecosystem Services Valuation**: Uses established economic coefficients for different service categories and ecosystem types
- **Service Categories**: Provisioning (food, water, timber), Regulating (climate, water, erosion control), Cultural (recreation, spiritual), Supporting (soil, nutrients, habitat)
- **Quality Adjustment**: Values are adjusted based on ecosystem quality derived from satellite indicators (NDVI, spectral health, data quality)
- **Temporal Analysis**: Tracks value changes over time to measure ecosystem growth or degradation in economic terms

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **Folium**: Interactive mapping library for geographic visualization
- **Plotly**: Interactive charting and dashboard creation
- **Pandas/NumPy**: Data manipulation and numerical computations

### Satellite Data Integration
- **API Integration**: Configured to connect to satellite data providers (currently using demo endpoints)
- **Environment Variables**: `SATELLITE_API_KEY` for authentication with satellite data services
- **Data Sources**: Designed to work with commercial satellite imagery APIs for real-time environmental monitoring

### Geospatial Processing
- **Coordinate Systems**: Handles geographic coordinate processing and area calculations
- **Time Series Analysis**: Temporal analysis of environmental metrics over user-defined periods
- **Bounding Box Calculations**: Automatic extraction of geographic boundaries from selected areas

### Export and Reporting
- **Multiple Formats**: Support for CSV, JSON, and PDF report generation
- **Data Visualization**: Integration with plotting libraries for chart generation in exports
- **Base64 Encoding**: For handling binary data in export processes
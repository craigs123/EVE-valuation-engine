# Ecosystem Valuation Engine (EVE)

## Overview

This is a Streamlit-based geospatial analysis application called the Ecosystem Valuation Engine (EVE), designed for environmental researchers to track ecosystem growth and natural capital using satellite data. EVE provides an interactive mapping interface where users can select geographic areas and analyze various environmental metrics including NDVI (Normalized Difference Vegetation Index), forest cover, carbon storage, and biodiversity indices. The application combines satellite imagery processing with natural capital calculations to provide comprehensive ecosystem health assessments over time.

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
  - Natural capital metrics calculation (`natural_capital_metrics.py`) 
  - Visualization generation (`visualization.py`)
  - Data export capabilities (`data_export.py`)
- **Analysis Engine**: Calculates ecosystem health indicators using satellite imagery and environmental data
- **Time Series Processing**: Handles temporal analysis of environmental changes over user-selected date ranges

### Data Storage Solutions
- **Sample Data**: JSON files containing predefined sample areas with expected metrics
- **Session Storage**: In-memory storage using Streamlit session state for user selections and analysis results
- **Export Formats**: CSV and JSON export capabilities for analysis results

### Calculation Methodology
- **Carbon Storage**: Uses ecosystem-specific conversion factors (forest: 150 tons CO2/hectare, wetland: 200, grassland: 50)
- **Biodiversity Assessment**: Weighted scoring system considering vegetation diversity, habitat connectivity, edge density, and fragmentation
- **NDVI Analysis**: Vegetation health assessment using normalized difference vegetation index
- **Forest Cover**: Land use classification and coverage percentage calculations

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
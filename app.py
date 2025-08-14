"""
Ecosystem Valuation Engine - Clean Map Implementation
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Ecosystem Valuation Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2e8b57;
    text-align: center;
    margin-bottom: 0.5rem;
}
.subtitle {
    font-size: 1.2rem;
    color: #666;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-container {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #2e8b57;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Title and header
st.markdown('<h1 class="main-header">🌱 Ecosystem Valuation Engine</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Track ecosystem services and natural capital value changes over time</p>', unsafe_allow_html=True)

# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Sidebar configuration
with st.sidebar:
    st.header("Analysis Settings")
    
    # Ecosystem type override
    ecosystem_override = st.selectbox(
        "Ecosystem Type",
        options=["Auto-detect from satellite data", "Forest", "Grassland", "Wetland", "Agricultural", "Coastal", "Urban", "Desert"],
        help="Override automatic ecosystem detection if needed"
    )
    
    # Analysis detail level
    analysis_detail = st.selectbox(
        "Analysis Detail",
        options=["Quick Overview", "Detailed Analysis"],
        help="Quick overview shows main values. Detailed includes service categories and trends."
    )
    
    # Store settings
    st.session_state.ecosystem_override = ecosystem_override
    st.session_state.analysis_detail = analysis_detail
    
    # Service categories (only for detailed analysis)
    if analysis_detail == "Detailed Analysis":
        selected_metrics = ['ecosystem_services_total', 'provisioning', 'regulating', 'cultural', 'supporting']
    else:
        selected_metrics = ['ecosystem_services_total']
    
    st.markdown("---")
    
    # Clear button
    if st.button("🗑️ Clear Area & Results", help="Start over with a new area"):
        st.session_state.analysis_results = None
        st.session_state.selected_area = None
        st.session_state.area_coordinates = []
        st.rerun()

# Initialize analyze_button as False
analyze_button = False

# Map and preview in columns
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🗺️ Select Your Area")
    st.info("Use the drawing tools (rectangle/polygon icons) in the map toolbar to select an area")
    
    # Create interactive map
    m = folium.Map(location=[40.0, -100.0], zoom_start=4)
    
    # Add existing selection if available
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = st.session_state.area_coordinates
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',
            weight=3,
            fillColor='green',
            fillOpacity=0.2,
            popup="Selected Area"
        ).add_to(m)

    # Add drawing tools
    from folium.plugins import Draw
    draw = Draw(
        draw_options={
            'polyline': False,
            'polygon': True,
            'circle': False,
            'rectangle': True,
            'marker': False,
            'circlemarker': False,
        },
        edit_options={
            'remove': True,
            'edit': False
        }
    )
    draw.add_to(m)
    
    # Display map with drawing capability
    map_data = st_folium(
        m, 
        width=700, 
        height=400,
        returned_objects=["all_drawings"],
        key="area_map"
    )
    
    # Process map interactions
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        latest_drawing = map_data['all_drawings'][-1]
        
        if latest_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
            coordinates = latest_drawing['geometry']['coordinates'][0]
            
            # Check if this is a new selection
            current_coords = st.session_state.get('area_coordinates', [])
            is_new_selection = (not current_coords or coordinates != current_coords)
            
            if is_new_selection:
                # Save the new selection
                st.session_state.selected_area = {
                    'type': latest_drawing['geometry']['type'],
                    'coordinates': coordinates
                }
                st.session_state.area_coordinates = coordinates
                st.session_state.analysis_results = None
                
                # Calculate and show area
                area_coords = np.array(coordinates)
                if len(area_coords) > 2:
                    area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                    area_ha = area_km2 * 100
                    st.success(f"Area selected: {area_ha:.1f} hectares")
                st.rerun()
        else:
            st.warning("Please draw a polygon or rectangle area")
    
    # Display coordinates of selected area
    if st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
        st.markdown("### 📍 Selected Area Coordinates")
        coords = st.session_state.area_coordinates
        
        # Calculate bounding box
        lats = [coord[1] for coord in coords[:-1]]  # Exclude last duplicate point
        lons = [coord[0] for coord in coords[:-1]]
        
        col_bounds1, col_bounds2 = st.columns(2)
        with col_bounds1:
            st.metric("Min Latitude", f"{min(lats):.6f}")
            st.metric("Min Longitude", f"{min(lons):.6f}")
        with col_bounds2:
            st.metric("Max Latitude", f"{max(lats):.6f}")
            st.metric("Max Longitude", f"{max(lons):.6f}")
        
        # Show all coordinates in expandable section
        with st.expander("All Coordinates"):
            for i, coord in enumerate(coords[:-1]):  # Exclude last duplicate
                st.write(f"Point {i+1}: {coord[1]:.6f}°N, {coord[0]:.6f}°E")
    else:
        st.warning("No area selected yet. Use the drawing tools (rectangle/polygon) in the map toolbar.")
    
    # Analysis controls under the map
    st.markdown("### 📊 Analysis Controls")
    
    col_period, col_button = st.columns([2, 1])
    
    with col_period:
        time_preset = st.selectbox(
            "Analysis Period",
            options=["Past Year", "Past 6 Months", "Past 3 Months", "Custom Range"],
            index=0,
            key="map_time_preset"
        )
        
        if time_preset == "Custom Range":
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("From", value=datetime.now() - timedelta(days=365), key="map_start_date")
            with col_end:
                end_date = st.date_input("To", value=datetime.now(), key="map_end_date")
        else:
            preset_options = {
                "Past Year": (datetime.now() - timedelta(days=365), datetime.now()),
                "Past 6 Months": (datetime.now() - timedelta(days=180), datetime.now()),
                "Past 3 Months": (datetime.now() - timedelta(days=90), datetime.now())
            }
            start_date, end_date = preset_options[time_preset]
    
    with col_button:
        st.write("") # spacing
        if st.session_state.selected_area:
            analyze_button = st.button(
                "🚀 Calculate Value", 
                type="primary",
                use_container_width=True,
                help="Calculate ecosystem services value for selected area"
            )
        else:
            analyze_button = st.button(
                "Select area first", 
                disabled=True,
                use_container_width=True
            )

# Right column - Preview and results
with col2:
    st.subheader("📊 Analysis Preview")
    
    if st.session_state.get('selected_area'):
        st.success("✅ Area Selected")
        coords = st.session_state.area_coordinates
        
        # Calculate area in hectares
        area_coords = np.array(coords)
        if len(area_coords) > 2:
            area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
            area_ha = area_km2 * 100
            st.metric("Area Size", f"{area_ha:.1f} hectares")
        
        # Show analysis settings
        st.info(f"**Ecosystem:** {st.session_state.ecosystem_override}")
        st.info(f"**Analysis:** {st.session_state.analysis_detail}")
        
        if st.session_state.analysis_results:
            st.success("📈 Analysis Complete")
            st.write("Results are ready for viewing")
        else:
            st.info("Ready for analysis - click 'Calculate Value' button")
    else:
        st.warning("⚠️ No area selected")
        st.write("Select an area on the map to begin analysis")

# Full ecosystem analysis implementation
if analyze_button and st.session_state.selected_area and selected_metrics:
    # Show progress indicator
    from utils.user_guidance import show_progress_indicator
    
    progress_container = st.empty()
    status_container = st.empty()
    
    with progress_container.container():
        show_progress_indicator(1, 3)
        
        try:
            with status_container:
                with st.spinner("🔍 Processing satellite data and detecting ecosystems..."):
                    # Initialize processors
                    from utils.satellite_data import SatelliteDataProcessor
                    from utils.ecosystem_services import EcosystemServicesCalculator
                    from utils.natural_capital_metrics import NaturalCapitalMetrics
                    from utils.esvd_integration import ESVDIntegration
                    
                    satellite_processor = SatelliteDataProcessor()
                    ecosystem_calculator = EcosystemServicesCalculator()
                    capital_metrics = NaturalCapitalMetrics()
                    esvd_integration = ESVDIntegration()
                    
                    # Get area coordinates and calculate bounding box
                    coords = st.session_state.area_coordinates
                    area_coords = np.array(coords)
                    area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                    area_ha = area_km2 * 100
                    
                    # Extract bounding box
                    lats = [coord[1] for coord in coords[:-1]]
                    lons = [coord[0] for coord in coords[:-1]]
                    bbox = [min(lons), min(lats), max(lons), max(lats)]
            
            with progress_container.container():
                show_progress_indicator(2, 3)
                
                with status_container:
                    with st.spinner("🌍 Calculating ecosystem services values using ESVD database..."):
                        # Process satellite data for ecosystem detection
                        satellite_data = satellite_processor.get_time_series_data(bbox, start_date, end_date)
                        
                        # Detect ecosystem types or use override
                        if st.session_state.ecosystem_override == "Auto-detect from satellite data":
                            ecosystem_results = satellite_processor.detect_ecosystem_composition(satellite_data, bbox)
                        else:
                            # Use manual override
                            ecosystem_results = {
                                'dominant_ecosystem': st.session_state.ecosystem_override.lower(),
                                'ecosystem_composition': {st.session_state.ecosystem_override.lower(): 1.0},
                                'confidence': 1.0,
                                'quality_metrics': {'overall_quality': 0.85}
                            }
                        
                        # Calculate ecosystem services values using ESVD
                        ecosystem_values = ecosystem_calculator.calculate_comprehensive_values(
                            ecosystem_results, area_ha, selected_metrics
                        )
                        
                        # Get ESVD coefficients for transparency
                        esvd_coefficients = esvd_integration.get_coefficients_for_ecosystem(
                            ecosystem_results['dominant_ecosystem']
                        )
            
            with progress_container.container():
                show_progress_indicator(3, 3)
                
                with status_container:
                    with st.spinner("📊 Generating comprehensive analysis and trends..."):
                        # Calculate natural capital metrics
                        capital_analysis = capital_metrics.calculate_comprehensive_metrics(
                            ecosystem_values, satellite_data, area_ha
                        )
                        
                        # Compile comprehensive results
                        analysis_results = {
                            'ecosystem_analysis': ecosystem_results,
                            'ecosystem_values': ecosystem_values,
                            'natural_capital': capital_analysis,
                            'esvd_coefficients': esvd_coefficients,
                            'area_metrics': {
                                'area_ha': area_ha,
                                'area_km2': area_km2,
                                'bbox': bbox
                            },
                            'analysis_settings': {
                                'start_date': start_date.strftime('%Y-%m-%d'),
                                'end_date': end_date.strftime('%Y-%m-%d'),
                                'ecosystem_override': st.session_state.ecosystem_override,
                                'detail_level': st.session_state.analysis_detail,
                                'selected_metrics': selected_metrics
                            }
                        }
                        
                        # Store results in session state
                        st.session_state.analysis_results = analysis_results
            
            # Clear progress indicators
            progress_container.empty()
            status_container.empty()
            
            # Show success message
            st.success("✅ Analysis complete! Scroll down to view comprehensive results.")
            st.rerun()
            
        except Exception as e:
            progress_container.empty()
            status_container.empty()
            st.error(f"Analysis failed: {str(e)}")
            st.warning("Please try again or contact support if the issue persists.")

# Display comprehensive results if available
if st.session_state.analysis_results:
    st.markdown("---")
    st.header("📈 Ecosystem Valuation Results")
    
    results = st.session_state.analysis_results
    ecosystem_values = results['ecosystem_values']
    area_metrics = results['area_metrics']
    ecosystem_analysis = results['ecosystem_analysis']
    
    # Main metrics overview
    st.subheader("💰 Economic Valuation Summary")
    
    col_main1, col_main2, col_main3, col_main4 = st.columns(4)
    
    with col_main1:
        total_annual_value = ecosystem_values.get('ecosystem_services_total', 0)
        st.metric(
            "Total Annual Value", 
            f"${total_annual_value:,.0f}",
            help="Total economic value of all ecosystem services per year"
        )
    
    with col_main2:
        value_per_ha = total_annual_value / area_metrics['area_ha'] if area_metrics['area_ha'] > 0 else 0
        st.metric(
            "Value per Hectare", 
            f"${value_per_ha:,.0f}/ha",
            help="Economic value per hectare per year"
        )
    
    with col_main3:
        st.metric(
            "Area Analyzed", 
            f"{area_metrics['area_ha']:.1f} ha",
            help=f"Total area: {area_metrics['area_km2']:.2f} km²"
        )
    
    with col_main4:
        dominant_ecosystem = ecosystem_analysis.get('dominant_ecosystem', 'Unknown').title()
        confidence = ecosystem_analysis.get('confidence', 0) * 100
        st.metric(
            "Ecosystem Type", 
            dominant_ecosystem,
            help=f"Detection confidence: {confidence:.1f}%"
        )
    
    # Detailed service categories (if detailed analysis selected)
    if st.session_state.analysis_detail == "Detailed Analysis":
        st.subheader("🌿 Ecosystem Services Breakdown")
        
        service_cols = st.columns(4)
        
        services = [
            ('provisioning', 'Provisioning', '🌾', 'Food, water, timber, fiber'),
            ('regulating', 'Regulating', '🌡️', 'Climate, water, erosion control'),
            ('cultural', 'Cultural', '🏞️', 'Recreation, spiritual, aesthetic'),
            ('supporting', 'Supporting', '🔄', 'Soil formation, nutrient cycling')
        ]
        
        for i, (key, name, icon, description) in enumerate(services):
            with service_cols[i]:
                value = ecosystem_values.get(key, 0)
                percentage = (value / total_annual_value * 100) if total_annual_value > 0 else 0
                
                st.markdown(f"""
                <div class="metric-container">
                    <h4>{icon} {name}</h4>
                    <h3>${value:,.0f}/year</h3>
                    <p>{percentage:.1f}% of total</p>
                    <small>{description}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Ecosystem composition
    if 'ecosystem_composition' in ecosystem_analysis:
        st.subheader("🗺️ Ecosystem Composition")
        
        composition = ecosystem_analysis['ecosystem_composition']
        if len(composition) > 1:
            # Multiple ecosystems detected
            comp_cols = st.columns(min(len(composition), 4))
            for i, (eco_type, percentage) in enumerate(composition.items()):
                if i < 4:  # Limit to 4 columns
                    with comp_cols[i]:
                        st.metric(
                            eco_type.title(),
                            f"{percentage*100:.1f}%",
                            help=f"Percentage of area classified as {eco_type}"
                        )
        else:
            # Single ecosystem
            eco_type, percentage = list(composition.items())[0]
            st.info(f"Area is {percentage*100:.1f}% classified as {eco_type.title()}")
    
    # Data sources and methodology
    with st.expander("📚 Data Sources & Methodology"):
        st.markdown("""
        **Data Sources:**
        - **ESVD (Ecosystem Services Valuation Database)**: 10,000+ peer-reviewed economic valuations
        - **Satellite Data**: Multi-spectral analysis for ecosystem detection
        - **TEEB Database**: The Economics of Ecosystems and Biodiversity coefficients
        
        **Methodology:**
        - Economic values sourced from authentic ESVD/TEEB databases
        - Values adjusted for regional economic conditions
        - Ecosystem detection using NDVI, NDWI, and NDBI indices
        - All values standardized to 2020 International dollars
        """)
        
        # Show ESVD coefficients used
        if 'esvd_coefficients' in results:
            st.markdown("**ESVD Coefficients Used:**")
            coefficients = results['esvd_coefficients']
            for service, coeff in coefficients.items():
                st.write(f"- {service.title()}: ${coeff:,.2f}/ha/year")
    
    # Export options
    st.subheader("📊 Export & Share")
    
    export_cols = st.columns(3)
    
    with export_cols[0]:
        if st.button("📄 Export to CSV", use_container_width=True):
            from utils.data_export import export_to_csv
            csv_data = export_to_csv(results)
            st.download_button(
                "Download CSV",
                csv_data,
                "ecosystem_analysis.csv",
                "text/csv"
            )
    
    with export_cols[1]:
        if st.button("📊 Generate Report", use_container_width=True):
            from utils.data_export import generate_pdf_report
            pdf_data = generate_pdf_report(results)
            st.download_button(
                "Download PDF Report",
                pdf_data,
                "ecosystem_valuation_report.pdf",
                "application/pdf"
            )
    
    with export_cols[2]:
        if st.button("🔗 Share Results", use_container_width=True):
            st.info("Share functionality will be available in the next update")
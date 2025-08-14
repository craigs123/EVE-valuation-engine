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
    st.info("Click the rectangle or polygon button in the toolbar, then click and drag on the map to draw your area")
    
    # Create interactive map with drawing capability
    m = folium.Map(
        location=[40.0, -100.0], 
        zoom_start=4
    )
    
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

    # Add drawing tools that should work
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
        edit_options={'remove': True}
    )
    draw.add_to(m)
    
    # Add JavaScript to disable panning but allow drawing
    disable_pan_js = """
    <script>
    setTimeout(function() {
        var map = window[Object.keys(window).find(key => key.startsWith('map_'))];
        if (map) {
            // Disable panning when not drawing
            var originalOnMouseDown = map.dragging._onMouseDown;
            map.dragging._onMouseDown = function(e) {
                // Only allow dragging if we're in draw mode
                var drawingActive = document.querySelector('.leaflet-draw-toolbar-button-enabled');
                if (!drawingActive) {
                    return; // Block panning
                }
                return originalOnMouseDown.call(this, e);
            };
        }
    }, 2000);
    </script>
    """
    m.get_root().html.add_child(folium.Element(disable_pan_js))
    
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

# Simple analysis placeholder (since we're focusing on map functionality)
if analyze_button and st.session_state.selected_area:
    with st.spinner("Calculating ecosystem values..."):
        # Simulate analysis
        import time
        time.sleep(2)
        
        # Calculate area for results
        coords = st.session_state.area_coordinates
        area_coords = np.array(coords)
        if len(area_coords) > 2:
            area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
            area_ha = area_km2 * 100
        else:
            area_ha = 100
        
        # Store simple results
        st.session_state.analysis_results = {
            'total_value': 12500,
            'area_ha': area_ha,
            'ecosystem_type': 'Forest' if st.session_state.ecosystem_override == "Auto-detect from satellite data" else st.session_state.ecosystem_override
        }
        st.success("Analysis complete!")
        st.rerun()

# Display results if available
if st.session_state.analysis_results:
    st.markdown("---")
    st.subheader("📈 Analysis Results")
    
    results = st.session_state.analysis_results
    
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.metric("Total Ecosystem Value", f"${results['total_value']:,}/year")
    with col_metrics[1]:
        st.metric("Value per Hectare", f"${results['total_value']/results['area_ha']:.0f}/ha/year")
    with col_metrics[2]:
        st.metric("Ecosystem Type", results['ecosystem_type'])
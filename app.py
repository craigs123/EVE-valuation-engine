"""
Ecosystem Valuation Engine - Working Map Implementation
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta

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

# Map and preview in columns
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🗺️ Select Your Area")
    st.info("Use the drawing tools in the map toolbar: click polygon or rectangle tool, then draw on the map")
    
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

    # Add drawing tools with proper configuration
    from folium.plugins import Draw
    draw = Draw(
        draw_options={
            'polyline': False,
            'polygon': {
                'allowIntersection': False,
                'showArea': True,
                'metric': True,
                'shapeOptions': {
                    'color': '#ff0000',
                    'weight': 2,
                    'fillOpacity': 0.2
                }
            },
            'rectangle': {
                'showArea': True,
                'metric': True,
                'shapeOptions': {
                    'color': '#ff0000',
                    'weight': 2,
                    'fillOpacity': 0.2
                }
            },
            'circle': False,
            'marker': False,
            'circlemarker': False,
        },
        edit_options={
            'remove': True,
            'edit': True
        },
        position='topleft'
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
    
    # Process drawing interactions from the toolbar
    if map_data and map_data.get('all_drawings') and len(map_data['all_drawings']) > 0:
        try:
            latest_drawing = map_data['all_drawings'][-1]
            
            if latest_drawing.get('geometry') and latest_drawing['geometry'].get('type') in ['Polygon']:
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
                # Show helpful message for drawing
                if latest_drawing.get('geometry'):
                    st.info("Use the polygon or rectangle tools in the map toolbar above")
        except Exception as e:
            st.error(f"Map interaction error: {str(e)}")
            st.info("Please try drawing the area again using the toolbar tools")
    
    # Display coordinates of selected area
    if st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
        st.markdown("### 📍 Selected Area Coordinates")
        coords = st.session_state.area_coordinates
        
        # Calculate bounding box
        lats = [coord[1] for coord in coords[:-1]]  # Exclude last duplicate point
        lons = [coord[0] for coord in coords[:-1]]
        
        st.markdown(f"<small>**Latitude:** {min(lats):.6f} to {max(lats):.6f}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>**Longitude:** {min(lons):.6f} to {max(lons):.6f}</small>", unsafe_allow_html=True)
        
        # Show all coordinates in expandable section
        with st.expander("All Coordinates"):
            for i, coord in enumerate(coords[:-1]):  # Exclude last duplicate
                st.markdown(f"<small>Point {i+1}: {coord[1]:.6f}°N, {coord[0]:.6f}°E</small>", unsafe_allow_html=True)
    else:
        st.warning("No area selected yet. Click on the map to start drawing a polygon.")

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
        
        # Analysis button
        if st.button("🚀 Calculate Value", type="primary", use_container_width=True):
            with st.spinner("Analyzing ecosystem..."):
                import time
                time.sleep(2)
                
                # Simple demonstration results
                st.session_state.analysis_results = {
                    'total_value': 25000,
                    'area_ha': area_ha if 'area_ha' in locals() else 100,
                    'ecosystem_type': 'Forest' if st.session_state.ecosystem_override == "Auto-detect from satellite data" else st.session_state.ecosystem_override.lower()
                }
                st.success("Analysis complete!")
                st.rerun()
        
        if st.session_state.analysis_results:
            st.success("📈 Analysis Complete")
            results = st.session_state.analysis_results
            st.metric("Annual Value", f"${results['total_value']:,}")
            st.metric("Value/Hectare", f"${results['total_value']//results['area_ha']:,}/ha")
        else:
            st.info("Ready for analysis - click 'Calculate Value' button")
    else:
        st.warning("⚠️ No area selected")
        st.write("Click on the map to start drawing a polygon for analysis")
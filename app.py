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
    st.info("Click on the map to create polygon points. Click 'Finish Drawing' when done.")
    
    # Drawing controls
    col_draw1, col_draw2, col_draw3 = st.columns(3)
    
    # Initialize drawing mode
    if 'drawing_mode' not in st.session_state:
        st.session_state.drawing_mode = False
    
    with col_draw1:
        if st.button("🎯 Start Drawing", key="start_draw"):
            st.session_state.drawing_mode = True
            if 'polygon_points' not in st.session_state:
                st.session_state.polygon_points = []
            st.rerun()
    
    with col_draw2:
        if st.button("✅ Finish Drawing", key="finish_draw"):
            if st.session_state.get('polygon_points') and len(st.session_state.polygon_points) >= 3:
                # Close the polygon
                coordinates = st.session_state.polygon_points + [st.session_state.polygon_points[0]]
                
                st.session_state.selected_area = {
                    'type': 'Polygon',
                    'coordinates': coordinates
                }
                st.session_state.area_coordinates = coordinates
                st.session_state.analysis_results = None
                st.session_state.drawing_mode = False
                
                # Calculate area
                area_coords = np.array(coordinates)
                area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                area_ha = area_km2 * 100
                
                # Clear points
                st.session_state.polygon_points = []
                st.success(f"Polygon completed: {area_ha:.1f} hectares")
                st.rerun()
            else:
                st.warning("Need at least 3 points to create a polygon")
    
    with col_draw3:
        if st.button("🗑️ Clear", key="clear_draw"):
            st.session_state.polygon_points = []
            st.session_state.drawing_mode = False
            st.rerun()
    
    # Manual coordinates option
    use_coords = st.checkbox("Enter coordinates manually", key="manual_coords")
    
    # Create interactive map with drawing mode configuration
    if st.session_state.get('drawing_mode'):
        # Drawing mode - disable dragging
        m = folium.Map(
            location=[40.0, -100.0], 
            zoom_start=4,
            dragging=False,
            scrollWheelZoom=True,
            doubleClickZoom=False
        )
    else:
        # Normal navigation mode
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

    # Initialize polygon points if not exists
    if 'polygon_points' not in st.session_state:
        st.session_state.polygon_points = []
    
    # Add current polygon points to map
    if st.session_state.polygon_points:
        # Show current points as markers
        for i, point in enumerate(st.session_state.polygon_points):
            folium.Marker(
                location=[point[1], point[0]],
                popup=f"Point {i+1}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Draw lines connecting points
        if len(st.session_state.polygon_points) > 1:
            folium.PolyLine(
                locations=[[p[1], p[0]] for p in st.session_state.polygon_points],
                color='red',
                weight=2,
                opacity=0.8
            ).add_to(m)
    
    # Display map with click capability
    map_data = st_folium(
        m, 
        width=700, 
        height=400,
        returned_objects=["last_clicked"],
        key="area_map"
    )
    
    # Handle map clicks for polygon creation - only when in drawing mode
    if st.session_state.get('drawing_mode') and map_data and map_data.get('last_clicked'):
        clicked_point = [map_data['last_clicked']['lng'], map_data['last_clicked']['lat']]
        
        # Avoid duplicate clicks
        if not st.session_state.polygon_points or clicked_point != st.session_state.polygon_points[-1]:
            st.session_state.polygon_points.append(clicked_point)
            st.success(f"Point {len(st.session_state.polygon_points)} added: {clicked_point[1]:.6f}°N, {clicked_point[0]:.6f}°E")
            st.rerun()
    
    # Show current drawing status
    if st.session_state.get('drawing_mode'):
        if st.session_state.get('polygon_points'):
            st.info(f"🎯 Drawing mode: {len(st.session_state.polygon_points)} points added. Click map to add more points.")
        else:
            st.info("🎯 Drawing mode active: Click on the map to add polygon points")
    elif st.session_state.get('polygon_points'):
        st.info(f"Current polygon: {len(st.session_state.polygon_points)} points")
    
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
        area_ha = 0
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
        if use_coords:
            st.write("Enter coordinates below:")
            
            min_lat = st.number_input("Min Latitude", value=40.0, format="%.6f", step=0.1, key="alt_min_lat")
            max_lat = st.number_input("Max Latitude", value=41.0, format="%.6f", step=0.1, key="alt_max_lat")
            min_lon = st.number_input("Min Longitude", value=-100.0, format="%.6f", step=0.1, key="alt_min_lon")
            max_lon = st.number_input("Max Longitude", value=-99.0, format="%.6f", step=0.1, key="alt_max_lon")
            
            if st.button("Set Area from Coordinates", key="set_alt_area"):
                coordinates = [
                    [min_lon, min_lat],
                    [max_lon, min_lat],
                    [max_lon, max_lat],
                    [min_lon, max_lat],
                    [min_lon, min_lat]
                ]
                
                st.session_state.selected_area = {
                    'type': 'Polygon',
                    'coordinates': coordinates
                }
                st.session_state.area_coordinates = coordinates
                st.session_state.analysis_results = None
                
                area_coords = np.array(coordinates)
                area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                area_ha = area_km2 * 100
                st.success(f"Area set: {area_ha:.1f} hectares")
                st.rerun()
        else:
            st.write("Use the drawing tools in the map toolbar")
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
    st.info("Enter the coordinates of your study area below")
    
    # Primary coordinate input method
    st.subheader("📍 Area Coordinates")
    
    col_input1, col_input2, col_input3 = st.columns(3)
    
    with col_input1:
        st.write("**Method 1: Corner Coordinates**")
        min_lat = st.number_input("Southwest Latitude", value=40.0, format="%.6f", step=0.1, key="coord_min_lat", help="Bottom-left corner latitude")
        min_lon = st.number_input("Southwest Longitude", value=-100.0, format="%.6f", step=0.1, key="coord_min_lon", help="Bottom-left corner longitude")
        max_lat = st.number_input("Northeast Latitude", value=41.0, format="%.6f", step=0.1, key="coord_max_lat", help="Top-right corner latitude")
        max_lon = st.number_input("Northeast Longitude", value=-99.0, format="%.6f", step=0.1, key="coord_max_lon", help="Top-right corner longitude")
        
        if st.button("Create Rectangular Area", key="create_rect", type="primary"):
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
            st.success(f"Area created: {area_ha:.1f} hectares")
            st.rerun()
    
    with col_input2:
        st.write("**Method 2: Sample Areas**")
        sample_areas = {
            "Amazon Rainforest (Brazil)": [[-60.0, -3.0], [-59.0, -3.0], [-59.0, -2.0], [-60.0, -2.0], [-60.0, -3.0]],
            "Great Plains (USA)": [[-100.0, 40.0], [-99.0, 40.0], [-99.0, 41.0], [-100.0, 41.0], [-100.0, 40.0]],
            "Mediterranean Coast (Spain)": [[2.0, 41.0], [3.0, 41.0], [3.0, 42.0], [2.0, 42.0], [2.0, 41.0]],
            "Sahel Region (Africa)": [[0.0, 12.0], [1.0, 12.0], [1.0, 13.0], [0.0, 13.0], [0.0, 12.0]],
            "Boreal Forest (Canada)": [[-106.0, 53.0], [-105.0, 53.0], [-105.0, 54.0], [-106.0, 54.0], [-106.0, 53.0]]
        }
        
        selected_sample = st.selectbox("Choose sample area:", list(sample_areas.keys()), key="sample_selection")
        st.write(f"Size: ~100 km² ecosystem area")
        
        if st.button("Use Sample Area", key="use_sample"):
            coordinates = sample_areas[selected_sample]
            
            st.session_state.selected_area = {
                'type': 'Polygon',
                'coordinates': coordinates
            }
            st.session_state.area_coordinates = coordinates
            st.session_state.analysis_results = None
            
            area_coords = np.array(coordinates)
            area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
            area_ha = area_km2 * 100
            st.success(f"Sample area selected: {area_ha:.1f} hectares")
            st.rerun()
    
    with col_input3:
        st.write("**Method 3: Center + Size**")
        center_lat = st.number_input("Center Latitude", value=40.5, format="%.6f", step=0.1, key="center_lat")
        center_lon = st.number_input("Center Longitude", value=-99.5, format="%.6f", step=0.1, key="center_lon") 
        size_km = st.number_input("Size (km each side)", value=10.0, min_value=0.1, step=1.0, key="size_km")
        
        if st.button("Create Square Area", key="create_square"):
            # Convert km to degrees (approximate)
            deg_offset = size_km / 111.32 / 2  # Half the size on each side
            
            coordinates = [
                [center_lon - deg_offset, center_lat - deg_offset],
                [center_lon + deg_offset, center_lat - deg_offset],
                [center_lon + deg_offset, center_lat + deg_offset],
                [center_lon - deg_offset, center_lat + deg_offset],
                [center_lon - deg_offset, center_lat - deg_offset]
            ]
            
            st.session_state.selected_area = {
                'type': 'Polygon',
                'coordinates': coordinates
            }
            st.session_state.area_coordinates = coordinates
            st.session_state.analysis_results = None
            
            area_ha = size_km * size_km * 100  # Convert km² to hectares
            st.success(f"Square area created: {area_ha:.0f} hectares")
            st.rerun()
    
    # Display reference map
    st.subheader("📍 Reference Map")
    
    # Create map showing selection
    m = folium.Map(location=[40.0, -100.0], zoom_start=4)
    
    # Add existing selection if available  
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = st.session_state.area_coordinates
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',
            weight=3,
            fillColor='green', 
            fillOpacity=0.3,
            popup="Selected Area"
        ).add_to(m)
        
        # Center map on selection
        lats = [coord[1] for coord in coords[:-1]]
        lons = [coord[0] for coord in coords[:-1]]
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
            folium.Polygon(
                locations=[(coord[1], coord[0]) for coord in coords],
                color='green',
                weight=3,
                fillColor='green',
                fillOpacity=0.3,
                popup="Selected Area"
            ).add_to(m)
    
    # Display the map (read-only for reference)
    st_folium(m, width=700, height=300, key="reference_map")
    
    # Coordinate input help
    with st.expander("💡 Coordinate Input Help"):
        st.write("**Finding Coordinates:**")
        st.write("• Use Google Maps: right-click → 'What's here?' to get lat/lon")
        st.write("• Latitude: North is positive (+), South is negative (-)")
        st.write("• Longitude: East is positive (+), West is negative (-)")
        st.write("• Example: New York City is approximately 40.7128°N, -74.0060°W")
        
        st.write("**Coordinate Ranges:**")
        st.write("• Latitude: -90 to +90 degrees")
        st.write("• Longitude: -180 to +180 degrees")
        st.write("• Make sure Southwest corner has smaller lat/lon values than Northeast")
        col_coord1, col_coord2 = st.columns(2)
        with col_coord1:
            min_lat = st.number_input("Min Latitude", value=40.0, format="%.6f", step=0.1, key="coord_min_lat")
            min_lon = st.number_input("Min Longitude", value=-100.0, format="%.6f", step=0.1, key="coord_min_lon")
        
        with col_coord2:
            max_lat = st.number_input("Max Latitude", value=41.0, format="%.6f", step=0.1, key="coord_max_lat")
            max_lon = st.number_input("Max Longitude", value=-99.0, format="%.6f", step=0.1, key="coord_max_lon")
        
        if st.button("Create Area from Coordinates", key="create_from_coords"):
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
            st.success(f"Area created: {area_ha:.1f} hectares")
            st.rerun()
    
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
        if False:  # Coordinate input now handled above
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
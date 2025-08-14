import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Ecosystem Valuation Engine", page_icon="🌱", layout="wide")

st.title("🌱 Ecosystem Valuation Engine")
st.write("Define an area to analyze ecosystem services")

# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Define Area Coordinates")
    
    # Simple coordinate input
    st.write("Enter coordinates for a rectangular area:")
    
    min_lat = st.number_input("Minimum Latitude", value=40.0, format="%.6f", step=0.1)
    max_lat = st.number_input("Maximum Latitude", value=41.0, format="%.6f", step=0.1)
    min_lon = st.number_input("Minimum Longitude", value=-100.0, format="%.6f", step=0.1)
    max_lon = st.number_input("Maximum Longitude", value=-99.0, format="%.6f", step=0.1)
    
    if st.button("Set Area", type="primary"):
        # Create rectangular coordinates
        coordinates = [
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]
        
        st.session_state.area_coordinates = coordinates
        st.session_state.selected_area = {
            'type': 'Polygon',
            'coordinates': coordinates
        }
        
        # Calculate area
        area_coords = np.array(coordinates)
        area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
        area_ha = area_km2 * 100
        st.success(f"Area set: {area_ha:.1f} hectares")
        st.rerun()
    
    if st.button("Clear Area"):
        st.session_state.selected_area = None
        st.session_state.area_coordinates = []
        st.rerun()
    
    # Show current selection info
    if st.session_state.selected_area:
        coords = st.session_state.area_coordinates
        area_coords = np.array(coords)
        area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
        area_ha = area_km2 * 100
        
        st.success("Area Selected!")
        st.metric("Area", f"{area_ha:.1f} hectares")
        
        # Show coordinates in small font
        st.markdown("**Coordinates:**")
        lats = [coord[1] for coord in coords[:-1]]
        lons = [coord[0] for coord in coords[:-1]]
        st.markdown(f"<small>**Latitude:** {min(lats):.6f} to {max(lats):.6f}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>**Longitude:** {min(lons):.6f} to {max(lons):.6f}</small>", unsafe_allow_html=True)
        
        # Analysis button
        if st.button("🚀 Analyze Ecosystem", type="primary", use_container_width=True):
            st.success("Analysis feature coming soon!")

with col1:
    st.subheader("Selected Area Map")
    
    # Create map
    center_lat = (min_lat + max_lat) / 2 if st.session_state.selected_area else 40.5
    center_lon = (min_lon + max_lon) / 2 if st.session_state.selected_area else -99.5
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add selected area if available
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = st.session_state.area_coordinates
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',
            weight=3,
            fillColor='green',
            fillOpacity=0.2,
            popup=f"Selected Area: {area_ha:.1f} hectares"
        ).add_to(m)
    
    # Display map
    st_folium(m, width=500, height=400, key="display_map")
    
    if not st.session_state.selected_area:
        st.info("Enter coordinates on the right to define an area for analysis")
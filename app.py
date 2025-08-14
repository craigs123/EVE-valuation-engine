import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Ecosystem Valuation Engine", page_icon="🌱", layout="wide")

st.title("🌱 Ecosystem Valuation Engine")
st.write("Draw an area on the map to analyze ecosystem services")

# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []

# Create map
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

# Add drawing capability with updated syntax
from folium.plugins import Draw
draw = Draw(
    draw_options={
        'polygon': {'allowIntersection': False},
        'rectangle': {'shapeOptions': {'color': '#ff0000'}},
        'polyline': False,
        'circle': False,
        'marker': False,
        'circlemarker': False,
    },
    edit_options={'edit': False}
)
draw.add_to(m)

# Display map
st.write("Use the polygon or rectangle tools in the map toolbar")
map_data = st_folium(
    m, 
    width=700, 
    height=500,
    returned_objects=["all_drawings"],
    key="map"
)

# Debug information
st.write("Debug Info:")
if map_data:
    st.json(map_data)
    
    # Process drawings
    if map_data.get('all_drawings') and len(map_data['all_drawings']) > 0:
        st.success(f"Found {len(map_data['all_drawings'])} drawing(s)")
        
        latest = map_data['all_drawings'][-1]
        if latest['geometry']['type'] == 'Polygon':
            coords = latest['geometry']['coordinates'][0]
            st.session_state.area_coordinates = coords
            st.session_state.selected_area = latest
            
            # Calculate area
            area_coords = np.array(coords)
            if len(area_coords) > 2:
                area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                area_ha = area_km2 * 100
                st.metric("Area", f"{area_ha:.1f} hectares")
                
            # Show coordinates
            st.write("Coordinates:")
            for i, coord in enumerate(coords):
                st.write(f"Point {i+1}: {coord[1]:.6f}°N, {coord[0]:.6f}°E")
    else:
        st.info("No drawings detected. Try using the drawing tools in the map.")
else:
    st.warning("Map data not available")

# Clear button
if st.button("Clear Selection"):
    st.session_state.selected_area = None
    st.session_state.area_coordinates = []
    st.rerun()
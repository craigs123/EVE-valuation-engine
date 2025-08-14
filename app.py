import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

st.title("Simple Map Test")

# Create basic map
m = folium.Map(location=[40.0, -100.0], zoom_start=4)

# Add drawing tools
draw = Draw(
    draw_options={
        'polygon': True,
        'rectangle': True,
        'circle': False,
        'marker': False,
        'polyline': False,
        'circlemarker': False,
    }
)
draw.add_to(m)

# Display map
map_data = st_folium(m, width=700, height=400, returned_objects=["all_drawings"], key="test_map")

# Show map data
if map_data:
    st.write("Map data returned:")
    st.json(map_data)
    
    if map_data.get('all_drawings'):
        st.write(f"Number of drawings: {len(map_data['all_drawings'])}")
        for i, drawing in enumerate(map_data['all_drawings']):
            st.write(f"Drawing {i}: {drawing['geometry']['type']}")
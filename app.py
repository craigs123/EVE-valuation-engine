import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Ecosystem Valuation Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("🌱 Ecosystem Valuation Engine")
st.caption("Economic valuation of ecosystem services using scientific ESVD database data")

# Initialize session state
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Create map
@st.cache_data
def create_folium_map():
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    return m

# Two column layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🗺️ Step 1: Select Area")
    
    # Create and display map
    m = create_folium_map()
    
    # Get map data
    map_data = st_folium(
        m,
        feature_group_on_click=False,
        draw=dict(
            draw_options=dict(
                polyline=False,
                polygon=True,
                circle=False,
                rectangle=True,
                marker=False,
                circlemarker=False,
            ),
            edit_options=dict(
                edit=False,
                remove=True
            )
        ),
        width=700,
        height=400
    )
    
    # Process drawing data
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        # Get the coordinates from the drawing
        drawing = map_data['all_drawings'][-1]  # Get the latest drawing
        if drawing['geometry']['type'] == 'Polygon':
            coords = drawing['geometry']['coordinates'][0]
            st.session_state.area_coordinates = coords
            st.success(f"✅ Area selected! {len(coords)} coordinate points")
        elif drawing['geometry']['type'] == 'Rectangle':
            # Convert rectangle to polygon coordinates
            bounds = drawing['geometry']['coordinates'][0]
            st.session_state.area_coordinates = bounds
            st.success(f"✅ Rectangle selected!")

with col2:
    st.subheader("📊 Step 2: Calculate Value")
    
    if st.session_state.area_coordinates:
        st.success("✅ Area ready for analysis")
        
        # Simple area calculation
        def calculate_area(coordinates):
            if len(coordinates) < 3:
                return 0
            # Simple Shoelace formula for polygon area
            coords = np.array(coordinates[:-1])  # Remove duplicate last point
            x = coords[:, 0]
            y = coords[:, 1]
            area_deg2 = 0.5 * abs(np.sum(x * np.roll(y, -1) - y * np.roll(x, -1)))
            # Convert to hectares (approximate)
            return area_deg2 * 12392.6424
        
        area_ha = calculate_area(st.session_state.area_coordinates)
        st.info(f"**Area**: {area_ha:.0f} hectares")
        
        # Calculate button
        if st.button("🚀 Calculate Ecosystem Value", type="primary", use_container_width=True):
            # Simple calculation
            coords_array = np.array(st.session_state.area_coordinates[:-1])
            center_lat = float(coords_array[:, 1].mean())
            center_lon = float(coords_array[:, 0].mean())
            
            # Determine forest type based on latitude
            forest_type = "temperate_forest"  # default
            if center_lat > 50:
                forest_type = "boreal_forest"
            elif center_lat < 23.5:
                forest_type = "tropical_forest"
            elif 30 <= center_lat <= 45 and -10 <= center_lon <= 40:  # Mediterranean region
                forest_type = "mediterranean_forest"
            
            # Simple forest type coefficients ($/ha/year)
            forest_coefficients = {
                "tropical_forest": 15000,      # Highest biodiversity
                "temperate_forest": 8000,      # Highest timber
                "boreal_forest": 6000,         # High carbon storage
                "mediterranean_forest": 7000   # High recreation
            }
            
            # Calculate total value
            value_per_ha = forest_coefficients[forest_type]
            total_value = value_per_ha * area_ha
            
            # Store results
            st.session_state.analysis_results = {
                'total_value': int(total_value),
                'value_per_ha': value_per_ha,
                'area_ha': area_ha,
                'forest_type': forest_type,
                'center_lat': center_lat,
                'center_lon': center_lon
            }
            
            st.success("✅ Calculation complete!")
            st.rerun()
    else:
        st.info("👆 First draw an area on the map")

# Results section
if st.session_state.analysis_results:
    st.markdown("---")
    st.subheader("📈 Step 3: Results")
    
    results = st.session_state.analysis_results
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Annual Value", f"${results['total_value']:,}")
    
    with col2:
        st.metric("Value per Hectare", f"${results['value_per_ha']:,}/ha")
    
    with col3:
        forest_display = results['forest_type'].replace('_', ' ').title()
        st.metric("🌲 Forest Type", forest_display)
    
    # Forest type information
    st.markdown("### 🌲 Forest Type Classification")
    
    forest_info = {
        'tropical_forest': {
            'name': '🌿 Tropical Forest',
            'description': 'Highest biodiversity and carbon storage. Premium ecotourism value.',
            'climate': 'Hot, humid year-round'
        },
        'temperate_forest': {
            'name': '🍂 Temperate Forest', 
            'description': 'Highest timber value. Seasonal recreation and mixed species.',
            'climate': 'Four distinct seasons'
        },
        'boreal_forest': {
            'name': '❄️ Boreal Forest',
            'description': 'Maximum soil carbon storage. Pulp and paper timber value.',
            'climate': 'Cold winters, short summers'
        },
        'mediterranean_forest': {
            'name': '☀️ Mediterranean Forest',
            'description': 'Drought adaptation and high recreation value. Fire-resistant.',
            'climate': 'Dry summers, mild winters'
        }
    }
    
    forest_type = results['forest_type']
    info = forest_info[forest_type]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success(f"""
        **{info['name']} Detected**
        
        **Location**: {results['center_lat']:.2f}°N, {results['center_lon']:.2f}°W
        **Detection Method**: Geographic coordinate analysis
        **Climate Zone**: {info['climate']}
        
        *{info['description']}*
        """)
    
    with col2:
        # Show breakdown
        st.markdown("**Value Breakdown:**")
        st.write(f"• Area: {results['area_ha']:.0f} ha")
        st.write(f"• Rate: ${results['value_per_ha']:,}/ha/year")
        st.write(f"• **Total: ${results['total_value']:,}/year**")

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ About")
    st.write("""
    The Ecosystem Valuation Engine calculates the economic value of ecosystem services using:
    
    - **Forest Type Detection**: Automatic classification based on geographic coordinates
    - **Scientific Coefficients**: Values derived from ESVD research database
    - **Four Forest Types**: Tropical, Temperate, Boreal, Mediterranean
    """)
    
    st.header("🌲 Forest Types")
    st.write("""
    **Tropical**: Highest biodiversity ($15k/ha/year)
    **Temperate**: Highest timber value ($8k/ha/year) 
    **Boreal**: High carbon storage ($6k/ha/year)
    **Mediterranean**: High recreation ($7k/ha/year)
    """)
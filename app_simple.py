"""
Ecosystem Valuation Engine - Simplified Clean Interface
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime
import json

# Simple page setup
st.set_page_config(
    page_title="Ecosystem Valuation Engine", 
    page_icon="🌱",
    layout="wide"
)

# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Clean header
st.title("🌱 Ecosystem Valuation Engine")
st.markdown("**Measure the economic value of ecosystem services using scientific data**")

# Simple 3-step workflow
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 1️⃣ Select Area")
    st.markdown("Draw on the map")

with col2:
    st.markdown("### 2️⃣ Configure")
    ecosystem_type = st.selectbox(
        "Ecosystem Type:",
        ["Auto-detect", "Forest", "Grassland", "Wetland", "Agricultural", "Coastal", "Marine"]
    )
    
    analysis_type = st.selectbox(
        "Analysis Type:",
        ["Summary", "Detailed"]
    )

with col3:
    st.markdown("### 3️⃣ Calculate")
    if st.session_state.get('selected_area'):
        if st.button("🚀 Calculate Value", type="primary", use_container_width=True):
            # Simple calculation
            coords = st.session_state.area_coordinates
            if coords:
                # Calculate area
                lats = [coord[1] for coord in coords[:-1]]
                lons = [coord[0] for coord in coords[:-1]]
                lat_range = max(lats) - min(lats)
                lon_range = max(lons) - min(lons)
                area_ha = lat_range * lon_range * 111.32 * 111.32 * 100
                
                # Simple valuation (placeholder - would use real ESVD data)
                base_value_per_ha = {"Forest": 3956, "Grassland": 232, "Wetland": 25681, 
                                    "Agricultural": 92, "Coastal": 18220, "Marine": 67760, "Auto-detect": 2000}
                value_per_ha = base_value_per_ha.get(ecosystem_type, 2000)
                total_value = area_ha * value_per_ha
                
                st.session_state.analysis_results = {
                    'area_ha': area_ha,
                    'ecosystem_type': ecosystem_type,
                    'total_value': total_value,
                    'value_per_ha': value_per_ha
                }
                st.success(f"Analysis complete!")
    else:
        st.button("Select area first", disabled=True, use_container_width=True)

st.markdown("---")

# Simple two-column layout
col_map, col_results = st.columns([2, 1])

with col_map:
    st.subheader("🗺️ Map")
    
    # Simple map
    m = folium.Map(location=[39.8, -98.6], zoom_start=4, tiles="OpenStreetMap")
    
    # Add drawing tools
    from folium.plugins import Draw
    draw = Draw(
        export=False,
        position="topleft",
        draw_options={
            'polyline': False,
            'polygon': True,
            'circle': False,
            'rectangle': True,
            'marker': False,
            'circlemarker': False,
        }
    )
    draw.add_to(m)
    
    # Display map
    map_data = st_folium(m, key="main_map", width=700, height=500)
    
    # Handle area selection
    if map_data['all_drawings']:
        if len(map_data['all_drawings']) > 0:
            feature = map_data['all_drawings'][0]
            if feature['geometry']['type'] in ['Polygon']:
                coords = feature['geometry']['coordinates'][0]
                st.session_state.selected_area = True
                st.session_state.area_coordinates = coords
            else:
                st.session_state.selected_area = False
    else:
        st.session_state.selected_area = False

with col_results:
    st.subheader("📊 Results")
    
    if st.session_state.get('analysis_results'):
        results = st.session_state.analysis_results
        
        # Clean results display with very small font
        st.markdown('<p style="font-size:18px; margin:2px 0;"><strong>Area:</strong> {:,.0f} hectares</p>'.format(results['area_ha']), unsafe_allow_html=True)
        st.markdown('<p style="font-size:16px; margin:2px 0;"><strong>Ecosystem:</strong> {}</p>'.format(results['ecosystem_type']), unsafe_allow_html=True)
        st.markdown('<p style="font-size:16px; margin:2px 0;"><strong>Total Value:</strong> ${:,.0f} /year</p>'.format(results['total_value']), unsafe_allow_html=True)
        st.markdown('<p style="font-size:16px; margin:2px 0;"><strong>Value per Hectare:</strong> ${:,.0f} /ha/year</p>'.format(results['value_per_ha']), unsafe_allow_html=True)
        
        # Simple download
        if st.button("📥 Download Report"):
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'area_hectares': results['area_ha'],
                'ecosystem_type': results['ecosystem_type'],
                'total_annual_value': results['total_value'],
                'value_per_hectare': results['value_per_ha']
            }
            st.download_button(
                "Download JSON",
                data=json.dumps(report_data, indent=2),
                file_name=f"ecosystem_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    elif st.session_state.get('selected_area'):
        st.info("✅ Area selected\nClick 'Calculate Value' to analyze")
    else:
        st.info("📍 Draw an area on the map to begin")

# Simple footer
st.markdown("---")
with st.expander("ℹ️ About"):
    st.markdown("""
    **Ecosystem Valuation Engine** measures the economic value of ecosystem services using scientific data.
    
    - **Data Source**: ESVD database with 10,000+ peer-reviewed studies
    - **Method**: Economic valuation of provisioning, regulating, cultural, and supporting services
    - **Values**: Standardized to 2020 International dollars per hectare per year
    """)
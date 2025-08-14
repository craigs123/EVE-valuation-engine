"""
Ecosystem Valuation Engine - Simplified Working Version
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Ecosystem Valuation Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []

# Header
st.markdown('<h1 class="main-header">🌱 Ecosystem Valuation Engine</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Measure natural capital growth through economic valuation of ecosystem services</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    ecosystem_override = st.selectbox(
        "Ecosystem Type",
        options=["Auto-detect from satellite data", "forest", "grassland", "wetland", "agricultural", "coastal", "urban", "desert"],
        index=0
    )
    
    analysis_detail = st.selectbox(
        "Analysis Detail",
        options=["Quick Overview", "Detailed Analysis"],
        index=1
    )
    
    if st.button("Clear Area & Results"):
        st.session_state.analysis_results = None
        st.session_state.selected_area = None
        st.session_state.area_coordinates = []
        st.rerun()

# Main content
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Select Your Area")
    
    # Simple coordinate input method
    st.info("Enter coordinates to define a rectangular area:")
    
    col_coord1, col_coord2 = st.columns(2)
    with col_coord1:
        st.write("**Southwest Corner:**")
        min_lat = st.number_input("Latitude", value=40.0, format="%.6f", key="min_lat")
        min_lon = st.number_input("Longitude", value=-100.0, format="%.6f", key="min_lon")
    with col_coord2:
        st.write("**Northeast Corner:**")
        max_lat = st.number_input("Latitude", value=41.0, format="%.6f", key="max_lat")
        max_lon = st.number_input("Longitude", value=-99.0, format="%.6f", key="max_lon")
    
    if st.button("Set Area from Coordinates", type="primary"):
        # Create rectangular coordinates
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
        
        # Calculate and show area
        area_coords = np.array(coordinates)
        area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
        area_ha = area_km2 * 100
        st.success(f"Area set: {area_ha:.1f} hectares")
        st.rerun()
    
    # Display map with selected area
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = st.session_state.area_coordinates
        lats = [coord[1] for coord in coords[:-1]]
        lons = [coord[0] for coord in coords[:-1]]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Calculate zoom level based on area size
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        if max_range < 0.01:
            zoom_level = 12
        elif max_range < 0.1:
            zoom_level = 10
        elif max_range < 1.0:
            zoom_level = 8
        else:
            zoom_level = 6
            
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)
        
        # Add selected area
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',
            weight=3,
            fillColor='green',
            fillOpacity=0.2,
            popup="Selected Area"
        ).add_to(m)
    else:
        # Default map view
        m = folium.Map(location=[40.0, -100.0], zoom_start=4)
    
    # Display map (no drawing tools for now)
    st_folium(m, width=700, height=400, key="display_map")
    
    # Sample areas for quick testing
    st.markdown("---")
    st.markdown("**Quick Test Areas:**")
    sample_areas = {
        "Central Park, NYC": (40.764, -73.973, 40.800, -73.949),
        "Golden Gate Park, SF": (37.769, -122.511, 37.775, -122.453),
        "Hyde Park, London": (51.508, -0.175, 51.513, -0.159)
    }
    
    selected_sample = st.selectbox("Or choose a sample area:", ["None"] + list(sample_areas.keys()))
    
    if selected_sample != "None" and st.button(f"Load {selected_sample}"):
        min_lat, min_lon, max_lat, max_lon = sample_areas[selected_sample]
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
        st.success(f"Loaded {selected_sample}")
        st.rerun()

with col2:
    st.subheader("Analysis Preview")
    
    if st.session_state.get('selected_area'):
        st.success("✅ Area Selected")
        coords = st.session_state.area_coordinates
        
        # Calculate area
        area_coords = np.array(coords)
        if len(area_coords) > 2:
            area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
            area_ha = area_km2 * 100
            st.metric("Area", f"{area_ha:.1f} hectares")
        
        # Analysis controls
        st.subheader("Analysis Controls")
        
        time_preset = st.selectbox(
            "Analysis Period",
            options=["Past Year", "Past 6 Months", "Past 3 Months"],
            index=0
        )
        
        preset_options = {
            "Past Year": (datetime.now() - timedelta(days=365), datetime.now()),
            "Past 6 Months": (datetime.now() - timedelta(days=180), datetime.now()),
            "Past 3 Months": (datetime.now() - timedelta(days=90), datetime.now())
        }
        start_date, end_date = preset_options[time_preset]
        
        # Analysis button
        if st.button("🚀 Calculate Value", type="primary", use_container_width=True):
            with st.spinner("Calculating ecosystem services..."):
                # ESVD coefficients (2020 USD/ha/year)
                esvd_coefficients = {
                    'forest': {
                        'provisioning': 762, 'regulating': 4258, 'cultural': 428, 'supporting': 287,
                        'ecosystem_services_total': 5735
                    },
                    'grassland': {
                        'provisioning': 232, 'regulating': 1654, 'cultural': 87, 'supporting': 126,
                        'ecosystem_services_total': 2099
                    },
                    'wetland': {
                        'provisioning': 1350, 'regulating': 8240, 'cultural': 781, 'supporting': 394,
                        'ecosystem_services_total': 10765
                    },
                    'agricultural': {
                        'provisioning': 5567, 'regulating': 612, 'cultural': 32, 'supporting': 95,
                        'ecosystem_services_total': 6306
                    }
                }
                
                # Determine ecosystem type
                if ecosystem_override == "Auto-detect from satellite data":
                    detected_ecosystem = "grassland"  # Simplified for demo
                    st.info("⚠️ Using geographic fallback: Grassland (satellite APIs need authentication)")
                else:
                    detected_ecosystem = ecosystem_override
                
                # Calculate values
                coeffs = esvd_coefficients.get(detected_ecosystem, esvd_coefficients['grassland'])
                
                ecosystem_values = {}
                selected_metrics = ['ecosystem_services_total', 'provisioning', 'regulating', 'cultural', 'supporting'] if analysis_detail == "Detailed Analysis" else ['ecosystem_services_total']
                
                for metric in selected_metrics:
                    if metric in coeffs:
                        per_hectare_value = coeffs[metric]
                        total_annual_value = per_hectare_value * area_ha
                        
                        ecosystem_values[metric] = {
                            'total': total_annual_value,
                            'per_hectare': per_hectare_value,
                            'area_hectares': area_ha
                        }
                
                # Store results
                st.session_state.analysis_results = {
                    'ecosystem_type': detected_ecosystem,
                    'ecosystem_values': ecosystem_values,
                    'area_hectares': area_ha,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                st.success("✅ Analysis complete!")
                st.rerun()
    else:
        st.warning("⚠️ No area selected")
        st.write("Select an area on the map to begin analysis")

# Display results
if st.session_state.get('analysis_results'):
    st.markdown("---")
    st.header("📈 Ecosystem Valuation Results")
    
    results = st.session_state.analysis_results
    ecosystem_values = results['ecosystem_values']
    
    # Main metrics
    st.subheader("💰 Economic Valuation Summary")
    
    if 'ecosystem_services_total' in ecosystem_values:
        total_value = ecosystem_values['ecosystem_services_total']['total']
        per_ha_value = ecosystem_values['ecosystem_services_total']['per_hectare']
        area_ha = ecosystem_values['ecosystem_services_total']['area_hectares']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Annual Value", f"${total_value:,.0f}")
        with col2:
            st.metric("Per Hectare Value", f"${per_ha_value:,.0f}")
        with col3:
            st.metric("Area Analyzed", f"{area_ha:.1f} ha")
        
        # Service breakdown chart if detailed analysis
        if len(ecosystem_values) > 1:
            st.subheader("📊 Service Category Breakdown")
            
            categories = []
            values = []
            
            for service, data in ecosystem_values.items():
                if service != 'ecosystem_services_total':
                    categories.append(service.replace('_', ' ').title())
                    values.append(data['total'])
            
            if categories:
                fig = go.Figure(data=[
                    go.Bar(x=categories, y=values,
                           marker_color=['#1976D2', '#388E3C', '#F57C00', '#7B1FA2'],
                           text=[f'${v:,.0f}' for v in values],
                           textposition='auto')
                ])
                fig.update_layout(
                    title="Annual Value by Service Category",
                    xaxis_title="Service Category",
                    yaxis_title="Annual Value (USD)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Analysis details
        with st.expander("📖 Analysis Details"):
            st.write(f"**Ecosystem Type:** {results['ecosystem_type'].title()}")
            st.write(f"**Analysis Date:** {results['analysis_timestamp'][:10]}")
            st.write(f"**Data Source:** ESVD Global Database")
            st.write(f"**Currency:** 2020 USD")
            st.write("**Note:** Values are based on global average coefficients from peer-reviewed studies")
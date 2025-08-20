import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta
import json
import gc

# Ultra-performance configuration for preview environment
st.set_page_config(
    page_title="Ecosystem Valuation Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Aggressive caching for all heavy operations
@st.cache_resource(ttl=3600)
def get_database_modules():
    try:
        from database import (
            init_database, initialize_user_session,
            EcosystemAnalysisDB, SavedAreaDB, NaturalCapitalBaselineDB
        )
        return {
            'init_db': init_database,
            'init_session': initialize_user_session,
            'AnalysisDB': EcosystemAnalysisDB,
            'AreaDB': SavedAreaDB,
            'BaselineDB': NaturalCapitalBaselineDB
        }
    except:
        return None

@st.cache_data(ttl=3600)
def get_styles():
    return """<style>
.main-header{font-size:2.5rem;font-weight:700;color:#2e8b57;text-align:center}
.subtitle{font-size:1.2rem;color:#666;text-align:center;margin-bottom:1rem}
.metric-container{background:#f8f9fa;padding:1rem;border-radius:0.5rem;border-left:4px solid #2e8b57;margin:0.5rem 0}
</style>"""

@st.cache_resource(ttl=1800)
def create_map(lat=39.8283, lon=-98.5795, zoom=5):
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        prefer_canvas=True,
        max_zoom=12,
        attributionControl=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        boxZoom=False,
        keyboard=False
    )

@st.cache_data(ttl=1800)
def calculate_area_fast(coordinates):
    if not coordinates or len(coordinates) < 3:
        return 0.0
    coords = np.array(coordinates[:-1], dtype=np.float32)
    x, y = coords[:, 0], coords[:, 1]
    area_deg2 = 0.5 * abs(np.sum(x * np.roll(y, -1) - y * np.roll(x, -1)))
    return area_deg2 * 12321.0  # Direct conversion to hectares

# Minimal UI setup
st.markdown(get_styles(), unsafe_allow_html=True)
st.markdown('<h1 class="main-header">🌱 Ecosystem Valuation Engine</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Fast ecosystem analysis for preview environment</p>', unsafe_allow_html=True)

# Simplified database check
db_modules = get_database_modules()
if db_modules and 'db_ready' not in st.session_state:
    try:
        if db_modules['init_db']():
            st.session_state.db_ready = True
            st.session_state.user_id = db_modules['init_session']()
        else:
            st.session_state.db_ready = False
    except:
        st.session_state.db_ready = False

# Sidebar with minimal settings
with st.sidebar:
    st.header("⚙️ Settings")
    max_samples = st.slider("Sample Points", 4, 20, 10, help="Fewer points = faster analysis")
    st.session_state.max_sampling_limit = max_samples
    
    date_start = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    date_end = st.date_input("End Date", datetime.now())
    
    if st.button("🗑️ Clear All"):
        for key in list(st.session_state.keys()):
            if key not in ['db_ready', 'user_id']:
                del st.session_state[key]
        gc.collect()
        st.rerun()

# Main interface
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🗺️ Select Area")
    st.info(f"Draw on map • Max {max_samples} sample points for speed")
    
    # Ultra-simplified map
    if st.session_state.get('area_coordinates'):
        coords = st.session_state.area_coordinates
        coords_array = np.array(coords[:-1], dtype=np.float32)
        center_lat = float(coords_array[:, 1].mean())
        center_lon = float(coords_array[:, 0].mean())
        m = create_map(center_lat, center_lon, 8)
        
        # Add selected area
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='#28a745',
            weight=2,
            fill=True,
            fillOpacity=0.3
        ).add_to(m)
    else:
        m = create_map()
    
    # Add drawing capability
    from folium.plugins import Draw
    draw = Draw(export=False, position='topleft', 
               draw_options={'polyline': False, 'circle': False, 'marker': False, 
                           'circlemarker': False, 'polygon': True, 'rectangle': True})
    draw.add_to(m)
    
    # Display map
    map_data = st_folium(m, width=700, height=400, returned_objects=["all_drawings"])
    
    # Process map selection
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        last_drawing = map_data['all_drawings'][-1]
        if last_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
            coords = last_drawing['geometry']['coordinates'][0]
            st.session_state.area_coordinates = coords
            st.session_state.selected_area = True
            
            area_ha = calculate_area_fast(coords)
            st.session_state.area_ha = area_ha
            
            st.success(f"✅ Area selected: {area_ha:.2f} hectares")

with col2:
    st.subheader("📊 Analysis")
    
    if st.session_state.get('selected_area'):
        area_ha = st.session_state.get('area_ha', 0)
        st.metric("Selected Area", f"{area_ha:.2f} ha")
        
        # Simplified analysis button
        if st.button("🔍 Analyze Ecosystem", type="primary"):
            with st.spinner("Analyzing..."):
                try:
                    # Fast ecosystem detection
                    @st.cache_resource
                    def get_detector():
                        from utils.openlandmap_integration import detect_ecosystem_type
                        return detect_ecosystem_type
                    
                    detect_func = get_detector()
                    coords = st.session_state.area_coordinates
                    
                    # Minimal progress tracking
                    progress = st.progress(0)
                    status = st.empty()
                    
                    def quick_progress(current, total):
                        if current == total or current % max(1, total//4) == 0:
                            progress.progress(current/total)
                            status.info(f"Progress: {current}/{total}")
                    
                    ecosystem_info = detect_func(
                        coords, max_samples, quick_progress
                    )
                    
                    progress.progress(0.8)
                    status.info("Calculating values...")
                    
                    # Fast value calculation
                    @st.cache_resource
                    def get_calculator():
                        from utils.ecosystem_services import calculate_ecosystem_values
                        return calculate_ecosystem_values
                    
                    calc_func = get_calculator()
                    results = calc_func(
                        area_hectares=area_ha,
                        ecosystem_type=ecosystem_info.get('ecosystem_type', 'Mixed'),
                        detected_ecosystem_info=ecosystem_info
                    )
                    
                    progress.progress(1.0)
                    status.success("✅ Complete!")
                    
                    st.session_state.analysis_results = results
                    st.session_state.detected_ecosystem = ecosystem_info
                    
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    
    # Show results
    if st.session_state.get('analysis_results'):
        results = st.session_state.analysis_results
        
        st.markdown("### 💰 Economic Value")
        total_value = results.get('total_annual_value', 0)
        per_ha_value = results.get('value_per_hectare', 0)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Value", f"${total_value:,.0f}/year")
        with col_b:
            st.metric("Per Hectare", f"${per_ha_value:,.0f}/ha/year")
        
        # Service breakdown
        if 'service_breakdown' in results:
            st.markdown("### 🌿 Services")
            services = results['service_breakdown']
            
            for service, value in services.items():
                if value > 0:
                    st.metric(service.title(), f"${value:,.0f}/year")
        
        # Ecosystem composition
        if st.session_state.get('detected_ecosystem', {}).get('ecosystem_composition'):
            st.markdown("### 🗺️ Composition")
            comp = st.session_state.detected_ecosystem['ecosystem_composition']
            
            for eco_type, percentage in comp.items():
                if percentage > 0:
                    st.write(f"**{eco_type}**: {percentage:.1f}%")
        
        # Save analysis
        if st.session_state.get('db_ready') and db_modules:
            st.markdown("### 💾 Save Analysis")
            
            with st.form("save_form"):
                name = st.text_input("Analysis Name", "My Analysis")
                description = st.text_area("Description", "")
                
                if st.form_submit_button("Save Analysis"):
                    try:
                        analysis_db = db_modules['AnalysisDB']()
                        
                        analysis_data = {
                            'user_id': st.session_state.user_id,
                            'area_name': name,
                            'description': description,
                            'coordinates': json.dumps(st.session_state.area_coordinates),
                            'area_hectares': st.session_state.area_ha,
                            'total_value': total_value,
                            'value_per_hectare': per_ha_value,
                            'ecosystem_type': st.session_state.detected_ecosystem.get('ecosystem_type', 'Unknown'),
                            'analysis_date': datetime.now(),
                            'sampling_points': max_samples
                        }
                        
                        if analysis_db.save_analysis(analysis_data):
                            st.success("✅ Analysis saved!")
                        else:
                            st.error("❌ Save failed")
                    except Exception as e:
                        st.error(f"Save error: {str(e)}")
    else:
        st.info("Select an area and run analysis to see results")

# Memory cleanup
if st.session_state.get('cleanup_needed'):
    gc.collect()
    st.session_state.cleanup_needed = False
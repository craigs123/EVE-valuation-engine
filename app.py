"""
Ecosystem Valuation Engine - Clean Map Implementation
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta
import json

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
.small-coordinates {
    font-size: 0.8rem;
}
.small-coordinates h3 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}
.small-coordinates .metric-container {
    padding: 0.5rem;
    font-size: 0.75rem;
}
.coordinate-bounds {
    font-size: 0.75rem;
    margin: 0.5rem 0;
}
.coordinate-bounds .metric-label {
    font-size: 0.7rem;
    color: #666;
}
.coordinate-bounds .metric-value {
    font-size: 0.8rem;
    font-weight: 500;
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
        options=["Auto-detect from OpenLandMap", "Forest", "Grassland", "Wetland", "Agricultural", "Coastal", "Urban", "Desert"],
        help="Auto-detection uses OpenLandMap.com for authentic land cover data"
    )
    
    # Store settings
    st.session_state.ecosystem_override = ecosystem_override
    
    st.markdown("---")
    
    # Clear button
    if st.button("🗑️ Clear Area & Results", help="Start over with a new area"):
        st.session_state.analysis_results = None
        st.session_state.selected_area = None
        st.session_state.area_coordinates = []
        st.rerun()

# Initialize analyze_button as False
analyze_button = False

# Map and preview in columns
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🗺️ Select Your Area")
    st.info("Use the drawing tools (rectangle/polygon icons) in the map toolbar to select an area")
    
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

    # Add drawing tools
    from folium.plugins import Draw
    draw = Draw(
        draw_options={
            'polyline': False,
            'polygon': True,
            'circle': False,
            'rectangle': True,
            'marker': False,
            'circlemarker': False,
        },
        edit_options={
            'remove': True,
            'edit': False
        }
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
    
    # Process map interactions
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        latest_drawing = map_data['all_drawings'][-1]
        
        if latest_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
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
            st.warning("Please draw a polygon or rectangle area")
    
    # Display coordinates of selected area
    if st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
        st.markdown('<div class="small-coordinates">', unsafe_allow_html=True)
        st.markdown("### 📍 Selected Area Coordinates")
        coords = st.session_state.area_coordinates
        
        # Calculate bounding box
        lats = [coord[1] for coord in coords[:-1]]  # Exclude last duplicate point
        lons = [coord[0] for coord in coords[:-1]]
        
        # Display min values on one line, max on next
        st.markdown(f"""
        <div class="coordinate-bounds">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                <span><span class="metric-label">Min Lat:</span> <span class="metric-value">{min(lats):.6f}</span></span>
                <span><span class="metric-label">Min Lon:</span> <span class="metric-value">{min(lons):.6f}</span></span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span><span class="metric-label">Max Lat:</span> <span class="metric-value">{max(lats):.6f}</span></span>
                <span><span class="metric-label">Max Lon:</span> <span class="metric-value">{max(lons):.6f}</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show all coordinates in expandable section
        with st.expander("All Coordinates"):
            for i, coord in enumerate(coords[:-1]):  # Exclude last duplicate
                st.markdown(f"<small>Point {i+1}: {coord[1]:.6f}°N, {coord[0]:.6f}°E</small>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No area selected yet. Use the drawing tools (rectangle/polygon) in the map toolbar.")
    
    # Analysis controls under the map
    st.markdown("### 📊 Analysis Controls")
    
    col_period, col_button = st.columns([2, 1])
    
    with col_period:
        time_preset = st.selectbox(
            "Analysis Period",
            options=["Past Year", "Past 6 Months", "Past 3 Months", "Custom Range"],
            index=0,
            key="map_time_preset"
        )
        
        if time_preset == "Custom Range":
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("From", value=datetime.now() - timedelta(days=365), key="map_start_date")
            with col_end:
                end_date = st.date_input("To", value=datetime.now(), key="map_end_date")
        else:
            preset_options = {
                "Past Year": (datetime.now() - timedelta(days=365), datetime.now()),
                "Past 6 Months": (datetime.now() - timedelta(days=180), datetime.now()),
                "Past 3 Months": (datetime.now() - timedelta(days=90), datetime.now())
            }
            start_date, end_date = preset_options[time_preset]
        
        # Analysis detail level (moved from sidebar)
        analysis_detail = st.selectbox(
            "Analysis Detail",
            options=["Summary Analysis", "Detailed Analysis"],
            help="Summary shows total value and basic metrics. Detailed includes service breakdown, calculations, and methodology.",
            key="analysis_detail_main"
        )
        
        # Store setting
        st.session_state.analysis_detail = analysis_detail
    
    with col_button:
        st.write("") # spacing
        if st.session_state.selected_area:
            analyze_button = st.button(
                "🚀 Calculate Value", 
                type="primary",
                use_container_width=True,
                help="Calculate ecosystem services value for selected area"
            )
        else:
            analyze_button = st.button(
                "Select area first", 
                disabled=True,
                use_container_width=True
            )

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
        
        # Show ecosystem detection status
        if st.session_state.ecosystem_override == "Auto-detect from OpenLandMap":
            if 'detected_ecosystem' in st.session_state:
                ecosystem_info = st.session_state.detected_ecosystem
                st.info(f"**Detected:** {ecosystem_info['primary_ecosystem']} ({ecosystem_info['confidence']:.0%} confidence)")
            else:
                st.info("**Ecosystem:** Will detect automatically")
        else:
            st.info(f"**Ecosystem:** {st.session_state.ecosystem_override}")
        st.info(f"**Analysis:** {st.session_state.analysis_detail}")
        
        if st.session_state.analysis_results:
            st.success("📈 Analysis Complete")
            st.write("Results are ready for viewing")
        else:
            st.info("Ready for analysis - click 'Calculate Value' button")
    else:
        st.warning("⚠️ No area selected")
        st.write("Select an area on the map to begin analysis")

# Analysis with OpenLandMap ecosystem detection
if analyze_button and st.session_state.selected_area:
    # Check area size limits before proceeding
    try:
        coords = np.array(st.session_state.area_coordinates)
        area_km2 = abs(np.sum((coords[:-1, 0] * coords[1:, 1]) - (coords[1:, 0] * coords[:-1, 1]))) * 111.32 * 111.32 / 2
        area_ha = area_km2 * 100
        
        if area_ha > 10000:
            st.error(f"⚠️ Selected area ({area_ha:,.0f} hectares) exceeds the maximum limit of 10,000 hectares. Please select a smaller area for accurate and timely analysis.")
            st.info("💡 **Why the limit?** Larger areas require more sample points for accurate ecosystem detection, which increases processing time. The 10,000 hectare limit ensures fast, reliable results.")
        else:
            with st.spinner("Analyzing ecosystem and calculating values..."):
                # Detect ecosystem type if auto-detection is enabled
                ecosystem_type = st.session_state.ecosystem_override
                
                if st.session_state.ecosystem_override == "Auto-detect from OpenLandMap":
                    try:
                        from utils.openlandmap_integration import detect_ecosystem_type
                        
                        # Show detection progress
                        st.info("🔍 Detecting ecosystem type using OpenLandMap...")
                        
                        ecosystem_info = detect_ecosystem_type(st.session_state.area_coordinates)
                        st.session_state.detected_ecosystem = ecosystem_info
                        ecosystem_type = ecosystem_info['primary_ecosystem']
                        
                        # Show detection results with details
                        if ecosystem_info['successful_queries'] > 0:
                            st.success(f"✅ **Detected: {ecosystem_type}** ({ecosystem_info['confidence']:.0%} confidence from {ecosystem_info['successful_queries']} sample points)")
                            st.info(f"📊 Coverage: {ecosystem_info.get('coverage_percentage', 100):.0f}% | Source: {ecosystem_info.get('source', 'OpenLandMap')}")
                        else:
                            st.info(f"🗺️ **Detected: {ecosystem_type}** (Geographic analysis - OpenLandMap unavailable)")
                            
                    except Exception as e:
                        st.warning(f"⚠️ OpenLandMap detection failed: {str(e)}")
                        st.info("🗺️ **Using fallback: Grassland** (Geographic analysis)")
                        ecosystem_type = "Grassland"
                        # Store fallback detection info
                        st.session_state.detected_ecosystem = {
                            'primary_ecosystem': 'Grassland',
                            'confidence': 0.5,
                            'successful_queries': 0,
                            'source': 'Geographic fallback',
                            'coverage_percentage': 100
                        }
                
                # Calculate authentic ecosystem values using ESVD database
                from utils.esvd_integration import calculate_ecosystem_services_value, calculate_mixed_ecosystem_services_value
                
                # Get center coordinates for regional adjustment
                center_lat = float(np.mean([coord[1] for coord in coords[:-1]]))
                center_lon = float(np.mean([coord[0] for coord in coords[:-1]]))
                
                # Check if we have mixed ecosystem data for weighted calculation
                if (st.session_state.get('detected_ecosystem') and 
                    'ecosystem_distribution' in st.session_state.detected_ecosystem and
                    len(st.session_state.detected_ecosystem['ecosystem_distribution']) > 1):
                    
                    # Use mixed ecosystem calculation with proper weighting
                    ecosystem_distribution = st.session_state.detected_ecosystem['ecosystem_distribution']
                    st.info(f"🌍 **Mixed Ecosystem Detected**: {len(ecosystem_distribution)} types found - using weighted calculation")
                    
                    # Show composition breakdown
                    for eco_type, data in ecosystem_distribution.items():
                        proportion = data['count'] / st.session_state.detected_ecosystem['successful_queries'] * 100
                        st.write(f"   • {eco_type}: {proportion:.0f}% ({data['count']} sample points)")
                    
                    esvd_results = calculate_mixed_ecosystem_services_value(
                        ecosystem_distribution=ecosystem_distribution,
                        area_hectares=area_ha,
                        coordinates=(center_lat, center_lon)
                    )
                else:
                    # Single ecosystem calculation
                    esvd_results = calculate_ecosystem_services_value(
                        ecosystem_type=ecosystem_type,
                        area_hectares=area_ha,
                        coordinates=(center_lat, center_lon)
                    )
                
                # Store comprehensive analysis results
                st.session_state.analysis_results = {
                    'total_value': int(esvd_results['metadata']['total_value']),
                    'area_ha': area_ha,
                    'ecosystem_type': ecosystem_type,
                    'esvd_results': esvd_results,
                    'value_per_ha': esvd_results['metadata']['value_per_hectare'],
                    'data_source': 'ESVD/TEEB Database',
                    'regional_factor': esvd_results['metadata']['regional_adjustment']
                }
                
                st.success("Analysis complete!")
                st.rerun()
                
    except Exception as e:
        st.error(f"Error processing area: {e}")
        st.info("Please try selecting the area again.")

# Display results if available
if st.session_state.analysis_results:
    st.markdown("---")
    
    # Different displays based on analysis detail level
    analysis_mode = st.session_state.get('analysis_detail', 'Summary Analysis')
    
    if analysis_mode == "Summary Analysis":
        st.subheader("📈 Summary Results")
        results = st.session_state.analysis_results
        
        # Simple metrics display for summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Annual Value", f"${results['total_value']:,}")
        with col2:
            per_ha = results.get('value_per_ha', results['total_value']/results['area_ha'])
            st.metric("Value per Hectare", "")
            st.markdown(f"**${per_ha:.0f}/ha**")
            st.caption("per hectare annually")
        with col3:
            st.metric("Area Analyzed", f"{results['area_ha']:,.0f} ha")
        
        # Basic info with ecosystem composition
        if 'ecosystem_composition' in results.get('metadata', {}):
            composition_text = ", ".join([f"{eco}: {prop*100:.0f}%" for eco, prop in results['metadata']['ecosystem_composition'].items()])
            st.info(f"**Mixed Ecosystem**: {composition_text} | **Data Source**: {results.get('data_source', 'ESVD/TEEB Database')}")
        else:
            st.info(f"**Ecosystem Type**: {results['ecosystem_type']} | **Data Source**: {results.get('data_source', 'ESVD/TEEB Database')}")
        
        # Option to upgrade to detailed view
        if st.button("🔍 View Detailed Analysis", type="secondary"):
            st.session_state['analysis_detail'] = 'Detailed Analysis'
            st.rerun()
            
    else:  # Detailed Analysis
        st.subheader("📈 Detailed Analysis Results")
        results = st.session_state.analysis_results
        
        col_metrics = st.columns(3)
        with col_metrics[0]:
            st.metric("Total Ecosystem Value", f"${results['total_value']:,}/year")
            with st.expander("💡 How this value is calculated"):
                st.markdown(f"""
                **Total Ecosystem Value**: ${results['total_value']:,}/year
                
                This represents the annual economic contribution of all ecosystem services in the selected area.
                
                **Calculation Method**:
                1. **Service Categories**: Sum of Provisioning + Regulating + Cultural + Supporting services
                2. **Base Values**: ESVD coefficients ($/ha/year) for each service type
                3. **Area Scaling**: Multiply by {results['area_ha']:,.0f} hectares
                4. **Regional Adjustment**: Apply factor of {results.get('regional_factor', 1.0):.2f} for local conditions
                
                **Data Sources**:
                - ESVD Database: 10,874+ peer-reviewed value estimates
                - TEEB Integration: Economics of Ecosystems and Biodiversity
                - Scientific Standards: 2020 International dollars per hectare per year
                """)
                
        with col_metrics[1]:
            per_ha_detailed = results.get('value_per_ha', results['total_value']/results['area_ha'])
            st.metric("Value per Hectare", "")
            st.markdown(f"**${per_ha_detailed:.0f}/ha**")
            st.caption("per hectare annually")
            with st.expander("💡 Per hectare calculation"):
                st.markdown(f"""
                **Value per Hectare**: ${per_ha_detailed:.0f}/ha/year
                
                **Formula**: Total Value ÷ Area
                - Total Value: ${results['total_value']:,}/year
                - Area: {results['area_ha']:,.0f} hectares
                - Per Hectare: ${results['total_value']:,} ÷ {results['area_ha']:,.0f} = ${per_ha_detailed:.0f}/ha/year
                
                **What this means**:
                Each hectare of {results['ecosystem_type'].lower()} provides ${per_ha_detailed:.0f} worth of ecosystem 
                services annually, including clean air, water filtration, carbon storage, recreation, and biodiversity support.
                
                **Regional Context**:
                This value has been adjusted by a factor of {results.get('regional_factor', 1.0):.2f} to account for:
                - Local income levels and purchasing power
                - Regional cost of living differences  
                - Data availability and quality for this geographic area
                """)
                
        with col_metrics[2]:
            # Show ecosystem composition for mixed areas
            if 'ecosystem_composition' in results.get('metadata', {}):
                composition = results['metadata']['ecosystem_composition']
                dominant_type = max(composition.keys(), key=lambda k: composition[k])
                st.metric("Primary Ecosystem", f"{dominant_type}")
                st.caption(f"Mixed area: {len(composition)} ecosystem types")
            else:
                st.metric("Ecosystem Type", results['ecosystem_type'])
            with st.expander("💡 Ecosystem detection method"):
                # Handle both single and mixed ecosystem displays
                if 'ecosystem_composition' in results.get('metadata', {}):
                    st.markdown("**Mixed Ecosystem Area Detected**")
                    composition = results['metadata']['ecosystem_composition']
                    
                    st.markdown("**Ecosystem Composition**:")
                    for ecosystem, proportion in composition.items():
                        st.markdown(f"- **{ecosystem}**: {proportion*100:.0f}% of area")
                    
                    st.markdown(f"**Calculation Method**: Weighted by area proportion")
                    if 'individual_ecosystem_results' in results:
                        st.markdown("**Individual Ecosystem Values**:")
                        for ecosystem, data in results['individual_ecosystem_results'].items():
                            st.markdown(f"- {ecosystem}: ${data['total_value']:,.0f}/year ({data['area_hectares']:.0f} ha)")
                else:
                    st.markdown(f"""
                    **Detected Ecosystem Type**: {results['ecosystem_type']}
                    """)
                
                st.markdown("**Detection Method**:")
                if 'detected_ecosystem' in st.session_state:
                    ecosystem_info = st.session_state.detected_ecosystem
                    st.markdown(f"""
                    - **Confidence**: {ecosystem_info.get('confidence', 0):.0%}
                    - **Coverage**: {ecosystem_info.get('coverage_percentage', 0):.0f}% of selected area
                    - **Sample Points**: {ecosystem_info.get('successful_queries', 0)} of {ecosystem_info.get('total_samples', 4)} analyzed
                    - **Source**: {ecosystem_info.get('source', 'Geographic analysis')}
                    """)
                    
                    if 'ecosystem_distribution' in ecosystem_info:
                        st.markdown("**Sample Point Distribution**:")
                        for ecosystem, data in ecosystem_info['ecosystem_distribution'].items():
                            confidence = data['confidence'] / data['count'] if data['count'] > 0 else 0
                            st.markdown(f"- {ecosystem}: {data['count']} sample points, {confidence:.0%} avg confidence")
                
                st.markdown(f"""
                **How Detection Works**:
                1. **Area-Based Sampling**: Sample density scales with area size (1 point per 100 hectares)
                2. **Grid Distribution**: Points arranged in grid pattern across your selected area  
                3. **OpenLandMap Integration**: Queries global land cover databases for each sample point
                4. **Confidence Assessment**: Based on successful detections and data source quality
                
                **Area Limits**: Maximum 10,000 hectares (100 sample points) for optimal performance
                
                **Mixed Ecosystem Handling**:
                When multiple ecosystem types are detected, the system calculates values for each type separately 
                and combines them using area-weighted proportions based on sample point distribution.
                """)
        # Show data source and methodology
        st.info(f"📊 **Data Source**: {results.get('data_source', 'ESVD/TEEB Database')} | **Regional Factor**: {results.get('regional_factor', 1.0):.2f}")
        
        with st.expander("💡 Data sources and methodology"):
            st.markdown(f"""
            **Primary Data Sources**:
            
            **ESVD (Ecosystem Services Valuation Database)**:
            - World's largest open-access ecosystem services database
            - 10,874+ peer-reviewed value estimates from 1,100+ scientific studies
            - Global coverage: 140+ countries, 15 biomes, 23 ecosystem services
            - Maintained by: Environmental Economics research community
            
            **TEEB (The Economics of Ecosystems and Biodiversity)**:
            - Integrated within ESVD coefficients
            - Focus on policy-relevant ecosystem service values
            - Emphasis on biodiversity and natural capital accounting
            
            **Regional Adjustment Factor: {results.get('regional_factor', 1.0):.2f}**:
            This factor adjusts base ESVD values for local conditions:
            - Income adjustment: Regional purchasing power differences
            - Cost of living: Local economic conditions and price levels
            - Data quality: Availability and reliability of regional studies
            
            **Standardization**:
            - All values converted to 2020 International dollars
            - Per hectare per year basis for global comparability
            - Quality assurance: Only peer-reviewed studies included
            
            **Calculation Formula**:
            Final Value = (Base ESVD Coefficient) × (Area in hectares) × (Regional Factor)
            """)
    
    # Show ecosystem services breakdown if available
    if 'esvd_results' in results:
        st.markdown("### 🌿 Ecosystem Services Breakdown")
        esvd_data = results['esvd_results']
        
        if 'provisioning' in esvd_data:
            categories = ['provisioning', 'regulating', 'cultural', 'supporting']
            cols = st.columns(4)
            
            for i, category in enumerate(categories):
                if category in esvd_data:
                    total = esvd_data[category].get('total', 0)
                    with cols[i]:
                        per_ha_category = total / results['area_ha'] if results['area_ha'] > 0 else 0
                        st.metric(
                            f"{category.title()} Services",
                            f"${total:,.0f}/year"
                        )
                        st.caption(f"${per_ha_category:.0f}/ha • {(total/results['total_value']*100):.0f}% of total" if results['total_value'] > 0 else f"${per_ha_category:.0f}/ha")
                        
                        with st.expander(f"💡 {category.title()} services breakdown"):
                            st.markdown(f"**{category.title()} Services Calculation**")
                            
                            # Show individual service calculations
                            for service, value in esvd_data[category].items():
                                if service != 'total' and value > 0:
                                    service_name = service.replace('_', ' ').title()
                                    
                                    # Get the base coefficient from ESVD
                                    from utils.esvd_integration import ESVDIntegration
                                    esvd_inst = ESVDIntegration()
                                    ecosystem_mapped = esvd_inst.map_ecosystem_type(results['ecosystem_type'])
                                    
                                    if ecosystem_mapped and category in esvd_inst.esvd_coefficients:
                                        base_coeff = esvd_inst.esvd_coefficients[category].get(service, {}).get(ecosystem_mapped, 0)
                                        regional_factor = results.get('regional_factor', 1.0)
                                        area_ha = results['area_ha']
                                        
                                        st.markdown(f"""
                                        **{service_name}**: ${value:,.0f}/year
                                        - Base ESVD coefficient: ${base_coeff}/ha/year
                                        - Area: {area_ha:,.0f} hectares
                                        - Regional adjustment factor: {regional_factor:.2f}
                                        - Calculation: ${base_coeff} × {area_ha:,.0f} ha × {regional_factor:.2f} = ${value:,.0f}/year
                                        """)
                            
                            # Add methodology explanation
                            st.markdown(f"""
                            **Methodology for {category.title()} Services:**
                            
                            These values are derived from the ESVD (Ecosystem Services Valuation Database), which contains 
                            10,874+ peer-reviewed value estimates from 1,100+ scientific studies. Each coefficient represents 
                            the economic value of ecosystem services based on:
                            
                            - **Base Coefficients**: From peer-reviewed literature in ESVD/TEEB databases
                            - **Regional Adjustment**: Accounts for local income levels, cost of living, and data quality
                            - **Standardization**: All values in 2020 International dollars per hectare per year
                            - **Quality Assurance**: Only peer-reviewed studies included in calculations
                            """)
        # Option to switch to summary view
        st.markdown("---")
        if st.button("📊 Switch to Summary View", type="secondary"):
            st.session_state['analysis_detail'] = 'Summary Analysis'
            st.rerun()
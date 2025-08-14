import streamlit as st
import folium
from streamlit_folium import st_folium, folium_static
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import numpy as np
from utils.satellite_data import SatelliteDataProcessor
from utils.natural_capital_metrics import NaturalCapitalCalculator
from utils.ecosystem_services import EcosystemServicesCalculator
from utils.visualization import create_time_series_chart, create_metrics_dashboard, create_services_dashboard
from utils.data_export import export_to_csv, export_report

# Page configuration
st.set_page_config(
    page_title="Ecosystem Valuation Engine (EVE)",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display ESVD integration status in sidebar
with st.sidebar:
    st.subheader("🗃️ Open Source Database Integration")
    
    try:
        from utils.esvd_integration import ESVDIntegration
        esvd = ESVDIntegration()
        status = esvd.validate_esvd_connection()
        
        st.success("✅ ESVD Integration Active")
        st.write(f"📊 Database Version: {status.get('database_version', 'Unknown')}")
        st.write(f"🔢 Coefficient Count: {status.get('coefficient_count', 'Unknown')}")
        st.write(f"🌍 Ecosystem Types: {status.get('ecosystem_types_supported', 'Unknown')}")
        st.write(f"🏛️ Data Quality: {status.get('data_quality', 'Unknown')}")
        
        with st.expander("📈 Database Details"):
            st.write("**ESVD (Ecosystem Services Valuation Database)**")
            st.write("- World's largest open-access database")
            st.write("- 10,000+ peer-reviewed value records")
            st.write("- 2020 International dollar standardization")
            st.write("- Regional adjustment factors applied")
            
    except Exception as e:
        st.warning("⚠️ ESVD Integration: Limited")
        st.write("Using cached coefficients from ESVD/TEEB research")
        
    st.markdown("---")
    st.subheader("📝 About EVE")
    st.write("""
    **Ecosystem Valuation Engine** measures ecosystem growth through economic valuation of four service categories:
    
    - 🥬 **Provisioning**: Food, water, timber
    - 🌡️ **Regulating**: Climate, water regulation  
    - 🎨 **Cultural**: Recreation, spiritual value
    - 🔄 **Supporting**: Soil, nutrients, habitat
    """)
    
    st.markdown("---")
    st.write("**Data Sources:**")
    st.write("• ESVD - Ecosystem Services Valuation Database")
    st.write("• TEEB - The Economics of Ecosystems and Biodiversity")
    st.write("• InVEST - Integrated Valuation of Ecosystem Services")
    st.write("• Peer-reviewed ecosystem services research")

# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []

# Main title and description
st.title("🌱 Ecosystem Valuation Engine")
st.markdown("""
**Measure the economic value of nature's benefits.** Select an area on the map to discover its annual ecosystem service value in dollars.
""")

# Help page navigation
col_nav1, col_nav2 = st.columns([4, 1])
with col_nav2:
    if st.button("❓ Help & Guide", help="Learn about ecosystem services and how to use EVE"):
        st.session_state.show_help_page = not st.session_state.get('show_help_page', False)

# Show help page if requested
if st.session_state.get('show_help_page', False):
    st.markdown("---")
    st.header("📚 Help & User Guide")
    
    help_tab1, help_tab2, help_tab3 = st.tabs(["🌍 What are Ecosystem Services?", "💡 Tips & Best Practices", "❓ Quick Help"])
    
    with help_tab1:
        from utils.user_guidance import show_ecosystem_service_explanation
        show_ecosystem_service_explanation()
    
    with help_tab2:
        from utils.user_guidance import show_tips_and_best_practices
        show_tips_and_best_practices()
    
    with help_tab3:
        from utils.user_guidance import show_quick_help
        show_quick_help()
    
    st.markdown("---")
    if st.button("🔙 Back to Analysis"):
        st.session_state.show_help_page = False
        st.rerun()
    
    st.stop()  # Don't show the rest of the interface when help is open

# Simplified sidebar for advanced settings only
with st.sidebar:
    st.header("⚙️ Advanced Settings")
    
    # Ecosystem override (simplified)
    with st.expander("🔬 Ecosystem Detection"):
        st.caption("EVE automatically detects ecosystem types. Override only if needed.")
        
        ecosystem_override = st.selectbox(
            "Force Specific Type",
            options=[None, 'forest', 'grassland', 'wetland', 'agricultural', 'coastal'],
            index=0,
            format_func=lambda x: "Auto-detect" if x is None else x.title()
        )
    
    with st.expander("📊 Analysis Detail Level"):
        analysis_detail = st.radio(
            "Choose analysis depth",
            options=["Quick Overview", "Detailed Analysis"],
            index=1,
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
    
# Initialize analyze_button as False
analyze_button = False

# Map and preview in columns
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🗺️ Select Your Area")
    
    # Create interactive map with better default view
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = st.session_state.area_coordinates
        center_lat = sum(coord[1] for coord in coords) / len(coords)
        center_lon = sum(coord[0] for coord in coords) / len(coords)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add current selection to map as a highlight
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',
            weight=3,
            fillColor='green',
            fillOpacity=0.2,
            popup="Selected Area"
        ).add_to(m)
    else:
        m = folium.Map(location=[20, 0], zoom_start=2)  # Global view
    
    # Add drawing tools with better configuration
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
            'edit': False  # Disable editing to prevent confusion - user draws new area instead
        }
    )
    draw.add_to(m)
    

    
    # Display map and capture interactions
    map_data = st_folium(m, width=700, height=400, returned_objects=["all_drawings"], key="area_map")
    
    # Process map interactions - automatically save single area selection
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        # Get the latest drawing (most recent selection)
        latest_drawing = map_data['all_drawings'][-1]
        
        if latest_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
            coordinates = latest_drawing['geometry']['coordinates'][0]
            
            # Check if this is a new selection (different from stored one)
            current_coords = st.session_state.get('area_coordinates', [])
            is_new_selection = (not current_coords or 
                              len(coordinates) != len(current_coords) or 
                              coordinates != current_coords)
            
            if is_new_selection:
                # Automatically save the new selection
                st.session_state.selected_area = {
                    'type': latest_drawing['geometry']['type'],
                    'coordinates': coordinates
                }
                st.session_state.area_coordinates = coordinates
                
                # Clear any previous analysis results since area changed
                st.session_state.analysis_results = None
                
                # Show confirmation with area size
                area_coords = np.array(coordinates)
                if len(area_coords) > 2:
                    area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                    area_ha = area_km2 * 100
                    st.success(f"✅ Area selected: {area_ha:.1f} hectares")
                else:
                    st.success(f"✅ Area selected: {len(coordinates)} points")
                    
                # Auto-refresh to show updated preview
                st.rerun()
        else:
            st.warning("Please draw a polygon or rectangle area")
    elif st.session_state.selected_area:
        # Show existing selection status
        if st.session_state.area_coordinates:
            area_coords = np.array(st.session_state.area_coordinates)
            if len(area_coords) > 2:
                area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                area_ha = area_km2 * 100
                st.info(f"📍 Current area: {area_ha:.1f} hectares (draw new area to replace)")
            else:
                st.info("📍 Area selected (draw new area to replace)")
    
    # Add clear area button for easy reset
    if st.session_state.selected_area:
        if st.button("🗑️ Clear Area", help="Remove current selection and start over"):
            st.session_state.selected_area = None
            st.session_state.area_coordinates = []
            st.session_state.analysis_results = None
            st.rerun()
    
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

# Analysis processing (after button is defined)
if analyze_button and st.session_state.selected_area and selected_metrics:
    # Show progress indicator
    from utils.user_guidance import show_progress_indicator
    
    progress_container = st.empty()
    status_container = st.empty()
    
    with progress_container.container():
        show_progress_indicator(1, 3)
        
        try:
            with status_container:
                with st.spinner("🔍 Processing satellite data and detecting ecosystems..."):
                    # Initialize processors
                    satellite_processor = SatelliteDataProcessor()
                    services_calculator = EcosystemServicesCalculator()
                    
                    # Get area boundaries
                    area_bounds = st.session_state.selected_area
                    
                    # Use dates from analysis controls
                    analysis_start = start_date if isinstance(start_date, datetime) else datetime.combine(start_date, datetime.min.time())
                    analysis_end = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.min.time())
                    
                    # Process satellite data for the selected time range
                    satellite_data = satellite_processor.get_time_series_data(
                        area_bounds, analysis_start, analysis_end
                    )
                    
                    # Update progress
                    with progress_container.container():
                        show_progress_indicator(2, 3)
                    
                    status_container.empty()
                    with status_container:
                        with st.spinner("💰 Calculating ecosystem service values..."):
                            # Use manual override if provided, otherwise use automatic detection
                            override_type = st.session_state.get('ecosystem_override')
                            
                            # Calculate ecosystem services valuation
                            services_results = services_calculator.calculate_ecosystem_services_value(
                                satellite_data, area_bounds, ecosystem_type=override_type if override_type != "auto_detect" else None
                            )
            
            # Check for errors
            if 'error' in services_results:
                st.error(f"⚠️ Analysis Error: {services_results['error']}")
                st.write("**Debug Information:**")
                st.write(f"- Ecosystem override: {override_type}")
                st.write(f"- Area bounds: {area_bounds}")
                st.write(f"- Satellite data keys: {list(satellite_data.keys()) if satellite_data else 'No data'}")
                if satellite_data:
                    eco_detection = satellite_data.get('ecosystem_detection', {})
                    multi_detection = satellite_data.get('multi_ecosystem_detection', {})
                    st.write(f"- Single detection: {eco_detection.get('detected_type', 'Unknown')}")
                    st.write(f"- Multi detection: {multi_detection.get('primary_ecosystem', 'Unknown')}")
                st.stop()
            
            # Calculate service category trends
            category_trends = services_calculator.calculate_service_category_trends(services_results)
            
            # Prepare results based on selected metrics
            results = {}
            if 'ecosystem_services_total' in selected_metrics:
                results['ecosystem_services_total'] = services_results
            
            for category in ['provisioning', 'regulating', 'cultural', 'supporting']:
                if category in selected_metrics and category in category_trends:
                    results[category] = category_trends[category]
            
            st.session_state.analysis_results = {
                'metrics': results,
                'services_data': services_results,
                'ecosystem_type': services_results.get('ecosystem_type', 'unknown'),
                'time_range': (analysis_start.date() if hasattr(analysis_start, 'date') else analysis_start, 
                               analysis_end.date() if hasattr(analysis_end, 'date') else analysis_end),
                'area_bounds': area_bounds,
                'satellite_data': satellite_data
            }
            
            # Complete analysis
            with progress_container.container():
                show_progress_indicator(3, 3)
            
            status_container.empty()
            current_value = services_results.get('current_value', 0)
            
            # Show completion message with key insight
            ecosystem_type = services_results.get('ecosystem_type', 'unknown')
            if ecosystem_type == 'multi_ecosystem':
                composition = services_results.get('ecosystem_composition', {})
                primary = services_results.get('primary_ecosystem', 'mixed')
                st.success(f"✅ Analysis complete! Multi-ecosystem area (primary: {primary}) valued at ${current_value:,.0f}/year")
            else:
                st.success(f"✅ Analysis complete! {ecosystem_type.title()} ecosystem valued at ${current_value:,.0f}/year")
                
        except Exception as e:
            progress_container.empty()
            status_container.empty()
            
            st.error(f"Analysis failed: {str(e)}")
            
            # Provide helpful error guidance
            if "ecosystem_type" in str(e).lower():
                st.info("💡 Try selecting a different area or using the manual ecosystem override in Advanced Settings.")
            elif "satellite" in str(e).lower():
                st.info("💡 This might be a temporary satellite data issue. Try again in a moment.")
            elif "area" in str(e).lower():
                st.info("💡 Try drawing a larger area (at least 10 hectares) for better results.")
            
            with st.expander("🔧 Technical Details"):
                st.write("This might be due to satellite data availability or ecosystem type configuration.")
                st.write(f"Error details: {str(e)}")

with col2:
    st.subheader("💰 Area Preview")
    
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = np.array(st.session_state.area_coordinates)
        if len(coords) > 2:
            # Calculate area
            area_km2 = abs(np.sum((coords[:-1, 0] * coords[1:, 1]) - (coords[1:, 0] * coords[:-1, 1]))) * 111.32 * 111.32 / 2
            area_ha = area_km2 * 100
            
            # Quick ecosystem detection
            from utils.satellite_data import SatelliteDataProcessor
            sat_processor = SatelliteDataProcessor()
            
            bbox = {
                'min_lat': min(coord[1] for coord in coords),
                'max_lat': max(coord[1] for coord in coords),
                'min_lon': min(coord[0] for coord in coords),
                'max_lon': max(coord[0] for coord in coords)
            }
            
            mock_time_series = [{'red_mean': 0.2, 'nir_mean': 0.3, 'green_mean': 0.15, 'swir1_mean': 0.25}]
            detection_result = sat_processor._detect_ecosystem_type(bbox, mock_time_series)
            ecosystem_type = detection_result.get('detected_type', 'forest')
            confidence = detection_result.get('confidence', 0.5)
            
            # Estimate value
            base_values = {'forest': 4726, 'grassland': 232, 'wetland': 32423, 'agricultural': 129, 'coastal': 5726}
            estimated_value = base_values.get(ecosystem_type, 2000) * area_ha
            
            # Display metrics in a cleaner way
            st.metric("📏 Area Size", f"{area_ha:.1f} hectares")
            
            confidence_emoji = "🎯" if confidence > 0.8 else "📍" if confidence > 0.6 else "❓"
            st.metric(
                "🌍 Ecosystem Type", 
                ecosystem_type.title(),
                f"{confidence_emoji} {confidence:.0%} confidence"
            )
            
            st.metric(
                "💰 Estimated Value", 
                f"${estimated_value:,.0f}/year",
                f"${estimated_value/area_ha:,.0f}/ha/year"
            )
            
            # Show what this value represents
            st.info("This includes all ecosystem services: food, water, climate regulation, recreation, and habitat.")
            
            # Quick comparison
            if ecosystem_type == 'wetland':
                st.success("💧 Wetlands provide exceptional water regulation and habitat services!")
            elif ecosystem_type == 'forest':
                st.success("🌲 Forests excel at carbon storage and biodiversity support!")
            elif ecosystem_type == 'coastal':
                st.success("🏖️ Coastal areas provide storm protection and recreation value!")
    else:
        st.info("Draw an area on the map to see preview")

# Define service category names for display
service_categories = {
    'ecosystem_services_total': '💰 Total Ecosystem Value',
    'provisioning': '🌾 Provisioning Services', 
    'regulating': '🌡️ Regulating Services',
    'cultural': '🎨 Cultural Services',
    'supporting': '🌱 Supporting Services'
}

# Analysis Results Section
if st.session_state.analysis_results:
    st.header("📈 Analysis Results")
    
    results = st.session_state.analysis_results
    metrics_data = results['metrics']
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["💰 Value Dashboard", "📈 Service Trends", "🔍 Service Breakdown", "📊 Detailed Analysis", "📚 Data Sources", "📤 Export"])
    
    with tab1:
        st.subheader("💰 Ecosystem Services Value Dashboard")
        
        # Display key economic metrics
        if 'services_data' in results and results['services_data']:
            services_data = results['services_data']
            
            # Main value metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_value = services_data.get('current_value', 0)
                previous_value = services_data.get('previous_value', current_value)
                change = current_value - previous_value
                st.metric(
                    "Total Annual Value",
                    f"${current_value:,.0f}",
                    f"${change:+,.0f}" if change != 0 else None
                )
            
            with col2:
                value_per_ha = services_data.get('value_per_hectare', 0)
                detected_ecosystem = services_data.get('detected_ecosystem_type', 'Unknown')
                st.metric(
                    "Value per Hectare",
                    f"${value_per_ha:,.0f}/ha/year"
                )
                
                # Show ecosystem composition
                if services_data.get('ecosystem_type') == 'multi_ecosystem':
                    # Multi-ecosystem display
                    composition = services_data.get('ecosystem_composition', {})
                    primary = services_data.get('primary_ecosystem', 'Unknown')
                    diversity_metrics = services_data.get('diversity_metrics', {})
                    
                    st.metric(
                        "🌍 Multi-Ecosystem Area",
                        f"Primary: {primary.title()}",
                        f"{len(composition)} ecosystem types"
                    )
                else:
                    # Single ecosystem display
                    ecosystem_detection = services_data.get('ecosystem_detection', {})
                    if ecosystem_detection:
                        detected_type = ecosystem_detection.get('detected_type', 'Unknown')
                        confidence = ecosystem_detection.get('confidence', 0)
                        
                        confidence_icon = "🎯" if confidence > 0.8 else "📍" if confidence > 0.6 else "❓"
                        st.metric(
                            f"{confidence_icon} Detected Ecosystem",
                            f"{detected_type.title()}",
                            f"{confidence:.0%} confidence"
                        )
                    else:
                        st.metric("Ecosystem Type", detected_ecosystem.title())
            
            with col3:
                annual_change = services_data.get('annual_change_usd', 0)
                st.metric(
                    "Annual Change",
                    f"${annual_change:+,.0f}/year"
                )
            
            with col4:
                area_ha = services_data.get('area_hectares', 0)
                ecosystem = services_data.get('ecosystem_type', 'unknown')
                st.metric(
                    "Area & Type",
                    f"{area_ha:.1f} ha",
                    f"{ecosystem.title()}"
                )
            
            # Service category breakdown
            if 'service_breakdown' in services_data:
                st.subheader("Service Categories Distribution")
                breakdown = services_data['service_breakdown']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Provisioning", f"{breakdown.get('provisioning_percent', 0):.1f}%")
                with col2:
                    st.metric("Regulating", f"{breakdown.get('regulating_percent', 0):.1f}%")
                with col3:
                    st.metric("Cultural", f"{breakdown.get('cultural_percent', 0):.1f}%")
                with col4:
                    st.metric("Supporting", f"{breakdown.get('supporting_percent', 0):.1f}%")
            
            # Multi-ecosystem composition display
            if services_data.get('ecosystem_type') == 'multi_ecosystem':
                st.subheader("🌍 Ecosystem Composition Analysis")
                
                composition = services_data.get('ecosystem_composition', {})
                ecosystem_results = services_data.get('ecosystem_results', {})
                diversity_metrics = services_data.get('diversity_metrics', {})
                
                # Ecosystem composition breakdown
                col_comp1, col_comp2 = st.columns(2)
                
                with col_comp1:
                    st.write("**Ecosystem Type Distribution:**")
                    for eco_type, percentage in sorted(composition.items(), key=lambda x: x[1], reverse=True):
                        st.write(f"• {eco_type.title()}: {percentage:.1f}%")
                
                with col_comp2:
                    st.write("**Diversity Metrics:**")
                    st.write(f"• Shannon Diversity: {diversity_metrics.get('shannon_diversity', 0):.2f}")
                    st.write(f"• Simpson Diversity: {diversity_metrics.get('simpson_diversity', 0):.2f}")
                    st.write(f"• Homogeneity Index: {diversity_metrics.get('homogeneity_index', 0):.1f}%")
                
                # Individual ecosystem values
                st.write("**Economic Value by Ecosystem Type:**")
                
                eco_cols = st.columns(min(len(ecosystem_results), 4))
                for i, (eco_type, results) in enumerate(ecosystem_results.items()):
                    with eco_cols[i % 4]:
                        current_val = results.get('current_value', 0)
                        area_pct = results.get('area_percentage', 0)
                        value_per_ha = results.get('value_per_hectare', 0)
                        
                        st.metric(
                            f"{eco_type.title()}",
                            f"${current_val:,.0f}/year",
                            f"{area_pct:.1f}% of area"
                        )
                        st.caption(f"${value_per_ha:,.0f}/ha/year")
            
            # Valuation summary and data source
            if 'valuation_summary' in services_data:
                st.info(f"📊 **Summary:** {services_data['valuation_summary']}")
            
            # Show detailed data source information
            if 'data_source' in services_data:
                data_source = services_data['data_source']
                esvd_metadata = services_data.get('esvd_metadata', {})
                
                st.subheader("📚 Data Sources & Methodology")
                
                if 'ESVD' in data_source:
                    st.success(f"**Primary Data Source:** {data_source}")
                    
                    # Detailed source attribution
                    st.info("""
                    **Source Attribution:**
                    
                    **ESVD (Ecosystem Services Valuation Database)**
                    - World's largest open-access database for ecosystem service valuations
                    - 10,874+ value records from 1,100+ peer-reviewed studies
                    - Maintained by Foundation for Sustainable Development (FSD)
                    - Website: https://www.esvd.net/
                    - Citation: Brander, L.M. et al. (2024). Ecosystem Services Valuation Database (ESVD)
                    
                    **TEEB (The Economics of Ecosystems and Biodiversity)**
                    - Original database with 1,350+ value estimates from 320+ publications
                    - Covering 300+ case studies across all biomes and continents
                    - Website: https://teebweb.org/
                    - Integration through ESVD platform
                    
                    **InVEST Framework (Natural Capital Project)**
                    - Methodological framework for ecosystem services modeling
                    - Stanford University, WWF, The Nature Conservancy
                    - Website: https://naturalcapitalproject.stanford.edu/
                    """)
                    
                    # Technical details
                    with st.expander("🔬 Technical Methodology"):
                        st.write(f"""
                        **Value Standardization:**
                        - Currency: 2020 International Dollars (Int$) per hectare per year
                        - Regional adjustment factor: {services_data.get('regional_adjustment', 1.0):.2f}x
                        - Database version: {services_data.get('database_version', 'Unknown')}
                        
                        **Coefficient Categories:**
                        - Provisioning Services: Food production, fresh water, timber/fiber, genetic resources
                        - Regulating Services: Climate regulation, water regulation, erosion control, pollution control
                        - Cultural Services: Recreation, aesthetic value, spiritual value, educational value
                        - Supporting Services: Soil formation, nutrient cycling, primary production, habitat provision
                        
                        **Quality Adjustments:**
                        - Satellite-derived ecosystem health indicators (NDVI, spectral analysis)
                        - Temporal ecosystem condition changes
                        - Geographic and climatic factors
                        """)
                else:
                    st.warning(f"**Data Source:** {data_source}")
                    st.info("""
                    **Fallback Source Attribution:**
                    - Using cached coefficients derived from ESVD/TEEB research
                    - Values based on established ecosystem services literature
                    - Standardized to comparable units for analysis
                    """)
            
            # Add citation recommendation
            st.subheader("📖 Recommended Citation")
            st.code("""
When using results from this analysis, please cite:

Primary Database:
Brander, L.M., de Groot, R., Guisado Goñi, V., van 't Hoff, V., Schägner, P., 
Solomonides, S., McVittie, A., Eppink, F., Sposato, M., Do, L., Ghermandi, A., 
and Sinclair, M. (2024). Ecosystem Services Valuation Database (ESVD). 
Foundation for Sustainable Development and Brander Environmental Economics.

Analysis Tool:
Ecosystem Valuation Engine (EVE) - Natural Capital Measurement Tool with 
ESVD Integration [Computer software]. (2024).
            """, language="text")
        
        elif metrics_data:
            # Fallback to regular metrics display
            metric_cols = st.columns(len(metrics_data))
            
            for i, (metric_name, metric_data) in enumerate(metrics_data.items()):
                with metric_cols[i]:
                    if isinstance(metric_data, dict) and 'current_value' in metric_data:
                        current_val = metric_data['current_value']
                        previous_val = metric_data.get('previous_value', current_val)
                        change = current_val - previous_val if previous_val != 0 else 0
                        
                        st.metric(
                            service_categories.get(metric_name, metric_name),
                            f"${current_val:,.0f}" if 'value' in metric_name else f"{current_val:.3f}",
                            f"${change:+,.0f}" if 'value' in metric_name and change != 0 else f"{change:+.3f}" if change != 0 else None
                        )
    
    with tab2:
        st.subheader("📈 Ecosystem Services Value Trends")
        
        if 'services_data' in results and 'time_series' in results['services_data']:
            services_time_series = results['services_data']['time_series']
            
            # Total value trend
            dates = [datetime.fromisoformat(point['date'].replace('Z', '')) for point in services_time_series]
            total_values = [point['total_value'] for point in services_time_series]
            
            # Create time series chart for total value
            ts_fig = create_time_series_chart(
                [{'date': point['date'], 'value': point['total_value'], 'quality': 'good'} 
                 for point in services_time_series],
                'total_ecosystem_value',
                'Total Ecosystem Services Value (USD/year)'
            )
            st.plotly_chart(ts_fig, use_container_width=True)
            
            # Service categories trends
            st.subheader("Service Categories Over Time")
            
            # Create comparison chart for service categories
            category_data = {}
            for point in services_time_series:
                date = point['date']
                for category in ['provisioning', 'regulating', 'cultural', 'supporting']:
                    if category not in category_data:
                        category_data[category] = []
                    category_data[category].append({
                        'date': date,
                        'value': point.get(category, {}).get('total', 0)
                    })
            
            # Display individual category trends
            selected_category = st.selectbox(
                "Select service category for detailed trend:",
                options=['provisioning', 'regulating', 'cultural', 'supporting'],
                format_func=lambda x: service_categories[x]
            )
            
            if selected_category in category_data:
                category_fig = create_time_series_chart(
                    category_data[selected_category],
                    selected_category,
                    service_categories[selected_category]
                )
                st.plotly_chart(category_fig, use_container_width=True)
                
                # Show trend analysis
                values = [d['value'] for d in category_data[selected_category]]
                if len(values) > 1:
                    trend = np.polyfit(range(len(values)), values, 1)[0]
                    annual_trend = trend * 365
                    trend_direction = "📈 Increasing" if trend > 100 else "📉 Decreasing" if trend < -100 else "➡️ Stable"
                    st.write(f"**{selected_category.title()} Services Trend:** {trend_direction}")
                    st.write(f"**Annual Change Rate:** ${annual_trend:+,.0f}/year")
        
        elif metrics_data:
            # Fallback for individual metrics
            selected_ts_metric = st.selectbox(
                "Select metric for time series analysis:",
                options=list(metrics_data.keys()),
                format_func=lambda x: service_categories.get(x, x)
            )
            
            if selected_ts_metric in metrics_data:
                metric_data = metrics_data[selected_ts_metric]
                if isinstance(metric_data, dict) and 'time_series' in metric_data:
                    ts_fig = create_time_series_chart(
                        metric_data['time_series'], 
                        selected_ts_metric,
                        service_categories.get(selected_ts_metric, selected_ts_metric)
                    )
                    st.plotly_chart(ts_fig, use_container_width=True)
    
    with tab3:
        st.subheader("🔍 Service Categories Breakdown")
        
        if 'services_data' in results and 'time_series' in results['services_data']:
            # Get the latest time point for detailed breakdown
            latest_point = results['services_data']['time_series'][-1]
            
            # Display each service category in detail
            categories = ['provisioning', 'regulating', 'cultural', 'supporting']
            
            for category in categories:
                if category in latest_point:
                    category_data = latest_point[category]
                    with st.expander(f"💰 {service_categories[category]} - ${category_data.get('total', 0):,.0f}/year"):
                        
                        # Show individual services within category
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Individual Services:**")
                            for service, value in category_data.items():
                                if service != 'total' and isinstance(value, (int, float)):
                                    st.write(f"- {service.replace('_', ' ').title()}: ${value:,.0f}/year")
                        
                        with col2:
                            st.write("**Category Statistics:**")
                            total_value = category_data.get('total', 0)
                            ecosystem_total = latest_point.get('total_value', 1)
                            percentage = (total_value / ecosystem_total * 100) if ecosystem_total > 0 else 0
                            
                            st.write(f"- Total Category Value: ${total_value:,.0f}/year")
                            st.write(f"- Percentage of Total: {percentage:.1f}%")
                            st.write(f"- Value per Hectare: ${total_value / results['services_data'].get('area_hectares', 1):,.0f}/ha/year")
                            
                            # Show ecosystem quality impact
                            quality = latest_point.get('ecosystem_quality', 'unknown')
                            st.write(f"- Ecosystem Quality: {quality.title()}")
        
        else:
            # Fallback for individual metrics
            for metric_name, metric_data in metrics_data.items():
                with st.expander(f"📊 {service_categories.get(metric_name, metric_name)}"):
                    if isinstance(metric_data, dict):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Current Statistics:**")
                            for key, value in metric_data.items():
                                if key not in ['time_series', 'spatial_data']:
                                    if isinstance(value, (int, float)):
                                        display_value = f"${value:,.0f}" if 'value' in key else f"{value:.4f}"
                                        st.write(f"- {key.replace('_', ' ').title()}: {display_value}")
                                    else:
                                        st.write(f"- {key.replace('_', ' ').title()}: {value}")
                        
                        with col2:
                            if 'spatial_data' in metric_data and metric_data['spatial_data']:
                                st.write("**Additional Details:**")
                                spatial_stats = metric_data['spatial_data']
                                for key, value in spatial_stats.items():
                                    if isinstance(value, (int, float)):
                                        st.write(f"- {key.replace('_', ' ').title()}: {value:.4f}")
                                    else:
                                        st.write(f"- {key.replace('_', ' ').title()}: {value}")
    
    with tab4:
        st.subheader("📊 Detailed Technical Analysis")
        
        if 'services_data' in results:
            services_data = results['services_data']
            
            # Technical metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Valuation Methodology:**")
                st.write(f"- Ecosystem Type: {services_data.get('ecosystem_type', 'Unknown').title()}")
                st.write(f"- Area: {services_data.get('area_hectares', 0):.2f} hectares")
                st.write(f"- Analysis Period: {len(services_data.get('time_series', []))} time points")
                
                # Show trend statistics
                trend = services_data.get('trend_slope', 0)
                if trend != 0:
                    trend_direction = "Positive" if trend > 0 else "Negative"
                    st.write(f"- Value Trend: {trend_direction} (${trend*365:+,.0f}/year)")
                
            with col2:
                st.write("**Data Quality Assessment:**")
                if 'time_series' in services_data:
                    time_series = services_data['time_series']
                    quality_counts = {}
                    for point in time_series:
                        quality = point.get('ecosystem_quality', 'unknown')
                        quality_counts[quality] = quality_counts.get(quality, 0) + 1
                    
                    for quality, count in quality_counts.items():
                        percentage = (count / len(time_series)) * 100
                        st.write(f"- {quality.title()}: {count} points ({percentage:.1f}%)")
            
            # Show coefficient information and ESVD integration status
            st.write("**Economic Valuation Basis:**")
            
            esvd_metadata = services_data.get('esvd_metadata', {})
            database_version = services_data.get('database_version', 'Unknown')
            data_source = services_data.get('data_source', 'Unknown')
            
            if 'ESVD' in data_source:
                st.success(f"""
                **✅ ESVD Integration Active**
                - Source: Ecosystem Services Valuation Database (ESVD) + TEEB Database
                - Database Version: {database_version}
                - Regional adjustment applied: {services_data.get('regional_adjustment', 1.0):.2f}x
                - Price level: 2020 International dollars
                - Values from {esvd_metadata.get('coefficient_count', '10,000+')} peer-reviewed studies
                - Geographic coverage: {esvd_metadata.get('ecosystem_types_supported', '9')} ecosystem types
                """)
                
                # Show specific coefficient sources used
                with st.expander("📊 Coefficient Sources Used in This Analysis"):
                    st.write(f"""
                    **For {ecosystem_type.title()} Ecosystem:**
                    
                    **Provisioning Services:**
                    - Food production values from {esvd_metadata.get('coefficient_count', '500+')} agricultural/forest studies
                    - Fresh water values from wetland and forest watershed studies
                    - Timber/fiber values from forestry economic studies
                    - Genetic resources from biodiversity valuation research
                    
                    **Regulating Services:**
                    - Climate regulation from carbon sequestration studies (high confidence)
                    - Water regulation from watershed management research
                    - Erosion control from soil conservation studies
                    - Pollution control from air/water quality improvement studies
                    
                    **Cultural Services:**
                    - Recreation values from travel cost and contingent valuation studies
                    - Aesthetic values from hedonic pricing and stated preference studies
                    - Spiritual/educational values from cultural ecosystem service research
                    
                    **Supporting Services:**
                    - Soil formation from agricultural productivity studies
                    - Nutrient cycling from ecosystem function research
                    - Habitat provision from biodiversity conservation studies
                    
                    All values adjusted for local ecosystem quality using satellite indicators.
                    """)
            else:
                st.info(f"""
                **📊 Valuation Methodology**
                - Source: {data_source} (ESVD/TEEB-derived coefficients)
                - Values from established ecosystem services research literature
                - Adjusted for ecosystem quality based on satellite indicators
                - Time series analysis tracks economic value changes over time
                """)
            
            # ESVD database status
            if st.button("🔍 Check ESVD Database Status"):
                with st.spinner("Checking ESVD integration status..."):
                    from utils.esvd_integration import ESVDIntegration
                    esvd = ESVDIntegration()
                    status = esvd.validate_esvd_connection()
                    
                    st.write("**ESVD Database Status:**")
                    for key, value in status.items():
                        icon = "✅" if value else "❌" if isinstance(value, bool) else "ℹ️"
                        st.write(f"{icon} {key.replace('_', ' ').title()}: {value}")
        
    with tab5:
        st.subheader("📚 Data Sources & Methodology")
        
        if 'services_data' in results:
            services_data = results['services_data']
            data_source = services_data.get('data_source', 'Unknown')
            esvd_metadata = services_data.get('esvd_metadata', {})
            
            # Primary source attribution
            st.success("**Primary Data Sources Used in This Analysis**")
            
            if 'ESVD' in data_source:
                # ESVD/TEEB integration details
                st.markdown("""
                ### 🗃️ ESVD (Ecosystem Services Valuation Database)
                **Primary Source for Economic Coefficients**
                - **Database**: World's largest open-access ecosystem services valuation database
                - **Content**: 10,874+ value records from 1,100+ peer-reviewed studies
                - **Maintainer**: Foundation for Sustainable Development (FSD)
                - **Website**: https://www.esvd.net/
                - **Geographic Coverage**: 140+ countries across all continents
                - **Standardization**: 2020 International dollars per hectare per year
                
                ### 🌍 TEEB (The Economics of Ecosystems and Biodiversity)
                **Secondary Source Integration**
                - **Database**: 1,350+ value estimates from 320+ publications
                - **Coverage**: 300+ case studies across all biomes
                - **Website**: https://teebweb.org/
                - **Integration**: Values incorporated through ESVD platform
                
                ### 🔬 InVEST Framework
                **Methodological Foundation**
                - **Organization**: Natural Capital Project (Stanford, WWF, The Nature Conservancy)
                - **Purpose**: Ecosystem services modeling framework
                - **Website**: https://naturalcapitalproject.stanford.edu/
                """)
                
                # Show specific methodology for this analysis
                st.markdown("### 📊 This Analysis Methodology")
                ecosystem_type = results.get('ecosystem_type', 'Unknown')
                
                if ecosystem_type == 'multi_ecosystem':
                    services_data = results.get('services_data', {})
                    composition = services_data.get('ecosystem_composition', {})
                    primary = services_data.get('primary_ecosystem', 'Unknown')
                    
                    st.write(f"""
                    **Multi-Ecosystem Analysis**
                    - **Primary Ecosystem**: {primary.title()}
                    - **Ecosystem Types Present**: {', '.join([eco.title() for eco in composition.keys()])}
                    - **Analysis Method**: Spatial grid analysis with composition weighting
                    - **Grid Resolution**: 4x4 sub-areas analyzed individually
                    - **Value Calculation**: Separate ESVD coefficients applied to each ecosystem type based on area coverage
                    """)
                else:
                    st.write(f"""
                    **Ecosystem Type Analyzed**: {ecosystem_type.title()}
                
                **Service Categories & Data Sources**:
                
                **🥬 Provisioning Services**
                - Food production: Agricultural productivity studies from ESVD
                - Fresh water: Watershed and wetland valuation studies
                - Timber/fiber: Forest resource economic studies
                - Genetic resources: Biodiversity conservation research
                
                **🌡️ Regulating Services**
                - Climate regulation: Carbon sequestration and storage studies
                - Water regulation: Watershed management and flood control research
                - Erosion control: Soil conservation economic studies
                - Pollution control: Air and water quality improvement studies
                
                **🎨 Cultural Services**
                - Recreation: Travel cost method and contingent valuation studies
                - Aesthetic value: Hedonic pricing and stated preference research
                - Spiritual/educational: Cultural ecosystem service valuations
                
                **🔄 Supporting Services**
                - Soil formation: Agricultural productivity studies
                - Nutrient cycling: Ecosystem function research
                - Habitat provision: Biodiversity conservation studies
                """)
                
                # Technical details
                st.markdown("### ⚙️ Technical Implementation")
                st.write(f"""
                - **Regional Adjustment Factor**: {services_data.get('regional_adjustment', 1.0):.2f}x
                - **Database Version**: {services_data.get('database_version', 'Unknown')}
                - **Data Quality Level**: {esvd_metadata.get('data_quality', 'Unknown')}
                - **Satellite Integration**: NDVI and spectral health indicators applied
                - **Time Series**: Economic value tracking over selected period
                """)
            
            else:
                st.info(f"""
                **Data Source**: {data_source}
                
                This analysis uses cached coefficients derived from ESVD/TEEB research.
                Values are based on established ecosystem services literature and 
                standardized for comparative analysis.
                """)
            
            # Citation information
            st.markdown("### 📖 Required Citations")
            st.markdown("""
            **When using results from this analysis, please cite:**
            
            **Primary Database:**
            ```
            Brander, L.M., de Groot, R., Guisado Goñi, V., van 't Hoff, V., Schägner, P., 
            Solomonides, S., McVittie, A., Eppink, F., Sposato, M., Do, L., Ghermandi, A., 
            and Sinclair, M. (2024). Ecosystem Services Valuation Database (ESVD). 
            Foundation for Sustainable Development and Brander Environmental Economics.
            ```
            
            **Analysis Tool:**
            ```
            Ecosystem Valuation Engine (EVE) - Natural Capital Measurement Tool with 
            ESVD Integration [Computer software]. (2024).
            ```
            """)
            
            # Data quality and limitations
            with st.expander("⚠️ Data Quality & Limitations"):
                st.write("""
                **Data Quality Considerations:**
                - All economic coefficients from peer-reviewed research
                - Values standardized to 2020 International dollars
                - Regional adjustments applied based on geographic location
                - Ecosystem quality adjustments from satellite indicators
                
                **Limitations:**
                - Economic values represent monetary estimates, not market prices
                - Results are indicative and should be used with local context
                - Satellite data quality affects temporal precision
                - Regional adjustments are approximate
                
                **Best Practices:**
                - Use results for comparative analysis and trend identification
                - Consider local economic conditions when interpreting values
                - Combine with local knowledge and stakeholder input
                - Validate with ground-truth data when available
                """)
    
    with tab6:
        st.subheader("Export Data and Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Export Options:**")
            
            if st.button("📊 Export Metrics as CSV"):
                csv_data = export_to_csv(results)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name=f"natural_capital_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            if st.button("📄 Generate PDF Report"):
                try:
                    pdf_data = export_report(results, st.session_state.selected_area)
                    st.download_button(
                        label="💾 Download Report",
                        data=pdf_data,
                        file_name=f"natural_capital_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {str(e)}")
                    st.info("CSV export is available as an alternative.")
        
        with col2:
            st.write("**Analysis Summary:**")
            st.json({
                'analysis_date': datetime.now().isoformat(),
                'time_range': {
                    'start': results['time_range'][0].isoformat(),
                    'end': results['time_range'][1].isoformat()
                },
                'metrics_calculated': list(metrics_data.keys()),
                'area_type': st.session_state.selected_area['type'] if st.session_state.selected_area else 'None'
            })

# Footer
st.markdown("---")
st.markdown("""
**Ecosystem Valuation Engine (EVE)** - Built with Streamlit for environmental research and ecosystem monitoring.  
For questions or support, please refer to the documentation or contact your system administrator.
""")

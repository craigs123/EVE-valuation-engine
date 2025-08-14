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
st.title("🌱 Ecosystem Valuation Engine (EVE)")
st.markdown("""
EVE measures ecosystem growth through economic valuation of ecosystem services: **provisioning** (food, water, timber), 
**regulating** (climate, water, erosion control), **cultural** (recreation, spiritual value), and **supporting** (soil formation, nutrient cycling).
Select an area on the map below to begin valuation.
""")

# Sidebar for controls
with st.sidebar:
    st.header("Analysis Parameters")
    
    # Time range selection
    st.subheader("Time Range")
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=365),
        max_value=datetime.now()
    )
    end_date = st.date_input(
        "End Date",
        value=datetime.now(),
        max_value=datetime.now()
    )
    
    # Ecosystem type selection
    st.subheader("Ecosystem Configuration")
    ecosystem_type = st.selectbox(
        "Select Ecosystem Type",
        options=['forest', 'grassland', 'wetland', 'agricultural', 'coastal'],
        index=0,
        help="This affects the baseline valuation coefficients for ecosystem services"
    )
    
    # Store ecosystem type in session state for preview calculations
    st.session_state.ecosystem_type = ecosystem_type
    
    # Service categories selection
    st.subheader("Ecosystem Services Categories")
    service_categories = {
        'ecosystem_services_total': 'Total Ecosystem Services Value',
        'provisioning': 'Provisioning Services (food, water, timber)',
        'regulating': 'Regulating Services (climate, water regulation)',
        'cultural': 'Cultural Services (recreation, aesthetic)',
        'supporting': 'Supporting Services (soil, nutrients, habitat)'
    }
    
    selected_metrics = st.multiselect(
        "Select Service Categories to Analyze",
        options=list(service_categories.keys()),
        default=['ecosystem_services_total', 'provisioning', 'regulating'],
        format_func=lambda x: service_categories[x]
    )
    
    # Analysis button
    if st.button("💰 Calculate Ecosystem Services Value", type="primary", disabled=not st.session_state.selected_area):
        if st.session_state.selected_area and selected_metrics:
            with st.spinner("Processing satellite data and calculating ecosystem services values..."):
                try:
                    # Initialize processors
                    satellite_processor = SatelliteDataProcessor()
                    services_calculator = EcosystemServicesCalculator()
                    
                    # Get area boundaries
                    area_bounds = st.session_state.selected_area
                    
                    # Process satellite data for the selected time range
                    satellite_data = satellite_processor.get_time_series_data(
                        area_bounds, start_date, end_date
                    )
                    
                    # Calculate ecosystem services valuation
                    services_results = services_calculator.calculate_ecosystem_services_value(
                        satellite_data, area_bounds, ecosystem_type
                    )
                    
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
                        'ecosystem_type': ecosystem_type,
                        'time_range': (start_date, end_date),
                        'area_bounds': area_bounds,
                        'satellite_data': satellite_data
                    }
                    
                    current_value = services_results.get('current_value', 0)
                    st.success(f"✅ Ecosystem services valuation completed! Total value: ${current_value:,.0f}/year")
                    
                except Exception as e:
                    st.error(f"Valuation failed: {str(e)}")
                    st.error("This might be due to satellite data availability or ecosystem type configuration.")
    
    # Clear analysis button
    if st.button("🗑️ Clear Analysis"):
        st.session_state.analysis_results = None
        st.session_state.selected_area = None
        st.session_state.area_coordinates = []
        st.rerun()

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 Area Selection")
    
    # Create interactive map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
    
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
        edit_options={'edit': True}
    )
    draw.add_to(m)
    
    # Display map and capture interactions
    map_data = st_folium(m, width=700, height=500, returned_objects=["all_drawings"])
    
    # Process map interactions
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        # Get the latest drawing
        latest_drawing = map_data['all_drawings'][-1]
        if latest_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
            coordinates = latest_drawing['geometry']['coordinates'][0]
            st.session_state.selected_area = {
                'type': latest_drawing['geometry']['type'],
                'coordinates': coordinates
            }
            st.session_state.area_coordinates = coordinates
            
            # Display selected area info
            st.success(f"✅ Area selected: {latest_drawing['geometry']['type']}")
            st.write(f"Coordinates: {len(coordinates)} points")

with col2:
    st.subheader("💰 Economic Value Preview")
    
    if st.session_state.selected_area and st.session_state.area_coordinates:
        # Calculate basic area metrics
        coords = np.array(st.session_state.area_coordinates)
        if len(coords) > 2:
            # Simple area calculation (approximate)
            area_km2 = abs(np.sum((coords[:-1, 0] * coords[1:, 1]) - (coords[1:, 0] * coords[:-1, 1]))) * 111.32 * 111.32 / 2
            area_ha = area_km2 * 100
            
            # Quick valuation estimate based on ecosystem type
            ecosystem_type = st.session_state.get('ecosystem_type', 'forest')
            if True:  # Always show estimate
                base_values = {
                    'forest': 4726,  # USD/ha/year
                    'grassland': 232,
                    'wetland': 32423,
                    'agricultural': 129,
                    'coastal': 5726
                }
                estimated_value = base_values.get(ecosystem_type, 2000) * area_ha
                
                col2a, col2b = st.columns(2)
                with col2a:
                    st.metric("Area", f"{area_ha:.1f} ha")
                    st.metric("Ecosystem Type", ecosystem_type.title())
                with col2b:
                    st.metric("Est. Annual Value", f"${estimated_value:,.0f}")
                    st.metric("Value per Hectare", f"${estimated_value/area_ha:,.0f}")
                
                st.info("💡 Run full analysis to get detailed breakdown by service categories and time trends")
    else:
        st.info("👆 Select an area on the map to see economic value preview")

# Analysis Results Section
if st.session_state.analysis_results:
    st.header("📈 Analysis Results")
    
    results = st.session_state.analysis_results
    metrics_data = results['metrics']
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Value Dashboard", "📈 Service Trends", "🔍 Service Breakdown", "📊 Detailed Analysis", "📤 Export"])
    
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
                st.metric(
                    "Value per Hectare",
                    f"${value_per_ha:,.0f}/ha/year"
                )
            
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
            
            # Valuation summary and data source
            if 'valuation_summary' in services_data:
                st.info(f"📊 **Summary:** {services_data['valuation_summary']}")
            
            # Show data source information
            if 'data_source' in services_data:
                data_source = services_data['data_source']
                if 'ESVD' in data_source:
                    st.success(f"✅ **Data Source:** {data_source} - Using peer-reviewed open source coefficients")
                else:
                    st.warning(f"⚠️ **Data Source:** {data_source} - Consider enabling ESVD integration")
        
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
                - Using open source Ecosystem Services Valuation Database coefficients
                - Database Version: {database_version}
                - Regional adjustment applied: {services_data.get('regional_adjustment', 1.0):.2f}x
                - Price level: 2020 International dollars
                - Values based on {esvd_metadata.get('coefficient_count', '9,000+')} peer-reviewed studies
                """)
            else:
                st.info(f"""
                **📊 Valuation Methodology**
                - Source: {data_source}
                - Values adjusted for ecosystem quality based on satellite indicators
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

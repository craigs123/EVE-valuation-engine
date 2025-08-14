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
from utils.visualization import create_time_series_chart, create_metrics_dashboard
from utils.data_export import export_to_csv, export_report

# Page configuration
st.set_page_config(
    page_title="Natural Capital Measurement Tool",
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

# Main title and description
st.title("🌱 Natural Capital Measurement Tool")
st.markdown("""
This tool helps environmental researchers track ecosystem growth and natural capital using satellite data and geospatial analysis.
Select an area on the map below to begin analysis.
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
    
    # Metrics selection
    st.subheader("Natural Capital Metrics")
    metrics_options = {
        'NDVI': 'Normalized Difference Vegetation Index',
        'forest_cover': 'Forest Cover Percentage',
        'carbon_storage': 'Carbon Storage Estimates',
        'water_quality': 'Water Quality Proxies',
        'biodiversity_index': 'Biodiversity Indicators'
    }
    
    selected_metrics = st.multiselect(
        "Select Metrics to Calculate",
        options=list(metrics_options.keys()),
        default=['NDVI', 'forest_cover'],
        format_func=lambda x: metrics_options[x]
    )
    
    # Analysis button
    if st.button("🔍 Run Analysis", type="primary", disabled=not st.session_state.selected_area):
        if st.session_state.selected_area and selected_metrics:
            with st.spinner("Processing satellite data and calculating metrics..."):
                try:
                    # Initialize processors
                    satellite_processor = SatelliteDataProcessor()
                    metrics_calculator = NaturalCapitalCalculator()
                    
                    # Get area boundaries
                    area_bounds = st.session_state.selected_area
                    
                    # Process satellite data for the selected time range
                    satellite_data = satellite_processor.get_time_series_data(
                        area_bounds, start_date, end_date
                    )
                    
                    # Calculate natural capital metrics
                    results = {}
                    for metric in selected_metrics:
                        results[metric] = metrics_calculator.calculate_metric(
                            metric, satellite_data, area_bounds
                        )
                    
                    st.session_state.analysis_results = {
                        'metrics': results,
                        'time_range': (start_date, end_date),
                        'area_bounds': area_bounds,
                        'satellite_data': satellite_data
                    }
                    
                    st.success("Analysis completed successfully!")
                    
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    st.error("This might be due to satellite data availability or API limitations.")
    
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
    st.subheader("📊 Quick Metrics")
    
    if st.session_state.selected_area and st.session_state.area_coordinates:
        # Calculate basic area metrics
        coords = np.array(st.session_state.area_coordinates)
        if len(coords) > 2:
            # Simple area calculation (approximate)
            area_km2 = abs(np.sum((coords[:-1, 0] * coords[1:, 1]) - (coords[1:, 0] * coords[:-1, 1]))) * 111.32 * 111.32 / 2
            
            col2a, col2b = st.columns(2)
            with col2a:
                st.metric("Selected Area", f"{area_km2:.2f} km²")
            with col2b:
                st.metric("Coordinates", f"{len(coords)} points")
            
            # Show coordinate bounds
            if len(coords) > 0:
                lat_bounds = [min(coord[1] for coord in coords), max(coord[1] for coord in coords)]
                lon_bounds = [min(coord[0] for coord in coords), max(coord[0] for coord in coords)]
                
                st.write("**Bounding Box:**")
                st.write(f"Latitude: {lat_bounds[0]:.4f} to {lat_bounds[1]:.4f}")
                st.write(f"Longitude: {lon_bounds[0]:.4f} to {lon_bounds[1]:.4f}")
    else:
        st.info("👆 Select an area on the map to see basic metrics")

# Analysis Results Section
if st.session_state.analysis_results:
    st.header("📈 Analysis Results")
    
    results = st.session_state.analysis_results
    metrics_data = results['metrics']
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Time Series", "📋 Detailed Metrics", "📤 Export"])
    
    with tab1:
        st.subheader("Natural Capital Dashboard")
        
        # Display key metrics in columns
        if metrics_data:
            metric_cols = st.columns(len(metrics_data))
            
            for i, (metric_name, metric_data) in enumerate(metrics_data.items()):
                with metric_cols[i]:
                    if isinstance(metric_data, dict) and 'current_value' in metric_data:
                        current_val = metric_data['current_value']
                        previous_val = metric_data.get('previous_value', current_val)
                        change = current_val - previous_val if previous_val != 0 else 0
                        
                        st.metric(
                            metrics_options.get(metric_name, metric_name),
                            f"{current_val:.3f}",
                            f"{change:+.3f}" if change != 0 else None
                        )
            
            # Create dashboard visualization
            dashboard_fig = create_metrics_dashboard(metrics_data)
            if dashboard_fig:
                st.plotly_chart(dashboard_fig, use_container_width=True)
    
    with tab2:
        st.subheader("Time Series Analysis")
        
        if metrics_data:
            # Select metric for time series
            selected_ts_metric = st.selectbox(
                "Select metric for time series analysis:",
                options=list(metrics_data.keys()),
                format_func=lambda x: metrics_options.get(x, x)
            )
            
            if selected_ts_metric in metrics_data:
                metric_data = metrics_data[selected_ts_metric]
                if isinstance(metric_data, dict) and 'time_series' in metric_data:
                    ts_fig = create_time_series_chart(
                        metric_data['time_series'], 
                        selected_ts_metric,
                        metrics_options.get(selected_ts_metric, selected_ts_metric)
                    )
                    st.plotly_chart(ts_fig, use_container_width=True)
                    
                    # Show trend analysis
                    ts_data = metric_data['time_series']
                    if len(ts_data) > 1:
                        trend = np.polyfit(range(len(ts_data)), [d['value'] for d in ts_data], 1)[0]
                        trend_direction = "📈 Increasing" if trend > 0 else "📉 Decreasing" if trend < 0 else "➡️ Stable"
                        st.write(f"**Trend:** {trend_direction} (slope: {trend:.6f})")
    
    with tab3:
        st.subheader("Detailed Metrics")
        
        for metric_name, metric_data in metrics_data.items():
            with st.expander(f"📊 {metrics_options.get(metric_name, metric_name)}"):
                if isinstance(metric_data, dict):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Current Statistics:**")
                        for key, value in metric_data.items():
                            if key not in ['time_series', 'spatial_data']:
                                if isinstance(value, (int, float)):
                                    st.write(f"- {key.replace('_', ' ').title()}: {value:.4f}")
                                else:
                                    st.write(f"- {key.replace('_', ' ').title()}: {value}")
                    
                    with col2:
                        if 'spatial_data' in metric_data and metric_data['spatial_data']:
                            st.write("**Spatial Statistics:**")
                            spatial_stats = metric_data['spatial_data']
                            for key, value in spatial_stats.items():
                                if isinstance(value, (int, float)):
                                    st.write(f"- {key.replace('_', ' ').title()}: {value:.4f}")
                                else:
                                    st.write(f"- {key.replace('_', ' ').title()}: {value}")
    
    with tab4:
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
**Natural Capital Measurement Tool** - Built with Streamlit for environmental research and ecosystem monitoring.  
For questions or support, please refer to the documentation or contact your system administrator.
""")

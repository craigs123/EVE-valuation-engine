"""
Visualization Module for Natural Capital Metrics
Creates interactive charts and dashboards for data visualization
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

def create_time_series_chart(time_series_data: List[Dict], metric_name: str, metric_title: str) -> go.Figure:
    """
    Create an interactive time series chart for a natural capital metric
    
    Args:
        time_series_data: List of time series data points
        metric_name: Internal name of the metric
        metric_title: Display title for the metric
        
    Returns:
        Plotly figure object
    """
    if not time_series_data:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No time series data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title=f"{metric_title} - Time Series")
        return fig
    
    # Extract dates and values
    dates = [datetime.fromisoformat(point['date'].replace('Z', '')) for point in time_series_data]
    values = [point['value'] for point in time_series_data]
    
    # Create the main time series plot
    fig = go.Figure()
    
    # Add main line
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name=metric_title,
        line=dict(color='#2E7D32', width=3),
        marker=dict(size=8, color='#2E7D32'),
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Date: %{x}<br>' +
                     'Value: %{y:.4f}<br>' +
                     '<extra></extra>'
    ))
    
    # Add trend line if we have enough data points
    if len(values) > 2:
        # Calculate trend line
        x_numeric = list(range(len(values)))
        z = np.polyfit(x_numeric, values, 1)
        trend_line = [z[0] * x + z[1] for x in x_numeric]
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=trend_line,
            mode='lines',
            name='Trend',
            line=dict(color='#FF6B6B', width=2, dash='dash'),
            hovertemplate='<b>Trend Line</b><br>' +
                         'Date: %{x}<br>' +
                         'Trend Value: %{y:.4f}<br>' +
                         '<extra></extra>'
        ))
    
    # Add quality indicators if available
    good_quality_dates = []
    good_quality_values = []
    poor_quality_dates = []
    poor_quality_values = []
    
    for point in time_series_data:
        date = datetime.fromisoformat(point['date'].replace('Z', ''))
        value = point['value']
        quality = point.get('quality', 'unknown')
        
        if quality == 'good':
            good_quality_dates.append(date)
            good_quality_values.append(value)
        else:
            poor_quality_dates.append(date)
            poor_quality_values.append(value)
    
    # Add quality markers
    if good_quality_dates:
        fig.add_trace(go.Scatter(
            x=good_quality_dates,
            y=good_quality_values,
            mode='markers',
            name='Good Quality',
            marker=dict(size=10, color='green', symbol='circle'),
            showlegend=True,
            hovertemplate='<b>Good Quality Data</b><br>' +
                         'Date: %{x}<br>' +
                         'Value: %{y:.4f}<br>' +
                         '<extra></extra>'
        ))
    
    if poor_quality_dates:
        fig.add_trace(go.Scatter(
            x=poor_quality_dates,
            y=poor_quality_values,
            mode='markers',
            name='Lower Quality',
            marker=dict(size=10, color='orange', symbol='triangle-up'),
            showlegend=True,
            hovertemplate='<b>Lower Quality Data</b><br>' +
                         'Date: %{x}<br>' +
                         'Value: %{y:.4f}<br>' +
                         '<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=f"{metric_title} - Time Series Analysis",
        xaxis_title="Date",
        yaxis_title=get_metric_unit(metric_name),
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_metrics_dashboard(metrics_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Create a comprehensive dashboard showing multiple metrics
    
    Args:
        metrics_data: Dictionary containing all calculated metrics
        
    Returns:
        Plotly figure object or None if no data
    """
    if not metrics_data:
        return None
    
    # Prepare data for visualization
    metric_names = []
    current_values = []
    previous_values = []
    trends = []
    
    for metric_name, metric_data in metrics_data.items():
        if isinstance(metric_data, dict) and 'current_value' in metric_data:
            metric_names.append(metric_name.upper())
            current_values.append(metric_data['current_value'])
            previous_values.append(metric_data.get('previous_value', metric_data['current_value']))
            trends.append(metric_data.get('trend_slope', 0))
    
    if not metric_names:
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Current vs Previous Values',
            'Trend Analysis',
            'Metric Comparison (Normalized)',
            'Change Analysis'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "radar"}, {"type": "scatter"}]
        ]
    )
    
    # 1. Current vs Previous Values (Bar Chart)
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=current_values,
            name='Current',
            marker_color='#2E7D32',
            yaxis='y',
            offsetgroup=1
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=previous_values,
            name='Previous',
            marker_color='#81C784',
            yaxis='y',
            offsetgroup=2
        ),
        row=1, col=1
    )
    
    # 2. Trend Analysis (Bar Chart)
    trend_colors = ['green' if t > 0 else 'red' if t < 0 else 'gray' for t in trends]
    
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=trends,
            name='Trend',
            marker_color=trend_colors,
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Normalized Metrics (Radar Chart)
    # Normalize values to 0-1 scale for comparison
    if current_values:
        max_val = max(abs(v) for v in current_values if v != 0)
        if max_val > 0:
            normalized_values = [abs(v) / max_val for v in current_values]
        else:
            normalized_values = current_values
        
        fig.add_trace(
            go.Scatterpolar(
                r=normalized_values,
                theta=metric_names,
                fill='toself',
                name='Normalized Values',
                line_color='#2E7D32',
                showlegend=False
            ),
            row=2, col=1
        )
    
    # 4. Change Analysis (Scatter Plot)
    changes = [curr - prev for curr, prev in zip(current_values, previous_values)]
    
    fig.add_trace(
        go.Scatter(
            x=metric_names,
            y=changes,
            mode='markers',
            name='Change',
            marker=dict(
                size=15,
                color=[change for change in changes],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Change", x=1.1)
            ),
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Add horizontal line at zero for change plot
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)
    
    # Update layout
    fig.update_layout(
        title_text="Natural Capital Metrics Dashboard",
        height=800,
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    # Update axis titles
    fig.update_xaxes(title_text="Metrics", row=1, col=1)
    fig.update_yaxes(title_text="Values", row=1, col=1)
    fig.update_xaxes(title_text="Metrics", row=1, col=2)
    fig.update_yaxes(title_text="Trend Slope", row=1, col=2)
    fig.update_xaxes(title_text="Metrics", row=2, col=2)
    fig.update_yaxes(title_text="Change", row=2, col=2)
    
    return fig

def create_comparison_chart(metric_data: Dict[str, Any], metric_name: str) -> go.Figure:
    """
    Create a detailed comparison chart for a specific metric
    
    Args:
        metric_data: Data for the specific metric
        metric_name: Name of the metric
        
    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Time Series',
            'Statistical Distribution',
            'Quality Assessment',
            'Spatial Variation'
        )
    )
    
    # Time Series
    if 'time_series' in metric_data and metric_data['time_series']:
        ts_data = metric_data['time_series']
        dates = [datetime.fromisoformat(point['date'].replace('Z', '')) for point in ts_data]
        values = [point['value'] for point in ts_data]
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Time Series',
                line=dict(color='#2E7D32'),
                showlegend=False
            ),
            row=1, col=1
        )
    
    # Statistical Distribution
    if 'time_series' in metric_data and metric_data['time_series']:
        values = [point['value'] for point in metric_data['time_series']]
        
        fig.add_trace(
            go.Histogram(
                x=values,
                name='Distribution',
                marker_color='#2E7D32',
                showlegend=False,
                nbinsx=10
            ),
            row=1, col=2
        )
    
    # Quality Assessment
    if 'time_series' in metric_data and metric_data['time_series']:
        quality_counts = {}
        for point in metric_data['time_series']:
            quality = point.get('quality', 'unknown')
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        if quality_counts:
            fig.add_trace(
                go.Pie(
                    labels=list(quality_counts.keys()),
                    values=list(quality_counts.values()),
                    name='Quality',
                    showlegend=False
                ),
                row=2, col=1
            )
    
    # Spatial Variation (if available)
    if 'spatial_data' in metric_data and metric_data['spatial_data']:
        spatial_data = metric_data['spatial_data']
        metrics = list(spatial_data.keys())
        values = [spatial_data[k] for k in metrics if isinstance(spatial_data[k], (int, float))]
        metrics = metrics[:len(values)]  # Ensure same length
        
        if metrics and values:
            fig.add_trace(
                go.Bar(
                    x=metrics,
                    y=values,
                    name='Spatial Stats',
                    marker_color='#2E7D32',
                    showlegend=False
                ),
                row=2, col=2
            )
    
    fig.update_layout(
        title=f"Detailed Analysis: {metric_name.upper()}",
        height=600,
        template='plotly_white'
    )
    
    return fig

def create_export_summary_chart(metrics_data: Dict[str, Any]) -> go.Figure:
    """
    Create a summary chart suitable for reports
    
    Args:
        metrics_data: All metrics data
        
    Returns:
        Plotly figure object
    """
    # Extract key metrics for summary
    summary_data = {}
    
    for metric_name, metric_data in metrics_data.items():
        if isinstance(metric_data, dict) and 'current_value' in metric_data:
            summary_data[metric_name] = {
                'current': metric_data['current_value'],
                'trend': metric_data.get('trend_slope', 0),
                'quality': 'Good' if metric_data.get('current_value', 0) > 0 else 'Poor'
            }
    
    if not summary_data:
        fig = go.Figure()
        fig.add_annotation(text="No data available for summary", x=0.5, y=0.5)
        return fig
    
    # Create summary visualization
    metric_names = list(summary_data.keys())
    current_values = [summary_data[m]['current'] for m in metric_names]
    trends = [summary_data[m]['trend'] for m in metric_names]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Current Status', 'Trends'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Current status
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=current_values,
            name='Current Values',
            marker_color='#2E7D32'
        ),
        row=1, col=1
    )
    
    # Trends
    trend_colors = ['green' if t > 0 else 'red' if t < 0 else 'gray' for t in trends]
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=trends,
            name='Trends',
            marker_color=trend_colors
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Natural Capital Metrics Summary",
        template='plotly_white',
        height=400,
        showlegend=False
    )
    
    return fig

def get_metric_unit(metric_name: str) -> str:
    """
    Get the appropriate unit for a given metric
    
    Args:
        metric_name: Name of the metric
        
    Returns:
        Unit string
    """
    units = {
        'NDVI': 'Index (-1 to 1)',
        'forest_cover': 'Percentage (%)',
        'carbon_storage': 'Tons CO₂',
        'water_quality': 'Quality Score (0-100)',
        'biodiversity_index': 'Biodiversity Score (0-100)'
    }
    
    return units.get(metric_name, 'Value')

def create_area_visualization(area_bounds: Dict, metrics_summary: Dict) -> go.Figure:
    """
    Create a visualization showing the selected area with metric overlays
    
    Args:
        area_bounds: Area boundary information
        metrics_summary: Summary of calculated metrics
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    if area_bounds and 'coordinates' in area_bounds:
        coords = area_bounds['coordinates']
        lats = [coord[1] for coord in coords] + [coords[0][1]]  # Close the polygon
        lons = [coord[0] for coord in coords] + [coords[0][0]]
        
        # Add the area boundary
        fig.add_trace(go.Scatter(
            x=lons,
            y=lats,
            fill='toself',
            fillcolor='rgba(46, 125, 50, 0.3)',
            line=dict(color='#2E7D32', width=2),
            name='Selected Area',
            hovertemplate='<b>Selected Area</b><br>' +
                         'Lat: %{y:.4f}<br>' +
                         'Lon: %{x:.4f}<br>' +
                         '<extra></extra>'
        ))
        
        # Add center point with metrics info
        center_lat = np.mean(lats[:-1])
        center_lon = np.mean(lons[:-1])
        
        hover_text = "Area Center<br>"
        if metrics_summary:
            for metric, value in metrics_summary.items():
                if isinstance(value, (int, float)):
                    hover_text += f"{metric}: {value:.3f}<br>"
        
        fig.add_trace(go.Scatter(
            x=[center_lon],
            y=[center_lat],
            mode='markers',
            marker=dict(size=15, color='red', symbol='star'),
            name='Area Center',
            hovertemplate=hover_text + '<extra></extra>'
        ))
    
    fig.update_layout(
        title="Selected Area Visualization",
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        template='plotly_white',
        height=500,
        showlegend=True
    )
    
    # Make sure the aspect ratio is correct for geographic data
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    
    return fig

"""
Multi-Database Visualization Components
Creates charts and displays for comparing multiple valuation databases
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, Any, List
import pandas as pd
import numpy as np

def create_database_comparison_chart(multi_db_results: Dict[str, Any]) -> go.Figure:
    """
    Create a comparison chart showing values from all databases
    """
    if 'database_results' not in multi_db_results:
        return go.Figure()
    
    databases = []
    total_values = []
    provisioning_values = []
    regulating_values = []
    cultural_values = []
    supporting_values = []
    
    for db_name, db_data in multi_db_results['database_results'].items():
        if 'values' in db_data:
            values = db_data['values']
            databases.append(db_data['metadata']['name'])
            
            # Extract values for each service category
            total_values.append(values.get('ecosystem_services_total', {}).get('total', 0))
            provisioning_values.append(values.get('provisioning', {}).get('total', 0))
            regulating_values.append(values.get('regulating', {}).get('total', 0))
            cultural_values.append(values.get('cultural', {}).get('total', 0))
            supporting_values.append(values.get('supporting', {}).get('total', 0))
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Total Annual Value by Database',
            'Service Categories Comparison',
            'Database Uncertainty Range',
            'Per-Hectare Values'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "box"}, {"type": "scatter"}]
        ]
    )
    
    # 1. Total values by database
    fig.add_trace(
        go.Bar(
            x=databases,
            y=total_values,
            name='Total Value',
            marker_color=['#2E7D32', '#4CAF50', '#81C784', '#A5D6A7'],
            text=[f'${v:,.0f}/year' for v in total_values],
            textposition='auto',
        ),
        row=1, col=1
    )
    
    # 2. Service categories stacked bar
    fig.add_trace(
        go.Bar(x=databases, y=provisioning_values, name='Provisioning', 
               marker_color='#1976D2'),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=databases, y=regulating_values, name='Regulating', 
               marker_color='#388E3C'),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=databases, y=cultural_values, name='Cultural', 
               marker_color='#F57C00'),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=databases, y=supporting_values, name='Supporting', 
               marker_color='#7B1FA2'),
        row=1, col=2
    )
    
    # 3. Uncertainty range box plot
    if 'statistical_summary' in multi_db_results:
        stats = multi_db_results['statistical_summary'].get('ecosystem_services_total', {})
        if stats:
            fig.add_trace(
                go.Box(
                    y=total_values,
                    name='Value Distribution',
                    marker_color='#2E7D32',
                    boxmean=True
                ),
                row=2, col=1
            )
    
    # 4. Per-hectare comparison
    if multi_db_results.get('area_hectares', 0) > 0:
        area_ha = multi_db_results['area_hectares']
        per_ha_values = [v/area_ha for v in total_values]
        
        fig.add_trace(
            go.Scatter(
                x=databases,
                y=per_ha_values,
                mode='markers+lines',
                name='Per Hectare',
                marker=dict(size=12, color='#2E7D32'),
                line=dict(width=3)
            ),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text="Multi-Database Natural Capital Valuation Comparison",
        title_x=0.5,
        showlegend=True,
        barmode='stack'
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Database", row=1, col=1)
    fig.update_yaxes(title_text="Annual Value (USD)", row=1, col=1)
    fig.update_xaxes(title_text="Database", row=1, col=2)
    fig.update_yaxes(title_text="Annual Value (USD)", row=1, col=2)
    fig.update_yaxes(title_text="Annual Value (USD)", row=2, col=1)
    fig.update_xaxes(title_text="Database", row=2, col=2)
    fig.update_yaxes(title_text="Value per Hectare (USD/ha)", row=2, col=2)
    
    return fig

def display_database_details(multi_db_results: Dict[str, Any]):
    """
    Display detailed information about each database and methodology
    """
    if 'database_results' not in multi_db_results:
        return
    
    st.subheader("📊 Database Methodologies & Sources")
    
    # Create tabs for each database
    db_names = list(multi_db_results['database_results'].keys())
    tabs = st.tabs([db_data['metadata']['name'] for db_data in multi_db_results['database_results'].values()])
    
    for i, (db_name, tab) in enumerate(zip(db_names, tabs)):
        with tab:
            db_data = multi_db_results['database_results'][db_name]
            metadata = db_data['metadata']
            values = db_data['values']
            
            # Database information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Database Information:**")
                st.write(f"• **Records**: {metadata['records']}")
                st.write(f"• **Approach**: {metadata['approach']}")
                st.write(f"• **Currency**: {metadata['currency']}")
                st.write(f"• **Confidence**: {metadata['confidence']}")
            
            with col2:
                if 'ecosystem_services_total' in values:
                    total = values['ecosystem_services_total']['total']
                    per_ha = values['ecosystem_services_total']['per_hectare']
                    st.metric(
                        label="Total Annual Value",
                        value=f"${total:,.0f}",
                        delta=f"${per_ha:,.0f}/ha/year"
                    )
            
            # Service breakdown
            if len(values) > 1:
                st.write("**Service Category Breakdown:**")
                service_data = []
                for service, data in values.items():
                    if service != 'ecosystem_services_total' and 'total' in data:
                        service_data.append({
                            'Service': service.replace('_', ' ').title(),
                            'Annual Value (USD)': f"${data['total']:,.0f}",
                            'Per Hectare (USD/ha)': f"${data['per_hectare']:,.0f}"
                        })
                
                if service_data:
                    df = pd.DataFrame(service_data)
                    st.dataframe(df, use_container_width=True)

def create_uncertainty_analysis(multi_db_results: Dict[str, Any]) -> go.Figure:
    """
    Create detailed uncertainty analysis visualization
    """
    if 'statistical_summary' not in multi_db_results:
        return go.Figure()
    
    stats = multi_db_results['statistical_summary']
    
    # Create uncertainty visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Value Distribution Statistics',
            'Confidence Intervals',
            'Database Agreement Analysis',
            'Coefficient of Variation'
        )
    )
    
    services = ['provisioning', 'regulating', 'cultural', 'supporting', 'ecosystem_services_total']
    service_names = ['Provisioning', 'Regulating', 'Cultural', 'Supporting', 'Total']
    
    # 1. Statistics bars
    means = [stats.get(service, {}).get('mean', 0) for service in services]
    stds = [stats.get(service, {}).get('std', 0) for service in services]
    
    fig.add_trace(
        go.Bar(
            x=service_names,
            y=means,
            error_y=dict(type='data', array=stds),
            name='Mean ± Std Dev',
            marker_color='#2E7D32'
        ),
        row=1, col=1
    )
    
    # 2. Min-Max ranges
    mins = [stats.get(service, {}).get('min', 0) for service in services]
    maxs = [stats.get(service, {}).get('max', 0) for service in services]
    
    fig.add_trace(
        go.Scatter(
            x=service_names,
            y=maxs,
            mode='markers',
            name='Maximum',
            marker=dict(symbol='triangle-up', size=10, color='red')
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=service_names,
            y=means,
            mode='markers+lines',
            name='Mean',
            marker=dict(size=8, color='#2E7D32'),
            line=dict(width=2)
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=service_names,
            y=mins,
            mode='markers',
            name='Minimum',
            marker=dict(symbol='triangle-down', size=10, color='blue')
        ),
        row=1, col=2
    )
    
    # 3. Database agreement (coefficient of variation)
    cvs = []
    for service in services:
        service_stats = stats.get(service, {})
        mean_val = service_stats.get('mean', 0)
        std_val = service_stats.get('std', 0)
        cv = (std_val / mean_val * 100) if mean_val > 0 else 0
        cvs.append(cv)
    
    fig.add_trace(
        go.Bar(
            x=service_names,
            y=cvs,
            name='Coefficient of Variation (%)',
            marker_color='#FF6B35',
            text=[f'{cv:.1f}%' for cv in cvs],
            textposition='auto'
        ),
        row=2, col=1
    )
    
    # 4. Range percentages
    range_pcts = [stats.get(service, {}).get('range_percent', 0) for service in services]
    
    fig.add_trace(
        go.Scatter(
            x=service_names,
            y=range_pcts,
            mode='markers+lines',
            name='Range as % of Mean',
            marker=dict(size=12, color='#7B1FA2'),
            line=dict(width=3)
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=700,
        title_text="Uncertainty Analysis Across Databases",
        title_x=0.5,
        showlegend=True
    )
    
    # Update axes
    fig.update_yaxes(title_text="Annual Value (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Annual Value (USD)", row=1, col=2)
    fig.update_yaxes(title_text="Coefficient of Variation (%)", row=2, col=1)
    fig.update_yaxes(title_text="Range as % of Mean", row=2, col=2)
    
    return fig

def display_valuation_summary(multi_db_results: Dict[str, Any]):
    """
    Display comprehensive valuation summary with key insights
    """
    if 'valuation_range' not in multi_db_results:
        return
    
    vr = multi_db_results['valuation_range']
    
    st.subheader("💰 Valuation Summary")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Low Estimate",
            value=f"${vr['low_estimate']:,.0f}",
            help="Minimum value across all databases"
        )
    
    with col2:
        st.metric(
            label="Best Estimate",
            value=f"${vr['best_estimate']:,.0f}",
            help="Mean value across all databases"
        )
    
    with col3:
        st.metric(
            label="High Estimate", 
            value=f"${vr['high_estimate']:,.0f}",
            help="Maximum value across all databases"
        )
    
    with col4:
        uncertainty = ((vr['high_estimate'] - vr['low_estimate']) / vr['best_estimate']) * 100
        st.metric(
            label="Uncertainty Range",
            value=f"±{uncertainty:.0f}%",
            help="Range as percentage of best estimate"
        )
    
    # Confidence interval
    ci = vr.get('confidence_interval_95', {})
    if ci:
        st.info(f"""
        **95% Confidence Interval**: ${ci['lower']:,.0f} - ${ci['upper']:,.0f}
        
        This range indicates that we can be 95% confident the true value falls within this interval 
        based on the variation across {vr['databases_used']} independent databases.
        """)
    
    # Interpretation guidelines
    with st.expander("📖 How to Interpret These Values"):
        st.write("""
        **Database Sources:**
        - **ESVD**: Global meta-analysis of 10,000+ peer-reviewed studies
        - **TEEB**: Policy-oriented synthesis with 6,400+ value records  
        - **InVEST**: Biophysical modeling approach with spatial data
        - **WAVES/SEEA**: UN standardized national accounting methods
        
        **Value Interpretation:**
        - **Low-High Range**: Shows natural variation in methodologies and data sources
        - **Best Estimate**: Statistical mean provides most balanced valuation
        - **Uncertainty**: Higher uncertainty indicates need for location-specific studies
        
        **Usage Recommendations:**
        - Use **Best Estimate** for planning and policy decisions
        - Report **Full Range** for transparency and risk assessment
        - Consider **Confidence Interval** for statistical rigor
        """)
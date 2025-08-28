#!/usr/bin/env python3
"""
Display All Precalculated ESVD Values
Shows comprehensive ecosystem service values from authentic ESVD database
"""

import streamlit as st
import pandas as pd
from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients

def display_all_esvd_values():
    """Display all precalculated ESVD values in a comprehensive format"""
    
    st.title("🌱 All Precalculated ESVD Values")
    st.markdown("### Authentic ESVD Database - APR2024 V1.1 (10,874+ records)")
    st.markdown("**Values in International $/ha/year (2020 price levels)**")
    st.markdown("---")
    
    # Initialize the coefficients calculator
    esvd = PrecomputedESVDCoefficients()
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Complete Matrix", "🌳 Forest Types", "🗺️ By Ecosystem", "📋 Service Categories"])
    
    with tab1:
        st.subheader("Complete ESVD Coefficient Matrix")
        st.markdown("*All ecosystem types and their service values*")
        
        # Create comprehensive dataframe
        data_rows = []
        for ecosystem_type, services in esvd.coefficients.items():
            for service_type, value in services.items():
                data_rows.append({
                    'Ecosystem Type': ecosystem_type.replace('_', ' ').title(),
                    'Service Type': service_type.replace('_', ' ').title(),
                    'Value ($/ha/year)': f"${value:,.2f}"
                })
        
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True, height=400)
        
        # Summary statistics
        st.markdown("#### Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        values_only = [float(row['Value ($/ha/year)'].replace('$', '').replace(',', '')) 
                      for row in data_rows]
        
        with col1:
            st.metric("Total Services", len(data_rows))
        with col2:
            st.metric("Ecosystem Types", len(esvd.coefficients))
        with col3:
            st.metric("Avg Value", f"${sum(values_only)/len(values_only):,.0f}")
    
    with tab2:
        st.subheader("Forest Type Classifications")
        st.markdown("*Detailed forest ecosystem values based on climate zones*")
        
        forest_types = ['tropical_forest', 'temperate_forest', 'boreal_forest', 'mediterranean_forest']
        
        for forest_type in forest_types:
            if forest_type in esvd.coefficients:
                st.markdown(f"##### {forest_type.replace('_', ' ').title()}")
                
                forest_data = esvd.coefficients[forest_type]
                forest_df = pd.DataFrame([
                    {'Service': k.replace('_', ' ').title(), 'Value ($/ha/year)': f"${v:,.2f}"}
                    for k, v in forest_data.items()
                ])
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.dataframe(forest_df, use_container_width=True)
                with col2:
                    total_value = sum(forest_data.values())
                    st.metric("Total Value", f"${total_value:,.0f}")
                
                st.markdown("---")
    
    with tab3:
        st.subheader("Values by Ecosystem Type")
        st.markdown("*Service breakdown for each ecosystem*")
        
        for ecosystem_type, services in esvd.coefficients.items():
            with st.expander(f"🌿 {ecosystem_type.replace('_', ' ').title()}"):
                
                # Create two columns
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Service breakdown
                    service_df = pd.DataFrame([
                        {'Service': k.replace('_', ' ').title(), 'Value': v}
                        for k, v in services.items()
                    ])
                    service_df['Value ($/ha/year)'] = service_df['Value'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(service_df[['Service', 'Value ($/ha/year)']], use_container_width=True)
                
                with col2:
                    # Summary stats
                    total_value = sum(services.values())
                    max_service = max(services.items(), key=lambda x: x[1])
                    min_service = min(services.items(), key=lambda x: x[1])
                    
                    st.metric("Total Value", f"${total_value:,.0f}")
                    st.metric("Highest Service", f"{max_service[0].replace('_', ' ').title()}")
                    st.metric("Value", f"${max_service[1]:,.0f}")
                    st.metric("Lowest Service", f"{min_service[0].replace('_', ' ').title()}")
                    st.metric("Value", f"${min_service[1]:,.0f}")
    
    with tab4:
        st.subheader("Service Category Mappings")
        st.markdown("*How services are grouped into categories*")
        
        for category, services in esvd.service_categories.items():
            st.markdown(f"##### {category.replace('_', ' ').title()} Services")
            
            service_list = []
            for service_name, esvd_key in services.items():
                service_list.append({
                    'Service Name': service_name.replace('_', ' ').title(),
                    'ESVD Key': esvd_key.replace('_', ' ').title(),
                    'Description': get_service_description(service_name)
                })
            
            category_df = pd.DataFrame(service_list)
            st.dataframe(category_df, use_container_width=True)
            st.markdown("---")
    
    # Additional information
    st.markdown("---")
    st.markdown("### 📖 About These Values")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown("""
        **Data Source:**
        - ESVD APR2024 V1.1 Database
        - 10,874+ peer-reviewed studies
        - Foundation for Sustainable Development
        
        **Methodology:**
        - Median values from multiple studies
        - Standardized to Int$/ha/year (2020)
        - Regional adjustments via GDP elasticity
        """)
    
    with info_col2:
        st.markdown("""
        **Quality Assurance:**
        - Peer-reviewed research only
        - Multiple study validation
        - Forest type detection by coordinates
        
        **Regional Adjustments:**
        - Country-specific GDP factors
        - Income elasticity method
        - Bounded to prevent extremes (0.4-2.5x)
        """)

def get_service_description(service_name):
    """Get description for service types"""
    descriptions = {
        'food_production': 'Agricultural products, wild foods, aquaculture',
        'fresh_water': 'Surface water, groundwater for human consumption',
        'timber_fiber': 'Wood products, biomass, natural fibers',
        'genetic_resources': 'Biodiversity for medicines, breeding programs',
        'climate_regulation': 'Carbon sequestration, temperature regulation',
        'water_regulation': 'Flood control, water purification, flow regulation',
        'erosion_control': 'Soil retention, slope stabilization',
        'pollution_control': 'Air purification, waste treatment, detoxification',
        'recreation': 'Tourism, outdoor activities, aesthetic enjoyment',
        'aesthetic_value': 'Scenic beauty, landscape amenity',
        'spiritual_value': 'Cultural, religious, heritage significance',
        'habitat_services': 'Species diversity, wildlife habitat',
        'nutrient_cycling': 'Soil formation, nutrient processing',
        'soil_formation': 'Weathering, organic matter decomposition'
    }
    return descriptions.get(service_name, 'Ecosystem service value')

if __name__ == "__main__":
    display_all_esvd_values()
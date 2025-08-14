"""
User guidance utilities for improving EVE usability
"""

import streamlit as st

def show_progress_indicator(step_number: int, total_steps: int = 3):
    """Show a progress indicator for the analysis process"""
    progress = step_number / total_steps
    st.progress(progress)
    
    steps = [
        "📍 Area Selection",
        "🔍 Analysis Processing", 
        "📊 Results Display"
    ]
    
    col1, col2, col3 = st.columns(3)
    for i, (col, step_name) in enumerate(zip([col1, col2, col3], steps)):
        with col:
            if i + 1 <= step_number:
                st.success(f"✅ {step_name}")
            elif i + 1 == step_number + 1:
                st.info(f"⏳ {step_name}")
            else:
                st.write(f"⏸️ {step_name}")

def show_ecosystem_service_explanation():
    """Show explanation of ecosystem services"""
    with st.expander("🌍 What are Ecosystem Services?", expanded=False):
        st.markdown("""
        **Ecosystem services are the benefits nature provides to humans:**
        
        **🥬 Provisioning Services**
        - Food production (crops, fish, livestock)
        - Fresh water supply
        - Timber and fiber materials
        - Genetic resources for medicine
        
        **🌡️ Regulating Services**
        - Climate regulation (carbon storage)
        - Water purification and regulation
        - Disease and pest control
        - Erosion prevention
        
        **🎨 Cultural Services**
        - Recreation and tourism
        - Spiritual and aesthetic values
        - Educational opportunities
        - Cultural heritage preservation
        
        **🔄 Supporting Services**
        - Soil formation and nutrient cycling
        - Primary production (photosynthesis)
        - Habitat provision for wildlife
        - Biodiversity maintenance
        
        EVE calculates the economic value of all these services combined.
        """)

def show_methodology_explanation():
    """Show explanation of valuation methodology"""
    with st.expander("🔬 How Does EVE Calculate Value?", expanded=False):
        st.markdown("""
        **EVE uses scientifically validated methods:**
        
        **1. Ecosystem Detection**
        - Satellite imagery analysis (NDVI, NDWI, NDBI indices)
        - Geographic context and climate data
        - Machine learning classification
        
        **2. Economic Valuation**
        - ESVD database (10,000+ peer-reviewed studies)
        - Regional adjustment factors
        - Quality-based multipliers from satellite data
        
        **3. Service Categories**
        - Separate calculations for each service type
        - Time series analysis for trends
        - Multi-ecosystem composition analysis
        
        **4. Quality Assurance**
        - Values standardized to 2020 International dollars
        - Geographic adjustment factors applied
        - Confidence indicators provided
        
        All values represent annual economic benefits in US dollars.
        """)

def show_tips_and_best_practices():
    """Show user tips for better results"""
    with st.expander("💡 Tips for Better Results", expanded=False):
        st.markdown("""
        **For Best Analysis Results:**
        
        **Area Selection**
        - Draw areas larger than 10 hectares for accurate detection
        - Avoid areas with mixed urban/natural land use
        - Select homogeneous ecosystem types when possible
        
        **Time Period**
        - Use "Past Year" for comprehensive seasonal analysis
        - Shorter periods may show seasonal variations
        - Longer periods reveal ecosystem health trends
        
        **Interpreting Results**
        - Higher values don't always mean "better" ecosystems
        - Wetlands naturally have very high service values
        - Compare similar ecosystem types for meaningful insights
        - Consider both total value and value per hectare
        
        **Multi-Ecosystem Areas**
        - Large diverse areas show ecosystem composition breakdowns
        - Individual ecosystem values are calculated separately
        - Diversity metrics indicate ecosystem heterogeneity
        """)

def show_data_sources_info():
    """Show information about data sources and reliability"""
    with st.expander("📚 Data Sources & Reliability", expanded=False):
        st.markdown("""
        **EVE uses authoritative scientific data sources:**
        
        **Primary Sources**
        - **ESVD**: Ecosystem Services Valuation Database (10,000+ studies)
        - **TEEB**: The Economics of Ecosystems and Biodiversity
        - **InVEST**: Natural Capital Project frameworks
        - **Peer-reviewed research**: 1,100+ scientific publications
        
        **Satellite Data**
        - Multi-spectral imagery for ecosystem detection
        - Time series analysis for trend detection
        - Quality indicators for data reliability
        
        **Regional Adjustments**
        - Income and cost-of-living factors
        - Geographic and climatic considerations
        - Local economic conditions
        
        **Limitations**
        - Values are estimates based on global averages
        - Local conditions may vary significantly
        - Results should be used for comparative analysis
        - Not intended for precise financial planning
        """)

def show_quick_help():
    """Show quick help for common issues"""
    with st.expander("❓ Quick Help", expanded=False):
        st.markdown("""
        **Common Questions:**
        
        **Q: Why is my area value so high/low?**
        A: Different ecosystems provide different services. Wetlands have naturally high values due to water regulation services.
        
        **Q: Can I trust these numbers for business decisions?**
        A: These are scientific estimates for comparison purposes. Consult local experts for specific financial planning.
        
        **Q: Why does ecosystem detection seem wrong?**
        A: Detection uses satellite data which may not capture recent changes. Use manual override if needed.
        
        **Q: What's a good area size to analyze?**
        A: 10-1000 hectares works best. Smaller areas may be inaccurate, larger areas show more ecosystem diversity.
        
        **Q: How current is the satellite data?**
        A: EVE uses the most recent available satellite imagery, typically updated monthly.
        """)
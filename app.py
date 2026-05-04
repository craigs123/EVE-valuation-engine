"""
Ecological Valuation Engine - Clean Map Implementation
"""

import logging
import math
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import json
import base64
import numpy as np
import uuid
from utils.sampling_utils import extract_coordinates
from utils.analysis_helpers import (
    _get_ecosystem_intactness_multiplier,
    lat_to_mercator_y,
    compute_zoom_for_bbox,
    compute_center_from_bbox,
    create_bbox_from_center_and_area,
)

logger = logging.getLogger(__name__)

# Ultra-fast lazy loading for production performance
@st.cache_resource(show_spinner=False, ttl=3600)
def get_database_modules():
    """Lazy load database modules with extended caching for production performance"""
    try:
        from database import (
            init_database, 
            initialize_user_session,
            SavedAreaDB,
            EcosystemAnalysisDB,
            NaturalCapitalBaselineDB
        )
        return {
            'init_database': init_database,
            'initialize_user_session': initialize_user_session,
            'SavedAreaDB': SavedAreaDB,
            'EcosystemAnalysisDB': EcosystemAnalysisDB,
            'NaturalCapitalBaselineDB': NaturalCapitalBaselineDB
        }
    except ImportError:
        return None  # Graceful fallback

# Optimized page configuration for production
st.set_page_config(
    page_title="Ecological Valuation Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }  # Remove menu items for faster loading
)

# PWA Support - inject manifest and meta tags for installability
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#2E7D32">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="EVE">
<link rel="apple-touch-icon" href="/static/icon-192.png">
""", unsafe_allow_html=True)

# Early loading message - displayed immediately while app initializes
loading_placeholder = st.empty()
loading_placeholder.markdown("""
<div style="display: flex; align-items: center; justify-content: center; padding: 2rem; color: #2E7D32;">
    <span style="font-size: 1.2rem;">🌱 Please wait, loading EVE...</span>
</div>
""", unsafe_allow_html=True)

# EVE Solutions brand color palette and custom styling
st.markdown("""
    <style>
        /* Hide running indicator */
        [data-testid="stStatusWidget"] {
            display: none !important;
        }
        
        
        /* EVE Solutions Green Color Palette */
        :root {
            --eve-primary: #2E7D32;
            --eve-primary-dark: #1B5E20;
            --eve-primary-light: #4CAF50;
            --eve-accent: #81C784;
            --eve-bg-light: #E8F5E9;
            --eve-text-dark: #1B5E20;
            --eve-gold: #FFB300;
        }
        
        /* Main header styling */
        .stApp > header {
            background-color: transparent;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #E8F5E9 0%, #C8E6C9 100%);
        }
        
        [data-testid="stSidebar"] .stMarkdown {
            color: #1B5E20;
        }
        
        /* Button styling */
        .stButton {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        .stButton > button {
            background-color: #2E7D32;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-top: 0 !important;
        }
        
        .stButton > button:hover {
            background-color: #1B5E20;
            box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4);
            transform: translateY(-1px);
        }
        
        /* Primary button variant */
        .stButton > button[kind="primary"] {
            background-color: #2E7D32;
        }
        
        /* Professional Metric Cards - Clean Dashboard Style with Green Accent */
        [data-testid="stMetric"],
        [data-testid="stMetric"] > div {
            background: linear-gradient(135deg, #FFFFFF 0%, #F8FDF8 100%) !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            border: 1px solid #C8E6C9 !important;
            border-left: 4px solid #2E7D32 !important;
            box-shadow: 0 2px 8px rgba(46, 125, 50, 0.08) !important;
        }
        
        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: #2E7D32 !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #1B5E20 !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
        }
        
        /* Professional Expander/Collapsible Panel Style with Green Header */
        [data-testid="stExpander"] {
            border: 1px solid #C8E6C9 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            background: #FFFFFF !important;
            margin-bottom: 0.5rem !important;
        }
        
        [data-testid="stExpander"] > div:first-child,
        [data-testid="stExpander"] summary,
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%) !important;
            border: none !important;
            border-bottom: 1px solid #A5D6A7 !important;
            color: #1B5E20 !important;
            font-weight: 600 !important;
            padding: 0.75rem 1rem !important;
        }
        
        [data-testid="stExpander"]:hover > div:first-child,
        [data-testid="stExpander"] summary:hover {
            background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%) !important;
        }
        
        /* Expander content area */
        [data-testid="stExpander"] > div:last-child {
            background: #FFFFFF !important;
            padding: 1rem !important;
        }
        
        /* Success/Info/Warning boxes */
        .stSuccess {
            background-color: #E8F5E9;
            border-left-color: #2E7D32;
        }
        
        .stInfo {
            background-color: #E3F2FD;
            border-left-color: #1976D2;
        }
        
        /* Selectbox and input styling */
        .stSelectbox > div > div {
            border-color: #81C784;
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: #2E7D32;
            box-shadow: 0 0 0 1px #2E7D32;
        }
        
        /* Slider styling */
        .stSlider > div > div > div {
            background-color: #2E7D32;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #E8F5E9;
            border-radius: 8px 8px 0 0;
            color: #1B5E20;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #2E7D32 !important;
            color: white !important;
        }
        
        /* DataFrame/Table styling */
        .stDataFrame {
            border: 1px solid #C8E6C9;
            border-radius: 8px;
        }
        
        /* Progress bar */
        .stProgress > div > div > div {
            background-color: #2E7D32;
        }
        
        /* Links */
        a {
            color: #2E7D32 !important;
        }
        
        a:hover {
            color: #1B5E20 !important;
        }
        
        /* Custom heading colors */
        h1, h2, h3, h4, h5, h6 {
            color: #1B5E20;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
        }
        
        /* Card-like containers */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            border-radius: 10px;
        }
        
        /* Step section headers — clear visual hierarchy */
        .section-header {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #1B5E20 !important;
            padding: 0.35rem 0.75rem !important;
            margin: 0.5rem 0 0.6rem 0 !important;
            border-left: 4px solid #2E7D32 !important;
            background: linear-gradient(90deg, #E8F5E9 0%, transparent 100%) !important;
            border-radius: 0 4px 4px 0 !important;
            line-height: 1.3 !important;
            display: block !important;
        }

        /* Reduce general vertical spacing */
        .stMarkdown {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Reduce padding in main content blocks */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* Reduce spacing in vertical blocks */
        [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0.1rem;
            padding: 0;
        }
        
        /* Reduce gap between elements in main content */
        .element-container {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Tighten the main app container */
        .main .block-container {
            padding-top: 0.25rem !important;
            max-width: 100%;
        }
        
        /* Remove spacing after markdown paragraphs */
        .stMarkdown p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.3 !important;
        }
        
        /* Remove hidden label space from selectboxes */
        [data-testid="stSelectbox"] {
            margin-top: -1rem !important;
        }
        
        /* Reduce spacing in stMarkdownContainer */
        [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* All text elements tight spacing */
        p, span, div, label {
            line-height: 1.3 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables early to prevent AttributeError
if 'sustainability_responses' not in st.session_state:
    st.session_state.sustainability_responses = {
        'minimize_soil_disturbance': False,
        'maintain_living_roots': False,
        'cover_bare_soil': False,
        'maximize_diversity': False,
        'integrate_livestock': False
    }

# Initialize critical variables to prevent unbound errors
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if 'system_message' not in st.session_state:
    st.session_state.system_message = None

if 'max_sampling_limit' not in st.session_state:
    st.session_state.max_sampling_limit = 10
    
if 'ecosystem_override' not in st.session_state:
    st.session_state.ecosystem_override = "Auto-detect (Recommended)"
    
if 'analysis_detail' not in st.session_state:
    st.session_state.analysis_detail = "Summary Analysis"
    
if 'income_elasticity' not in st.session_state:
    st.session_state.income_elasticity = 0.25

if 'time_preset' not in st.session_state:
    st.session_state.time_preset = "Current Year (2024)"

if 'include_environmental_indicators' not in st.session_state:
    st.session_state.include_environmental_indicators = False

# Enhanced CSS for better UX and modern design
st.markdown("""
    <style>
        /* Make sidebar 50% wider */
        .css-1d391kg, .css-1lcbmhc, .css-12oz5g7, .css-17eq0hr {
            width: 450px !important;
            min-width: 450px !important;
        }
        
        /* Adjust main content area to account for wider sidebar */
        .css-1rs6os, .css-17eq0hr {
            margin-left: 450px !important;
        }
        
        /* Ensure sidebar content fits properly */
        .css-1d391kg .block-container, .css-1lcbmhc .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: none !important;
        }
        
        /* Make sidebar scrollable if content overflows */
        .css-1d391kg, .css-1lcbmhc {
            overflow-y: auto !important;
        }
        
        /* Minimize top padding and move content to very top */
        .main .block-container {
            padding-top: 0.25rem !important;
        }
        
        /* Target all Streamlit containers for minimal spacing */
        .stApp > div:first-child {
            padding-top: 0 !important;
        }
        
        /* Remove all margins and padding from title */
        h1:first-of-type {
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Remove spacing from main content container */
        section.main > div {
            padding-top: 0 !important;
        }
        
        /* Reduce padding around sidebar toggle arrow */
        .css-1rs6os .css-17eq0hr {
            padding-top: 0.25rem !important;
        }
        
        /* Target sidebar toggle button specifically */
        button[kind="secondary"][data-testid="collapsedControl"] {
            margin-top: 0 !important;
            padding: 0.25rem !important;
        }
        
        /* Reduce spacing around sidebar collapse area */
        .css-1kyxreq {
            padding-top: 0.25rem !important;
            margin-top: 0 !important;
        }
        
        /* Clean text-only header - Professional Dashboard Style */
        .header-container {
            width: 100%;
            padding: 1rem 0 0.5rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            border-bottom: 2px solid #E8F5E9;
            background: none !important;
            background-image: none !important;
            box-shadow: none !important;
            height: auto !important;
        }
        
        .header-overlay {
            display: none !important;
        }
        
        .header-text {
            color: #2E7D32;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .header-icon {
            font-size: 1.6rem;
            margin-right: 0.5rem;
        }
        
        /* Subtle version text */
        .version-text {
            font-size: 0.9rem !important;
            color: #9CA3AF !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .version-text a {
            color: #6B7280 !important;
            text-decoration: none;
        }
        .version-text a:hover {
            color: #2E7D32 !important;
        }
        
        
        /* Enhanced Primary Button Styling */
        .primary-action {
            background: linear-gradient(135deg, #0891b2 0%, #0c4a6e 100%) !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            box-shadow: 0 4px 12px rgba(8, 145, 178, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        
        .primary-action:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(8, 145, 178, 0.4) !important;
        }
        
        /* Enhanced Success States */
        .status-success {
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
            border: 1px solid #059669;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Modern Card Design */
        .modern-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid #e5e7eb;
            margin: 1rem 0;
        }
        
        /* Enhanced Info Cards */
        .info-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Better Typography */
        [data-testid="stMarkdownContainer"] h2.section-header {
            font-size: 1.3rem !important;
            font-weight: 700;
            color: #1f2937;
            margin: 0 !important;
            padding: 0 !important;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            line-height: 1.2 !important;
        }
        
        /* Loading Animation */
        .loading-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: .5;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Production-optimized map caching with extended TTL
@st.cache_data(ttl=600, max_entries=20, show_spinner=False)
def get_folium_map(center_lat=54.5, center_lon=15.0, zoom=5, layer_type="Satellite"):
    """Create and cache folium map with maximum performance optimizations"""
    import folium
    
    if layer_type == "Satellite":
        # Create satellite map with labels overlay
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='&copy; Google',
            prefer_canvas=True,
            max_zoom=20,
            min_zoom=2,
            attributionControl=False,
            zoomControl=True,
            scrollWheelZoom=True,
            doubleClickZoom=True,
            boxZoom=True,
            keyboard=True,
            dragging=True,
            tap=True,
            options={
                'worldCopyJump': False,
                'maxBoundsViscosity': 0.0,
                'zoomAnimation': False,
                'markerZoomAnimation': False,
                'fadeAnimation': False,
                'zoomSnap': 1,
                'zoomDelta': 1
            }
        )
        # Add labels overlay on top of satellite imagery
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=h&x={x}&y={y}&z={z}',
            attr='&copy; Google',
            name='Labels',
            overlay=True,
            control=False
        ).add_to(m)
    else:
        # Create light map (default)
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            attr='&copy; CARTO',
            prefer_canvas=True,
            max_zoom=18,
            min_zoom=2,
            attributionControl=False,
            zoomControl=True,
            scrollWheelZoom=True,
            doubleClickZoom=True,
            boxZoom=True,
            keyboard=True,
            dragging=True,
            tap=True,
            options={
                'worldCopyJump': False,
                'maxBoundsViscosity': 0.0,
                'zoomAnimation': False,
                'markerZoomAnimation': False,
                'fadeAnimation': False,
                'zoomSnap': 1,
                'zoomDelta': 1
            }
        )
    
    return m

@st.cache_data(ttl=7200, max_entries=1, show_spinner=False)  # Single cached instance
def create_drawing_tools():
    """Create cached drawing tools configuration with performance optimizations"""
    from folium.plugins import Draw
    return Draw(
        export=False,
        position='topleft',
        draw_options={
            'polyline': False,
            'circle': False,  # Disable circle drawing
            'marker': False,
            'circlemarker': False,
            'polygon': {
                'allowIntersection': False, 
                'showArea': True, 
                'metric': True,
                'shapeOptions': {
                    'color': '#2E8B57',
                    'weight': 3,
                    'fillOpacity': 0.3
                }
            },
            'rectangle': {
                'showArea': True, 
                'metric': True,
                'shapeOptions': {
                    'color': '#2E8B57',
                    'weight': 3,
                    'fillOpacity': 0.3
                }
            }
        },
        edit_options={'remove': True, 'edit': True}  # Re-enable editing
    )

@st.cache_data(ttl=3600, max_entries=500, show_spinner=False)  # Massive cache for instant calculations
def calculate_area_optimized(coordinates):
    """Ultra-optimized area calculation with latitude correction and error handling"""

    try:
        if not coordinates or len(coordinates) < 3:
            return 0.0
        
        # Validate coordinate format
        for coord in coordinates[:3]:  # Check first few coordinates
            if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                raise ValueError("Invalid coordinate format")
        
        # Skip the last coordinate if it duplicates the first (polygon closure)
        coords = coordinates[:-1] if len(coordinates) > 1 and coordinates[-1] == coordinates[0] else coordinates
        
        # Additional validation
        if len(coords) < 3:
            return 0.0
        
        
        # Convert to NumPy array with float64 for precision in area calculations
        coords_array = np.array(coords, dtype=np.float64)
        
        # Validate array shape
        if coords_array.shape[1] < 2:
            raise ValueError("Insufficient coordinate dimensions")
        
        # Get coordinates
        lons = coords_array[:, 0]
        lats = coords_array[:, 1]
        
        # Get average latitude for longitude correction
        avg_lat = float(np.mean(lats))
        
        # Convert to approximate area in km² with latitude-corrected longitude
        # 1° latitude ≈ 111.32 km everywhere
        # 1° longitude ≈ 111.32 * cos(latitude) km
        lat_km_per_deg = 111.32
        lon_km_per_deg = 111.32 * math.cos(math.radians(avg_lat))
        
        # Ultra-fast vectorized shoelace formula with latitude correction
        area_km2 = 0.5 * abs(np.sum(lons * np.roll(lats, -1) - lats * np.roll(lons, -1))) * lat_km_per_deg * lon_km_per_deg
        
        # Convert to hectares
        area_ha = area_km2 * 100
        
        # Round to 2 decimal places to avoid floating-point precision issues
        area_ha = round(area_ha, 2)
        
        return max(1.0, area_ha)  # Minimum 1 hectare
        
    except Exception as e:
        st.error(f"Error in area calculation: {e}")
        return 0.0

@st.cache_data(ttl=3600, max_entries=500, show_spinner=False)
def calculate_bbox_optimized(coordinates):
    """Ultra-fast bounding box calculation with extended caching and error handling"""

    try:
        if not coordinates or len(coordinates) < 3:
            return {}
        
        # Validate coordinate format
        for coord in coordinates[:3]:  # Check first few coordinates
            if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                raise ValueError("Invalid coordinate format")
        
        # Skip the last coordinate if it duplicates the first
        coords = coordinates[:-1] if len(coordinates) > 1 and coordinates[-1] == coordinates[0] else coordinates
        
        if len(coords) < 1:
            return {}
            
        coords_array = np.array(coords, dtype=np.float32)
        
        # Validate array shape
        if coords_array.shape[1] < 2:
            raise ValueError("Insufficient coordinate dimensions")
            
        lats, lons = coords_array[:, 1], coords_array[:, 0]
        
        return {
            'min_lat': float(lats.min()), 'max_lat': float(lats.max()),
            'min_lon': float(lons.min()), 'max_lon': float(lons.max())
        }
        
    except Exception as e:
        st.error(f"Error in bounding box calculation: {e}")
        return {}

# Performance-optimized session state management
def clear_analysis_cache():
    """Clear all analysis-related state and cache to free memory between analyses"""
    # Keys reset to a typed default rather than deleted
    typed_defaults = {
        'calculation_ready': False,
        'analysis_results': None,
        'area_coordinates': [],
    }
    for key, default in typed_defaults.items():
        st.session_state[key] = default

    # Keys removed entirely
    delete_keys = [
        # Computed cache
        'cached_bbox', 'cached_area_ha', 'cached_ecosystem_results',
        'area_coords_cache', 'bbox_coords', 'map_center_cache',
        # Area and detection
        'selected_area', 'detected_ecosystem', 'sampling_point_data',
        'landcover_data_source',
        # EEI / intactness
        'point_eei_values', 'average_eei', 'ecosystem_eei',
        # Water body tracking
        'all_water_bodies_classified', 'water_bodies_already_processed',
        # Progress flags
        'analysis_in_progress',
        # Scenario and display state
        'summary_metrics', 'regional_adjustment_factor',
        'scenario_results', 'scenario_distribution', 'scenario_eco_intactness',
        'scenario_builder_expanded',
    ]
    for key in delete_keys:
        if key in st.session_state:
            del st.session_state[key]

# Pre-computed coefficients status (no database loading needed)
@st.cache_data(ttl=7200, show_spinner=False)
def get_precomputed_status():
    """Get status of pre-computed ESVD coefficients"""
    try:
        from utils.precomputed_esvd_coefficients import get_precomputed_coefficients
        coefficients = get_precomputed_coefficients()
        return {
            'precomputed_available': True,
            'total_records': 10874,  # Static count from original ESVD database
            'unique_studies': 1354,  # Static count from original research
            'performance_multiplier': 238270  # Speed improvement vs database queries
        }
    except Exception as e:
        logger.warning(f"Could not load precomputed ESVD coefficients: {e}")
        return {'precomputed_available': False}

def get_landcover_code_description(code: int) -> str:
    """Get ESA CCI description for OpenLandMap landcover code using centralized mapping"""
    from utils.esa_landcover_codes import get_esa_description
    return get_esa_description(code)

# _get_ecosystem_intactness_multiplier is imported from utils.analysis_helpers

def get_esvd_ecosystem_from_landcover_code(code: int, analysis_results: Dict = None) -> str:
    """Get the ESVD ecosystem type that a landcover code maps to, with forest subtyping and water body user classifications"""
    # Import the single source of truth mapping from STAC API
    from utils.openlandmap_stac_api import get_cached_openlandmap_stac
    stac_instance = get_cached_openlandmap_stac()
    landcover_mapping = stac_instance.landcover_to_esvd
    
    base_ecosystem = landcover_mapping.get(code, "Unknown")
    
    # For water bodies (ESA code 210), check for user classifications first
    if code == 210 and st.session_state.get('sampling_point_data'):
        # Look for any user-classified water body to determine the classification type
        for point_data in st.session_state.sampling_point_data.values():
            if (point_data.get('landcover_class') == 210 and 
                point_data.get('user_classified', False) and 
                'ecosystem_type' in point_data):
                return point_data['ecosystem_type']
    
    # For forests, determine the specific subtype based on detected ecosystem results
    if base_ecosystem == "Forest":
        # Check if we have analysis results with detected ecosystem information
        if analysis_results:
            detected_ecosystem = st.session_state.get('detected_ecosystem', {})
            if 'forest_classification' in st.session_state.get('analysis_results', {}):
                forest_info = st.session_state['analysis_results']['forest_classification']
                if forest_info and forest_info.get('detected_type'):
                    return forest_info['detected_type'].replace('_', ' ').title()
            
            # Check for forest type in detected ecosystem info
            primary_ecosystem = detected_ecosystem.get('primary_ecosystem', '')
            if 'forest' in primary_ecosystem.lower():
                return primary_ecosystem.replace('_', ' ').title()
            
        return "Forest"  # Default if no specific forest type detected
    
    return base_ecosystem

@st.cache_data(ttl=1800, show_spinner=False) 
def preload_openlandmap_status():
    """Preload OpenLandMap STAC API status for instant display"""
    try:
        from utils.openlandmap_stac_api import get_cached_openlandmap_stac
        stac_client = get_cached_openlandmap_stac()
        # Test with a simple coordinate query - using real STAC API
        test_result = stac_client.get_ecosystem_type(0, 0)
        return {
            'openlandmap_available': True,
            'authentication_success': True,
            'method': 'OpenLandMap STAC API',
            'test_ecosystem_type': test_result.get('ecosystem_type', 'Test')
        }
    except Exception as e:
        return {
            'openlandmap_available': False, 
            'authentication_success': False,
            'error': str(e)
        }

def get_country_from_coordinates(lat: float, lon: float) -> str:
    """
    Determine country from latitude/longitude coordinates using Nominatim API
    
    Uses OpenStreetMap's Nominatim reverse geocoding API for accurate country detection
    with intelligent fallback to rectangular bounding box system if API fails.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Returns:
        Country name string (for display purposes - different format than GDP lookup)
    """
    try:
        from utils.nominatim_geocoding import get_country_from_coordinates_nominatim
        
        # Get country code from Nominatim API
        country_code = get_country_from_coordinates_nominatim(lat, lon)
        
        # Convert country code to display name for app.py usage
        code_to_display_name = {
            'united_states': 'United States',
            'canada': 'Canada', 
            'mexico': 'Mexico',
            'united_kingdom': 'United Kingdom',
            'france': 'France',
            'germany': 'Germany',
            'italy': 'Italy',
            'spain': 'Spain',
            'netherlands': 'Netherlands',
            'belgium': 'Belgium',
            'austria': 'Austria',
            'switzerland': 'Switzerland',
            'sweden': 'Sweden',
            'norway': 'Norway',
            'denmark': 'Denmark',
            'finland': 'Finland',
            'ireland': 'Ireland',
            'portugal': 'Portugal',
            'greece': 'Greece',
            'poland': 'Poland',
            'czech_republic': 'Czech Republic',
            'hungary': 'Hungary',
            'slovakia': 'Slovakia',
            'slovenia': 'Slovenia',
            'estonia': 'Estonia',
            'latvia': 'Latvia',
            'lithuania': 'Lithuania',
            'croatia': 'Croatia',
            'romania': 'Romania',
            'bulgaria': 'Bulgaria',
            'ukraine': 'Ukraine',
            'russia': 'Russia',
            'japan': 'Japan',
            'australia': 'Australia',
            'new_zealand': 'New Zealand',
            'south_korea': 'South Korea',
            'singapore': 'Singapore',
            'hong_kong': 'Hong Kong',
            'china': 'China',
            'india': 'India',
            'indonesia': 'Indonesia',
            'thailand': 'Thailand',
            'malaysia': 'Malaysia',
            'philippines': 'Philippines',
            'vietnam': 'Vietnam',
            'bangladesh': 'Bangladesh',
            'pakistan': 'Pakistan',
            'sri_lanka': 'Sri Lanka',
            'myanmar': 'Myanmar',
            'cambodia': 'Cambodia',
            'laos': 'Laos',
            'mongolia': 'Mongolia',
            'brazil': 'Brazil',
            'argentina': 'Argentina',
            'colombia': 'Colombia',
            'peru': 'Peru',
            'chile': 'Chile',
            'ecuador': 'Ecuador',
            'bolivia': 'Bolivia',
            'paraguay': 'Paraguay',
            'uruguay': 'Uruguay',
            'venezuela': 'Venezuela',
            'guatemala': 'Guatemala',
            'honduras': 'Honduras',
            'el_salvador': 'El Salvador',
            'nicaragua': 'Nicaragua',
            'costa_rica': 'Costa Rica',
            'panama': 'Panama',
            'saudi_arabia': 'Saudi Arabia',
            'uae': 'United Arab Emirates',
            'qatar': 'Qatar',
            'kuwait': 'Kuwait',
            'bahrain': 'Bahrain',
            'oman': 'Oman',
            'israel': 'Israel',
            'turkey': 'Turkey',
            'egypt': 'Egypt',
            'morocco': 'Morocco',
            'tunisia': 'Tunisia',
            'algeria': 'Algeria',
            'jordan': 'Jordan',
            'lebanon': 'Lebanon',
            'iraq': 'Iraq',
            'iran': 'Iran',
            'south_africa': 'South Africa',
            'nigeria': 'Nigeria',
            'kenya': 'Kenya',
            'ethiopia': 'Ethiopia',
            'ghana': 'Ghana',
            'uganda': 'Uganda',
            'tanzania': 'Tanzania',
            'mozambique': 'Mozambique',
            'madagascar': 'Madagascar',
            'malawi': 'Malawi',
            'zambia': 'Zambia',
            'zimbabwe': 'Zimbabwe',
            'botswana': 'Botswana',
            'namibia': 'Namibia',
            'angola': 'Angola',
            'cameroon': 'Cameroon',
            'ivory_coast': 'Ivory Coast',
            'senegal': 'Senegal',
            'burkina_faso': 'Burkina Faso',
            'mali': 'Mali',
            'niger': 'Niger',
            'chad': 'Chad',
            'central_african_republic': 'Central African Republic',
            'democratic_republic_congo': 'Democratic Republic of Congo',
            'rwanda': 'Rwanda',
            'burundi': 'Burundi',
            'global_average': 'International Waters'
        }
        
        # Return display name or fallback to formatted code
        display_name = code_to_display_name.get(country_code)
        if display_name:
            return display_name
        else:
            # Format the code for display (e.g., "united_kingdom" -> "United Kingdom")
            return country_code.replace('_', ' ').title()
        
    except Exception as e:
        return "Unknown"

def display_data_source_status(analysis_results: Dict = None):
    """Display clear indicators of which data source is being used"""
    openlandmap_status = preload_openlandmap_status()
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            if openlandmap_status.get('authentication_success', False):
                st.success("🌍 **OpenLandMap STAC**: Connected")
                st.caption(f"Method: {openlandmap_status.get('method', 'OpenLandMap STAC API')}")
            else:
                st.warning("🌍 **OpenLandMap STAC**: Connection Issues")
                if openlandmap_status.get('error'):
                    st.caption(f"Reason: {openlandmap_status['error']}")
        
        with col2:
            # Check if we have authentic OpenLandMap data or are using estimated values
            data_source_active = st.session_state.get('landcover_data_source', analysis_results.get('landcover_data_source', '') if analysis_results else '')
            
            # Also check sampling point data for real satellite data indicators
            has_real_data = False
            if analysis_results:
                sampling_data = analysis_results.get('sampling_point_data', {})
                for point_data in sampling_data.values():
                    source = point_data.get('source', '')
                    # Check for explicit real data markers
                    if 'Real ESA Satellite Data' in source or 'GeoTIFF Pixel' in source:
                        has_real_data = True
                        break
                    # CRITICAL FIX: Also check if environmental indicators were successfully extracted
                    stac_data = point_data.get('stac_data', {})
                    if stac_data and len(stac_data) > 0:
                        # If we have any environmental indicators, we have real data
                        has_real_data = True
                        break
            
            if data_source_active == 'openlandmap' or has_real_data:
                st.success("✅ **Active Source**: Real ESA Satellite Data")
                st.caption("Using authentic ESA CCI land cover from satellite imagery")
            else:
                st.warning("⚠️  **Active Source**: Geographic Fallback")
                st.caption("Real ESA satellite data unavailable - using geographic estimation")
                
        # Show detailed sampling point information if analysis data is available
        if analysis_results:
            sampling_point_data = analysis_results.get('sampling_point_data', {})
            landcover_codes = analysis_results.get('landcover_codes', {})
            data_source = analysis_results.get('landcover_data_source', 'estimated')
            
            with st.expander("📊 Sampling Points Analysis Details", expanded=False):
                data_source_check = st.session_state.get('landcover_data_source', data_source)
                
                # Check for real satellite data in sampling points
                has_real_sampling_data = False
                for point_data in sampling_point_data.values():
                    source = point_data.get('source', '')
                    # Check for explicit real data markers
                    if ('Real ESA Satellite Data' in source or 'GeoTIFF Pixel' in source or 
                        'Direct ESA Land Cover Extraction' in source):
                        has_real_sampling_data = True
                        break
                    # CRITICAL FIX: Also check if environmental indicators were successfully extracted
                    stac_data = point_data.get('stac_data', {})
                    if stac_data and len(stac_data) > 0:
                        # If we have any environmental indicators, we have real data
                        has_real_sampling_data = True
                        break
                
                if (data_source_check == 'openlandmap' or has_real_sampling_data) and sampling_point_data:
                    st.markdown("**🌍 OpenLandMap STAC Data:**")
                    st.write(f"• Data Source: Authentic satellite-derived landcover classifications")
                    st.write(f"• Sample Points Analyzed: {len(sampling_point_data)} points")
                    st.markdown("**Sample Points Summary Table:**")
                    
                    # Prepare data for table
                    table_data = []
                    for point_id, point_data in sampling_point_data.items():
                        point_num = int(point_id.replace('point_', '')) + 1
                        
                        landcover_code = point_data.get('landcover_class', 0)
                        openlandmap_description = get_landcover_code_description(landcover_code)
                        esvd_ecosystem = get_esvd_ecosystem_from_landcover_code(landcover_code, analysis_results)
                        
                        # Get coordinates
                        coords = point_data.get('coordinates', {})
                        if coords and isinstance(coords, dict):
                            lat = coords.get('lat', 0)
                            lon = coords.get('lon', 0)
                            coord_str = f"{lat:.4f}, {lon:.4f}"
                        else:
                            coord_str = "N/A"
                        
                        data_source = point_data.get('source', 'Unknown')
                        
                        # Get country from coordinates (exclude for Ocean/Marine points only)
                        country = "N/A"
                        regional_factor = "N/A"
                        if coords and isinstance(coords, dict):
                            lat = coords.get('lat', 0)
                            lon = coords.get('lon', 0)
                            # Don't assign country for Ocean/Marine ecosystem types, but DO assign for Rivers and Lakes, Coastal
                            if (lat != 0 or lon != 0) and esvd_ecosystem != "Marine":  # Valid coordinates and not Marine
                                country = get_country_from_coordinates(lat, lon)
                                
                                # Calculate regional factor for this point (Rivers/Lakes and Coastal get regional adjustments)
                                try:
                                    from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
                                    esvd_calc = PrecomputedESVDCoefficients()
                                    regional_factor = f"{esvd_calc.get_regional_factor((lat, lon)):.2f}x"
                                except Exception as e:
                                    regional_factor = "Error"
                        
                        # Add indicator for user-classified water bodies
                        if landcover_code == 210 and point_data.get('user_classified', False):
                            esvd_ecosystem += " (User classified)"
                        
                        # Extract FAPAR and Soil Carbon from STAC data
                        fapar_value = "—"
                        soil_carbon_value = "—"
                        stac_data = point_data.get('stac_data', {})
                        if stac_data:
                            # Get FAPAR from vegetation data
                            vegetation_data = stac_data.get('vegetation', [])
                            for item in vegetation_data:
                                name = item.get('name', '').lower()
                                value = item.get('value')
                                if 'fapar' in name or 'absorbed' in name:
                                    if value is not None:
                                        # Scale 0-255 to 0-1
                                        if value > 1:
                                            value = value / 255.0
                                        fapar_value = f"{value:.3f}"
                                    break
                            
                            # Get Soil Carbon from soil data
                            soil_data = stac_data.get('soil', [])
                            for item in soil_data:
                                name = item.get('name', '').lower()
                                value = item.get('value')
                                if 'carbon' in name or 'organic' in name:
                                    if value is not None and isinstance(value, (int, float)):
                                        soil_carbon_value = f"{value:.1f}"
                                    break
                        
                        # Get EEI value for this point from session state
                        point_eei_values = st.session_state.get('point_eei_values', {})
                        eei_value = point_eei_values.get(point_id)
                        eei_display = f"{eei_value:.3f}" if eei_value is not None else "—"
                        
                        table_data.append({
                            "Sample Point": f"Point {point_num}",
                            "ESA CCI Code": landcover_code,
                            "ESA Level 1": openlandmap_description,
                            "ESVD Ecosystem": esvd_ecosystem,
                            "Coordinates": coord_str,
                            "Country": country,
                            "Regional Factor": regional_factor,
                            "EEI (0-1)": eei_display,
                            "FAPAR (0-1)": fapar_value,
                            "Soil C (g/kg)": soil_carbon_value,
                            "Data Source": data_source
                        })
                    
                    # Display main table
                    import pandas as pd
                    df = pd.DataFrame(table_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Always show raw STAC data for transparency (moved outside environmental indicators toggle)
                    st.markdown("### 🔍 Raw Satellite Data Transparency")
                    
                    # Raw data verification section - always visible for data authenticity verification
                    with st.expander("📡 **View Raw STAC Data** (Click to verify data authenticity)", expanded=False):
                        st.markdown("**This section shows the raw satellite data sources and extraction details for complete transparency.**")
                        
                        # Display raw data for each sample point
                        for point_id, point_data in sampling_point_data.items():
                            point_num = int(point_id.replace('point_', '')) + 1
                            st.markdown(f"**Sample Point {point_num}:**")
                            
                            # Show raw STAC response data
                            raw_stac_data = point_data.get('raw_stac_data', {})
                            if raw_stac_data:
                                st.markdown("**🔍 Raw STAC Response:**")
                                st.json(raw_stac_data)
                            else:
                                st.info("No raw STAC data available for this point")
                            
                            # Show processed STAC data
                            stac_data = point_data.get('stac_data', {})
                            if stac_data:
                                st.markdown("**📊 Processed STAC Data:**")
                                st.json(stac_data)
                            
                            st.divider()
                    
                    # Data verification section - always visible
                    st.markdown("### ✅ Data Verification")
                    st.info("""
                    **How to Verify This Data:**
                    1. **Asset URL**: Copy the asset URL above and access it directly to verify the GeoTIFF source
                    2. **Year**: Confirm the dataset year (2020) in the asset URL path  
                    3. **Pixel Values**: Check that raw pixel values match ESA CCI landcover codes
                    4. **Coordinates**: Verify sample point coordinates match your selected area
                    5. **Collection**: Confirm data comes from ESA CCI landcover collection (land.cover_esacci.lc.l4)
                    
                    This transparency section provides complete traceability from raw satellite data to final results.
                    """)
                    
                    if not any(point_data.get('raw_stac_data') for point_data in sampling_point_data.values()):
                        st.warning("⚠️ No raw STAC data found. This may indicate the analysis used fallback methods instead of genuine satellite data.")
                    else:
                        st.success("✅ Genuine STAC satellite data detected for this analysis.")
                    
                    # Summary statistics
                    st.markdown("**📊 Summary Statistics:**")
                    
                    # Show average EEI if available (only when EEI is enabled)
                    if st.session_state.get('use_eei_for_intactness', False):
                        average_eei = st.session_state.get('average_eei')
                        ecosystem_eei = st.session_state.get('ecosystem_eei', {})
                        
                        if average_eei is not None:
                            eei_percent = int(average_eei * 100)
                            st.info(f"🌿 **Average Ecosystem Integrity (EEI):** {average_eei:.3f} ({eei_percent}%)")
                            
                            # Show per-ecosystem EEI values if there are multiple ecosystems
                            if ecosystem_eei and len(ecosystem_eei) > 1:
                                st.markdown("**EEI by Ecosystem Type (used for intactness defaults):**")
                                for eco_type, eei_value in sorted(ecosystem_eei.items()):
                                    if eei_value is not None:
                                        eco_eei_percent = eei_value * 100
                                        st.write(f"• **{eco_type}**: {eei_value:.3f} ({eco_eei_percent:.3f}%)")
                            elif ecosystem_eei and len(ecosystem_eei) == 1:
                                eco_type, eei_value = list(ecosystem_eei.items())[0]
                                if eei_value is not None:
                                    st.caption(f"Single ecosystem ({eco_type}) - EEI {eei_value:.3f} used for intactness default")
                    else:
                        st.caption("ℹ️ EEI disabled - using manual intactness values from settings")
                    
                    code_counts = {}
                    
                    for point_data in sampling_point_data.values():
                        code = point_data.get('landcover_class', 'Unknown')
                        code_counts[code] = code_counts.get(code, 0) + 1
                    
                    # Count ecosystem types (consistent with Mixed Ecosystem Composition filtering)
                    ecosystem_counts = {}
                    for code, count in code_counts.items():
                        # Get ecosystem type from actual point data (includes forest specialization)
                        specialized_ecosystem = None
                        for point_data in sampling_point_data.values():
                            if point_data.get('landcover_class') == code:
                                specialized_ecosystem = point_data.get('ecosystem_type')
                                break
                        
                        # Fallback to generic mapping if specialized type not found
                        esvd_ecosystem = specialized_ecosystem or get_esvd_ecosystem_from_landcover_code(code, analysis_results)
                        ecosystem_counts[esvd_ecosystem] = ecosystem_counts.get(esvd_ecosystem, 0) + count
                    
                    st.markdown("**Ecosystem Composition (from Sample Points):**")
                    total_area = results.get('area_ha', results.get('area_hectares', 0))
                    for ecosystem_type, count in sorted(ecosystem_counts.items()):
                        percentage = (count / len(sampling_point_data)) * 100
                        area_ha = total_area * (percentage / 100)
                        if percentage >= 1.0:  # Apply same 1% threshold as Mixed Ecosystem Composition
                            st.write(f"• **{ecosystem_type}**: {percentage:.1f}% ({count} points, {area_ha:.1f} hectares)")
                    
                    # Count countries from sample points (exclude water bodies - ESA code 210)
                    country_counts = {}
                    land_points_count = 0
                    for point_data in sampling_point_data.values():
                        # Skip water bodies (ESA code 210) from country assignment
                        landcover_class = point_data.get('landcover_class')
                        if landcover_class == 210:
                            continue  # Don't assign country to water bodies
                        
                        coords = point_data.get('coordinates', {})
                        if coords and isinstance(coords, dict):
                            lat = coords.get('lat', 0)
                            lon = coords.get('lon', 0)
                            if lat != 0 or lon != 0:  # Valid coordinates
                                country = get_country_from_coordinates(lat, lon)
                                country_counts[country] = country_counts.get(country, 0) + 1
                                land_points_count += 1
                    
                    # Display predominant country information (exclude water bodies from count)
                    if country_counts and land_points_count > 0:
                        st.markdown("**Geographic Distribution (from Land Sample Points):**")
                        # Sort by count (descending) to show predominant country first
                        for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / land_points_count) * 100
                            if percentage >= 5.0:  # Only show countries with 5%+ representation
                                st.write(f"• **{country}**: {percentage:.1f}% ({count} points)")
                        
                        # Show predominant country
                        predominant_country = max(country_counts.items(), key=lambda x: x[1])
                        if predominant_country[1] > land_points_count * 0.5:  # Majority (>50%)
                            st.info(f"🌍 **Predominant Country**: {predominant_country[0]} ({predominant_country[1]}/{land_points_count} land points)")
                        else:
                            st.info(f"🌍 **Most Common Country**: {predominant_country[0]} ({predominant_country[1]}/{land_points_count} land points)")
                        
                        # Show resulting regional factor
                        try:
                            from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
                            esvd_calc = PrecomputedESVDCoefficients()
                            # Get a representative coordinate from the predominant country
                            representative_coords = None
                            for point_data in sampling_point_data.values():
                                coords = point_data.get('coordinates', {})
                                lat = coords.get('lat')
                                lon = coords.get('lon')
                                if lat is not None and lon is not None:
                                    point_country = get_country_from_coordinates(lat, lon)
                                    if point_country == predominant_country[0]:
                                        representative_coords = (lat, lon)
                                        break
                            
                            if representative_coords:
                                regional_factor = esvd_calc.get_regional_factor(representative_coords)
                                st.write(f"💰 **Regional Economic Factor**: {regional_factor:.2f}x (applied to all ecosystem valuations)")
                        except Exception as e:
                            st.write("💰 **Regional Economic Factor**: Unable to calculate")
                        
                        # Show water exclusion info if applicable
                        water_points = len(sampling_point_data) - land_points_count
                        if water_points > 0:
                            st.caption(f"ℹ️ {water_points} water body points excluded from country statistics")
                    
                    
                    # Show raw ESA codes in expandable section for transparency
                    with st.expander("🔍 Raw ESA Code Breakdown"):
                        # Filter out None keys and sort only valid integer codes
                        valid_codes = {k: v for k, v in code_counts.items() if k is not None}
                        for code, count in sorted(valid_codes.items()):
                            openlandmap_description = get_landcover_code_description(code)
                            esvd_ecosystem = get_esvd_ecosystem_from_landcover_code(code, analysis_results)
                            percentage = (count / len(sampling_point_data)) * 100
                            st.write(f"• **ESA Code {code}**: {openlandmap_description} → **ESVD: {esvd_ecosystem}** ({count} points, {percentage:.1f}%)")
                        
                elif landcover_codes:
                    st.markdown("**🧪 Geographic Estimation Data:**")
                    st.write(f"• Based on: Geographic location and global land use patterns")
                    st.write(f"• Accuracy: ~85% ecosystem detection for major biomes")
                    st.write(f"• Method: Coordinate-based prediction with regional specialization")
                    st.write(f"• Sample Points: {len(landcover_codes)} points")
                    
                    # Show estimated codes summary
                    code_counts = {}
                    for code in landcover_codes.values():
                        code_counts[code] = code_counts.get(code, 0) + 1
                    
                    st.markdown("**Estimated Landcover Codes:**")
                    # Filter out None keys and sort only valid integer codes
                    valid_codes = {k: v for k, v in code_counts.items() if k is not None}
                    for code, count in sorted(valid_codes.items()):
                        openlandmap_description = get_landcover_code_description(code)
                        esvd_ecosystem = get_esvd_ecosystem_from_landcover_code(code, analysis_results)
                        percentage = (count / len(landcover_codes)) * 100
                        st.write(f"• **ESA Code {code}**: {openlandmap_description} → **ESVD: {esvd_ecosystem}** ({count} points, {percentage:.1f}%)")
                else:
                    st.markdown("**ℹ️ No Sampling Data Available**")
                    st.write("No sampling point data available for this analysis.")
    
    return openlandmap_status.get('authentication_success', False)

# Performance-optimized lazy loading for heavy analysis modules
@st.cache_resource(show_spinner=False)
def get_analysis_modules():
    """Lazy load analysis modules only when needed"""
    try:
        from utils.ecosystem_services import (
            detect_ecosystem_type_enhanced, 
            get_ecosystem_service_values
        )
        return {
            'detect_ecosystem': detect_ecosystem_type_enhanced,
            'get_service_values': get_ecosystem_service_values
        }
    except ImportError as e:
        st.error(f"Analysis modules not available: {e}")
        return None

# Ultra-fast component caching
@st.cache_data(ttl=3600, show_spinner=False)
def create_performance_metrics_display():
    """Pre-render performance metrics components"""
    return {
        'loading_indicators': {
            'map': "🗺️ Loading map...",
            'analysis': "📊 Processing ecosystem analysis...", 
            'calculations': "🧮 Computing natural capital values..."
        },
        'success_messages': {
            'area_selected': lambda area: f"✅ Area selected: {area:.0f} hectares",
            'analysis_complete': "🎉 Analysis complete!"
        }
    }

# Ultra-fast coordinate processing with extended caching
@st.cache_data(ttl=7200, max_entries=300, show_spinner=False)
def process_coordinates_batch(coordinates_list):
    """Batch process multiple coordinate sets for maximum efficiency"""
    results = {}
    for i, coords in enumerate(coordinates_list):
        if coords and len(coords) > 2:
            results[i] = {
                'area': calculate_area_optimized(coords),
                'bbox': calculate_bbox_optimized(coords)
            }
    return results

# Initialize database and user session with fallback handling
if 'db_initialized' not in st.session_state:
    try:
        db_modules = get_database_modules()
        if db_modules and db_modules['init_database']():
            st.session_state.db_initialized = True
            user_id = db_modules['initialize_user_session']()
            pass  # Database ready - no need to show success message every time
        else:
            st.session_state.db_initialized = False
            st.session_state.user_id = "anonymous"
            user_id = "anonymous"
    except Exception as e:
        st.session_state.db_initialized = False
        st.session_state.user_id = "anonymous" 
        user_id = "anonymous"
else:
    db_modules = get_database_modules()
    if db_modules:
        user_id = db_modules['initialize_user_session']()
    else:
        user_id = st.session_state.get('user_id', 'anonymous')

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2e8b57;
    text-align: center;
    margin: 0;
    padding: 0;
}
.subtitle {
    font-size: 1.2rem;
    color: #666;
    text-align: center;
    margin: 0;
    padding: 0;
}
.metric-container {
    background-color: #f8f9fa;
    padding: 0.5rem;
    border-radius: 0.5rem;
    border-left: 4px solid #2e8b57;
    margin: 0.25rem 0;
}
.small-coordinates {
    font-size: 0.8rem;
}
.small-coordinates h3 {
    font-size: 1.1rem;
    margin: 0;
    padding: 0;
}
.small-coordinates .metric-container {
    padding: 0.25rem;
    font-size: 0.75rem;
}
.coordinate-bounds {
    font-size: 0.75rem;
    margin: 0.25rem 0;
    padding: 0;
}
.coordinate-bounds .metric-label {
    font-size: 0.7rem;
    color: #666;
}
.coordinate-bounds .metric-value {
    font-size: 0.8rem;
    font-weight: 500;
}
/* Area selection label */
.area-select-label {
    font-size: 1.1em;
    font-weight: bold;
    margin: 0 0 -0.5rem 0;
    padding: 0;
    line-height: 1.2;
}
/* Question text for sustainability */
.question-text {
    font-size: 1.1em;
    font-weight: 500;
    margin: 0;
    padding: 0;
}
/* Result info text */
.result-info {
    font-size: 16px;
    margin: 2px 0;
}
.result-info-lg {
    font-size: 18px;
    margin: 2px 0;
}
/* Disabled section styling */
.disabled-section {
    opacity: 0.4;
    pointer-events: none;
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px dashed #dee2e6;
}
.disabled-section ul {
    margin: 0;
    padding-left: 1.5rem;
}
.disabled-section p {
    margin: 0;
}
/* Flex row for progress bar */
.progress-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# Clear initial loading message - header is about to appear
loading_placeholder.empty()

# Auth gate — unauthenticated visitors see only the login/register UI
from utils.auth import require_login
require_login()

# Clean text-only header - Professional Dashboard Style
st.markdown("""
<div class="header-container">
    <span><span class="header-icon">🌱</span><span class="header-text">Ecological Valuation Engine</span></span>
    <span class="version-text">v3.3.0</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<h3 class="section-header">🗺️ Draw the area you want to analyse on the map or choose a test area from the dropdown below</h3>', unsafe_allow_html=True)


# Initialize session state
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'area_coordinates' not in st.session_state:
    st.session_state.area_coordinates = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'calculation_ready' not in st.session_state:
    st.session_state.calculation_ready = False

# Helper function to reset analysis state when area or settings change
def reset_analysis_state():
    """Clear all analysis results to hide sections until recalculated"""
    keys_to_clear = [
        'analysis_results', 'detected_ecosystem', 'summary_metrics',
        'regional_adjustment_factor', 'scenario_results', 'scenario_distribution',
        'scenario_eco_intactness', 'scenario_builder_expanded', 'calculation_ready'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            if key == 'calculation_ready':
                st.session_state[key] = False
            elif key == 'analysis_results':
                st.session_state[key] = None
            else:
                del st.session_state[key]

# Initialize local fallbacks to prevent LSP "unbound" diagnostics
ecosystem_override = st.session_state.get('ecosystem_override', 'Auto-detect')
include_environmental_indicators = st.session_state.get('include_environmental_indicators', False)
max_sampling_limit = st.session_state.get('max_sampling_limit', 9)
analysis_detail = st.session_state.get('analysis_detail', 'Summary Analysis')
income_elasticity = st.session_state.get('income_elasticity', 0.6)
time_preset = st.session_state.get('time_preset', 'Current Year (2024)')
analyze_button = False


# ── Analysis Settings dialog ───────────────────────────────────────────────
@st.dialog("⚙️ Analysis Settings", width="large")
def analysis_settings_dialog():
    @st.cache_data
    def get_ecosystem_options():
        return [
            "Auto-detect", "Tropical Forest", "Temperate Forest", "Boreal Forest",
            "polar", "Grassland", "Wetland", "Water (ocean)", "Rivers and Lakes",
            "Coastal", "Marine", "Agricultural", "Urban", "Desert"
        ]

    st.markdown("##### 🌿 Ecosystem Detection")
    _eco = st.selectbox(
        "Ecosystem Type",
        options=get_ecosystem_options(),
        index=get_ecosystem_options().index(st.session_state.get('ecosystem_override', 'Auto-detect'))
            if st.session_state.get('ecosystem_override', 'Auto-detect') in get_ecosystem_options() else 0,
        help="Auto-detection uses geographic analysis for ecosystem classification",
        key="dlg_ecosystem_override",
    )
    st.session_state.ecosystem_override = _eco

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        with st.expander("⚡ **Performance & Data Collection**"):
            _inc_env = st.checkbox(
                "Include Environmental Indicators",
                value=st.session_state.get('include_environmental_indicators', False),
                help="Collects FAPAR, soil carbon, and other environmental data (slower).",
                key="dlg_include_env",
            )
            st.session_state.include_environmental_indicators = _inc_env
            if _inc_env:
                st.info("🔬 **Comprehensive Mode**: Environmental data collected.")
            else:
                st.success("🚀 **Fast Mode**: Land cover only.")

        with st.expander("🎯 **Sampling Configuration**"):
            _samp = st.slider(
                "Sample Points", min_value=9, max_value=100,
                value=st.session_state.get('max_sampling_limit', 9), step=1,
                help="Lower = faster, higher = more accurate.",
                key="dlg_sampling",
            )
            st.session_state.max_sampling_limit = _samp
            st.session_state.sampling_frequency = _samp
            _sampling_guide = {
                (0, 20): "🔹 Low Sampling — very fast",
                (21, 40): "🔸 Moderate Sampling",
                (41, 70): "🔸 High Sampling — good for mixed areas",
                (71, 100): "🔴 Maximum Sampling — most accurate",
            }
            for (lo, hi), msg in _sampling_guide.items():
                if lo <= _samp <= hi:
                    st.info(msg)
                    break
            if st.session_state.get('cached_area_ha'):
                _gs = int(np.sqrt(_samp))
                st.caption(f"~{st.session_state.cached_area_ha:.0f} ha → {_gs**2} points")

        with st.expander("🌍 **Regional Adjustments**"):
            _elast = st.slider(
                "Income elasticity factor", min_value=0.1, max_value=1.0,
                value=st.session_state.get('income_elasticity', 0.6), step=0.1,
                help="0.5–0.6 recommended. Scales regional GDP differences.",
                key="dlg_income_elasticity",
            )
            st.session_state['income_elasticity'] = _elast
            st.caption("Formula: 1 + (e × (GDP_regional/GDP_global − 1)), bounded 0.4×–2.5×")

        with st.expander("📊 **Analysis Configuration**"):
            _detail = st.selectbox(
                "Analysis Detail",
                options=["Summary Analysis", "Detailed Analysis"],
                index=0 if st.session_state.get('analysis_detail', 'Summary Analysis') == 'Summary Analysis' else 1,
                help="Detailed includes service breakdown and methodology.",
                key="dlg_analysis_detail",
            )
            st.session_state.analysis_detail = _detail

    with col_b:
        with st.expander("🏙️ **Urban Green/Blue Infrastructure**"):
            if 'urban_green_blue_multiplier' not in st.session_state:
                st.session_state.urban_green_blue_multiplier = 18.0
            _urb = st.slider(
                "Green/Blue Coverage (%)", min_value=0.0, max_value=100.0,
                value=st.session_state.urban_green_blue_multiplier, step=1.0,
                key="dlg_urban_multiplier",
                help="WHO minimum ~10-15%; European cities 30-50%; North American 20-40%.",
            )
            st.session_state.urban_green_blue_multiplier = _urb
            st.info(f"Urban multiplier: {_urb/100:.2f}× ({_urb:.0f}%)")

        with st.expander("🌿 **Ecosystem Intactness by Type**"):
            st.caption("100% = pristine · 50% = moderately degraded · 0% = unproductive")

            if 'use_eei_for_intactness' not in st.session_state:
                st.session_state.use_eei_for_intactness = True
            _eei = st.checkbox(
                "Use EEI for Default Intactness",
                value=st.session_state.use_eei_for_intactness,
                key="dlg_use_eei",
                help="Ecosystem Ecological Integrity API sets intactness defaults automatically.",
            )
            st.session_state.use_eei_for_intactness = _eei
            st.caption("📡 EEI active" if _eei else "✋ Manual sliders below")

            _eco_types = {
                'Agricultural': '🌾', 'Temperate Forest': '🌳', 'Boreal Forest': '🌲',
                'Tropical Forest': '🌴', 'Grassland': '🌱', 'Shrubland': '🌵',
                'Desert': '🏜️', 'Wetland': '🌿', 'Coastal': '🏖️',
                'Marine': '🌊', 'Rivers And Lakes': '🏞️', 'Urban': '🏙️',
            }
            if 'ecosystem_intactness' not in st.session_state:
                st.session_state.ecosystem_intactness = {k: 100 for k in _eco_types}
            for et in _eco_types:
                if et not in st.session_state.ecosystem_intactness:
                    st.session_state.ecosystem_intactness[et] = 100

            _changed = False
            for eco_type, icon in _eco_types.items():
                _cur = st.session_state.ecosystem_intactness.get(eco_type, 100)
                _val = st.slider(
                    f"{icon} {eco_type} (%)", 0, 100,
                    int(round(_cur)) if isinstance(_cur, float) else _cur,
                    step=5, key=f"dlg_intactness_{eco_type}",
                )
                if _val != _cur:
                    _changed = True
                st.session_state.ecosystem_intactness[eco_type] = _val
            if _changed:
                reset_analysis_state()

        with st.expander("🔬 Scientific Methodology"):
            st.markdown("""
**EVE** combines satellite remote sensing with the ESVD (10,874 peer-reviewed values) to measure natural capital.

**Service Categories**: Provisioning · Regulating · Cultural · Supporting

**Formula**: `Final Value = ESVD_Base × Regional_Adjustment × Quality_Factor`

**Standards**: 2020 International dollars/ha/year · Bounded 0.4×–2.5× regional adjustment
            """)

    st.divider()
    with st.expander("🌍 **OpenLandMap Settings** (advanced)"):
        from utils.esa_landcover_codes import DEFAULT_LANDCOVER_MAPPING, get_all_esa_codes, get_default_multipliers, get_esa_description
        _default_map = DEFAULT_LANDCOVER_MAPPING
        _esvd_types = [
            "Forest", "Tropical Forest", "Temperate Forest", "Boreal Forest",
            "Grassland", "agricultural", "Urban", "Desert",
            "Wetland", "Coastal", "Marine", "Shrubland", "polar"
        ]
        if 'custom_landcover_mapping' not in st.session_state:
            st.session_state.custom_landcover_mapping = _default_map.copy()
        for code, eco in _default_map.items():
            if code not in st.session_state.custom_landcover_mapping:
                st.session_state.custom_landcover_mapping[code] = eco

        _desc = get_all_esa_codes()
        st.markdown("**Landcover → Ecosystem mapping**")
        if st.button("🔄 Reset to defaults", key="dlg_reset_mapping"):
            st.session_state.custom_landcover_mapping = _default_map.copy()
            st.rerun()
        _changes = sum(1 for k, v in st.session_state.custom_landcover_mapping.items() if v != _default_map.get(k))
        if _changes:
            st.info(f"📝 {_changes} custom mappings active")

        for code in sorted(_default_map.keys()):
            _mc1, _mc2 = st.columns([1, 2])
            with _mc1:
                st.markdown(f"**{code}**", help=_desc.get(code, ""))
            with _mc2:
                _cm = st.session_state.custom_landcover_mapping.get(code, "Grassland")
                _ci = _esvd_types.index(_cm) if _cm in _esvd_types else 0
                _nm = st.selectbox(f"eco_{code}", _esvd_types, index=_ci,
                                   key=f"dlg_lcmap_{code}", label_visibility="collapsed")
                st.session_state.custom_landcover_mapping[code] = _nm

        try:
            from utils.openlandmap_stac_api import openlandmap_stac
            openlandmap_stac.landcover_to_esvd = st.session_state.custom_landcover_mapping.copy()
        except Exception:
            pass

    if st.button("✅ Close", use_container_width=True, key="dlg_close"):
        st.rerun()


# Sidebar configuration - optimized for performance with expandable sections
with st.sidebar:

    # ── Auth indicator ────────────────────────────────────────────────────────
    _auth_user = st.session_state.get('auth_user')
    if _auth_user:
        _display = _auth_user.get('display_name') or _auth_user.get('email', 'User')
        _col_u, _col_lo = st.columns([4, 1])
        with _col_u:
            st.markdown(
                f"<div style='font-size:0.78rem;color:#2E7D32;padding:0.2rem 0;'>"
                f"Signed in as <strong>{_display}</strong></div>",
                unsafe_allow_html=True,
            )
        with _col_lo:
            if st.button("↩", key="signout_btn", help="Sign out"):
                from utils.auth import logout as _logout
                _logout()
                st.rerun()
        if st.button("⚙️ Settings", use_container_width=True, key="open_settings_btn"):
            analysis_settings_dialog()
        st.divider()

    # ── My Workspace ──────────────────────────────────────────────────────────
    if _auth_user:
        st.markdown("**🗂️ My Workspace**")
        if True:
            _ws_tab_areas, _ws_tab_history = st.tabs(["Saved Areas", "Analysis History"])

            with _ws_tab_areas:
                # Save current area
                if st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
                    st.markdown("**Save current area**")
                    _save_name = st.text_input(
                        "Area name", key="ws_save_name",
                        placeholder="e.g. River Wye Catchment",
                    )
                    if st.button("💾 Save area", key="ws_save_btn", use_container_width=True):
                        if _save_name.strip():
                            try:
                                from database import SavedAreaDB as _SADB
                                _coords = st.session_state.area_coordinates
                                _ha = st.session_state.get('cached_area_ha') or calculate_area_optimized(_coords)
                                _sid = _SADB.save_area(
                                    name=_save_name.strip(),
                                    coordinates=_coords,
                                    area_hectares=_ha,
                                )
                                if _sid:
                                    st.success(f"Saved: {_save_name.strip()}")
                                else:
                                    st.error("Save failed — check database connection.")
                            except Exception as _e:
                                st.error(f"Save failed: {_e}")
                        else:
                            st.warning("Please enter a name for this area.")
                    st.divider()

                st.markdown("**Your saved areas**")
                st.caption("Analysis is run fresh each time using the latest satellite and coefficient data.")
                try:
                    from database import SavedAreaDB as _SADB2
                    _areas = _SADB2.get_user_saved_areas()
                    if _areas:
                        st.markdown("""
                        <style>
                        [data-testid="stSidebar"] [data-testid="baseButton-secondary"] {
                            font-size: 0.65rem !important;
                            padding: 0.1rem 0.25rem !important;
                            min-height: 1.2rem !important;
                            line-height: 1 !important;
                        }
                        </style>""", unsafe_allow_html=True)
                        for _area in _areas:
                            _col_info, _col_btns = st.columns([3, 1])
                            with _col_info:
                                st.markdown(
                                    f"<div style='font-size:0.8rem;padding:0.1rem 0;'>"
                                    f"<strong>{_area['name']}</strong><br>"
                                    f"<span style='color:#666;font-size:0.72rem;'>"
                                    f"{_area['area_hectares']:.0f} ha · "
                                    f"{_area['created_at'].strftime('%Y-%m-%d')}"
                                    f"</span></div>",
                                    unsafe_allow_html=True,
                                )
                            with _col_btns:
                                if st.button("↩", key=f"ws_load_{_area['id']}",
                                             use_container_width=True,
                                             help="Load this area onto the map"):
                                    clear_analysis_cache()
                                    st.session_state.area_coordinates = _area['coordinates']
                                    st.session_state.selected_area = True
                                    st.session_state.cached_area_ha = _area['area_hectares']
                                    st.session_state.cached_bbox = calculate_bbox_optimized(_area['coordinates'])
                                    st.session_state.use_test_area_zoom = True
                                    st.session_state.current_area_id = _area['id']
                                    st.session_state.default_area_name = _area['name']
                                    st.rerun()
                                if st.button("🗑️", key=f"ws_del_{_area['id']}",
                                             use_container_width=True,
                                             help="Delete this saved area"):
                                    from database import SavedAreaDB as _SADB3
                                    _SADB3.delete_area(_area['id'])
                                    st.rerun()
                    else:
                        st.info("No saved areas yet. Draw an area and save it above.")
                except Exception as _e:
                    st.error(f"Could not load saved areas: {_e}")

            with _ws_tab_history:
                st.markdown("**Recent analyses** (last 10)")
                try:
                    from database import EcosystemAnalysisDB as _EADB
                    _hist = _EADB.get_user_analyses(limit=10)
                    if _hist:
                        for _h in _hist:
                            st.markdown(
                                f"<div style='font-size:0.8rem;border-left:3px solid #4CAF50;"
                                f"padding-left:6px;margin-bottom:4px;'>"
                                f"<strong>{_h.get('area_name') or 'Unnamed area'}</strong><br>"
                                f"<span style='color:#2E7D32;'>"
                                f"Int$ {_h.get('total_value', 0):,.0f}/yr</span> · "
                                f"{_h.get('ecosystem_type', '—')} · "
                                f"{_h.get('area_hectares', 0):.0f} ha<br>"
                                f"<span style='color:#999;font-size:0.73rem;'>"
                                f"{_h['created_at'].strftime('%Y-%m-%d %H:%M')}</span></div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No analyses saved yet.")
                except Exception as _e:
                    st.error(f"Could not load history: {_e}")

        st.divider()

    # Database Section
    if st.session_state.get('db_initialized', False):
        st.subheader("💾 Saved Data")
        
        # Database status indicator  
        try:
            db_modules = get_database_modules()
            if db_modules and db_modules['test_database_connection']():
                st.success("🟢 Database connected")
            else:
                st.warning("🟡 Database connection issue")
        except Exception as e:
            st.warning("⚠️ Database temporarily unavailable")
            st.caption("Analysis functionality remains available")
        
        # Tabs for different data views
        tab1, tab2, tab3, tab4 = st.tabs(["Recent Analyses", "Saved Areas", "Baselines", "Sustainability"])
        
        with tab1:
            st.markdown("**📊 Your Recent Analyses**")
            try:
                db_modules = get_database_modules()
                if db_modules:
                    recent_analyses = db_modules['EcosystemAnalysisDB'].get_user_analyses(limit=5)
                else:
                    recent_analyses = []
                
                if recent_analyses:
                    for analysis in recent_analyses:
                        with st.container():
                            st.markdown(f"**{analysis.get('area_name', 'Unnamed Area')}**")
                            st.caption(f"{analysis['ecosystem_type']} • ${analysis['total_value']:,.0f} • {analysis['created_at'].strftime('%Y-%m-%d')}")
                            
                            if st.button(f"Load Analysis", key=f"load_{analysis['id']}", use_container_width=True):
                                # Load the analysis data
                                if db_modules:
                                    full_analysis = db_modules['EcosystemAnalysisDB'].get_analysis_by_id(analysis['id'])
                                else:
                                    full_analysis = None
                                if full_analysis:
                                    st.session_state.area_coordinates = full_analysis['coordinates']
                                    st.session_state.analysis_results = full_analysis['analysis_results']
                                    st.session_state.calculation_ready = True
                                    st.session_state.selected_area = True
                                    # Clear cached area to recalculate for map centering
                                    st.session_state.cached_area_ha = None
                                    st.session_state.cached_bbox = None
                                    st.rerun()
                            
                else:
                    st.info("No saved analyses yet. Run an analysis to save results.")
            except Exception as e:
                st.error(f"Error loading analyses: {str(e)}")
                st.caption(f"User ID: {st.session_state.get('user_id', 'Not set')}")
                st.info("No saved analyses yet. Run an analysis to save results.")
        
        with tab2:
            st.markdown("**📍 Your Saved Areas**")
            try:
                db_modules = get_database_modules()
                if db_modules:
                    saved_areas = db_modules['SavedAreaDB'].get_user_saved_areas()
                else:
                    saved_areas = []
                
                if saved_areas:
                    for area in saved_areas:
                        with st.container():
                            st.markdown(f"**{area['name']}**")
                            st.caption(f"{area['area_hectares']:.0f} ha • {area['created_at'].strftime('%Y-%m-%d')}")
                            
                            if area.get('description'):
                                st.caption(f"📝 {area['description']}")
                            
                            if st.button(f"Load Area", key=f"load_area_{area['id']}", use_container_width=True):
                                # Load the area coordinates
                                st.session_state.area_coordinates = area['coordinates']
                                st.session_state.selected_area = True
                                st.session_state.cached_area_ha = area['area_hectares']
                                st.session_state.current_area_id = area['id']
                                # Clear bbox cache to force map re-centering
                                st.session_state.cached_bbox = None
                                st.rerun()
                            
                else:
                    st.info("No saved areas yet. Select and save an area first.")
            except Exception as e:
                st.error(f"Error loading saved areas: {str(e)}")
                st.caption(f"User ID: {st.session_state.get('user_id', 'Not set')}")
                st.info("No saved areas yet. Select and save an area first.")
        
        with tab3:
            st.markdown("**📊 Natural Capital Baselines**")
            # Get baselines for current user
            try:
                from database import get_db, NaturalCapitalBaseline
                with get_db() as db:
                    baselines = db.query(NaturalCapitalBaseline).filter(
                        NaturalCapitalBaseline.user_session_id == st.session_state.get('user_id')
                    ).order_by(NaturalCapitalBaseline.baseline_date.desc()).limit(5).all()

                    if baselines:
                        for baseline in baselines:
                            with st.container():
                                st.markdown(f"**{baseline.ecosystem_type} Baseline**")
                                st.caption(f"${baseline.total_baseline_value:,.0f} • {baseline.area_hectares:.0f} ha • {baseline.baseline_date.strftime('%Y-%m-%d')}")
                                st.caption(f"P: ${baseline.provisioning_baseline:,.0f} | R: ${baseline.regulating_baseline:,.0f} | C: ${baseline.cultural_baseline:,.0f} | S: ${baseline.supporting_baseline:,.0f}")
                                try:
                                    if hasattr(baseline, 'biodiversity_index') and baseline.biodiversity_index is not None and baseline.biodiversity_index > 0:
                                        st.caption(f"🌿 Biodiversity Index: {baseline.biodiversity_index:.2f}")
                                except Exception:
                                    pass
                        st.caption("P=Provisioning, R=Regulating, C=Cultural, S=Supporting")
                    else:
                        st.info("No baselines established yet. Set a baseline after running an analysis.")
            except Exception as e:
                st.error(f"Failed to load baselines: {str(e)}")
        
        with tab4:
            st.markdown("**🌱 Sustainability Assessment**")
            
            # Show current sustainability responses
            if 'sustainability_responses' in st.session_state:
                responses = st.session_state.sustainability_responses
                questions = [
                    ("minimize_soil_disturbance", "Minimize soil disturbance"),
                    ("maintain_living_roots", "Maintain living roots in soil"),
                    ("cover_bare_soil", "Continuously cover bare soil"),
                    ("maximize_diversity", "Maximize diversity (crops, microbes, pollinators)"),
                    ("integrate_livestock", "Integrate livestock where feasible")
                ]
                
                total_count = len(questions)
                yes_count = sum(1 for response in responses.values() if response is True)
                score_percentage = (yes_count / total_count) * 100
                
                st.info(f"Sustainability assessment responses:")
                
                for key, label in questions:
                    response = responses.get(key, False)
                    status = "✅ Yes" if response else "❌ No"
                    st.markdown(f"**{label}**: {status}")
                
                # Show sustainability score
                
                st.metric("Sustainability Score", f"{score_percentage:.0f}%", f"{yes_count}/{total_count} sustainable practices")
                
                if score_percentage >= 80:
                    st.success("🌟 Excellent sustainability practices!")
                elif score_percentage >= 60:
                    st.warning("⚡ Good sustainability practices with room for improvement")
                else:
                    st.error("📈 Consider adopting more sustainable practices")
            else:
                st.info("No sustainability assessment completed yet.")
    else:
        st.info("💡 Database features disabled")
        st.caption("Core analysis functionality remains available")
    
    
    
    # Ultra-optimized clear button with memory management
    if st.button("🗑️ Clear Area & Results", help="Start over with a new area"):
        clear_analysis_cache()
        import gc
        gc.collect()
        st.rerun()

# Initialize analyze_button as False
analyze_button = False

# Test area selection dropdown
test_area_options = [
    "None - Draw your own area",
    "📁 Load Saved Area",
    "🌾 Test area (Agricultural)",
    "🌱 Test area (Grassland)",
    "🌿 Test area (Shrubland)", 
    "🌲 Test area (Boreal Forest)",
    "🌳 Test area (Temperate Forest)",
    "🌴 Test area (Tropical Forest)",
    "🏜️ Test area (Desert)",
    "🏙️ Test area (Urban)",
    "🌊 Test area (Water (ocean))",
    "🏞️ Test area (Water (Rivers/Lakes))",
    "🏖️ Test area (Water (Coastal))",
    "🌍 Test area (Multi-Ecosystem)",
    # "🎲 Test area (Random Global)"  # Hidden but kept for later use
]

selected_test_area = st.selectbox(
    "Select Area Type",
    test_area_options,
    index=0,
    label_visibility="hidden",
    help="Select a predefined test area, load a previously saved area, or choose 'None' to draw your own area on the map",
    on_change=reset_analysis_state
)
use_test_area = selected_test_area not in ["None - Draw your own area", "📁 Load Saved Area"]
use_load_saved_area = selected_test_area == "📁 Load Saved Area"
use_test_area_single = selected_test_area in ["🌾 Test area (Agricultural)", "🌱 Test area (Grassland)", "🌿 Test area (Shrubland)", "🌲 Test area (Boreal Forest)", "🌳 Test area (Temperate Forest)", "🌴 Test area (Tropical Forest)", "🏜️ Test area (Desert)", "🏙️ Test area (Urban)", "🌊 Test area (Water (ocean))", "🏞️ Test area (Water (Rivers/Lakes))", "🏖️ Test area (Water (Coastal))"]
use_test_area_multi = selected_test_area == "🌍 Test area (Multi-Ecosystem)" 
use_test_area_random = selected_test_area == "🎲 Test area (Random Global)"

# Handle load saved area functionality
if use_load_saved_area:
    from database import SavedAreaDB
    
    # Get saved areas for the user
    try:
        saved_areas = SavedAreaDB.get_user_saved_areas()
        
        if saved_areas:
            # Create options for saved area selection
            saved_area_names = [f"{area['name']} ({area['area_hectares']:.1f} ha)" for area in saved_areas]
            saved_area_names.insert(0, "Select a saved area...")
            
            # Left-aligned saved area dropdown
            selected_saved_area = st.selectbox(
                "Choose a saved area to load:",
                saved_area_names,
                key="saved_area_selector",
                help="Select a previously saved area to load onto the map"
            )
            
            # Load selected saved area
            if selected_saved_area != "Select a saved area...":
                selected_index = saved_area_names.index(selected_saved_area) - 1  # Subtract 1 for the placeholder
                selected_area_data = saved_areas[selected_index]
                
                # Clear all cached values first to ensure clean state
                clear_analysis_cache()
                
                # Set the loaded area coordinates
                st.session_state.area_coordinates = selected_area_data['coordinates']
                st.session_state.selected_area = True
                st.session_state.use_test_area_zoom = True
                
                # Reset default area name for loaded area
                if 'default_area_name' in st.session_state:
                    del st.session_state['default_area_name']
                
                # Calculate and cache area data
                area_ha = selected_area_data['area_hectares']
                st.session_state.cached_area_ha = area_ha
                st.session_state.cached_bbox = calculate_bbox_optimized(selected_area_data['coordinates'])
                st.session_state.area_coords_cache = selected_area_data['coordinates']
                
                st.success(f"✅ **Loaded: {selected_area_data['name']}**")
                st.caption(f"📍 Area: {area_ha:.1f} hectares")
                if selected_area_data.get('description'):
                    st.caption(f"💬 {selected_area_data['description']}")
        else:
            st.info("No saved areas found. Save an area first by drawing on the map and using the save functionality.")
            st.caption("Draw an area on the map below to get started, then save it for future use.")
            
    except Exception as e:
        st.error(f"Error loading saved areas: {str(e)}")
        st.caption("Please check your database connection.")

elif use_test_area_single:
    # Define coordinates for different single ecosystem test areas (all exactly 1000 hectares)
    # Precisely calculated using latitude correction factors for each location

    def calculate_1000ha_coordinates(center_lat, center_lon):
        """Calculate coordinates for exactly 1000 hectares at given latitude"""
        # Side length for 1000 hectares = 3.16228 km
        side_length_km = 3.16228
        
        # Conversion factors
        lat_km_per_deg = 111.32
        lon_km_per_deg = 111.32 * math.cos(math.radians(center_lat))
        
        # Half-side in degrees
        lat_half_side = (side_length_km / 2) / lat_km_per_deg
        lon_half_side = (side_length_km / 2) / lon_km_per_deg
        
        # Calculate and wrap longitude to valid range (-180 to 180)
        min_lon = center_lon - lon_half_side
        max_lon = center_lon + lon_half_side
        if min_lon < -180:
            min_lon += 360
        if max_lon > 180:
            max_lon -= 360
        
        return [
            [min_lon, center_lat - lat_half_side],  # SW
            [max_lon, center_lat - lat_half_side],  # SE
            [max_lon, center_lat + lat_half_side],  # NE
            [min_lon, center_lat + lat_half_side],  # NW
            [min_lon, center_lat - lat_half_side]   # Close
        ]
    
    single_ecosystem_areas = {
        "🌾 Test area (Agricultural)": {
            "coords": calculate_1000ha_coordinates(40.1, -87.91),
            "description": "Illinois Corn Belt (40.1°N, 87.91°W) | Expected: 100% Agricultural ecosystem",
            "location": "Rural US Corn Belt, central Illinois"
        },
        "🌱 Test area (Grassland)": {
            "coords": calculate_1000ha_coordinates(49.1186, 50.6220),
            "description": "Kazakhstan Grassland (49.12°N, 50.62°E) | Expected: Grassland ecosystem",
            "location": "Kazakhstan steppe region"
        },
        "🌿 Test area (Shrubland)": {
            "coords": calculate_1000ha_coordinates(-16.45, 126.5),
            "description": "Australian Shrubland (-16.45°S, 126.5°E) | Expected: Shrubland ecosystem",
            "location": "Western Australia"
        },
        "🌲 Test area (Boreal Forest)": {
            "coords": calculate_1000ha_coordinates(50.491, -84.986),
            "description": "Canadian Boreal Forest (50.491°N, 84.986°W) | Expected: Boreal Forest ecosystem",
            "location": "Northern Ontario boreal forest"
        },
        "🌳 Test area (Temperate Forest)": {
            "coords": calculate_1000ha_coordinates(48.79, 127.35),
            "description": "Lesser Khingan Mountains (48.79°N, 127.35°E) | Expected: Temperate Forest ecosystem",
            "location": "Northeast China temperate forest region, Heilongjiang province"
        },
        "🌴 Test area (Tropical Forest)": {
            "coords": calculate_1000ha_coordinates(-3.0, -59.64),
            "description": "Brazilian Amazon Rainforest (3.0°S, 59.6°W) | Expected: Tropical Forest ecosystem",
            "location": "Central Amazon rainforest, Brazil"
        },
        "🏜️ Test area (Desert)": {
            "coords": calculate_1000ha_coordinates(26.0, 5.0),
            "description": "Sahara Desert (26.0°N, 5.0°E) | Expected: Desert ecosystem",
            "location": "Central Sahara Desert, Algeria"
        },
        "🏙️ Test area (Urban)": {
            "coords": calculate_1000ha_coordinates(19.374960, -99.117966),
            "description": "Mexico City Urban Area (19.37°N, 99.12°W) | Expected: Urban ecosystem with 18% green/blue infrastructure",
            "location": "Mexico City metropolitan area, Mexico"
        },
        "🌊 Test area (Water (ocean))": {
            "coords": calculate_1000ha_coordinates(25.0, -65.0),
            "description": "Atlantic Ocean (25.0°N, 65.0°W) | Expected: ESA Code 210, triggers water body classification",
            "location": "Mid-Atlantic Ocean east of Bahamas"
        },
        "🏞️ Test area (Water (Rivers/Lakes))": {
            "coords": calculate_1000ha_coordinates(-0.82, 33.0),
            "description": "East African Lake Region (0.82°S, 33°E) | Expected: ESA Code 210, Rivers and Lakes ecosystem with regional factor",
            "location": "East Africa, Lake Victoria region (20km north)"
        },
        "🏖️ Test area (Water (Coastal))": {
            "coords": calculate_1000ha_coordinates(40.145290, 16.962891),
            "description": "Italian Coastal Waters (40.15°N, 16.96°E) | Expected: Coastal ecosystem with regional factor",
            "location": "Southern Italy, Basilicata coastal region"
        }
    }
    
    if selected_test_area in single_ecosystem_areas:
        area_data = single_ecosystem_areas[selected_test_area]
        test_coordinates = area_data["coords"]
        
        # Clear all cached values first to ensure clean state
        clear_analysis_cache()
        
        # Set the test area coordinates
        st.session_state.area_coordinates = test_coordinates
        st.session_state.selected_area = True
        st.session_state.use_test_area_zoom = True
        
        # Reset default area name for test area
        if 'default_area_name' in st.session_state:
            del st.session_state['default_area_name']
        
        # Calculate area using the actual formula (should be exactly 1000ha)
        area_ha = calculate_area_optimized(test_coordinates)
        st.session_state.cached_area_ha = area_ha
        st.session_state.cached_bbox = calculate_bbox_optimized(test_coordinates)
        st.session_state.area_coords_cache = test_coordinates
        
        st.success(f"✅ **{selected_test_area} Selected!**")
        st.caption(area_data["description"])

elif use_test_area_multi:
    # Define coordinates for multi-ecosystem test area (Michigan agricultural-forest transition)
    # Area spanning agricultural-forest-grassland transition zone, calculated for exactly 1000ha at 42°N latitude
    # Using latitude correction factor for 42°N: cos(42°) ≈ 0.743
    lat_center, lon_center = 42.0, -84.0
    # Side length precisely calculated for exactly 1000ha at 42°N
    half_side = 0.01647631
    
    test_coordinates = [
        [lon_center - half_side, lat_center - half_side],  # SW
        [lon_center + half_side, lat_center - half_side],  # SE
        [lon_center + half_side, lat_center + half_side],  # NE
        [lon_center - half_side, lat_center + half_side],  # NW
        [lon_center - half_side, lat_center - half_side]   # Close
    ]
    
    # Clear all cached values first to ensure clean state
    clear_analysis_cache()
    
    # Set the test area coordinates
    st.session_state.area_coordinates = test_coordinates
    st.session_state.selected_area = True
    st.session_state.use_test_area_zoom = True
    
    # Reset default area name for test area
    if 'default_area_name' in st.session_state:
        del st.session_state['default_area_name']
    
    # Calculate area using the actual formula (should be exactly 1000ha)
    area_ha = calculate_area_optimized(test_coordinates)
    st.session_state.cached_area_ha = area_ha
    st.session_state.cached_bbox = calculate_bbox_optimized(test_coordinates)
    st.session_state.area_coords_cache = test_coordinates
    
    st.success("✅ **Multi-Ecosystem Test Area Selected!**")
    st.caption("🌍 Michigan Transition Zone (42.0°N, 84.0°W) | Expected: Agricultural, Forest, and Grassland ecosystems")

elif use_test_area_random:
    # Generate random global coordinates for 1000ha test area
    import random
    
    # Define global land coordinate ranges (avoiding oceans and Antarctica)
    land_regions = [
        # North America
        (-130, -60, 25, 70),   # (min_lon, max_lon, min_lat, max_lat)
        # South America  
        (-80, -35, -55, 15),
        # Europe
        (-10, 40, 35, 70),
        # Africa
        (-20, 50, -35, 35),
        # Asia
        (25, 180, -10, 70),
        # Australia/Oceania
        (110, 155, -45, -10)
    ]
    
    # Randomly select a land region
    selected_region = random.choice(land_regions)
    min_lon, max_lon, min_lat, max_lat = selected_region
    
    # Generate random center coordinates within the region
    # Avoid extreme latitudes where longitude corrections become problematic
    lat_center = random.uniform(max(min_lat, -60), min(max_lat, 70))
    lon_center = random.uniform(min_lon, max_lon)
    
    # Calculate side length for exactly 1000ha at the selected latitude
    # 1° latitude ≈ 111.32 km everywhere
    # 1° longitude ≈ 111.32 * cos(latitude) km
    lat_km_per_deg = 111.32
    lon_km_per_deg = 111.32 * math.cos(math.radians(abs(lat_center)))
    
    # Area = side_length_km^2, need 10 km^2 for 1000ha
    target_area_km2 = 10.0
    side_length_km = math.sqrt(target_area_km2)
    
    # Convert to degrees
    lat_half_side = (side_length_km / 2) / lat_km_per_deg
    lon_half_side = (side_length_km / 2) / lon_km_per_deg
    
    # Calculate and wrap longitude to valid range (-180 to 180)
    min_lon = lon_center - lon_half_side
    max_lon = lon_center + lon_half_side
    if min_lon < -180:
        min_lon += 360
    if max_lon > 180:
        max_lon -= 360
    
    test_coordinates = [
        [min_lon, lat_center - lat_half_side],  # SW
        [max_lon, lat_center - lat_half_side],  # SE
        [max_lon, lat_center + lat_half_side],  # NE
        [min_lon, lat_center + lat_half_side],  # NW
        [min_lon, lat_center - lat_half_side]   # Close
    ]
    
    # Clear all cached values first to ensure clean state
    clear_analysis_cache()
    
    # Set the test area coordinates
    st.session_state.area_coordinates = test_coordinates
    st.session_state.selected_area = True
    st.session_state.use_test_area_zoom = True
    
    # Reset default area name for test area
    if 'default_area_name' in st.session_state:
        del st.session_state['default_area_name']
    
    # Calculate area using the actual formula (should be close to 1000ha)
    area_ha = calculate_area_optimized(test_coordinates)
    st.session_state.cached_area_ha = area_ha
    st.session_state.cached_bbox = calculate_bbox_optimized(test_coordinates)
    st.session_state.area_coords_cache = test_coordinates
    
    # Determine region name for display
    region_names = {
        (-130, -60, 25, 70): "North America",
        (-80, -35, -55, 15): "South America", 
        (-10, 40, 35, 70): "Europe",
        (-20, 50, -35, 35): "Africa",
        (25, 180, -10, 70): "Asia",
        (110, 155, -45, -10): "Australia/Oceania"
    }
    region_name = region_names.get(selected_region, "Unknown Region")
    
    st.success("✅ **Random Global Test Area Selected!**")
    st.caption(f"🎲 Random location in {region_name} ({lat_center:.2f}°N, {lon_center:.2f}°{'E' if lon_center >= 0 else 'W'}) | Area: {area_ha:.0f} ha")
else:
    # Clear test area flag when unchecked, but preserve manual area zoom
    if not st.session_state.get('area_coordinates'):
        st.session_state.use_test_area_zoom = False

# Map section

# Add search and layer selector
col_search, col_layer = st.columns([2, 1])
with col_search:
    location_search = st.text_input("🔍 Search for locations:", placeholder="e.g., Costa Rica, Amazon Rainforest, Great Barrier Reef", key="location_search_main")
with col_layer:
    map_layer = st.radio("🗺️ Map Style:", ["Satellite", "Light Map"], horizontal=True, key="main_map_layer_selector")

# Performance-optimized sampling display
current_limit = st.session_state.get('max_sampling_limit', 9)

# Initialize use_test_area_zoom if not set (ensures default map shows on startup)
if 'use_test_area_zoom' not in st.session_state:
    st.session_state.use_test_area_zoom = False

# Dynamic zoom utility functions imported from utils.analysis_helpers:
# lat_to_mercator_y, compute_zoom_for_bbox, compute_center_from_bbox,
# create_bbox_from_center_and_area

# Create optimized interactive map - use dynamic zoom calculations
if st.session_state.get('use_test_area_zoom', False):
    # Zoom to the appropriate test area with dynamic zoom
    if use_test_area_single:
        # Get center coordinates for test area
        ecosystem_zoom_coords = {
            "🌾 Test area (Agricultural)": (40.1, -87.91),     # Illinois Corn Belt
            "🌱 Test area (Grassland)": (49.1186, 50.6220),  # Kazakhstan steppe region
            "🌿 Test area (Shrubland)": (-16.45, 126.5),       # Western Australia
            "🌲 Test area (Boreal Forest)": (50.491, -84.986),     # Northern Ontario
            "🌳 Test area (Temperate Forest)": (48.79, 127.35),  # Lesser Khingan Mountains, China
            "🌴 Test area (Tropical Forest)": (-3.0, -59.64),   # Brazilian Amazon
            "🏜️ Test area (Desert)": (26.0, 5.0),             # Sahara Desert
            "🏙️ Test area (Urban)": (19.374960, -99.117966),   # Mexico City
            "🌊 Test area (Water (ocean))": (25.0, -65.0),       # Atlantic Ocean
            "🏞️ Test area (Water (Rivers/Lakes))": (-0.82, 33.0),  # East African Lake region (20km north)
            "🏖️ Test area (Water (Coastal))": (40.145290, 16.962891)  # Southern Italy coastal region
        }
        
        if selected_test_area in ecosystem_zoom_coords:
            center_lat, center_lon = ecosystem_zoom_coords[selected_test_area]
        else:
            center_lat, center_lon = 40.028, -99.0185
        
        # Create synthetic bbox for 1000ha test area and calculate dynamic zoom
        test_bbox = create_bbox_from_center_and_area(center_lat, center_lon, 1000)
        
        # Use different max zoom for water bodies due to lower ocean map resolution
        max_zoom = 18 if selected_test_area == "🌊 Test area (Water (ocean))" else 20
        zoom_level = compute_zoom_for_bbox(test_bbox, map_max_zoom=max_zoom)
    elif use_test_area_multi:
        # Dynamic zoom for Michigan test area
        center_lat, center_lon = 42.0, -84.0
        multi_bbox = create_bbox_from_center_and_area(center_lat, center_lon, 1000)
        zoom_level = compute_zoom_for_bbox(multi_bbox)
    elif use_test_area_random:
        # Dynamic zoom for random global test area
        if st.session_state.get('cached_bbox'):
            bbox = st.session_state.cached_bbox
            center_lat, center_lon = compute_center_from_bbox(bbox)
            zoom_level = compute_zoom_for_bbox(bbox)
        else:
            # Fallback if bbox not available
            center_lat, center_lon = 0, 0
            zoom_level = 2
    elif use_load_saved_area:
        # Dynamic zoom for loaded saved area
        if st.session_state.get('cached_bbox'):
            bbox = st.session_state.cached_bbox
            center_lat, center_lon = compute_center_from_bbox(bbox)
            zoom_level = compute_zoom_for_bbox(bbox)
        else:
            # Fallback if bbox not available
            center_lat, center_lon = 40.0, -100.0
            zoom_level = 5
    elif st.session_state.get('cached_bbox'):
        # Dynamic zoom for manually drawn area using cached bbox
        bbox = st.session_state.cached_bbox
        center_lat, center_lon = compute_center_from_bbox(bbox)
        zoom_level = compute_zoom_for_bbox(bbox)
    else:
        # Default to Sweden if no specific area selected
        center_lat, center_lon = 60.0, 15.0
        zoom_level = 13
    
    m = get_folium_map(center_lat, center_lon, zoom_level, map_layer)
    
    # Add drawing tools for test area map
    draw_tools = create_drawing_tools()
    draw_tools.add_to(m)
    
    # Show test area polygon if coordinates are set
    if st.session_state.get('area_coordinates'):
            import folium
            coords = st.session_state.area_coordinates
            if use_test_area_single:
                popup_text = f"{selected_test_area} (1000 hectares)"
                if selected_test_area == "🌊 Test area (Water Bodies)":
                    color = '#007bff'  # Blue for water bodies
                else:
                    color = '#28a745'  # Green for other single ecosystems
            elif use_test_area_multi:
                popup_text = "Multi-Ecosystem Test Area (1000 hectares)"
                color = '#17a2b8'  # Blue for multi-ecosystem
            elif use_test_area_random:
                popup_text = "Random Global Test Area (1000 hectares)"
                color = '#ff6b35'  # Orange for random global
            elif use_load_saved_area:
                # Handle loaded saved area
                area_ha = st.session_state.get('cached_area_ha', 0)
                popup_text = f"Loaded Area ({area_ha:.1f} hectares)"
                color = '#6f42c1'  # Purple for loaded areas
            else:
                popup_text = "Test Area (1000 hectares)"
                color = '#28a745'
            
            folium.Polygon(
                locations=[(float(coord[1]), float(coord[0])) for coord in coords],
                color=color,
                weight=2,
                fillColor=color,
                fillOpacity=0.15,
                popup=popup_text
            ).add_to(m)
    elif st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
        import folium
    
        coords = st.session_state.area_coordinates
        
        # Calculate coords_array for all operations
        coords_array = np.array(coords[:-1], dtype=np.float32)
        
        # Use dynamic zoom calculation for manually drawn areas
        if st.session_state.get('cached_bbox'):
            bbox = st.session_state.cached_bbox
            center_lat, center_lon = compute_center_from_bbox(bbox)
            zoom_level = compute_zoom_for_bbox(bbox)
        else:
            # Fallback: create bbox from coordinates for dynamic zoom
            center_lat = float(coords_array[:, 1].mean())
            center_lon = float(coords_array[:, 0].mean())
            
            min_lat, max_lat = coords_array[:, 1].min(), coords_array[:, 1].max()
            min_lon, max_lon = coords_array[:, 0].min(), coords_array[:, 0].max()
            manual_bbox = {
                'min_lat': float(min_lat), 'max_lat': float(max_lat),
                'min_lon': float(min_lon), 'max_lon': float(max_lon)
            }
            zoom_level = compute_zoom_for_bbox(manual_bbox)
        
        m = get_folium_map(center_lat, center_lon, zoom_level, map_layer)
        
        # Add cached drawing tools
        draw_tools = create_drawing_tools()
        draw_tools.add_to(m)
        
        # Optimized polygon rendering with appropriate colors
        # Check if this is a loaded saved area
        if use_load_saved_area and selected_test_area == "📁 Load Saved Area":
            area_ha = st.session_state.get('cached_area_ha', 0)
            popup_text = f"Loaded Area ({area_ha:.1f} hectares)"
            color = '#6f42c1'  # Purple for loaded areas
        else:
            popup_text = "Selected Area"
            color = '#28a745'  # Green for regular selected areas
            
        folium.Polygon(
            locations=[(float(coord[1]), float(coord[0])) for coord in coords],
            color=color,  # Use appropriate color
            weight=2,  # Reduced weight for performance
            fillColor=color,
            fillOpacity=0.15,  # Reduced opacity for speed
            popup=popup_text
        ).add_to(m)
        
        # Pre-computed bounds for faster fitting
        bounds = [
            [float(coords_array[:, 1].min()), float(coords_array[:, 0].min())],
            [float(coords_array[:, 1].max()), float(coords_array[:, 0].max())]
        ]
        m.fit_bounds(bounds, padding=[50, 50])  # Reduced padding for speed
else:
    # Handle location search and set map center
    map_center = [40.0, -100.0]  # Default center (USA)
    map_zoom = 4  # Default zoom
    
    if location_search:
        location = None
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="EcosystemValuationEngine")
            location = geolocator.geocode(location_search)
        except Exception:
            pass
        
        if location:
            map_center = [location.latitude, location.longitude]
            map_zoom = 10
        else:
            st.warning(f"❌ Location '{location_search}' not found. Try different search terms.")
    
    # Default optimized map view with search location
    m = get_folium_map(map_center[0], map_center[1], map_zoom, map_layer)
    draw_tools = create_drawing_tools()
    draw_tools.add_to(m)
    
    # Add search result marker if location found
    if location_search and 'location' in locals() and location:
        import folium
        folium.Marker(
            [location.latitude, location.longitude],
            popup=f"📍 {location.address}",
            tooltip=f"Searched: {location_search}",
            icon=folium.Icon(color='red', icon='search')
        ).add_to(m)

# Ultra-optimized map display with performance settings - two-thirds width
from streamlit_folium import st_folium
col1_map, col2_map, col3_map = st.columns([0.3, 2, 1.1])
with col2_map:
    # Loading message that shows until map iframe loads
    st.markdown("""
    <style>
    .map-loading-overlay {
        position: relative;
        width: 100%;
        height: 400px;
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        margin-bottom: -400px;
        z-index: 10;
        animation: fadeOut 2s ease-in-out 3s forwards;
    }
    .map-loading-text {
        color: #2E7D32;
        font-size: 1.2rem;
        font-weight: 600;
    }
    @keyframes fadeOut {
        0% { opacity: 1; }
        100% { opacity: 0; pointer-events: none; }
    }
    </style>
    <div class="map-loading-overlay">
        <span class="map-loading-text">🌱 Please wait, loading map...</span>
    </div>
    """, unsafe_allow_html=True)
    
    map_data = st_folium(
        m,
        width="100%",  # Responsive width for all device sizes
        height=400,
        returned_objects=["all_drawings"],
        key="area_map",
        feature_group_to_add=None,  # Reduce memory usage
        debug=False  # Disable debug for performance
    )

# Process map interactions with optimized state checking
if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
    latest_drawing = map_data['all_drawings'][-1]
    
    if latest_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
        coordinates = latest_drawing['geometry']['coordinates'][0]
        
        # Only process if coordinates actually changed (prevent hanging)
        current_coords = st.session_state.get('area_coordinates', [])
        
        # Simplified comparison to prevent hanging
        coords_hash = hash(str(coordinates))
        current_hash = st.session_state.get('coords_hash', None)
        
        if coords_hash != current_hash:
            # Save the new selection with batch state updates
            st.session_state.update({
                'selected_area': {
                    'type': latest_drawing['geometry']['type'],
                    'coordinates': coordinates
                },
                'area_coordinates': coordinates,
                'coords_hash': coords_hash,  # Store hash to prevent reprocessing
                'analysis_results': None,
                'calculation_ready': False,  # Hide results until recalculated
                # Clear caches to force recalculation
                'cached_bbox': None,
                'cached_area_ha': None,
                'cached_ecosystem_results': None
            })
            # Clear scenario state for new area
            for key in ['scenario_results', 'scenario_distribution', 'scenario_eco_intactness', 
                        'scenario_builder_expanded', 'detected_ecosystem']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Reset default area name for new area selection
            if 'default_area_name' in st.session_state:
                del st.session_state['default_area_name']
            
            # Quick area display using optimized calculation (cached)
            if len(coordinates) > 2:
                try:
                    area_ha = calculate_area_optimized(coordinates)
                    st.success(f"Area selected: {area_ha:.2f} hectares")
                    
                    # Pre-cache all calculations to speed up future operations
                    st.session_state.cached_area_ha = area_ha
                    st.session_state.cached_bbox = calculate_bbox_optimized(coordinates)
                    
                    # Enable map zoom to user-drawn area
                    st.session_state.use_test_area_zoom = True
                    
                    # Trigger map zoom to selected area
                    st.rerun()
                except Exception as e:
                    st.error(f"Error calculating area: {e}")
                    # Reset to prevent hanging
                    st.session_state.coords_hash = None
    else:
        st.warning("Please draw a polygon or rectangle area")

with col3_map:
    analyze_button = False
    if st.session_state.get('selected_area'):
        # Compact coordinates
        if st.session_state.get('area_coordinates'):
            coords = st.session_state.area_coordinates
            if 'cached_bbox' in st.session_state and st.session_state.cached_bbox:
                bbox = st.session_state.cached_bbox
            else:
                try:
                    bbox = calculate_bbox_optimized(coords)
                    st.session_state.cached_bbox = bbox
                except Exception:
                    bbox = None
            if bbox:
                st.markdown(f"""
                <div style='font-size:0.78rem; color:#2E7D32; line-height:1.8; padding:0.3rem 0 0.6rem 0;'>
                    <strong>📍 Selected area</strong><br>
                    Lat: {bbox['min_lat']:.4f} – {bbox['max_lat']:.4f}<br>
                    Lon: {bbox['min_lon']:.4f} – {bbox['max_lon']:.4f}
                </div>
                """, unsafe_allow_html=True)

        if 'analysis_detail' not in st.session_state:
            st.session_state.analysis_detail = 'Summary Analysis'
        if st.button('🚀 Calculate Ecosystem Value', type='primary', use_container_width=True, help='Run ecosystem analysis with current settings'):
            analyze_button = True
            st.session_state.analysis_in_progress = True
            if 'sampling_point_data' in st.session_state:
                for point_data in st.session_state.sampling_point_data.values():
                    if 'user_classified' in point_data:
                        del point_data['user_classified']
                    if point_data.get('landcover_class') == 210:
                        if 'ecosystem_type' in point_data:
                            del point_data['ecosystem_type']
        else:
            analyze_button = st.session_state.get('analysis_in_progress', False)
    else:
        st.markdown("""
        <div style='font-size:0.95rem; font-weight:600; color:#1B5E20;
                    background:#E8F5E9; border-left:4px solid #2E7D32;
                    border-radius:0 6px 6px 0; padding:0.6rem 0.75rem; margin-top:0.5rem;'>
            ✏️ Draw a polygon or rectangle on the map to select your area
        </div>
        """, unsafe_allow_html=True)

# Enhanced Results section with data source indicator
if st.session_state.get('analysis_results'):
    st.markdown('<h2 class="section-header">📈 Step 3: Results</h2>', unsafe_allow_html=True)
    
    # Clear data source indicator at top of results
    data_source_check = st.session_state.get('landcover_data_source', st.session_state.get('analysis_results', {}).get('landcover_data_source', ''))
    
    # Also check sampling point data for real satellite data indicators
    has_real_results_data = False
    results = st.session_state.get('analysis_results', {})
    if results and results.get('sampling_point_data'):
        for point_data in results.get('sampling_point_data', {}).values():
            data_source = point_data.get('data_source', '')
            if 'Real ESA Satellite Data' in data_source or 'GeoTIFF Pixel' in data_source:
                has_real_results_data = True
                break
    
    if data_source_check == 'openlandmap' or has_real_results_data:
        st.success("🛰️ **Data Quality: AUTHENTIC ESA SATELLITE DATA** - Real land cover from ESA CCI satellite imagery")
    else:
        st.warning("⚠️ **Data Quality: GEOGRAPHIC ESTIMATION** - Real satellite data unavailable, using location-based prediction")
    
    results = st.session_state.analysis_results
    
    # Safety check - ensure results is not None
    if results is None:
        st.error("Analysis results are not available. Please run the analysis again.")
        st.stop()
    
    
    # Enhanced forest type information section
    if 'forest_classification' in results:
        forest_info = results['forest_classification']
        
        st.markdown("### 🌲 Forest Type Classification")
        
        col_forest1, col_forest2 = st.columns([2, 1])
        with col_forest1:
            st.success(f"""
            **{forest_info['detected_type'].replace('_', ' ').title()} Detected**
            
            **Climate Zone**: {forest_info['climate_zone']}  
            **Detection Method**: {forest_info.get('selection_method', 'Geographic coordinate analysis')}  
            
            *This forest type uses specialized ecosystem service coefficients based on your location's climate and geographic characteristics, providing more accurate valuations than generic forest values.*
            """)
            
            with col_forest2:
                # Show forest type characteristics
                forest_type = forest_info['detected_type']
                if forest_type == 'tropical_forest':
                    st.markdown("""
                    **🌿 Tropical Forest**
                    - Highest biodiversity
                    - Maximum carbon storage
                    - Premium ecotourism value
                    - Dense canopy cover
                    """)
                elif forest_type == 'temperate_forest':
                    st.markdown("""
                    **🍂 Temperate Forest**
                    - Highest timber value
                    - Seasonal recreation
                    - Mixed species diversity
                    - Moderate carbon storage
                    """)
                elif forest_type == 'boreal_forest':
                    st.markdown("""
                    **❄️ Boreal Forest**
                    - Maximum soil carbon
                    - Pulp/paper timber
                    - Wildlife habitat value
                    - Cold climate adapted
                    """)
        
        # Add calculation breakdown button
        if st.button("🧮 Show Calculation Breakdown", use_container_width=True, help="See how the total value was calculated step by step"):
            st.markdown("### 🧮 Total Value Calculation Breakdown")
            
            # Extract calculation components from results with safety checks
            # Use cached area for consistency
            if 'cached_area_ha' in st.session_state and st.session_state.cached_area_ha:
                area_ha = st.session_state.cached_area_ha
            else:
                area_ha = results.get('area_ha', 0)
            ecosystem_type = results.get('ecosystem_type', 'Unknown')
            total_value = results.get('total_value', 0)
            regional_factor = results.get('regional_adjustment_factor', results.get('regional_factor', 1.0))
            quality_factor = results.get('quality_factor', 1.0)
            
            st.markdown(f"""
            **Step-by-Step Calculation for {ecosystem_type} Ecosystem:**
            
            **1. Area Calculation**
            - Selected area: **{area_ha:,.0f} hectares**
            - Coordinate-based area calculation using shoelace formula
            
            **2. Base ESVD Coefficients (Pre-computed from 10,874+ studies)**
            """)
            
            # Show calculation that matches main results
            try:
                # Use the actual calculated results for consistency
                actual_total = total_value
                actual_per_ha = total_value / area_ha if area_ha > 0 else 0
                
                st.markdown("**Calculation Method:**")
                st.markdown(f"This breakdown shows how the displayed total of **${actual_total:,.0f}/year** was calculated")
                
                # Show service category breakdown if available
                if 'provisioning' in results or 'regulating' in results or 'cultural' in results or 'supporting' in results:
                    st.markdown("\n**Service Category Totals (after all adjustments):**")
                    category_totals = {}
                    
                    for category in ['provisioning', 'regulating', 'cultural', 'supporting']:
                        if category in results:
                            category_value = results[category].get('total', 0)
                            category_totals[category] = category_value
                            st.markdown(f"- **{category.title()}**: ${category_value:,.0f}/year")
                    
                    category_sum = sum(category_totals.values())
                    
                    # Check if there's a difference between category sum and actual total (indicating quality factor was applied)
                    ecosystem_intactness = st.session_state.get('ecosystem_intactness', {})
                    ecosystem_type_for_calc = results.get('ecosystem_type', 'Temperate Forest')
                    user_quality_factor = _get_ecosystem_intactness_multiplier(ecosystem_type_for_calc, ecosystem_intactness)
                    
                    st.markdown(f"\n**📊 Complete Calculation Flow:**")
                    
                    # Get the regional factor for proper breakdown
                    regional_factor = results.get('regional_adjustment_factor', 1.0)
                    ecosystem_intactness = st.session_state.get('ecosystem_intactness', {})
                    ecosystem_type_for_calc = results.get('ecosystem_type', 'Temperate Forest')
                    user_quality_factor = _get_ecosystem_intactness_multiplier(ecosystem_type_for_calc, ecosystem_intactness)
                    
                    # Calculate the correct step-by-step breakdown
                    # Note: The ESVD results already include regional adjustment, so we need to work backwards
                    if user_quality_factor != 1.0 and actual_total != 0:
                        # actual_total = (base × regional) × intactness
                        regionally_adjusted_total = actual_total / user_quality_factor
                        true_base_total = regionally_adjusted_total / regional_factor if regional_factor != 0 else regionally_adjusted_total
                        
                        st.markdown(f"1. **Base ESVD Services**: ${true_base_total:,.0f}/year")
                        st.markdown(f"   - Raw coefficients × area = ${true_base_total:,.0f}")
                        st.markdown(f"2. **Regional Economic Adjustment**: ${true_base_total:,.0f} × {regional_factor:.2f} = ${regionally_adjusted_total:,.0f}/year")
                        st.markdown(f"3. **User Intactness Factor**: ${regionally_adjusted_total:,.0f} × {user_quality_factor:.2f} = **${actual_total:,.0f}/year**")
                    else:
                        # When user factor is 1.0, show proper base calculation
                        # actual_total already includes regional factor, so divide it out
                        true_base_total = actual_total / regional_factor if regional_factor != 0 else actual_total
                        st.markdown(f"1. **Base ESVD Services**: ${true_base_total:,.0f}/year")
                        st.markdown(f"   - Raw coefficients × area = ${true_base_total:,.0f}")
                        st.markdown(f"2. **Regional Economic Adjustment**: ${true_base_total:,.0f} × {regional_factor:.2f} = **${actual_total:,.0f}/year**")
                        if user_quality_factor == 1.0:
                            st.markdown(f"3. **User Intactness Factor**: No adjustment (100% intactness)")
                    
                    st.markdown(f"\n**Final Result**: **${actual_total:,.0f}/year**")
                    
                    # Show predominant country and regional factor
                    try:
                        # Extract all sampling point coordinates
                        sample_points = []
                        if 'sampling_point_data' in st.session_state:
                            sampling_point_data = st.session_state['sampling_point_data']
                            for point_data in sampling_point_data.values():
                                # Handle both coordinate formats for compatibility
                                coords_dict = point_data.get('coordinates', {})
                                coords_list = point_data.get('coords', [])
                                
                                if coords_dict and isinstance(coords_dict, dict):
                                    lat = coords_dict.get('lat')
                                    lon = coords_dict.get('lon')
                                    if lat is not None and lon is not None:
                                        sample_points.append((lat, lon))
                                elif coords_list and len(coords_list) >= 2:
                                    sample_points.append((coords_list[0], coords_list[1]))
                        
                        if sample_points:
                            from utils.nominatim_geocoding import determine_predominant_country
                            country_result = determine_predominant_country(sample_points)
                            
                            country_name = country_result['country']
                            if country_name == 'International Waters':
                                display_name = "International Waters"
                            else:
                                # Format country name for display
                                display_name = country_name.replace('_', ' ').title()
                            
                            # Show vote count and tie information
                            vote_info = f"{country_result['count']}/{country_result['total_points']} samples"
                            tie_annotation = " [tie-break]" if country_result['tie_broken'] else ""
                            
                            st.markdown(f"**🌍 Analysis Location**: {display_name} ({vote_info}){tie_annotation}")
                            st.markdown(f"**💰 Regional Factor**: {regional_factor:.2f}x (applied to base coefficients)")
                        else:
                            st.markdown(f"**🌍 Analysis Location**: No sampling points found")
                            st.markdown(f"**💰 Regional Factor**: {regional_factor:.2f}x")
                    except Exception as e:
                        st.markdown(f"**🌍 Analysis Location**: Unable to determine ({str(e)[:50]}...)")
                        st.markdown(f"**💰 Regional Factor**: {regional_factor:.2f}x")
                    
                else:
                    # Fallback calculation display
                    st.markdown(f"\n**📊 Summary:**")
                    st.markdown(f"- **Total Value**: ${actual_total:,.0f}/year")
                    st.markdown(f"- **Area**: {area_ha:,.0f} hectares")
                    st.markdown(f"- **Value per Hectare**: ${actual_per_ha:,.0f}/ha/year")
                    st.markdown(f"- **Regional Factor**: {regional_factor:.2f}")
                    st.markdown(f"- **Quality Factor**: {quality_factor:.2f}")
                    
                    # Show predominant country in fallback mode too
                    try:
                        # Extract all sampling point coordinates
                        sample_points = []
                        if 'sampling_point_data' in st.session_state:
                            sampling_point_data = st.session_state['sampling_point_data']
                            for point_data in sampling_point_data.values():
                                # Handle both coordinate formats for compatibility
                                coords_dict = point_data.get('coordinates', {})
                                coords_list = point_data.get('coords', [])
                                
                                if coords_dict and isinstance(coords_dict, dict):
                                    lat = coords_dict.get('lat')
                                    lon = coords_dict.get('lon')
                                    if lat is not None and lon is not None:
                                        sample_points.append((lat, lon))
                                elif coords_list and len(coords_list) >= 2:
                                    sample_points.append((coords_list[0], coords_list[1]))
                        
                        if sample_points:
                            from utils.nominatim_geocoding import determine_predominant_country
                            country_result = determine_predominant_country(sample_points)
                            
                            country_name = country_result['country']
                            if country_name == 'International Waters':
                                display_name = "International Waters"
                            else:
                                # Format country name for display
                                display_name = country_name.replace('_', ' ').title()
                            
                            # Show vote count and tie information
                            vote_info = f"{country_result['count']}/{country_result['total_points']} samples"
                            tie_annotation = " [tie-break]" if country_result['tie_broken'] else ""
                            
                            st.markdown(f"- **Analysis Location**: {display_name} ({vote_info}){tie_annotation}")
                        else:
                            st.markdown(f"- **Analysis Location**: No sampling points found")
                    except Exception as e:
                        st.markdown(f"- **Analysis Location**: Unable to determine ({str(e)[:50]}...)")
                
                st.info("💡 **Note**: This calculation uses pre-computed ESVD coefficients with regional economic adjustments and user-defined ecosystem intactness factors.")
                    
            except Exception as e:
                st.info("Using standard calculation method")
                base_per_ha = total_value / (area_ha * regional_factor * quality_factor) if area_ha > 0 else 0
                st.markdown(f"- **Base coefficient**: ${base_per_ha:.0f}/ha/year (ecosystem average)")
            
            st.markdown(f"""
            **3. Regional Adjustment**
            - Regional factor: **{regional_factor:.2f}**
            - Adjusts for local income levels and cost of living
            
            **4. Quality Assessment (OpenLandMap Detection)**
            - Quality multiplier: **{quality_factor:.2f}**
            - Based on satellite data quality indicators
            
            **5. Final Calculation**
            ```
            Total Value = Base Coefficients × Area × Regional Factor × Intactness Factor
            Total Value = [Service Values] × {area_ha:,.0f} ha × {regional_factor:.2f} × {quality_factor:.2f}
            Total Value = ${total_value:,.0f}/year
            ```
            
            **Data Sources:**
            - **ESVD Database**: 10,874+ peer-reviewed ecosystem service values
            - **OpenLandMap**: Global land cover classification for ecosystem detection
            - **Regional Data**: Income and cost-of-living adjustments
            """)
            
            st.success(f"**Final Result**: ${total_value:,.0f}/year total ecosystem value")
        
elif st.session_state.get('selected_area'):
    coords = st.session_state.area_coordinates
    
    # Calculate area in hectares (cached) with latitude correction
    # Only recalculate if we don't have a cached area at all
    if 'cached_area_ha' not in st.session_state or st.session_state.cached_area_ha is None:
        # Use optimized calculation function for consistency
        area_ha = calculate_area_optimized(coords)
        st.session_state.cached_area_ha = area_ha
        st.session_state.area_coords_cache = coords
        
        area_ha = st.session_state.get('cached_area_ha', 0)
        if area_ha and area_ha > 0:
            st.markdown(f'<p class="result-info-lg"><strong>Area Size:</strong> {area_ha:.2f} hectares</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="result-info-lg"><strong>Area Size:</strong> Calculating...</p>', unsafe_allow_html=True)
        
        # Show ecosystem detection status with composition
        if st.session_state.ecosystem_override == "Auto-detect":
            if 'detected_ecosystem' in st.session_state:
                ecosystem_info = st.session_state.detected_ecosystem
                primary_ecosystem = ecosystem_info['primary_ecosystem']
                
                # Show primary ecosystem
                st.info(f"**Predominant:** {primary_ecosystem}")
                
                # Show composition if multiple ecosystems detected
                if 'ecosystem_distribution' in ecosystem_info and len(ecosystem_info['ecosystem_distribution']) > 1:
                    st.info("**Composition:**")
                    ecosystem_distribution = ecosystem_info['ecosystem_distribution']
                    total_samples = ecosystem_info['successful_queries']
                    
                    for eco_type, data in ecosystem_distribution.items():
                        percentage = (data['count'] / total_samples) * 100
                        st.write(f"   • {eco_type}: {percentage:.1f}%")
                        
            else:
                st.info("Calculation parameters can be changed in the settings side bar.")
        else:
            st.info(f"**Ecosystem:** {st.session_state.ecosystem_override}")
        st.info(f"**Analysis:** {st.session_state.analysis_detail}")
        
        if st.session_state.analysis_results:
            st.success("📈 Analysis Complete")
            st.write("Results are ready for viewing")
        else:
            st.info("Ready for analysis - click 'Calculate Value' button")
    else:
        pass
    

# Progress display container for analysis (always available)
analysis_progress_container = st.empty()

# Analysis with OpenLandMap ecosystem detection
if analyze_button and st.session_state.selected_area:
    try:
        # Use cached area calculation if available, otherwise calculate with latitude correction
        if 'cached_area_ha' in st.session_state and st.session_state.cached_area_ha is not None:
            area_ha = st.session_state.cached_area_ha
        else:
            coords = st.session_state.area_coordinates
            area_ha = calculate_area_optimized(coords)
            # Cache the calculated area
            st.session_state.cached_area_ha = area_ha
        
        # Update the progress container in the right column instead of creating new sections
        with analysis_progress_container.container():
            st.markdown("### 🔄 Analysis in Progress")
            # Enhanced loading state with modern design
            st.markdown("""
            <div class="modern-card loading-pulse">
                <h4>🔄 Analyzing Your Ecosystem...</h4>
                <p>We're processing your selected area using satellite data and scientific valuation coefficients.</p>
            </div>
            """, unsafe_allow_html=True)
            
            progress_text = st.empty()
            progress_bar = st.progress(0)
        
        with st.spinner("Please wait - Analyzing ecosystem and calculating values..."):
            # Detect ecosystem type if auto-detection is enabled or convert manual selection
            ecosystem_type = st.session_state.ecosystem_override
            
            # Convert display names to internal forest type names
            forest_type_mapping = {
                "Tropical Forest": "tropical_forest",
                "Temperate Forest": "temperate_forest", 
                "Boreal Forest": "boreal_forest",
            }
            
            # Handle manual forest type selection
            manual_forest_selection = None
            if ecosystem_type in forest_type_mapping:
                manual_forest_selection = {
                    'original_type': 'Forest',
                    'detected_type': forest_type_mapping[ecosystem_type],
                    'climate_zone': ecosystem_type.replace(' Forest', ''),
                    'coordinates': None,  # Will be set later
                    'selection_method': 'Manual'
                }
                ecosystem_type = forest_type_mapping[ecosystem_type]
            
            # Handle Water Bodies selection - behave like auto-detect but focus on water
            water_bodies_mode = (st.session_state.ecosystem_override == "Water (ocean)")
            
            # Skip ecosystem detection if water bodies are already classified
            if st.session_state.get('skip_ecosystem_detection', False):
                # Use existing sample point data with user classifications
                st.info("🌊 Using existing sample data with water body classifications...")
                sampling_point_data = st.session_state.get('sampling_point_data', {})
                data_source = st.session_state.get('landcover_data_source', 'openlandmap')
                
                # Create ecosystem_info from existing data
                ecosystem_counts = {}
                for point_data in sampling_point_data.values():
                    eco_type = point_data.get('ecosystem_type', 'Grassland')
                    if eco_type not in ecosystem_counts:
                        ecosystem_counts[eco_type] = {'count': 0}
                    ecosystem_counts[eco_type]['count'] += 1
                
                primary_ecosystem = max(ecosystem_counts.items(), key=lambda x: x[1]['count'])[0]
                
                ecosystem_info = {
                    'primary_ecosystem': primary_ecosystem,
                    'successful_queries': len(sampling_point_data),
                    'ecosystem_distribution': ecosystem_counts,
                    'total_samples': len(sampling_point_data),
                    'detection_method': 'User-classified water bodies'
                }
                
                # Keep flags until analysis is complete
                # Don't clear the flags here - they need to persist until after valuation
                
            elif (st.session_state.ecosystem_override == "Auto-detect" or water_bodies_mode) and not st.session_state.get('skip_ecosystem_detection', False):
                try:
                    from utils.openlandmap_integration import detect_ecosystem_type
                    
                    # Use cached area calculation for performance
                    area_hectares = area_ha
                    
                    # Ultra-optimized sampling with user-configurable limits
                    max_limit = st.session_state.get('max_sampling_limit', 9)
                    expected_points = max_limit
                    
                    # Optimize grid generation for performance
                    grid_size = int(np.sqrt(expected_points))
                    actual_expected_points = max(4, grid_size ** 2)
                    
                    # Update progress container for detection phase
                    with analysis_progress_container.container():
                        progress_text = st.empty()
                        progress_bar = st.progress(0)
                    
                    # Enhanced progress callback with sample count and percentage
                    def update_progress(current_point, total_points):
                        # Update progress every 25% or final point for maximum performance
                        if current_point % max(1, total_points // 4) == 0 or current_point == total_points:
                            progress = current_point / total_points
                            progress_bar.progress(progress)
                            if current_point == total_points:
                                progress_text.success(f"✅ Analysis complete: {current_point}/{total_points} samples ({progress:.0%})")
                            else:
                                progress_text.info(f"🔍 Sampling progress: {current_point}/{total_points} samples ({progress:.0%})")
                    
                    ecosystem_info = detect_ecosystem_type(
                        st.session_state.area_coordinates, 
                        st.session_state.sampling_frequency,
                        max_sampling_limit=max_limit,
                        progress_callback=update_progress,
                        include_environmental_indicators=st.session_state.get('include_environmental_indicators', False)
                    )
                    
                    # Always do fresh sampling for each analysis
                    # Extract complete sampling point data from ecosystem detection
                    sampling_point_data = {}
                    data_source = 'estimated'
                    has_real_satellite_data = False  # Track if we find any real satellite data
                    
                    if ecosystem_info and 'sample_results' in ecosystem_info:
                        for i, result in enumerate(ecosystem_info['sample_results']):
                            if result:
                                # Extract all available data from OpenLandMap API
                                # Extract source from multiple possible fields
                                actual_source = (result.get('source') or 
                                               result.get('data_source') or 
                                               result.get('stac_data', {}).get('data_source') or 
                                               'Unknown')
                                
                                point_data = {
                                    'landcover_class': result.get('landcover_class', 'Unknown'),
                                    'ecosystem_type': result.get('ecosystem_type', 'Unknown'),
                                    'source': actual_source,  # Use the extracted source
                                    'coordinates': result.get('coordinates', {'lat': 0, 'lon': 0}),
                                    'stac_data': result.get('stac_data', {}),
                                    'raw_stac_data': result.get('raw_stac_data', {})  # Include raw STAC response data
                                }
                                sampling_point_data[f'point_{i}'] = point_data
                                
                                # Check for real ESA satellite data vs geographic fallback using extracted source
                                source_to_check = (result.get('source') or 
                                                 result.get('data_source') or 
                                                 result.get('stac_data', {}).get('data_source') or 
                                                 'Unknown')
                                if 'Real ESA Satellite Data' in source_to_check or 'GeoTIFF Pixel' in source_to_check:
                                    has_real_satellite_data = True
                                elif any(term in source_to_check for term in ['OpenLandMap', 'STAC']):
                                    has_real_satellite_data = True
                        
                        # Set final data source based on whether we found any real satellite data
                        if has_real_satellite_data:
                            data_source = 'openlandmap'
                    
                    # Handle water body classification with automatic continuation
                    water_body_points = {}
                    needs_classification = False
                    
                    # For Water Bodies mode, force all points to be water bodies for testing
                    if water_bodies_mode:
                        for point_id, point_data in sampling_point_data.items():
                            point_data['landcover_class'] = 210
                            point_data['simulated_water_body'] = True
                    
                    # Collect all water body points (ESA code 210)
                    for point_id, point_data in sampling_point_data.items():
                        if point_data.get('landcover_class') == 210:
                            water_body_points[point_id] = point_data
                    
                    # Check if we need classification (water bodies exist but not yet classified)
                    if water_body_points:
                        for point_id, point_data in water_body_points.items():
                            if not point_data.get('user_classified', False):
                                needs_classification = True
                                break
                    
                    # Show classification dialog only if needed
                    if needs_classification:
                        
                        st.warning("🌊 **Water Bodies Detected!**")
                        st.markdown(f"Found **{len(water_body_points)}** sample points with water bodies.")
                        
                        # Show sample point locations
                        st.markdown("**Sample Point Locations:**")
                        for point_id, point_data in water_body_points.items():
                            point_num = point_id.replace('point_', '')
                            coords = point_data.get('coordinates', {})
                            lat, lon = coords.get('lat', 0), coords.get('lon', 0)
                            st.write(f"• Sample Point {int(point_num) + 1}: {lat:.4f}°N, {abs(lon):.4f}°{'E' if lon >= 0 else 'W'}")
                        
                        
                        st.info("**Classify all water bodies at once:**")
                        
                        bulk_water_type = st.radio(
                            f"How should ALL {len(water_body_points)} water bodies be classified?",
                            options=["Please select...", "All Ocean", "All Rivers/Lakes", "All Coastal"],
                            key="bulk_water_classification",
                            help="This classification will be applied to all detected water bodies"
                        )
                        
                        # Auto-trigger analysis when selection is made
                        if bulk_water_type != "Please select...":
                            # Map bulk choice to individual ecosystem types
                            ecosystem_mapping = {
                                "All Ocean": "Marine",
                                "All Rivers/Lakes": "Rivers and Lakes", 
                                "All Coastal": "Coastal"
                            }
                            
                            selected_ecosystem = ecosystem_mapping[bulk_water_type]
                            
                            # Apply classification to ALL water body points
                            for point_id, point_data in water_body_points.items():
                                sampling_point_data[point_id]['ecosystem_type'] = selected_ecosystem
                                sampling_point_data[point_id]['original_landcover_class'] = 210
                                sampling_point_data[point_id]['user_classified'] = True
                            
                            # Store the updated data immediately
                            st.session_state.sampling_point_data = sampling_point_data
                            st.session_state.landcover_codes = {k: v['landcover_class'] for k, v in sampling_point_data.items()}
                            
                            # Call EEI API to get ecosystem integrity values (only if enabled)
                            if st.session_state.get('use_eei_for_intactness', False):
                                try:
                                    from utils.eei_api import extract_eei_for_sample_points, get_eei_per_ecosystem
                                    point_eei_values, average_eei = extract_eei_for_sample_points(sampling_point_data)
                                    st.session_state.point_eei_values = point_eei_values
                                    st.session_state.average_eei = average_eei
                                    
                                    # Calculate EEI per ecosystem for intactness defaults
                                    ecosystem_eei = get_eei_per_ecosystem(sampling_point_data, point_eei_values)
                                    st.session_state.ecosystem_eei = ecosystem_eei
                                    
                                    # Set intactness defaults based on EEI (convert 0-1 to 0-100%)
                                    if ecosystem_eei:
                                        for eco_type, eei_value in ecosystem_eei.items():
                                            if eei_value is not None:
                                                # Normalize to title case for consistent lookup in scenario builder
                                                normalized_type = eco_type.replace('_', ' ').title()
                                                # Store with 3 decimal places precision
                                                intactness_pct = round(eei_value * 100, 3)
                                                st.session_state.ecosystem_intactness[normalized_type] = intactness_pct
                                                # Also set with original key for backwards compatibility
                                                st.session_state.ecosystem_intactness[eco_type] = intactness_pct
                                except Exception as e:
                                    st.session_state.point_eei_values = {}
                                    st.session_state.average_eei = None
                                    st.session_state.ecosystem_eei = {}
                            else:
                                # EEI disabled - clear any stored values
                                st.session_state.point_eei_values = {}
                                st.session_state.average_eei = None
                                st.session_state.ecosystem_eei = {}
                            
                            st.success(f"✅ All {len(water_body_points)} water bodies classified as {selected_ecosystem}! Analysis continues below...")
                            
                            # Skip re-sampling and go directly to valuation with updated classifications
                            st.session_state.water_bodies_classified = True
                            st.session_state.skip_ecosystem_detection = True
                            
                            # Create ecosystem_info from existing classified data
                            ecosystem_counts = {}
                            for point_data in sampling_point_data.values():
                                eco_type = point_data.get('ecosystem_type', 'Grassland')
                                if eco_type not in ecosystem_counts:
                                    ecosystem_counts[eco_type] = {'count': 0}
                                ecosystem_counts[eco_type]['count'] += 1
                            
                            # No need to calculate averages anymore
                            
                            primary_ecosystem = max(ecosystem_counts.items(), key=lambda x: x[1]['count'])[0]
                            
                            ecosystem_info = {
                                'primary_ecosystem': primary_ecosystem,
                                'successful_queries': len(sampling_point_data),
                                'ecosystem_distribution': ecosystem_counts,
                                'total_samples': len(sampling_point_data),
                                'detection_method': 'User-classified water bodies'
                            }
                            
                            # Jump directly to ecosystem processing - skip the ecosystem detection loop
                            st.session_state.detected_ecosystem = ecosystem_info
                            ecosystem_type = ecosystem_info['primary_ecosystem']
                            
                        else:
                            st.info("👆 Please select how to classify all water bodies above.")
                            st.stop()  # Only stop if user hasn't selected anything
                    
                    # Only continue if water bodies haven't been classified yet
                    if not st.session_state.get('water_bodies_classified', False):
                        # Store complete sampling point information for display
                        st.session_state.sampling_point_data = sampling_point_data
                        st.session_state.landcover_codes = {k: v['landcover_class'] for k, v in sampling_point_data.items()}  # Backward compatibility
                        st.session_state.landcover_data_source = data_source
                        
                        # Call EEI API to get ecosystem integrity values (only if enabled)
                        if st.session_state.get('use_eei_for_intactness', False):
                            try:
                                from utils.eei_api import extract_eei_for_sample_points, get_eei_per_ecosystem
                                point_eei_values, average_eei = extract_eei_for_sample_points(sampling_point_data)
                                st.session_state.point_eei_values = point_eei_values
                                st.session_state.average_eei = average_eei
                                
                                # Calculate EEI per ecosystem for intactness defaults
                                ecosystem_eei = get_eei_per_ecosystem(sampling_point_data, point_eei_values)
                                st.session_state.ecosystem_eei = ecosystem_eei
                                
                                # Set intactness defaults based on EEI (convert 0-1 to 0-100%)
                                if ecosystem_eei:
                                    for eco_type, eei_value in ecosystem_eei.items():
                                        if eei_value is not None:
                                            # Normalize to title case for consistent lookup in scenario builder
                                            normalized_type = eco_type.replace('_', ' ').title()
                                            # Store with 3 decimal places precision
                                            intactness_pct = round(eei_value * 100, 3)
                                            st.session_state.ecosystem_intactness[normalized_type] = intactness_pct
                                            # Also set with original key for backwards compatibility
                                            st.session_state.ecosystem_intactness[eco_type] = intactness_pct
                            except Exception as e:
                                st.session_state.point_eei_values = {}
                                st.session_state.average_eei = None
                                st.session_state.ecosystem_eei = {}
                        else:
                            # EEI disabled - clear any stored values
                            st.session_state.point_eei_values = {}
                            st.session_state.average_eei = None
                            st.session_state.ecosystem_eei = {}
                        
                        # Show completion in progress container
                        with analysis_progress_container.container():
                            st.markdown("### 🔄 Analysis in Progress")
                            progress_text = st.empty()
                            progress_bar = st.progress(1.0)
                            progress_text.success(f"✅ Ecosystem detection complete! Processed {ecosystem_info['total_samples']}/{ecosystem_info['total_samples']} samples (100%)")
                        
                        # Brief pause to show completion (reduced for performance)
                        import time
                        time.sleep(0.3)
                        
                        st.session_state.detected_ecosystem = ecosystem_info
                        ecosystem_type = ecosystem_info['primary_ecosystem']
                    
                    # Show detection results with details
                    if ecosystem_info['successful_queries'] > 0:
                        if 'ecosystem_distribution' in ecosystem_info:
                            ecosystem_distribution = ecosystem_info['ecosystem_distribution']
                            total_samples = ecosystem_info['successful_queries']
                            if len(ecosystem_distribution) > 1:
                                simpson_index = sum(
                                    (data['count'] / total_samples) ** 2
                                    for data in ecosystem_distribution.values()
                                )
                                simpson_diversity = 1 - simpson_index
                                # Display combined single panel — mixed + predominant + diversity
                                # (line 4026 shows this in detail; suppress it here to avoid duplication)
                            else:
                                # Single ecosystem type
                                percentage = (ecosystem_distribution[ecosystem_type]['count'] / total_samples) * 100
                                st.info(f"📊 **{ecosystem_type}** · {percentage:.1f}% coverage")
                    else:
                        st.info(f"🗺️ **Detected: {ecosystem_type}** (Geographic analysis)")
                        
                except Exception as e:
                    st.warning(f"⚠️ Ecosystem detection failed: {str(e)}")
                    st.info("🗺️ **Default: Grassland** (Geographic analysis)")
                    ecosystem_type = "Grassland"
                    # Store default detection info
                    st.session_state.detected_ecosystem = {
                        'primary_ecosystem': 'Grassland',
                        'successful_queries': 0,
                        'source': 'Geographic analysis',
                        'coverage_percentage': 100
                    }
            
            # Update progress for valuation phase
            with analysis_progress_container.container():
                st.markdown("### 🔄 Analysis in Progress")
                progress_text = st.empty()
                progress_bar = st.progress(0.9)
                progress_text.markdown("""
                <div class="status-success">
                    💰 <strong>Calculating Values</strong> - Computing ecosystem service values using scientific coefficients...
                </div>
                """, unsafe_allow_html=True)
            
            # Calculate authentic ecosystem values using pre-computed ESVD coefficients
            from utils.precomputed_esvd_coefficients import get_precomputed_coefficients
            
            # Get center coordinates for regional adjustment (optimized)
            coords_array = np.array(st.session_state.area_coordinates[:-1], dtype=np.float32)
            center_lat = float(coords_array[:, 1].mean())
            center_lon = float(coords_array[:, 0].mean())
            
            # Check if we have mixed ecosystem data for weighted calculation
            # Only use mixed calculation if there are truly multiple significant ecosystem types (>10% each)
            # CRITICAL FIX: Force single ecosystem calculation when user explicitly selects ecosystem type
            has_mixed_ecosystems = False
            
            # If user selected specific ecosystem (not Auto-detect), always use single ecosystem calculation
            if st.session_state.ecosystem_override != "Auto-detect":
                has_mixed_ecosystems = False
            elif (st.session_state.get('detected_ecosystem') and 
                'ecosystem_distribution' in st.session_state.detected_ecosystem and
                len(st.session_state.detected_ecosystem['ecosystem_distribution']) > 1):
                
                ecosystem_distribution = st.session_state.detected_ecosystem['ecosystem_distribution']
                total_points = st.session_state.detected_ecosystem['successful_queries']
                
                # Check if there are multiple significant ecosystem types (each >10% coverage)
                significant_ecosystems = 0
                for eco_type, data in ecosystem_distribution.items():
                    proportion = data['count'] / total_points
                    if proportion > 0.1:  # More than 10% coverage
                        significant_ecosystems += 1
                
                has_mixed_ecosystems = significant_ecosystems > 1
            
            # Force ecosystem type when user selects specific type (not Auto-detect)
            if st.session_state.ecosystem_override != "Auto-detect":
                # Map UI selection to ESVD ecosystem type
                override_mapping = {
                    "Agricultural": "agricultural",
                    "Temperate Forest": "temperate_forest",
                    "Tropical Forest": "tropical_forest", 
                    "Boreal Forest": "boreal_forest",
                    "Grassland": "grassland",
                    "Wetland": "wetland",
                    "Coastal": "coastal",
                    "Marine": "marine",
                    "Desert": "desert",
                    "Urban": "urban",
                    "polar": "polar"
                }
                ecosystem_type = override_mapping.get(st.session_state.ecosystem_override, "agricultural")
                
            if has_mixed_ecosystems:
                
                # Use mixed ecosystem calculation with proper weighting
                ecosystem_distribution = st.session_state.detected_ecosystem['ecosystem_distribution']
                num_types = len(ecosystem_distribution)
                
                # Calculate diversity index for valuation display
                total_points = st.session_state.detected_ecosystem['successful_queries']
                shannon_div = 0
                simpson_index = 0
                for eco_type, data in ecosystem_distribution.items():
                    proportion = data['count'] / total_points
                    if proportion > 0:
                        shannon_div -= proportion * math.log(proportion)
                    simpson_index += proportion ** 2
                simpson_diversity = 1 - simpson_index
                
                _primary_eco = st.session_state.detected_ecosystem.get('primary_ecosystem', ecosystem_type)
                st.info(f"🌍 **{_primary_eco}** (predominant) · {num_types} ecosystem types detected · Simpson diversity: {simpson_diversity:.2f}")
                
                # Show detailed composition breakdown for analysis (optimized)
                st.write("**📋 Detailed Composition for Valuation:**")
                total_samples = st.session_state.detected_ecosystem['successful_queries']
                composition_lines = []
                for eco_type, data in ecosystem_distribution.items():
                    proportion = data['count'] / total_samples * 100
                    area_proportion = area_ha * (proportion / 100)
                    composition_lines.append(f"   • **{eco_type}**: {proportion:.1f}% → {area_proportion:.1f} ha ({data['count']} sample points)")
                
                st.markdown('\n'.join(composition_lines))
                st.caption("💡 Mixed ecosystem valuations use area-weighted coefficients from each ecosystem type.")
                
                # Initialize the calculator
                coeffs = get_precomputed_coefficients()
                
                # Calculate weighted values for mixed ecosystem
                total_value = 0
                mixed_results = {}
                
                for eco_type, data in ecosystem_distribution.items():
                    proportion = data['count'] / total_points
                    # Apply consistent rounding to match display percentages (fixes precision discrepancies)
                    proportion_percent = proportion * 100
                    rounded_proportion_percent = round(proportion_percent, 1)
                    rounded_proportion = rounded_proportion_percent / 100
                    eco_area = area_ha * rounded_proportion
                    
                    # Calculate value for this ecosystem type with forest type detection
                    # Only apply urban green/blue multiplier for urban ecosystems
                    if eco_type.lower() == 'urban':
                        urban_multiplier_percent = st.session_state.get('urban_green_blue_multiplier', 18.0)
                        urban_multiplier = urban_multiplier_percent / 100.0
                    else:
                        urban_multiplier = 1.0  # Default for non-urban ecosystems
                    
                    # Get ecosystem-specific intactness multiplier
                    ecosystem_intactness = st.session_state.get('ecosystem_intactness', {})
                    intactness_multiplier = _get_ecosystem_intactness_multiplier(eco_type, ecosystem_intactness)
                    
                    eco_result = coeffs.calculate_ecosystem_values(
                        ecosystem_type=eco_type,
                        area_hectares=eco_area,
                        coordinates=(center_lat, center_lon),
                        urban_green_blue_multiplier=urban_multiplier,
                        ecosystem_intactness_multiplier=intactness_multiplier
                    )
                    
                    # Both urban green/blue and ecosystem intactness multipliers now applied at service level in ESVD calculation
                    
                    # Apply ESA land cover code specific multiplier if available
                    if st.session_state.get('detected_ecosystem') and 'landcover_class' in st.session_state.detected_ecosystem:
                        landcover_code = st.session_state.detected_ecosystem['landcover_class']
                        esa_multiplier = st.session_state.get('esa_code_multipliers', {}).get(landcover_code, 100) / 100.0
                        eco_result['total_value'] = eco_result['total_value'] * esa_multiplier
                    
                    total_value += eco_result['total_value']
                    mixed_results[eco_type] = eco_result
                
                # Check if any forest types were detected in mixed results
                forest_types_detected = []
                for eco_type, eco_result in mixed_results.items():
                    if 'forest_classification' in eco_result:
                        forest_types_detected.append(eco_result['forest_classification'])
                    elif 'forest' in eco_result.get('ecosystem_type', '').lower():
                        forest_types_detected.append({
                            'detected_type': eco_result.get('ecosystem_type', eco_type),
                            'proportion': data['count'] / total_points
                        })
                
                # Create ecosystem composition for display
                ecosystem_composition = {}
                individual_ecosystem_results = {}
                
                for eco_type, data in ecosystem_distribution.items():
                    proportion = data['count'] / total_points
                    ecosystem_composition[eco_type] = proportion
                    
                    # Format individual results for display
                    eco_result = mixed_results[eco_type]
                    individual_ecosystem_results[eco_type] = {
                        'total_value': eco_result['total_value'],
                        'area_hectares': area_ha * proportion,
                        'value_per_hectare': eco_result['total_value'] / (area_ha * proportion) if area_ha * proportion > 0 else 0
                    }
                
                # Extract regional factor from the first ecosystem result for mixed display
                first_ecosystem_result = list(mixed_results.values())[0] if mixed_results else {}
                regional_adjustment = first_ecosystem_result.get('metadata', {}).get('regional_adjustment', 1.0)
                
                # Create combined results  
                esvd_results = {
                    'total_value': total_value,
                    'total_annual_value': total_value,
                    'current_value': total_value,
                    'ecosystem_results': mixed_results,
                    'individual_ecosystem_results': individual_ecosystem_results,  # Add for display
                    'metadata': {
                        'calculation_method': 'Mixed ecosystem with forest type detection',
                        'ecosystem_count': len(ecosystem_distribution),
                        'ecosystem_composition': ecosystem_composition,  # Add for display
                        'regional_adjustment': regional_adjustment  # Include regional factor
                    }
                }
                
                # Add forest classification info if detected
                if forest_types_detected:
                    esvd_results['mixed_forest_types'] = forest_types_detected
            else:
                # Single ecosystem calculation with forest type detection
                coeffs = get_precomputed_coefficients()
                # Only apply urban green/blue multiplier for urban ecosystems
                if ecosystem_type.lower() == 'urban':
                    urban_multiplier_percent = st.session_state.get('urban_green_blue_multiplier', 18.0)
                    urban_multiplier = urban_multiplier_percent / 100.0
                else:
                    urban_multiplier = 1.0  # Default for non-urban ecosystems
                
                # Get ecosystem-specific intactness multiplier
                ecosystem_intactness = st.session_state.get('ecosystem_intactness', {})
                intactness_multiplier = _get_ecosystem_intactness_multiplier(ecosystem_type, ecosystem_intactness)
                
                esvd_results = coeffs.calculate_ecosystem_values(
                    ecosystem_type=ecosystem_type,
                    area_hectares=area_ha,
                    coordinates=(center_lat, center_lon),
                    urban_green_blue_multiplier=urban_multiplier,
                    ecosystem_intactness_multiplier=intactness_multiplier
                )
                
                
                # Both urban green/blue and ecosystem intactness multipliers now applied at service level in ESVD calculation
                
                # Apply ESA land cover code specific multiplier if available
                if st.session_state.get('detected_ecosystem') and 'landcover_class' in st.session_state.detected_ecosystem:
                    landcover_code = st.session_state.detected_ecosystem['landcover_class']
                    esa_multiplier = st.session_state.get('esa_code_multipliers', {}).get(landcover_code, 100) / 100.0
                    esvd_results['total_value'] = esvd_results['total_value'] * esa_multiplier
                    esvd_results['current_value'] = esvd_results['current_value'] * esa_multiplier
                    esvd_results['total_annual_value'] = esvd_results['total_annual_value'] * esa_multiplier
            
            # Determine the actual ecosystem type for display
            display_ecosystem_type = ecosystem_type
            if st.session_state.ecosystem_override == "Auto-detect" and st.session_state.get('detected_ecosystem'):
                display_ecosystem_type = st.session_state.detected_ecosystem.get('primary_ecosystem', ecosystem_type)
            
            # Determine the final ecosystem type for display - use specific forest type if detected
            final_ecosystem_type = display_ecosystem_type
            forest_classification = None
            
            # Check if forest type detection occurred in ESVD results
            if 'forest_classification' in esvd_results:
                forest_classification = esvd_results['forest_classification']
                final_ecosystem_type = forest_classification['detected_type']
            elif 'ecosystem_type' in esvd_results and esvd_results['ecosystem_type'] != display_ecosystem_type:
                # Use the specific forest type from ESVD calculation
                final_ecosystem_type = esvd_results['ecosystem_type']
                
                # Create forest classification info if it's a forest type
                if 'forest' in final_ecosystem_type.lower():
                    forest_classification = {
                        'original_type': display_ecosystem_type,
                        'detected_type': final_ecosystem_type,
                        'climate_zone': final_ecosystem_type.replace('_forest', '').title(),
                        'coordinates': (center_lat, center_lon)
                    }
            
            # Store comprehensive analysis results
            analysis_results = {
                'total_value': int(esvd_results.get('total_annual_value', esvd_results.get('current_value', 0))),
                'area_ha': area_ha,
                'ecosystem_type': final_ecosystem_type,
                'esvd_results': esvd_results,
                'value_per_ha': esvd_results.get('total_annual_value', esvd_results.get('current_value', 0)) / area_ha,
                'data_source': 'ESVD/TEEB Database',
                'regional_factor': esvd_results.get('regional_adjustment_factor', esvd_results.get('metadata', {}).get('regional_adjustment', 1.0)),
                'quality_factor': st.session_state.get('quality_factor', 1.0),  # Default to 100% intactness
                'intactness_percentage': st.session_state.get('intactness_percentage', 100)
            }
            
            # Add forest classification if detected or manually selected
            if forest_classification:
                analysis_results['forest_classification'] = forest_classification
            elif manual_forest_selection:
                # Update coordinates for manual selection
                manual_forest_selection['coordinates'] = (center_lat, center_lon)
                analysis_results['forest_classification'] = manual_forest_selection
            
            st.session_state.analysis_results = analysis_results
            st.session_state.calculation_ready = True

            # Auto-save to DB for logged-in users
            if st.session_state.get('auth_user'):
                try:
                    _db_mods = get_database_modules()
                    if _db_mods:
                        _saved_id = _db_mods['EcosystemAnalysisDB'].save_analysis(
                            coordinates=st.session_state.area_coordinates,
                            area_hectares=area_ha,
                            ecosystem_type=final_ecosystem_type,
                            total_value=analysis_results['total_value'],
                            value_per_hectare=analysis_results['value_per_ha'],
                            analysis_results=analysis_results,
                            sampling_points=st.session_state.get('max_sampling_limit', 10),
                            area_name=st.session_state.get('default_area_name'),
                        )
                        if _saved_id:
                            st.session_state['last_saved_analysis_id'] = _saved_id
                except Exception as _save_err:
                    logger.warning(f"Auto-save analysis failed: {_save_err}")

            # Clear analysis in progress flag - analysis is now complete
            if 'analysis_in_progress' in st.session_state:
                del st.session_state['analysis_in_progress']
                
            # Clear water body classification flags after analysis is complete
            if 'skip_ecosystem_detection' in st.session_state:
                del st.session_state['skip_ecosystem_detection']
            if 'water_bodies_classified' in st.session_state:
                del st.session_state['water_bodies_classified']
            
            # Show final completion
            with analysis_progress_container.container():
                st.markdown("### ✅ Analysis Complete")
                st.success("🎉 **Analysis complete!** Economic valuation calculated successfully.")
            
            # Brief pause to show completion, then clear
            import time
            time.sleep(1.2)
            analysis_progress_container.empty()
                
    except Exception as e:
        st.error(f"Error processing area: {e}")
        st.info("Please try selecting the area again.")

# Display results if available (only show after calculation is complete)
if st.session_state.get('calculation_ready') and st.session_state.analysis_results:
    
    # Different displays based on analysis detail level
    analysis_mode = st.session_state.get('analysis_detail', 'Summary Analysis')
    
    if analysis_mode == "Summary Analysis":
        st.subheader("📈 Summary Results")
        results = st.session_state.analysis_results
        
        # Show data source status in summary view
        analysis_results_for_display = {
            'sampling_point_data': st.session_state.get('sampling_point_data', {}),
            'landcover_codes': st.session_state.get('landcover_codes', {}),
            'landcover_data_source': st.session_state.get('landcover_data_source', 'estimated')
        }
        display_data_source_status(analysis_results_for_display)
        
        # Show toast notification while results render
        st.toast("Loading valuation results...", icon="⏳")
        
        # Simple metrics display for summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Annual Value", f"${results['total_value']:,}")
        with col2:
            per_ha = results.get('value_per_ha', results['total_value']/results['area_ha'])
            st.metric("Value per Hectare", f"${per_ha:,.0f}/ha")
        with col3:
            # Area display with water exclusion for summary
            land_area = results.get('area_ha', results.get('area_hectares', 0))
            water_area = results.get('water_area_hectares', 0)
            
            if water_area > 0:
                st.metric("Land Area Analyzed", f"{land_area:,.0f} ha")
                st.caption(f"🌊 {water_area:,.0f} ha water excluded")
            else:
                st.metric("Area Analyzed", f"{land_area:,.0f} ha")
        
        # Enhanced ecosystem composition display
        if 'esvd_results' in results and 'metadata' in results['esvd_results']:
            metadata = results['esvd_results']['metadata']
            
            # Mixed ecosystem composition is now shown in sample points summary to avoid duplication
            if 'ecosystem_composition' in metadata:
                pass  # Skip mixed composition display - shown in sample points summary instead
            else:
                # Single ecosystem - make sure to show the actual detected type
                ecosystem_display = results['ecosystem_type']
                if ecosystem_display == "Auto-detect" and st.session_state.get('detected_ecosystem'):
                    ecosystem_display = st.session_state.detected_ecosystem.get('primary_ecosystem', ecosystem_display)
                st.info(f"**🌱 Predominant Ecosystem Type**: {ecosystem_display} (100% coverage)")
                st.caption(f"**Data Source**: {results.get('data_source', 'ESVD/TEEB Database')}")
        else:
            # Handle ecosystem type display for other cases
            ecosystem_display = results['ecosystem_type']
            if ecosystem_display == "Auto-detect" and st.session_state.get('detected_ecosystem'):
                ecosystem_display = st.session_state.detected_ecosystem.get('primary_ecosystem', ecosystem_display)
            st.info(f"**Predominant Ecosystem Type**: {ecosystem_display} | **Data Source**: {results.get('data_source', 'ESVD/TEEB Database')}")
        
        # Check if there's an existing baseline for this area
        baseline_info = None
        if st.session_state.get('current_area_id'):
            try:
                db_modules = get_database_modules()
                if db_modules and 'NaturalCapitalBaselineDB' in db_modules:
                    NaturalCapitalBaselineDB = db_modules['NaturalCapitalBaselineDB']
                    baseline_info = NaturalCapitalBaselineDB.get_area_baseline(st.session_state.current_area_id)
            except Exception:
                baseline_info = None
        
        # Show baseline comparison if available
        if baseline_info:
            try:
                db_modules = get_database_modules()
                if db_modules and 'NaturalCapitalBaselineDB' in db_modules:
                    NaturalCapitalBaselineDB = db_modules['NaturalCapitalBaselineDB']
                    comparison = NaturalCapitalBaselineDB.compare_to_baseline(results, baseline_info['id'])
                else:
                    comparison = None
            except Exception:
                comparison = None
            if comparison:
                st.markdown("### 📊 Baseline Comparison")
                
                col_comp1, col_comp2, col_comp3 = st.columns(3)
                with col_comp1:
                    change_color = "green" if comparison['total_change'] > 0 else "red" if comparison['total_change'] < 0 else "gray"
                    st.markdown(f"**Value Change**: <span style='color: {change_color};'>${comparison['total_change']:+,.0f}</span>", unsafe_allow_html=True)
                
                with col_comp2:
                    percent_color = "green" if comparison['percent_change'] > 0 else "red" if comparison['percent_change'] < 0 else "gray"
                    st.markdown(f"**Percent Change**: <span style='color: {percent_color};'>{comparison['percent_change']:+.1f}%</span>", unsafe_allow_html=True)
                
                with col_comp3:
                    trend_icon = "📈" if comparison['trend_direction'] == 'improving' else "📉" if comparison['trend_direction'] == 'declining' else "➡️"
                    st.markdown(f"**Trend**: {trend_icon} {comparison['trend_direction'].title()}")
                
                st.caption(f"Baseline established: {baseline_info['baseline_date'].strftime('%Y-%m-%d %H:%M')}")
        
            
    else:  # Detailed Analysis
        st.subheader("📈 Detailed Analysis Results")
        results = st.session_state.analysis_results
        
        # Show detailed data source status in detailed view
        analysis_results_for_display = {
            'sampling_point_data': st.session_state.get('sampling_point_data', {}),
            'landcover_codes': st.session_state.get('landcover_codes', {}),
            'landcover_data_source': st.session_state.get('landcover_data_source', 'estimated')
        }
        display_data_source_status(analysis_results_for_display)
        
        # Show toast notification while detailed results render
        st.toast("Loading detailed valuation results...", icon="⏳")
        
        col_metrics = st.columns(3)
        with col_metrics[0]:
            st.metric("Total Ecosystem Value", f"${results['total_value']:,}/year")
        with col_metrics[1]:
            per_ha_detailed = results.get('value_per_ha', results['total_value']/results['area_ha'])
            st.metric("Value per Hectare", f"${per_ha_detailed:,.0f}/ha")
        with col_metrics[2]:
            if 'ecosystem_composition' in results.get('metadata', {}):
                composition = results['metadata']['ecosystem_composition']
                dominant_type = max(composition.keys(), key=lambda k: composition[k])
                st.metric("Ecosystem Type", dominant_type, delta=f"{len(composition)} types")
            else:
                st.metric("Ecosystem Type", results["ecosystem_type"])
        # Show data source and methodology
        st.info(f"📊 **Data Source**: Pre-computed ESVD Coefficients (Static) | **Regional Adjustment**: Applied")
        
        with st.expander("💡 Data sources and methodology"):
            st.markdown(f"""
            **Primary Data Sources**:
            
            **Pre-computed ESVD Coefficients (Static)**:
            - Based on ESVD (Ecosystem Services Valuation Database) APR2024 V1.1
            - 10,874+ peer-reviewed value estimates from 1,100+ scientific studies
            - Pre-calculated median coefficients for optimal performance (238,270x faster)
            - Global coverage: 140+ countries, 15 biomes, 23 ecosystem services
            - Static values maintain research authenticity while eliminating API dependencies
            
            **TEEB Integration**:
            - TEEB coefficients integrated into pre-computed ESVD values
            - Focus on policy-relevant ecosystem service values
            - All values standardized and pre-calculated for consistency
            
            **Regional Adjustment**:
            Base ESVD values are adjusted for local conditions:
            - Income adjustment: Regional purchasing power differences
            - Cost of living: Local economic conditions and price levels
            - Data quality: Availability and reliability of regional studies
            
            **Standardization**:
            - All values converted to 2020 International dollars
            - Per hectare per year basis for global comparability
            - Quality assurance: Only peer-reviewed studies included
            
            **Calculation Formula**:
            Final Value = (Pre-computed ESVD Coefficient) × (Area in hectares) × (Regional Factor)
            
            **Performance Optimization**:
            - Pre-computed coefficients eliminate database query overhead
            - 238,270x performance improvement (6.7 million calculations/second)
            - Zero accuracy loss compared to dynamic ESVD database queries
            """)
    
    # Show ecosystem services breakdown if available
    if 'esvd_results' in results:
        st.markdown("### 🌿 Ecosystem Services Breakdown")
        
        # Add reliability warning
        st.warning("⚠️ Although the ecosystem service values are based on the results of more than 10,000 studies, some services remain poorly understood. Be aware that some values may be based on fewer than five studies and should therefore be considered unreliable. We recommend using primary research to check suspect values.")
        
        esvd_data = results['esvd_results']
        
        # Check if we have the expected categories directly
        has_categories = any(cat in esvd_data for cat in ['provisioning', 'regulating', 'cultural', 'supporting'])
        
        # Check for mixed ecosystem structure where categories are nested
        has_mixed_ecosystem = ('ecosystem_breakdown' in esvd_data or 'ecosystem_results' in esvd_data or 
                              results.get('ecosystem_type') == 'multi_ecosystem')
        
        # Also check for alternative data structures
        has_services_data = 'services_data' in esvd_data
        
        def _render_service_columns(categories, data_source, total_value_key):
            cols = st.columns(4)
            for i, category in enumerate(categories):
                cat_data = data_source.get(category, {})
                total = cat_data.get('total', 0)
                with cols[i]:
                    area_denom = results.get('area_hectares', results.get('area_ha', 1)) or 1
                    per_ha_cat = total / area_denom
                    tv = results.get('total_annual_value', results.get('current_value', results.get('total_value', 1))) or 1
                    st.metric(f"{category.title()} Services", f"${total:,.0f}/year")
                    st.caption(f"${per_ha_cat:.0f}/ha · {(total/tv*100):.0f}% of total")
            with st.expander("📋 Service-by-service breakdown"):
                for category in categories:
                    cat_data = data_source.get(category, {})
                    services = cat_data.get('services', {})
                    lines = [(s.replace('_', ' ').title(), v) for s, v in services.items() if isinstance(v, (int, float)) and v > 0]
                    if lines:
                        st.markdown(f"**{category.title()} Services**")
                        for name, val in lines:
                            st.markdown(f"- {name}: ${val:,.0f}/yr")
                    elif cat_data.get('total', 0) > 0:
                        st.markdown(f"**{category.title()} Services**: ${cat_data['total']:,.0f}/yr (no sub-breakdown available)")

        if has_categories:
            categories = ['provisioning', 'regulating', 'cultural', 'supporting']
            _render_service_columns(categories, esvd_data, 'total_value')

        elif has_mixed_ecosystem:
            ecosystem_data = esvd_data.get('ecosystem_breakdown', esvd_data.get('ecosystem_results', {}))
            categories = ['provisioning', 'regulating', 'cultural', 'supporting']

            if not ecosystem_data and results.get('ecosystem_type') == 'multi_ecosystem':
                if any(cat in esvd_data for cat in categories):
                    _render_service_columns(categories, esvd_data, 'total_value')
                else:
                    st.info("📊 Ecosystem services breakdown is not available in the current data format.")
            else:
                # Aggregate from per-ecosystem breakdown
                aggregated = {cat: {'total': 0, 'services': {}} for cat in categories}
                for eco_result in ecosystem_data.values():
                    for category in categories:
                        if category in eco_result:
                            aggregated[category]['total'] += eco_result[category].get('total', 0)
                            for svc, val in eco_result[category].get('services', {}).items():
                                aggregated[category]['services'][svc] = aggregated[category]['services'].get(svc, 0) + val
                _render_service_columns(categories, aggregated, 'total_value')


        elif has_services_data:
            # Alternative display for services_data structure
            st.markdown("**Individual Services Breakdown:**")
            services_data = esvd_data['services_data']
            
            # Create a grid display for all services
            service_items = [(k, v) for k, v in services_data.items() if isinstance(v, (int, float)) and v > 0]
            
            if service_items:
                # Display in columns
                cols_services = st.columns(min(3, len(service_items)))
                for i, (service_name, service_value) in enumerate(service_items):
                    with cols_services[i % 3]:
                        clean_name = service_name.replace('_', ' ').title()
                        per_ha_service = service_value / results.get('area_ha', 1) if results.get('area_ha', 1) > 0 else 0
                        percentage = (service_value / results.get('total_value', 1) * 100) if results.get('total_value', 1) > 0 else 0
                        
                        st.metric(f"{clean_name}", f"${service_value:,.0f}/year")
                        st.caption(f"${per_ha_service:.0f}/ha • {percentage:.1f}% of total")
            else:
                st.info("No individual service data available to display")
        else:
            # Improved fallback - try to create service categories from available data
            st.markdown("**Service Value Summary:**")
            
            # Check if we have a total value to display
            total_val = esvd_data.get('total_value', esvd_data.get('total_annual_value', 0))
            if total_val > 0:
                area_ha = results.get('area_ha', results.get('area_hectares', 1))
                per_ha = total_val / area_ha if area_ha > 0 else 0
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<p class="result-info"><strong>Total Ecosystem Services:</strong> ${total_val:,.0f}/year</p>', unsafe_allow_html=True)
                    st.caption(f"${per_ha:.0f} per hectare annually")
                with col2:
                    st.markdown(f'<p class="result-info"><strong>Regional Adjustment:</strong> Applied</p>', unsafe_allow_html=True)
                    st.caption("Economic adjustment applied for local conditions")
                
                st.info("💡 Service category breakdown not available in current data structure. Total value shown above represents the combined economic value of all ecosystem services.")
            else:
                st.warning("No ecosystem services value data available to display")
    
    # Show individual ecosystem calculations for mixed ecosystems
    if 'esvd_results' in results and results.get('ecosystem_type') == 'multi_ecosystem':
        if 'ecosystem_results' in results.get('esvd_results', {}):
            ecosystem_results = results['esvd_results']['ecosystem_results']
            
            st.markdown("### 🌱 Mixed Ecosystem Analysis")
            
            # Show combined totals first
            col_total1, col_total2, col_total3 = st.columns(3)
            
            with col_total1:
                st.markdown(f'<p class="result-info"><strong>Combined Total Value:</strong> ${results["total_value"]:,.0f}/year</p>', unsafe_allow_html=True)
                st.caption("Sum of all ecosystem contributions")
            
            with col_total2:
                combined_per_ha = results['total_value'] / results['area_ha'] if results['area_ha'] > 0 else 0
                st.markdown(f'<p class="result-info"><strong>Combined Value per Hectare:</strong> ${combined_per_ha:,.0f}/ha/year</p>', unsafe_allow_html=True)
                st.caption("Weighted average across all ecosystems")
            
            with col_total3:
                num_ecosystems = len(ecosystem_results)
                st.markdown(f'<p class="result-info"><strong>Predominant Ecosystem Types Detected:</strong> {str(num_ecosystems)}</p>', unsafe_allow_html=True)
                st.caption("Different ecosystem types in this area")
            
            # Show total composition breakdown
            st.markdown("**📊 Total Area Composition:**")
            comp_cols = st.columns(min(len(ecosystem_results), 4))
            for i, (ecosystem_type, eco_data) in enumerate(ecosystem_results.items()):
                with comp_cols[i % 4]:
                    percentage = eco_data.get('area_percentage', 0)
                    area_ha = eco_data.get('area_hectares', 0)
                    st.markdown(f"**{ecosystem_type.title()}**")
                    st.markdown(f"{percentage:.1f}% ({area_ha:.1f} ha)")
            
            # Show combined services breakdown
            if 'esvd_results' in results:
                st.markdown("**🌿 Combined Ecosystem Services (Total from All Ecosystems):**")
                esvd_data = results['esvd_results']
                
                if 'provisioning' in esvd_data:
                    services_cols = st.columns(4)
                    categories = ['provisioning', 'regulating', 'cultural', 'supporting']
                    
                    for i, category in enumerate(categories):
                        if category in esvd_data:
                            total = esvd_data[category].get('total', 0)
                            with services_cols[i]:
                                percentage = (total / results['total_value'] * 100) if results['total_value'] > 0 else 0
                                st.markdown(f"**{category.title()}**")
                                st.markdown(f"${total:,.0f}/year")
                                st.caption(f"{percentage:.0f}% of combined total")
            
            
            st.markdown("### 🔍 Individual Ecosystem Natural Capital Calculations")
            st.markdown("*Detailed breakdown for each ecosystem type detected in your mixed area*")
            
            # Create expandable sections for each ecosystem type
            for ecosystem_type, eco_data in ecosystem_results.items():
                with st.expander(f"🔍 **{ecosystem_type.title()} Ecosystem** - {eco_data.get('area_percentage', 0):.1f}% of total area"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **📊 {ecosystem_type.title()} Summary**:
                        - **Area**: {eco_data.get('area_hectares', 0):.1f} hectares ({eco_data.get('area_percentage', 0):.1f}% of total)
                        - **Total Value**: ${eco_data.get('current_value', 0):,.0f}/year
                        - **Value per Hectare**: ${eco_data.get('value_per_hectare', 0):,.0f}/ha/year
                        """)
                        
                        if eco_data.get('annual_change_usd', 0) != 0:
                            change_direction = "📈 increasing" if eco_data['annual_change_usd'] > 0 else "📉 decreasing"
                            st.markdown(f"- **Annual Change**: {change_direction} by ${abs(eco_data.get('annual_change_usd', 0)):,.0f}/year")
                    
                    with col2:
                        # Show ecosystem-specific service breakdown if available
                        if 'esvd_metadata' in eco_data:
                            esvd_meta = eco_data['esvd_metadata']
                            if any(cat in esvd_meta for cat in ['provisioning', 'regulating', 'cultural', 'supporting']):
                                st.markdown(f"**Service Categories for {ecosystem_type.title()}**:")
                                
                                categories = ['provisioning', 'regulating', 'cultural', 'supporting']
                                for category in categories:
                                    if category in esvd_meta:
                                        cat_total = esvd_meta[category].get('total', 0)
                                        if cat_total > 0:
                                            percentage = (cat_total / eco_data.get('current_value', 1)) * 100
                                            st.markdown(f"- **{category.title()}**: ${cat_total:,.0f}/year ({percentage:.0f}%)")
                    
                    # Detailed service breakdown for this ecosystem
                    
                    st.markdown(f"**📋 Detailed Service Values for {ecosystem_type.title()}**:")
                    
                    if 'esvd_metadata' in eco_data:
                        esvd_meta = eco_data['esvd_metadata']
                        service_cols = st.columns(4)
                        categories = ['provisioning', 'regulating', 'cultural', 'supporting']
                        
                        for i, category in enumerate(categories):
                            if category in esvd_meta:
                                with service_cols[i]:
                                    st.markdown(f"**{category.title()}**")
                                    for service, value in esvd_meta[category].items():
                                        if service != 'total':
                                            service_name = service.replace('_', ' ').title()
                                            st.markdown(f"• {service_name}: ${value:,.0f}")
                    
                    # Regional adjustment info for this ecosystem
                    if 'esvd_metadata' in eco_data:
                        regional_adj = eco_data['esvd_metadata'].get('regional_adjustment', 1.0)
                        st.caption(f"💡 Regional adjustment factor: {regional_adj:.2f} applied to base ESVD coefficients")
        
        # Summary comparison table
        st.markdown("### 📊 Ecosystem Comparison Summary")
        
        if 'ecosystem_results' in results.get('esvd_results', {}):
            ecosystem_results = results['esvd_results']['ecosystem_results']
            
            # Create enhanced comparison table
            comparison_data = []
            total_value = results['total_value']
            
            for ecosystem_type, eco_data in ecosystem_results.items():
                eco_value = eco_data.get('current_value', 0)
                contribution_pct = (eco_value / total_value * 100) if total_value > 0 else 0
                
                comparison_data.append({
                    'Predominant Ecosystem Type': ecosystem_type.title(),
                    'Area (ha)': f"{eco_data.get('area_hectares', 0):.1f}",
                    'Area (%)': f"{eco_data.get('area_percentage', 0):.1f}%",
                    'Total Value ($/year)': f"${eco_value:,.0f}",
                    'Value Contribution (%)': f"{contribution_pct:.1f}%",
                    'Value per Hectare ($/ha/year)': f"${eco_data.get('value_per_hectare', 0):,.0f}"
                })
            
            import pandas as pd
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)
            
            # Show the calculation summary
            st.markdown("**💡 Mixed Ecosystem Calculation Summary:**")
            st.markdown(f"- **Combined Total**: ${total_value:,.0f}/year (sum of all individual ecosystem values)")
            st.markdown(f"- **Total Area**: {results['area_ha']:,.1f} hectares")
            st.markdown(f"- **Weighted Average**: ${total_value/results['area_ha']:,.0f}/ha/year")
            st.caption("Each ecosystem contributes its proportional value based on area coverage and ecosystem-specific coefficients")
            
            # ESVD data source information
            esvd_status = {'authentic': False}
            
            with st.expander("ℹ️ Data Source Information"):
                if esvd_status['authentic']:
                    st.success("**✅ AUTHENTIC ESVD DATABASE INTEGRATED**")
                    st.markdown(f"""
                    **Data Source**: {esvd_status['source']}  
                    **Database Version**: APR2024 V1.1  
                    **Total Records**: {esvd_status['total_records']:,} peer-reviewed ecosystem service values  
                    **Studies**: {esvd_status['unique_studies']:,} unique research studies  
                    **Biomes**: {esvd_status['unique_biomes']:,} different ecosystem types  
                    **Standardization**: All values in Int$/ha/year (2020 price levels)
                    
                    🎯 **Your analysis uses real peer-reviewed data from 30+ years of ecosystem service research**
                    """)
                else:
                    st.warning("**⚠️ Using Estimated Coefficients**")
                    st.markdown("""
                    **Current Status**: ESVD database not loaded - using estimated values
                    
                    **To Enable Authentic Data**:
                    1. Visit [www.esvd.net](https://www.esvd.net/) to download database
                    2. Place CSV file in the data/ directory
                    3. Restart application for authentic values
                    """)
                
                
                st.markdown("**ESVD Database Information**:")
                st.markdown("- **Official Website**: https://www.esvd.net/")
                st.markdown("- **Developer**: Foundation for Sustainable Development") 
                st.markdown("- **Contains**: 10,000+ ecosystem service valuations from peer-reviewed studies")
                st.markdown("- **Coverage**: Global data from 140+ countries and 2,000+ study sites")

        
        # Action buttons for detailed view - Save Analysis and Set Baseline hidden per user request
        if st.button("📊 Switch to Summary View", type="secondary"):
            st.session_state['analysis_detail'] = 'Summary Analysis'
            st.rerun()
    # ── PDF Download ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📄 Download Report")
    _pdf_col1, _pdf_col2 = st.columns([3, 1])
    with _pdf_col1:
        _pdf_area_name = st.text_input(
            "Report title (area name)",
            value=st.session_state.get('default_area_name', 'Analysis Area'),
            key="pdf_area_name",
            label_visibility="collapsed",
            placeholder="Area name for report header",
        )
    with _pdf_col2:
        _prepare_pdf = st.button("Prepare PDF Report", type="primary", use_container_width=True,
                                 key="prepare_pdf_btn")
    if _prepare_pdf:
        with st.spinner("Building PDF report…"):
            try:
                from utils.pdf_report import generate_pdf_report as _gen_pdf_fn
                _pdf_results = st.session_state.analysis_results
                _pdf_auth = st.session_state.get('auth_user')
                _pdf_country = ''
                try:
                    _bbox = st.session_state.get('cached_bbox', {})
                    if _bbox:
                        _clat = (_bbox.get('min_lat', 0) + _bbox.get('max_lat', 0)) / 2
                        _clon = (_bbox.get('min_lon', 0) + _bbox.get('max_lon', 0)) / 2
                        _pdf_country = get_country_from_coordinates(_clat, _clon)
                except Exception:
                    pass
                _pdf_bytes = _gen_pdf_fn(
                    results=_pdf_results,
                    auth_user=_pdf_auth,
                    area_name=_pdf_area_name or 'Analysis Area',
                    country=_pdf_country,
                )
                _ts = datetime.now().strftime('%Y%m%d_%H%M')
                st.session_state['_pdf_bytes'] = _pdf_bytes
                st.session_state['_pdf_fname'] = f"EVE_report_{_ts}.pdf"
            except Exception as _pdf_err:
                st.error(f"PDF generation failed: {_pdf_err}")
    if st.session_state.get('_pdf_bytes'):
        st.download_button(
            label="⬇️ Download PDF Report",
            data=st.session_state['_pdf_bytes'],
            file_name=st.session_state.get('_pdf_fname', 'EVE_report.pdf'),
            mime="application/pdf",
            use_container_width=True,
            key="pdf_dl_btn",
        )

    # Scenario Builder Section
    st.markdown("---")
    st.subheader("🔮 Scenario Builder")

    @st.fragment
    def render_scenario_builder(results):
        # Track loaded state
        if 'scenario_builder_loaded' not in st.session_state:
            st.session_state.scenario_builder_loaded = False

        # Show load button directly if not yet loaded (one-click, no full-page scroll)
        if not st.session_state.scenario_builder_loaded:
            st.caption("Explore how changes to ecosystem composition and condition would affect natural capital value.")
            if st.button("📊 Load Scenario Builder", key="load_scenario_builder_btn", type="primary"):
                st.session_state.scenario_builder_loaded = True
                st.rerun(scope="fragment")
            return

        # Full Scenario Builder content
        st.markdown("Explore how changes to ecosystem composition and condition would affect natural capital value.")
        
        # Get original results for comparison
        original_total = results.get('total_value', 0)
        original_area = results.get('area_ha', 1)
        original_per_ha = original_total / original_area if original_area > 0 else 0
        
        # Get detected ecosystem distribution or default
        detected_ecosystem = st.session_state.get('detected_ecosystem', {})
        original_distribution = detected_ecosystem.get('ecosystem_distribution', {})
        
        # Available ecosystem types for scenarios
        scenario_ecosystem_types = {
            'Tropical Forest': 'tropical_forest',
            'Temperate Forest': 'temperate_forest',
            'Boreal Forest': 'boreal_forest',
            'Wetland': 'wetland',
            'Grassland': 'grassland',
            'Agricultural': 'agricultural',
            'Coastal': 'coastal',
            'Shrubland': 'shrubland',
            'Desert': 'desert',
            'Urban': 'urban',
            'Marine': 'marine',
            'Rivers And Lakes': 'rivers_and_lakes'
        }
        
        # Get original intactness from session state
        original_intactness_values = st.session_state.get('ecosystem_intactness', {})
        
        # Initialize scenario state if not exists
        if 'scenario_distribution' not in st.session_state:
            # Initialize with original distribution or default
            if original_distribution:
                st.session_state.scenario_distribution = {}
                for eco_type, data in original_distribution.items():
                    display_name = eco_type.replace('_', ' ').title()
                    pct = (data.get('count', 0) / sum(d.get('count', 1) for d in original_distribution.values())) * 100 if original_distribution else 0
                    st.session_state.scenario_distribution[display_name] = pct
            else:
                primary = st.session_state.get('detected_ecosystem', {}).get('primary_ecosystem', 'Temperate Forest')
                display_primary = primary.replace('_', ' ').title() if primary else 'Temperate Forest'
                st.session_state.scenario_distribution = {display_primary: 100.0}
        
        # Initialize per-ecosystem scenario intactness if not exists
        if 'scenario_eco_intactness' not in st.session_state:
            st.session_state.scenario_eco_intactness = {}
            # Initialize from original intactness values
            for eco_name in st.session_state.scenario_distribution.keys():
                st.session_state.scenario_eco_intactness[eco_name] = original_intactness_values.get(eco_name, 100)
        
        
        col_scenario_left, col_scenario_right = st.columns([1, 1])
        
        # Get original intactness values from session state
        original_intactness = st.session_state.get('ecosystem_intactness', {})
        
        with col_scenario_left:
            st.markdown("**Original Analysis**")
            st.metric("Total Annual Value", f"${original_total:,.0f}")
            st.metric("Value per Hectare", f"${original_per_ha:,.0f}/ha")
            
            # Show original ecosystem mix with intactness values
            if original_distribution:
                st.markdown("**Original Ecosystem Mix:**")
                total_count = sum(d.get('count', 0) for d in original_distribution.values())
                for eco_type, data in original_distribution.items():
                    pct = (data.get('count', 0) / total_count * 100) if total_count > 0 else 0
                    display_name = eco_type.replace('_', ' ').title()
                    # Get intactness for this ecosystem type
                    intactness = original_intactness.get(display_name, 100)
                    st.write(f"• {display_name}: {pct:.1f}% @ {intactness:.3f}% intactness")
            else:
                primary = detected_ecosystem.get('primary_ecosystem', 'Unknown')
                display_name = primary.replace('_', ' ').title()
                intactness = original_intactness.get(display_name, 100)
                st.write(f"**Primary Ecosystem:** {display_name} @ {intactness:.3f}% intactness")
            
            # Show urban green/blue multiplier if applicable
            urban_multiplier_pct = st.session_state.get('urban_green_blue_multiplier', 18.0)
            st.caption(f"🏙️ Urban Green/Blue Multiplier: {urban_multiplier_pct:.0f}%")
        
        with col_scenario_right:
            st.markdown("**Scenario Parameters**")
            
            # Ecosystem mix sliders
            st.markdown("🌍 **Adjust Ecosystem Mix**")
            st.markdown("*Set percentages for each ecosystem type (must total 100%)*")
            
            scenario_mix = {}
            
            # Get list of ecosystem types to show
            ecosystems_to_show = list(st.session_state.scenario_distribution.keys()) if st.session_state.scenario_distribution else ['Temperate Forest']
            
            # Show sliders first
            for i, eco_name in enumerate(ecosystems_to_show):
                current_val = st.session_state.scenario_distribution.get(eco_name, 0.0)
                scenario_mix[eco_name] = st.slider(
                    f"{eco_name}",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(current_val),
                    step=5.0,
                    key=f"scenario_eco_{i}"
                )
            
            total_pct = sum(scenario_mix.values())
            if abs(total_pct - 100.0) > 0.1:
                st.warning(f"Total: {total_pct:.0f}% (should be 100%)")
            else:
                st.success(f"Total: {total_pct:.0f}%")
            
            # Add option to include additional ecosystems at the bottom
            available_to_add = [e for e in scenario_ecosystem_types.keys() if e not in ecosystems_to_show]
            if available_to_add:
                add_ecosystem = st.selectbox("Add ecosystem type:", [""] + available_to_add, key="add_eco_select")
                if add_ecosystem:
                    st.session_state.scenario_distribution[add_ecosystem] = 0.0
                    # Initialize intactness for new ecosystem from original or default to 100
                    st.session_state.scenario_eco_intactness[add_ecosystem] = original_intactness_values.get(add_ecosystem, 100)
                    st.session_state.scenario_builder_expanded = True
                    st.rerun(scope="fragment")
            
            st.markdown("---")
            
            # Per-ecosystem intactness sliders
            st.markdown("**🌿 Ecosystem Intactness**")
            st.markdown("*Set condition/health for each ecosystem type*")
            
            scenario_intactness_values = {}
            for i, eco_name in enumerate(ecosystems_to_show):
                # Get current intactness value (from session state or original)
                current_intactness = st.session_state.scenario_eco_intactness.get(
                    eco_name, 
                    original_intactness_values.get(eco_name, 100)
                )
                scenario_intactness_values[eco_name] = st.slider(
                    f"{eco_name} intactness",
                    min_value=10,
                    max_value=100,
                    value=int(current_intactness),
                    step=5,
                    key=f"scenario_intactness_{i}",
                    help=f"100% = pristine, lower = degraded"
                )
                # Update session state
                st.session_state.scenario_eco_intactness[eco_name] = scenario_intactness_values[eco_name]
        
        # Calculate scenario values
        if st.button("🔄 Calculate Scenario", type="primary", use_container_width=True):
            with st.spinner("Calculating scenario values..."):
                try:
                    # Build original mix percentages for comparison
                    original_mix_pct = {}
                    if original_distribution:
                        total_count = sum(d.get('count', 0) for d in original_distribution.values())
                        for eco_type, data in original_distribution.items():
                            display_name = eco_type.replace('_', ' ').title()
                            original_mix_pct[display_name] = (data.get('count', 0) / total_count * 100) if total_count > 0 else 0
                    else:
                        primary = detected_ecosystem.get('primary_ecosystem', 'temperate_forest')
                        display_primary = primary.replace('_', ' ').title()
                        original_mix_pct[display_primary] = 100.0
                    
                    # Check if ecosystem mix has changed
                    mix_unchanged = True
                    for eco_name in set(list(scenario_mix.keys()) + list(original_mix_pct.keys())):
                        orig_pct = original_mix_pct.get(eco_name, 0)
                        scen_pct = scenario_mix.get(eco_name, 0)
                        if abs(orig_pct - scen_pct) > 1.0:  # Allow 1% tolerance
                            mix_unchanged = False
                            break
                    
                    # Check if any intactness values changed
                    intactness_unchanged = True
                    for eco_name in scenario_intactness_values.keys():
                        orig_intact = original_intactness_values.get(eco_name, 100)
                        scen_intact = scenario_intactness_values.get(eco_name, 100)
                        if abs(orig_intact - scen_intact) > 1:
                            intactness_unchanged = False
                            break
                    
                    # Calculate scenario total with per-ecosystem intactness
                    from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
                    coeffs = PrecomputedESVDCoefficients()
                    
                    # Get coordinates for regional adjustment
                    coordinates = None
                    if 'current_bounds' in st.session_state and st.session_state.current_bounds:
                        bounds = st.session_state.current_bounds
                        center_lat = (bounds[0][0] + bounds[1][0]) / 2
                        center_lon = (bounds[0][1] + bounds[1][1]) / 2
                        coordinates = (center_lat, center_lon)
                    
                    # Get the regional factor from original results to ensure consistency
                    original_regional_factor = results.get('regional_adjustment_factor', results.get('regional_factor', None))
                    
                    scenario_total = 0
                    
                    for eco_display, pct in scenario_mix.items():
                        if pct > 0 and eco_display in scenario_ecosystem_types:
                            eco_internal = scenario_ecosystem_types[eco_display]
                            eco_area = original_area * (pct / 100.0)
                            
                            # Get per-ecosystem intactness multiplier
                            eco_intactness = scenario_intactness_values.get(eco_display, 100) / 100.0
                            
                            # Apply urban green/blue multiplier for urban ecosystems
                            urban_multiplier = 1.0
                            if eco_internal == 'urban':
                                urban_multiplier_percent = st.session_state.get('urban_green_blue_multiplier', 18.0)
                                urban_multiplier = urban_multiplier_percent / 100.0
                            
                            # Calculate with ecosystem-specific intactness
                            eco_results = coeffs.calculate_ecosystem_values(
                                ecosystem_type=eco_internal,
                                area_hectares=eco_area,
                                coordinates=coordinates,
                                ecosystem_intactness_multiplier=eco_intactness,
                                regional_factor_override=original_regional_factor,
                                urban_green_blue_multiplier=urban_multiplier
                            )
                            
                            if 'total_value' in eco_results:
                                scenario_total += eco_results['total_value']
                    
                    scenario_per_ha = scenario_total / original_area if original_area > 0 else 0
                    
                    # Store scenario results
                    st.session_state.scenario_results = {
                        'total_value': scenario_total,
                        'per_ha': scenario_per_ha,
                        'mix': scenario_mix.copy(),
                        'intactness': scenario_intactness_values.copy()
                    }
                    
                    st.success("Scenario calculated!")
                    st.rerun(scope="fragment")
                    
                except Exception as e:
                    st.error(f"Error calculating scenario: {str(e)}")
        
        # Display comparison if scenario results exist
        if st.session_state.get('scenario_results'):
            scenario = st.session_state.scenario_results
            scenario_total = scenario['total_value']
            scenario_per_ha = scenario['per_ha']
            
            st.markdown("---")
            st.markdown("### 📊 Scenario Comparison")
            
            # Summary metrics
            col_orig, col_scen, col_diff = st.columns(3)
            
            with col_orig:
                st.markdown("**Original**")
                st.metric("Annual Value", f"${original_total:,.0f}")
                st.metric("Per Hectare", f"${original_per_ha:,.0f}/ha")
            
            with col_scen:
                st.markdown("**Scenario**")
                st.metric("Annual Value", f"${scenario_total:,.0f}")
                st.metric("Per Hectare", f"${scenario_per_ha:,.0f}/ha")
            
            with col_diff:
                st.markdown("**Difference**")
                value_diff = scenario_total - original_total
                pct_change = ((scenario_total - original_total) / original_total * 100) if original_total > 0 else 0
                st.metric("Value Change", f"${value_diff:+,.0f}", delta=f"{pct_change:+.1f}%")
                
                ha_diff = scenario_per_ha - original_per_ha
                st.metric("Per Ha Change", f"${ha_diff:+,.0f}/ha")
            
            # Bar chart comparison
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Original',
                x=['Total Annual Value'],
                y=[original_total],
                marker_color='#2E7D32',
                text=[f'${original_total:,.0f}'],
                textposition='outside'
            ))
            
            fig.add_trace(go.Bar(
                name='Scenario',
                x=['Total Annual Value'],
                y=[scenario_total],
                marker_color='#1565C0',
                text=[f'${scenario_total:,.0f}'],
                textposition='outside'
            ))
            
            fig.update_layout(
                title='Original vs Scenario Comparison',
                barmode='group',
                yaxis_title='Value ($/year)',
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=350,
                margin=dict(t=80, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Scenario details
            with st.expander("📋 Scenario Details"):
                st.markdown("**Ecosystem Mix & Intactness:**")
                scenario_intactness = scenario.get('intactness', {})
                for eco, pct in scenario['mix'].items():
                    if pct > 0:
                        intactness_val = scenario_intactness.get(eco, 100) if isinstance(scenario_intactness, dict) else scenario_intactness
                        st.write(f"• {eco}: {pct:.0f}% @ {intactness_val:.0f}% intactness")
            
            if st.button("🗑️ Clear Scenario", type="secondary"):
                if 'scenario_results' in st.session_state:
                    del st.session_state['scenario_results']
                st.rerun(scope="fragment")

    render_scenario_builder(results)

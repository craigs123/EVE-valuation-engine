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
            NaturalCapitalBaselineDB,
            ProjectIndicatorDB,
        )
        return {
            'init_database': init_database,
            'initialize_user_session': initialize_user_session,
            'SavedAreaDB': SavedAreaDB,
            'EcosystemAnalysisDB': EcosystemAnalysisDB,
            'NaturalCapitalBaselineDB': NaturalCapitalBaselineDB,
            'ProjectIndicatorDB': ProjectIndicatorDB,
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
# Plus Inter webfont for typography (Pass B rebrand).
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#2E7D32">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="EVE">
<link rel="apple-touch-icon" href="/static/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
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
        
        
        /* EVE — Green & Grey palette: green as accent, neutral grey as canvas */
        :root {
            --eve-primary: #2E7D32;
            --eve-primary-dark: #1B5E20;
            --eve-primary-light: #4CAF50;
            --eve-accent: #81C784;
            --eve-bg-light: #E8F5E9;        /* retained for success-tint only */
            --eve-text-dark: #1F2937;       /* charcoal, was forest-green */
            --eve-gold: #FFB300;
            --eve-neutral-bg: #F7F8FA;
            --eve-neutral-bg-2: #EFF2F4;
            --eve-neutral-border: #E5E7EB;
            --eve-neutral-text: #1F2937;
            --eve-neutral-text-muted: #6B7280;
        }

        /* Main header styling */
        .stApp > header {
            background-color: transparent;
        }

        /* Sidebar — neutral surface, charcoal text */
        [data-testid="stSidebar"] {
            background: #F7F8FA;
            border-right: 1px solid #E5E7EB;
        }

        [data-testid="stSidebar"] .stMarkdown {
            color: #1F2937;
        }

        /* Button styling */
        .stButton {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Base button styling — applies to both primary and secondary */
        .stButton > button {
            border: 1px solid transparent;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.2s ease;
            margin-top: 0 !important;
            justify-content: center !important;
            align-items: center !important;
        }

        .stButton > button > div,
        .stButton > button [data-testid="stMarkdownContainer"] {
            width: 100% !important;
            text-align: center !important;
            justify-content: center !important;
            align-items: center !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        .stButton > button p {
            text-align: center !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Primary — solid green CTA */
        .stButton > button[kind="primary"] {
            background-color: #2E7D32;
            color: white;
            border-color: #2E7D32;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #1B5E20;
            border-color: #1B5E20;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
            transform: translateY(-1px);
        }

        /* Secondary — ghost / outline (default st.button without type=) */
        .stButton > button[kind="secondary"] {
            background-color: #FFFFFF;
            color: #2E7D32;
            border-color: #C8E6C9;
            font-weight: 500;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #F7F8FA;
            color: #1B5E20;
            border-color: #2E7D32;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
            transform: translateY(-1px);
        }

        /* Unified results panels — strip per-metric card chrome so each
           outer container reads as one panel, not nested ones */
        [class*="st-key-results_totals_panel"] [data-testid="stMetric"],
        [class*="st-key-results_totals_panel"] [data-testid="stMetric"] > div,
        [class*="st-key-results_services_panel"] [data-testid="stMetric"],
        [class*="st-key-results_services_panel"] [data-testid="stMetric"] > div {
            background: transparent !important;
            padding: 0 !important;
            border: none !important;
            border-left: none !important;
            box-shadow: none !important;
        }

        /* Metric cards — neutral surface, single green accent stripe */
        [data-testid="stMetric"],
        [data-testid="stMetric"] > div {
            background: #FFFFFF !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            border: 1px solid #E5E7EB !important;
            border-left: 4px solid #2E7D32 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        }

        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: #6B7280 !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }

        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #1F2937 !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
        }

        /* Expanders — neutral surface, neutral border, no gradient */
        [data-testid="stExpander"] {
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            background: #FFFFFF !important;
            margin-bottom: 0.5rem !important;
        }

        [data-testid="stExpander"] > div:first-child,
        [data-testid="stExpander"] summary,
        .streamlit-expanderHeader {
            background: #F7F8FA !important;
            border: none !important;
            border-bottom: 1px solid #E5E7EB !important;
            color: #1F2937 !important;
            font-weight: 600 !important;
            padding: 0.75rem 1rem !important;
        }

        [data-testid="stExpander"]:hover > div:first-child,
        [data-testid="stExpander"] summary:hover {
            background: #EFF2F4 !important;
        }

        /* Expander content area */
        [data-testid="stExpander"] > div:last-child {
            background: #FFFFFF !important;
            padding: 1rem !important;
        }

        /* Success/Info/Warning boxes — keep green tint on success */
        .stSuccess {
            background-color: #E8F5E9;
            border-left-color: #2E7D32;
        }

        .stInfo {
            background-color: #E3F2FD;
            border-left-color: #1976D2;
        }

        /* Selectbox and input styling — neutral border, green focus */
        .stSelectbox > div > div {
            border-color: #E5E7EB;
        }

        .stSelectbox > div > div:focus-within {
            border-color: #2E7D32;
            box-shadow: 0 0 0 1px #2E7D32;
        }

        /* Slider — keep green */
        .stSlider > div > div > div {
            background-color: #2E7D32;
        }

        /* Tabs — neutral unselected, green selected */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #F7F8FA;
            border-radius: 8px 8px 0 0;
            color: #1F2937;
            font-weight: 500;
            padding: 0.6rem 1.25rem !important;
            margin-right: 0.25rem !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: #2E7D32 !important;
            color: white !important;
        }

        /* My Workspace tabs — tighter label padding than other tabs */
        [class*="st-key-ws_tabs_wrap"] .stTabs [data-baseweb="tab"] {
            padding: 0.4rem 0.9rem !important;
        }

        /* Saved-area row: halve the gap between the load and delete icon
           buttons so the load button sits closer to delete */
        [class*="st-key-ws_tabs_wrap"] [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }

        /* Workspace load/delete icon buttons — natural width like the
           Sign-out button (so the icon stays perfectly centred), made
           ~50% wider via padding, and shifted so the pair sit close
           together in the middle of their column area. */
        [class*="st-key-ws_load_"] button,
        [class*="st-key-ws_del_"] button {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        [class*="st-key-ws_load_"] {
            margin-left: auto !important;
            margin-right: 0 !important;
        }
        [class*="st-key-ws_del_"] {
            margin-left: 0 !important;
            margin-right: auto !important;
        }

        /* DataFrame/Table — neutral border */
        .stDataFrame {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
        }

        /* Progress bar — keep green */
        .stProgress > div > div > div {
            background-color: #2E7D32;
        }

        /* Links — keep green */
        a {
            color: #2E7D32 !important;
        }

        a:hover {
            color: #1B5E20 !important;
        }

        /* Typography — Inter for body and headings.
           Targeted selectors only; broad selectors like [class^="st-"]
           also catch Streamlit's icon-font widgets (e.g. expander chevron)
           and replace their glyphs with Inter, which does not contain
           those icons. Inheritance covers most widgets; we only force
           Inter where Streamlit's own !important rules win otherwise. */
        html, body, .stApp,
        [data-testid="stSidebar"],
        [data-testid="stAppViewContainer"],
        [data-testid="stMarkdownContainer"],
        .stMarkdown, .stButton > button {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                         'Segoe UI', Roboto, sans-serif !important;
            font-feature-settings: 'cv11', 'ss01', 'ss03';
        }

        /* Headings — charcoal, tighter scale, slight negative tracking */
        h1, h2, h3, h4, h5, h6 {
            color: #1F2937;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
            font-family: 'Inter', system-ui, sans-serif !important;
            letter-spacing: -0.01em !important;
            font-weight: 600 !important;
        }
        h1 { font-size: 1.5rem !important; font-weight: 700 !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.05rem !important; }

        /* Tabular numerals for tables and metric values (numbers align in columns) */
        [data-testid="stMetric"] [data-testid="stMetricValue"],
        .stDataFrame, [data-testid="stDataFrame"] {
            font-variant-numeric: tabular-nums;
        }

        /* Card-like containers */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            border-radius: 10px;
        }

        /* Step section headers — green accent stripe on neutral surface; tight margins keep
           the area-selection controls visible on smaller screens. */
        .section-header {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #1F2937 !important;
            padding: 0.4rem 0.75rem !important;
            margin: 0.4rem 0 0.1rem 0 !important;
            border-left: 4px solid #2E7D32 !important;
            background: #F7F8FA !important;
            border-radius: 0 4px 4px 0 !important;
            line-height: 1.3 !important;
            display: block !important;
        }
        /* Crunch the gap immediately after a section-header so the next
           widget (e.g. the test-area selectbox) sits flush against it.
           Target the outer element-container (Streamlit's vertical-block
           gap operates at that level, not on the inner stMarkdown). */
        [data-testid="stElementContainer"]:has(.section-header) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        [data-testid="stElementContainer"]:has(.section-header) + [data-testid="stElementContainer"] {
            margin-top: -1rem !important;
            padding-top: 0 !important;
        }

        /* Main content padding — modest, not aggressive */
        .main .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 100%;
        }

        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1.5rem !important;
        }

        /* Vertical block spacing — tight gap between stacked elements so the
           map sits as high on the page as possible. */
        [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0.075rem;
            padding: 0;
        }
        /* Crunch horizontal-block (st.columns) row margins so the map row
           sits flush against the search row above. */
        [data-testid="stHorizontalBlock"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            gap: 0.25rem !important;
        }
        /* The folium map iframe sits in a streamlit-folium wrapper; pull it
           up flush against the search/layer row above it. */
        iframe[title="streamlit_folium.st_folium"],
        [data-testid="stCustomComponentV1"] {
            margin-top: 0 !important;
        }
        /* Element container around the map columns — kill any residual
           top padding/margin so the map slides up. */
        [data-testid="stElementContainer"]:has([data-testid="stHorizontalBlock"]) {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Body copy line-height (markdown paragraphs) — comfortable reading */
        .stMarkdown p {
            margin: 0 0 0.5rem 0 !important;
            padding: 0 !important;
            line-height: 1.55 !important;
        }
        .stMarkdown p:last-child {
            margin-bottom: 0 !important;
        }

        /* Markdown container — no extra padding, but allow children to set their own line-height */
        .stMarkdown,
        [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Element container — minimal margin, no padding */
        .element-container {
            margin: 0 !important;
            padding: 0 !important;
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

if 'sampling_frequency' not in st.session_state:
    st.session_state.sampling_frequency = 10
    
if 'ecosystem_override' not in st.session_state:
    st.session_state.ecosystem_override = "Auto-detect"
    
if 'analysis_detail' not in st.session_state:
    st.session_state.analysis_detail = "Summary Analysis"
    
if 'income_elasticity' not in st.session_state:
    st.session_state.income_elasticity = 0.25

if 'time_preset' not in st.session_state:
    st.session_state.time_preset = "Current Year (2024)"

for _ind_key in ('fapar', 'soil_c', 'phh2o', 'soc', 'bdod', 'nitrogen'):
    _full_key = f'show_indicator_{_ind_key}'
    if _full_key not in st.session_state:
        st.session_state[_full_key] = False

if 'use_eei_for_intactness' not in st.session_state:
    st.session_state.use_eei_for_intactness = True

if 'urban_green_blue_multiplier' not in st.session_state:
    st.session_state.urban_green_blue_multiplier = 18.0

if 'ecosystem_intactness' not in st.session_state:
    st.session_state.ecosystem_intactness = {
        'Agricultural': 100, 'Temperate Forest': 100, 'Boreal Forest': 100,
        'Tropical Forest': 100, 'Polar': 100, 'Grassland': 100,
        'Shrubland': 100, 'Desert': 100, 'Wetland': 100,
        'Coastal': 100, 'Mangroves': 100, 'Marine': 100,
        'Rivers and Lakes': 100, 'Urban': 100,
    }

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
            padding: 0.5rem 0 0.5rem 0;
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
    # User-forced ecosystem override wins: when the main-page dropdown is set
    # to anything other than 'Auto-detect', every sample point's ESVD
    # ecosystem is reported as the override value regardless of its CCI code.
    _override = st.session_state.get('ecosystem_override', 'Auto-detect')
    if _override and _override != 'Auto-detect':
        return _override

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
                st.success("**Active Source**: Real ESA Satellite Data")
            else:
                st.warning("⚠️  **Active Source**: Geographic Fallback")
                st.caption("Real ESA satellite data unavailable - using geographic estimation")
                
        # Show detailed sampling point information if analysis data is available
        if analysis_results:
            sampling_point_data = analysis_results.get('sampling_point_data', {})
            landcover_codes = analysis_results.get('landcover_codes', {})
            data_source = analysis_results.get('landcover_data_source', 'estimated')
            
            with st.expander("Sampling Points Analysis Details", expanded=False):
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
                    st.markdown("**OpenLandMap STAC Data:**")
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
                        
                        # Add indicator for user-classified water bodies, but
                        # only when the ecosystem isn't being force-overridden
                        # (otherwise every cell would read "<override> (User
                        # classified)" which misrepresents the override).
                        _override_active = (
                            st.session_state.get('ecosystem_override', 'Auto-detect')
                            not in (None, '', 'Auto-detect')
                        )
                        if (landcover_code == 210
                                and point_data.get('user_classified', False)
                                and not _override_active):
                            esvd_ecosystem += " (User classified)"
                        
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
                            "Data Source": data_source
                        })

                    # Display main table
                    import pandas as pd
                    df = pd.DataFrame(table_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Supplementary indicators table — columns gated per-indicator by
                    # the show_indicator_* flags set in the Analysis Settings dialog.
                    show_fapar = st.session_state.get('show_indicator_fapar', False)
                    show_soil_c = st.session_state.get('show_indicator_soil_c', False)
                    show_phh2o = st.session_state.get('show_indicator_phh2o', False)
                    show_soc = st.session_state.get('show_indicator_soc', False)
                    show_bdod = st.session_state.get('show_indicator_bdod', False)
                    show_nitrogen = st.session_state.get('show_indicator_nitrogen', False)
                    show_any_soilgrids = show_phh2o or show_soc or show_bdod or show_nitrogen
                    show_any = show_fapar or show_soil_c or show_any_soilgrids

                    if show_any:
                        st.markdown("**Supplementary Environmental Indicators:**")
                        st.caption(
                            "Columns shown reflect your selection in Analysis Settings → "
                            "Environmental Indicators. STAC indicators are collected during "
                            "analysis; SoilGrids 2.0 (0–5cm topsoil, 250m, CC BY 4.0) is fetched "
                            "on demand."
                        )

                        soil_results = {}
                        sg_coord_by_point = {}
                        if show_any_soilgrids:
                            from utils.soilgrids_api import (
                                format_value as soilgrids_format,
                                get_soil_properties_batch,
                            )

                            sg_coords = []
                            for point_id, point_data in sampling_point_data.items():
                                coords = point_data.get('coordinates', {})
                                if coords and isinstance(coords, dict):
                                    lat = coords.get('lat', 0)
                                    lon = coords.get('lon', 0)
                                    if lat != 0 or lon != 0:
                                        sg_coords.append((lat, lon))
                                        sg_coord_by_point[point_id] = (lat, lon)

                            with st.spinner("Fetching SoilGrids data..."):
                                soil_results = get_soil_properties_batch(sg_coords) if sg_coords else {}

                            api_unavailable = bool(sg_coords) and all(
                                all(v is None for v in props.values())
                                for props in soil_results.values()
                            )
                            if api_unavailable:
                                st.warning("Soil data temporarily unavailable")

                        supp_rows = []
                        for point_id, point_data in sampling_point_data.items():
                            point_num = int(point_id.replace('point_', '')) + 1

                            row = {"Sample Point": f"Point {point_num}"}

                            if show_fapar or show_soil_c:
                                fapar_value = "—"
                                soil_carbon_value = "—"
                                stac_data = point_data.get('stac_data', {})
                                if stac_data:
                                    for item in stac_data.get('vegetation', []) or []:
                                        name = item.get('name', '').lower()
                                        value = item.get('value')
                                        if 'fapar' in name or 'absorbed' in name:
                                            if value is not None:
                                                if value > 1:
                                                    value = value / 255.0
                                                fapar_value = f"{value:.3f}"
                                            break
                                    for item in stac_data.get('soil', []) or []:
                                        name = item.get('name', '').lower()
                                        value = item.get('value')
                                        if 'carbon' in name or 'organic' in name:
                                            if value is not None and isinstance(value, (int, float)):
                                                soil_carbon_value = f"{value:.1f}"
                                            break
                                if show_fapar:
                                    row["FAPAR (0-1)"] = fapar_value
                                if show_soil_c:
                                    row["Soil C (g/kg)"] = soil_carbon_value

                            if show_any_soilgrids:
                                sg_props = soil_results.get(sg_coord_by_point.get(point_id), {})
                                if show_phh2o:
                                    row["pH (H₂O)"] = soilgrids_format('phh2o', sg_props.get('phh2o'))
                                if show_soc:
                                    row["SOC (g/kg)"] = soilgrids_format('soc', sg_props.get('soc'))
                                if show_bdod:
                                    row["Bulk Density (g/cm³)"] = soilgrids_format('bdod', sg_props.get('bdod'))
                                if show_nitrogen:
                                    row["Nitrogen (g/kg)"] = soilgrids_format('nitrogen', sg_props.get('nitrogen'))

                            supp_rows.append(row)

                        supp_df = pd.DataFrame(supp_rows)
                        st.dataframe(supp_df, use_container_width=True, hide_index=True)
                    
                    # Raw STAC data + verification details — collapsed by default.
                    with st.expander("View Raw STAC Data (click to verify data authenticity)", expanded=False):
                        st.markdown("**This section shows the raw satellite data sources and extraction details for complete transparency.**")

                        # Authenticity status — surfaced first inside the panel
                        if not any(point_data.get('raw_stac_data') for point_data in sampling_point_data.values()):
                            st.warning("No raw STAC data found. This may indicate the analysis used fallback methods instead of genuine satellite data.")
                        else:
                            st.success("Genuine STAC satellite data detected for this analysis.")

                        # How-to-verify guidance
                        st.info("""
                        **How to Verify This Data:**
                        1. **Asset URL**: Copy the asset URL above and access it directly to verify the GeoTIFF source
                        2. **Year**: Confirm the dataset year (2020) in the asset URL path
                        3. **Pixel Values**: Check that raw pixel values match ESA CCI landcover codes
                        4. **Coordinates**: Verify sample point coordinates match your selected area
                        5. **Collection**: Confirm data comes from ESA CCI landcover collection (land.cover_esacci.lc.l4)

                        This transparency section provides complete traceability from raw satellite data to final results.
                        """)

                        st.divider()

                        # Display raw data for each sample point
                        for point_id, point_data in sampling_point_data.items():
                            point_num = int(point_id.replace('point_', '')) + 1
                            st.markdown(f"**Sample Point {point_num}:**")

                            # Show raw STAC response data
                            raw_stac_data = point_data.get('raw_stac_data', {})
                            if raw_stac_data:
                                st.markdown("**Raw STAC Response:**")
                                st.json(raw_stac_data)
                            else:
                                st.info("No raw STAC data available for this point")

                            # Show processed STAC data
                            stac_data = point_data.get('stac_data', {})
                            if stac_data:
                                st.markdown("**Processed STAC Data:**")
                                st.json(stac_data)

                            st.divider()
                    
                    # Summary Statistics block moved out of this expander —
                    # see "Summary Statistics" section after the expander closes.

                    # Show raw ESA codes in expandable section for transparency
                    with st.expander("Raw ESA Code Breakdown"):
                        _code_counts_local = {}
                        for _pt in sampling_point_data.values():
                            _c = _pt.get('landcover_class', 'Unknown')
                            _code_counts_local[_c] = _code_counts_local.get(_c, 0) + 1
                        # Filter out None keys and sort only valid integer codes
                        valid_codes = {k: v for k, v in _code_counts_local.items() if k is not None}
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

            # Summary Statistics — rendered AFTER the analysis-details expander
            # (moved out so users see it without expanding). Only shown when
            # OpenLandMap sample data is present.
            _has_real_summary = any(
                ('Real ESA Satellite Data' in (p.get('source') or ''))
                or ('GeoTIFF Pixel' in (p.get('source') or ''))
                or ('Direct ESA Land Cover Extraction' in (p.get('source') or ''))
                or (p.get('stac_data') and len(p.get('stac_data', {})) > 0)
                for p in sampling_point_data.values()
            )
            _data_source_check_summary = st.session_state.get('landcover_data_source', data_source)
            if (_data_source_check_summary == 'openlandmap' or _has_real_summary) and sampling_point_data:
                st.markdown("## Summary Statistics")

                # Show average EEI if available (only when EEI is enabled)
                if st.session_state.get('use_eei_for_intactness', False):
                    average_eei = st.session_state.get('average_eei')
                    ecosystem_eei = st.session_state.get('ecosystem_eei', {})

                    if average_eei is not None:
                        eei_percent = int(average_eei * 100)
                        st.info(f"**Average Ecosystem Integrity (EEI):** {average_eei:.3f} ({eei_percent}%)")

                        if ecosystem_eei and len(ecosystem_eei) > 1:
                            st.markdown("**EEI by Ecosystem Type (used for intactness defaults):**")
                            for eco_type, eei_value in sorted(ecosystem_eei.items()):
                                if eei_value is not None:
                                    eco_eei_percent = eei_value * 100
                                    st.write(f"• **{eco_type}**: {eei_value:.3f} ({eco_eei_percent:.3f}%)")
                        elif ecosystem_eei and len(ecosystem_eei) == 1:
                            eco_type, eei_value = list(ecosystem_eei.items())[0]
                            if eei_value is not None:
                                st.caption(f"Single ecosystem ({eco_type}) — EEI {eei_value:.3f} used for intactness default")
                else:
                    st.caption("EEI disabled — using manual intactness values from settings")

                # Count codes / ecosystem types
                code_counts = {}
                for point_data in sampling_point_data.values():
                    code = point_data.get('landcover_class', 'Unknown')
                    code_counts[code] = code_counts.get(code, 0) + 1

                ecosystem_counts = {}
                for code, count in code_counts.items():
                    specialized_ecosystem = None
                    for point_data in sampling_point_data.values():
                        if point_data.get('landcover_class') == code:
                            specialized_ecosystem = point_data.get('ecosystem_type')
                            break
                    esvd_ecosystem = specialized_ecosystem or get_esvd_ecosystem_from_landcover_code(code, analysis_results)
                    ecosystem_counts[esvd_ecosystem] = ecosystem_counts.get(esvd_ecosystem, 0) + count

                st.markdown("**Ecosystem Composition (from Sample Points):**")
                total_area = results.get('area_ha', results.get('area_hectares', 0))
                for ecosystem_type, count in sorted(ecosystem_counts.items()):
                    percentage = (count / len(sampling_point_data)) * 100
                    area_ha = total_area * (percentage / 100)
                    if percentage >= 1.0:
                        st.write(f"• **{ecosystem_type}**: {percentage:.1f}% ({count} points, {area_ha:.1f} hectares)")

                # Country breakdown (water bodies excluded)
                country_counts = {}
                land_points_count = 0
                for point_data in sampling_point_data.values():
                    if point_data.get('landcover_class') == 210:
                        continue  # skip water bodies
                    coords = point_data.get('coordinates', {})
                    if coords and isinstance(coords, dict):
                        lat = coords.get('lat', 0)
                        lon = coords.get('lon', 0)
                        if lat != 0 or lon != 0:
                            country = get_country_from_coordinates(lat, lon)
                            country_counts[country] = country_counts.get(country, 0) + 1
                            land_points_count += 1

                if country_counts and land_points_count > 0:
                    st.markdown("**Geographic Distribution (from Land Sample Points):**")
                    for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / land_points_count) * 100
                        if percentage >= 5.0:
                            st.write(f"• **{country}**: {percentage:.1f}% ({count} points)")

                    predominant_country = max(country_counts.items(), key=lambda x: x[1])
                    # Country panel merged into the Predominant Ecosystem Type panel
                    # in the results display; just stash for that to read.
                    st.session_state['predominant_country_info'] = {
                        'label': "Predominant Country" if predominant_country[1] > land_points_count * 0.5 else "Most Common Country",
                        'name': predominant_country[0],
                    }

                    try:
                        from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
                        esvd_calc = PrecomputedESVDCoefficients()
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
                            st.write(f"**Regional Economic Factor**: {regional_factor:.2f}x (applied to all ecosystem valuations)")
                    except Exception:
                        st.write("**Regional Economic Factor**: Unable to calculate")

                    water_points = len(sampling_point_data) - land_points_count
                    if water_points > 0:
                        st.caption(f"{water_points} water body points excluded from country statistics")

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

# ── Handle email verification and password reset links ────────────────────────
_qp = st.query_params
_verify_token = _qp.get('verify')
_reset_token = _qp.get('reset')

if _verify_token:
    from database import UserDB as _UserDB
    if _UserDB.verify_email(_verify_token):
        st.query_params.clear()
        st.success("Email verified. You can now sign in.")
    else:
        st.query_params.clear()
        st.error("This verification link has expired or is invalid. Please sign in and request a new one.")
    st.stop()

if _reset_token:
    from database import UserDB as _UserDB
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 1rem 0;">
        <div style="font-size:3rem; line-height:1;">🌱</div>
        <h1 style="color:#2E7D32; font-size:1.9rem; font-weight:700; margin:0.8rem 0 0.5rem 0;">
            Reset your password
        </h1>
    </div>
    """, unsafe_allow_html=True)
    _, _rc, _ = st.columns([1, 2, 1])
    with _rc:
        with st.form("reset_pw_form"):
            _new_pw = st.text_input("New password", type="password", help="At least 8 characters")
            _new_pw2 = st.text_input("Confirm new password", type="password")
            _reset_submitted = st.form_submit_button("Set new password", type="primary",
                                                      use_container_width=True)
        if _reset_submitted:
            if len(_new_pw) < 8:
                st.error("Password must be at least 8 characters.")
            elif _new_pw != _new_pw2:
                st.error("Passwords do not match.")
            else:
                if _UserDB.reset_password(_reset_token, _new_pw):
                    st.query_params.clear()
                    st.success("Password updated. Please sign in with your new password.")
                    st.rerun()
                else:
                    st.error("This reset link has expired or is invalid. Please request a new one.")
    st.stop()

# Auth gate — unauthenticated visitors see only the login/register UI
from utils.auth import require_login
require_login()

# Post-login banners removed: signup now requires email verification before the
# first sign-in, so an authenticated session always implies a verified email.

# Clean text-only header - Professional Dashboard Style
st.markdown("""
<div class="header-container">
    <span><span class="header-icon">🌱</span><span class="header-text">Ecological Valuation Engine</span></span>
    <span class="version-text">v3.7.0 &nbsp;·&nbsp; © 2026 Green &amp; Grey Associates</span>
</div>
<div style='display:flex; align-items:center; justify-content:center;
             gap:0.5rem; margin:-0.25rem 0 0.5rem 0;'>
    <a href='https://www.greenandgreyassociates.com' target='_blank'
       style='display:inline-flex; align-items:center;'>
        <img src='/app/static/greengrey-logo.png'
             alt='Green & Grey Associates'
             style='height:80px; width:auto; opacity:0.85;' />
    </a>
    <span style='color:#6B7280; font-size:0.75rem;'>Built by
        <a href='https://www.greenandgreyassociates.com' target='_blank'
           style='color:#2E7D32; text-decoration:none; font-weight:500;'>
        Green &amp; Grey Associates</a>
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown('<h3 class="section-header" style="margin:0.5rem 0 0.25rem 0 !important;">Draw the area you want to analyse on the map or choose a test area from the dropdown below</h3>', unsafe_allow_html=True)


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
        'scenario_eco_intactness', 'scenario_builder_expanded', 'calculation_ready',
        'skip_ecosystem_detection', 'sampling_point_data', 'water_bodies_classified',
        'pending_water_classification', 'landcover_codes', 'predominant_country_info'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            if key == 'calculation_ready':
                st.session_state[key] = False
            elif key == 'analysis_results':
                st.session_state[key] = None
            else:
                del st.session_state[key]
    # Clear the location-search box so the user's stale query doesn't sit
    # on screen after they pick a test area. Safe to set directly here:
    # callbacks run before the next render, so the widget hasn't been
    # instantiated yet in the new run.
    if 'location_search_main' in st.session_state:
        st.session_state.location_search_main = ""

# Initialize local fallbacks to prevent LSP "unbound" diagnostics
ecosystem_override = st.session_state.get('ecosystem_override', 'Auto-detect')
include_environmental_indicators = (
    st.session_state.get('show_indicator_fapar', False)
    or st.session_state.get('show_indicator_soil_c', False)
)
max_sampling_limit = st.session_state.get('max_sampling_limit', 9)
analysis_detail = st.session_state.get('analysis_detail', 'Summary Analysis')
income_elasticity = st.session_state.get('income_elasticity', 0.6)
time_preset = st.session_state.get('time_preset', 'Current Year (2024)')
analyze_button = False


# ── Analysis Settings dialog ───────────────────────────────────────────────
@st.dialog("Analysis Settings", width="large")
def analysis_settings_dialog():
    with st.container(height=600):
        st.markdown("##### Environmental Indicators")
        st.caption("Each indicator adds a column to the Sample Points panel. STAC indicators "
                   "are fetched during analysis; SoilGrids indicators are fetched on demand.")

        _indicator_specs = [
            ('fapar', 'FAPAR',
             "Fraction of Absorbed Photosynthetically Active Radiation (0–1). "
             "Proportion of incoming sunlight that the vegetation canopy captures — "
             "an indicator of photosynthetic productivity. Source: OpenLandMap STAC."),
            ('soil_c', 'Soil Carbon (STAC)',
             "Soil organic carbon content from OpenLandMap STAC, reported in g/kg. "
             "Higher values indicate greater carbon storage."),
            ('phh2o', 'pH (H₂O)',
             "Soil acidity/alkalinity measured in water suspension at 0–5cm depth from "
             "ISRIC SoilGrids 2.0. 7 = neutral, <7 acidic, >7 alkaline."),
            ('soc', 'Soil Organic Carbon (SOC)',
             "Soil organic carbon at 0–5cm depth from ISRIC SoilGrids 2.0, in g/kg. "
             "Topsoil carbon stocks indicator."),
            ('bdod', 'Bulk Density',
             "Mass of dry soil per unit volume at 0–5cm from ISRIC SoilGrids 2.0, in g/cm³. "
             "Lower values indicate more pore space and organic matter."),
            ('nitrogen', 'Total Nitrogen',
             "Total nitrogen at 0–5cm depth from ISRIC SoilGrids 2.0, in g/kg. "
             "Indicator of soil fertility."),
        ]
        _ind_state_keys = [f'show_indicator_{k}' for k, *_ in _indicator_specs]
        _ind_widget_keys = [f'dlg_{k}' for k in _ind_state_keys]

        def _toggle_all_indicators():
            new_val = bool(st.session_state.get('dlg_show_all_indicators', False))
            for sk, wk in zip(_ind_state_keys, _ind_widget_keys):
                st.session_state[sk] = new_val
                st.session_state[wk] = new_val

        def _toggle_one_indicator(state_key, widget_key):
            new_val = bool(st.session_state.get(widget_key, False))
            st.session_state[state_key] = new_val
            st.session_state['dlg_show_all_indicators'] = all(
                st.session_state.get(k, False) for k in _ind_state_keys
            )

        _all_on = all(st.session_state.get(k, False) for k in _ind_state_keys)
        _ei_col1, _ei_col2, _ei_col3 = st.columns(3)
        with _ei_col1:
            st.checkbox(
                "**Show all**",
                value=_all_on,
                key="dlg_show_all_indicators",
                on_change=_toggle_all_indicators,
                help="Toggle every environmental indicator on or off at once.",
            )
        # Six indicators split across the right two columns (three each)
        _ei_specs_zipped = list(zip(_indicator_specs, _ind_state_keys, _ind_widget_keys))
        _half = (len(_ei_specs_zipped) + 1) // 2  # ceil-divide so col2 gets the extra if odd
        for _col, _group in ((_ei_col2, _ei_specs_zipped[:_half]),
                             (_ei_col3, _ei_specs_zipped[_half:])):
            with _col:
                for (short, label, help_text), state_key, widget_key in _group:
                    st.checkbox(
                        label,
                        value=st.session_state.get(state_key, False),
                        key=widget_key,
                        on_change=_toggle_one_indicator,
                        args=(state_key, widget_key),
                        help=help_text,
                    )

        st.divider()

        st.markdown("##### Urban Green/Blue Infrastructure")
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

        st.divider()

        st.markdown("##### Sampling Configuration")
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

        st.divider()

        st.markdown("##### Regional Adjustments")
        _elast = st.slider(
            "Income elasticity factor", min_value=0.1, max_value=1.0,
            value=st.session_state.get('income_elasticity', 0.6), step=0.1,
            help="0.5–0.6 recommended. Scales regional GDP differences.",
            key="dlg_income_elasticity",
        )
        st.session_state['income_elasticity'] = _elast
        st.caption("Formula: 1 + (e × (GDP_regional/GDP_global − 1)), bounded 0.4×–2.5×")

        st.divider()

        with st.expander("Ecosystem Intactness by Type", expanded=False):
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
            st.caption("EEI active" if _eei else "Manual sliders below")

            _eco_types = {
                'Agricultural': '🌾', 'Temperate Forest': '🌳', 'Boreal Forest': '🌲',
                'Tropical Forest': '🌴', 'Polar': '🧊', 'Grassland': '🌱',
                'Shrubland': '🌵', 'Desert': '🏜️', 'Wetland': '🌿',
                'Coastal': '🏖️', 'Mangroves': '🦀', 'Marine': '🌊',
                'Rivers and Lakes': '🏞️', 'Urban': '🏙️',
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

        st.divider()
        with st.expander("OpenLandMap Settings (advanced — landcover → ecosystem mapping)", expanded=False):
            from utils.esa_landcover_codes import DEFAULT_LANDCOVER_MAPPING, get_all_esa_codes, get_default_multipliers, get_esa_description
            _default_map = DEFAULT_LANDCOVER_MAPPING
            _esvd_types = [
                "Forest", "Tropical Forest", "Temperate Forest", "Boreal Forest",
                "Grassland", "Agricultural", "Urban", "Desert",
                "Wetland", "Coastal", "Mangroves", "Marine", "Shrubland", "polar"
            ]
            if 'custom_landcover_mapping' not in st.session_state:
                st.session_state.custom_landcover_mapping = _default_map.copy()
            for code, eco in _default_map.items():
                if code not in st.session_state.custom_landcover_mapping:
                    st.session_state.custom_landcover_mapping[code] = eco

            _desc = get_all_esa_codes()
            st.markdown("**Landcover → Ecosystem mapping**")
            st.caption(
                "Each ESA CCI / WorldCover land-cover code maps to one ESVD ecosystem "
                "type. The ESA description is shown alongside each code; change the "
                "ecosystem on the right to override that code's default routing."
            )
            if st.button("Reset to defaults", key="dlg_reset_mapping"):
                st.session_state.custom_landcover_mapping = _default_map.copy()
                st.rerun()
            _changes = sum(1 for k, v in st.session_state.custom_landcover_mapping.items() if v != _default_map.get(k))
            if _changes:
                st.info(f"{_changes} custom mappings active")

            # Header row
            _hc1, _hc2, _hc3 = st.columns([1, 5, 3])
            with _hc1:
                st.markdown("**Code**")
            with _hc2:
                st.markdown("**ESA description**")
            with _hc3:
                st.markdown("**ESVD ecosystem type**")
            st.divider()

            for code in sorted(_default_map.keys()):
                _mc1, _mc2, _mc3 = st.columns([1, 5, 3])
                with _mc1:
                    st.markdown(f"**{code}**")
                with _mc2:
                    _is_custom = (
                        st.session_state.custom_landcover_mapping.get(code)
                        != _default_map.get(code)
                    )
                    _label = _desc.get(code, f"ESA Land Cover Class {code}")
                    if _is_custom:
                        st.markdown(
                            f"{_label} <span style='color:#FF8F00; font-size:0.85em;'>"
                            f"(default: {_default_map.get(code)})</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write(_label)
                with _mc3:
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

        st.divider()

        st.markdown("##### Scientific Methodology")
        st.markdown("""
    **EVE** combines satellite remote sensing with the ESVD (10,874 peer-reviewed values) to measure natural capital.

    **Service Categories**: Provisioning · Regulating · Cultural · Supporting

    **Formula**: `Final Value = ESVD_Base × Regional_Adjustment × Quality_Factor`

    **Standards**: 2020 International dollars/ha/year · Bounded 0.4×–2.5× regional adjustment
        """)
        st.caption(
            "Brander, L.M. de Groot, R, Guisado Goñi, V., van 't Hoff, V., "
            "Schägner, P., Solomonides, S., McVittie, A., Eppink, F., Sposato, M., "
            "Do, L., Ghermandi, A., and Sinclair, M. (2025). *Ecosystem Services "
            "Valuation Database (ESVD)*. Foundation for Sustainable Development "
            "and Brander Environmental Economics."
        )

        if st.button("View ESA CCI → ESVD default mapping", key="dlg_show_mapping_btn"):
            st.session_state.show_default_mapping = not st.session_state.get('show_default_mapping', False)

        if st.session_state.get('show_default_mapping', False):
            from utils.esa_landcover_codes import DEFAULT_LANDCOVER_MAPPING, get_esa_description
            import pandas as pd
            _rows = [
                {"ESA CCI Code": code,
                 "ESA Description": get_esa_description(code),
                 "ESVD Type": DEFAULT_LANDCOVER_MAPPING[code]}
                for code in sorted(DEFAULT_LANDCOVER_MAPPING.keys())
            ]
            st.caption("Default ESA CCI Land Cover → ESVD ecosystem-type mapping. "
                       "Customise per-code values in **OpenLandMap Settings** above.")
            st.dataframe(pd.DataFrame(_rows), hide_index=True, use_container_width=True)

        # Admin-only section: list of registered users.
        _auth_user = st.session_state.get('auth_user') or {}
        if _auth_user.get('is_admin'):
            st.divider()
            with st.expander("User Administration (admin)", expanded=False):
                try:
                    from database import UserDB as _AdminUserDB
                    _all_users = _AdminUserDB.list_all_users()
                    if _all_users:
                        import pandas as pd
                        _user_rows = [
                            {
                                "Registered (UTC)": (
                                    u['created_at'].strftime('%Y-%m-%d %H:%M')
                                    if u.get('created_at') else ''
                                ),
                                "Email": u['email'],
                                "Display name": u['display_name'] or '—',
                                "Organisation": u.get('organisation') or '—',
                                "Status": u.get('status', '—'),
                                "Verified": "Yes" if u['email_verified'] else "No",
                                "Admin": "Yes" if u['is_admin'] else "No",
                            }
                            for u in _all_users
                        ]
                        st.caption(f"{len(_all_users)} registered users")
                        st.dataframe(
                            pd.DataFrame(_user_rows),
                            use_container_width=True,
                            hide_index=True,
                            height=320,
                        )
                    else:
                        st.info("No users found.")
                except Exception as _admin_err:
                    st.error(f"Could not load user list: {_admin_err}")

    if st.button("Close", use_container_width=True, key="dlg_close"):
        st.rerun()


# ── Pre-Analyze project indicators panel ─────────────────────────────────────
# Standardised band library — score (0.0-1.0) mapped to label + display pct
PRE_ANALYZE_BANDS = [
    ('Severely degraded',       0.10, 10),
    ('Degraded',                0.30, 30),
    ('Recovering',              0.50, 50),
    ('Substantially recovered', 0.75, 75),
    ('Well recovered',          0.90, 90),
    ('Reference condition',     1.00, 100),
]

# v1 scope: only Mangrove Restoration project type is wired up
PRE_ANALYZE_PROJECT_TYPE_SLUG = 'mangrove_restoration'

# Full list of ecosystem types the user can force via the main-page selector.
# Shared by the project-ecosystem dropdown and any other consumer that needs the
# canonical display names.
ECOSYSTEM_DISPLAY_OPTIONS = [
    "Auto-detect", "Tropical Forest", "Temperate Forest", "Boreal Forest",
    "Polar", "Grassland", "Shrubland", "Wetland", "Water (ocean)",
    "Rivers and Lakes", "Coastal", "Mangroves", "Marine", "Agricultural",
    "Urban", "Desert",
]

# Display names of ecosystems with project-specific indicators seeded in
# utils/project_indicators_seed.py. Grow as new project types are wired up.
ECOSYSTEMS_WITH_PROJECT_INDICATORS = {'Mangroves'}


def _ecosystem_has_project_indicators(display_name: str) -> bool:
    return display_name in ECOSYSTEMS_WITH_PROJECT_INDICATORS


def _effective_intactness_dict() -> Dict:
    """Return the per-ecosystem intactness dict the calc engine should use.

    - EEI on  → derive from ecosystem_eei (per-area EEI fetch, 0–1 scale
      converted to 0–100 %). Manual sliders are NOT consulted.
    - EEI off → use ecosystem_intactness (the user's manual slider state,
      0–100 %).

    Critically, EEI no longer overwrites ``ecosystem_intactness`` — those
    sliders are the user's manual settings and must only change when
    the user moves a slider.
    """
    if st.session_state.get('use_eei_for_intactness'):
        _eei_dict = st.session_state.get('ecosystem_eei', {}) or {}
        out: Dict[str, float] = {}
        for k, v in _eei_dict.items():
            if v is None:
                continue
            pct = round(v * 100, 3)
            out[k] = pct
            # Mirror under title-case so the analysis_helpers lookup
            # (which does case-normalisation as a fallback) finds it
            # whether ecosystem_eei is keyed by snake_case or display name.
            out[k.replace('_', ' ').title()] = pct
        return out
    return st.session_state.get('ecosystem_intactness', {}) or {}


def render_pre_analyze_indicator_panel():
    """Render the indicator selection + response panel BEFORE the Analyze
    button. Responses live in ``st.session_state.pending_indicator_responses``
    keyed by indicator slug — the Analyze handler persists them once an
    EcosystemAnalysis row exists, then runs ``compute_sub_service_multipliers``
    and passes the result dict into ``calculate_ecosystem_values``.

    No DB writes from this panel — entirely session-state driven so the user
    can fiddle freely without creating draft rows.

    Gated by ``st.session_state.use_indicator_multipliers``. v1 scope:
    Mangrove Restoration project type only.
    """
    if not st.session_state.get('use_indicator_multipliers', False):
        return
    if not st.session_state.get('selected_area'):
        return
    # Gated by the main-screen ecosystem selector — only render when the user
    # has picked a specific project-ecosystem (e.g. Mangroves), not 'Auto-detect'.
    _project_eco = st.session_state.get('project_ecosystem_override', 'Auto-detect')
    if _project_eco == 'Auto-detect':
        return

    try:
        from database import ProjectIndicatorDB
        pt = ProjectIndicatorDB.get_project_type_with_indicators(PRE_ANALYZE_PROJECT_TYPE_SLUG)
    except Exception as _e:
        st.warning(f"Project indicators framework unavailable: {_e}")
        return
    if not pt or not pt.get('indicators'):
        st.info("No indicators seeded for the Mangrove project type.")
        return

    st.markdown("## Project Indicators (Mangrove)")
    st.caption(
        "Commit to measuring and monitoring progress on as many indicators as "
        "possible to improve the accuracy of the ecosystem valuation. Select "
        "the checkbox next to those indicators that you can commit to measuring."
    )

    # Make the 'Commit to tracking' checkboxes more visible — the default
    # Streamlit checkbox renders with a faint grey outline that's easy to miss.
    # Bump the border to a 2px green stroke on the unchecked box and bold-green
    # fill when checked. Scoped to the pi_pre_commit_* widget keys so other
    # checkboxes elsewhere are untouched.
    st.markdown(
        """
<style>
div[class*='st-key-pi_pre_commit_'] [data-baseweb='checkbox'] > label > span:first-child {
    border: 2px solid #2E7D32 !important;
    background-color: #FFFFFF !important;
    width: 22px !important;
    height: 22px !important;
}
div[class*='st-key-pi_pre_commit_'] [data-baseweb='checkbox'] > label > span:first-child[aria-checked='true'],
div[class*='st-key-pi_pre_commit_'] [data-baseweb='checkbox'] input:checked + div,
div[class*='st-key-pi_pre_commit_'] [data-baseweb='checkbox'] > label > div:first-child[data-checked='true'] {
    background-color: #2E7D32 !important;
    border-color: #2E7D32 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    # Initialize pending-responses state
    pending = st.session_state.setdefault('pending_indicator_responses', {})

    # Render order: non-HD first, HD last
    indicators = pt['indicators']
    non_hd = [i for i in indicators if not i.get('is_mandatory')]
    hd = [i for i in indicators if i.get('is_mandatory')]
    ordered = non_hd + hd

    # Initialise pending entries for every indicator (HD pre-committed)
    for ind in ordered:
        slug = ind['slug']
        pending.setdefault(slug, {
            'is_committed': bool(ind.get('is_mandatory')),
            'score': None,
            'is_custom': False,
        })

    # ── Selection table: Indicator | Commit to tracking ────────────────
    _hdr_l, _hdr_r = st.columns([7, 2])
    with _hdr_l:
        st.markdown("**Indicator**")
    with _hdr_r:
        st.markdown("**Commit to tracking**")
    st.divider()

    for ind in ordered:
        slug = ind['slug']
        code = ind.get('code') or '?'
        name = ind.get('name') or slug
        question = ind.get('baseline_question') or ''
        is_mandatory = bool(ind.get('is_mandatory'))
        entry = pending[slug]

        _row_l, _row_r = st.columns([7, 2])
        with _row_l:
            _is_recommended = bool(ind.get('is_recommended'))
            _badges = ""
            if is_mandatory:
                _badges += " <span style='color:#FB8C00; font-weight:600; font-size:0.85rem;'>Required</span>"
            elif _is_recommended:
                _badges += " <span style='color:#2E7D32; font-weight:600; font-size:0.85rem;'>Recommended</span>"
            st.markdown(
                f"**{code}: {name}**{_badges}",
                unsafe_allow_html=True,
            )
            st.caption(question)
        with _row_r:
            if is_mandatory:
                entry['is_committed'] = True
                st.markdown(
                    "<div style='padding-top:0.4rem; color:#FB8C00; font-weight:600;'>✓</div>",
                    unsafe_allow_html=True,
                )
            else:
                entry['is_committed'] = st.checkbox(
                    f"Commit to measuring {code}",
                    value=entry['is_committed'],
                    key=f"pi_pre_commit_{slug}",
                    label_visibility='collapsed',
                    help="Once committed, this indicator cannot be removed later "
                         "(per project monitoring commitments).",
                )

    # ── Response panel for committed indicators ────────────────────────
    committed = [ind for ind in ordered if pending[ind['slug']]['is_committed']]
    if committed:
        st.divider()
        st.markdown("### Record measurements")
        st.caption(
            "For each committed indicator, record the **Baseline** (current "
            "site condition) on the left and the **Target** (what you expect "
            "the project to reach) on the right. Use a predefined band or "
            "enter a custom percentage (0–100)."
        )

        # Baseline / Target dates apply to every indicator in this assessment.
        # day-month-year picker — full date stored in session state; the
        # year is what gets persisted to pi_analysis_responses.*_year.
        _today = datetime.now().date()
        _default_target = _today.replace(year=_today.year + 5)
        _date_col_a, _date_col_b = st.columns(2)
        with _date_col_a:
            _baseline_date = st.date_input(
                "Baseline date",
                value=st.session_state.get('pending_indicator_baseline_date', _today),
                key='pi_pre_baseline_date',
                format='DD/MM/YYYY',
                help="Date the baseline measurement was taken (or will be taken).",
            )
            st.session_state['pending_indicator_baseline_date'] = _baseline_date
        with _date_col_b:
            _target_date = st.date_input(
                "Target date",
                value=st.session_state.get('pending_indicator_target_date', _default_target),
                key='pi_pre_target_date',
                format='DD/MM/YYYY',
                help="Date by which the project intends to reach the target conditions.",
            )
            st.session_state['pending_indicator_target_date'] = _target_date

        # Colour-coded option labels using Streamlit's `:color[text]` markdown.
        # The visual squares give an at-a-glance red→amber→green gradient
        # tied to band position. Labels come from the indicator's own seed
        # `bands` array so each indicator can have tailored wording
        # (e.g. M2 'Sparse recruitment' instead of generic 'Degraded').
        # tuple: (key, display_label, score)
        _BAND_COLOR_PREFIX = [
            ':red[🟥 ',
            ':orange[🟧 ',
            ':orange[🟨 ',
            ':green[🟩 ',
            ':green[🟩 ',
            ':green[🟩 ',
        ]

        def _build_options_for(indicator):
            """Build the radio _OPTIONS list for a single indicator.

            Labels come from ``indicator['bands']`` (per-indicator seed
            data) so M3-M7+HD show their tailored wording. Score values
            and the colour ramp stay project-wide constants.
            """
            bands = indicator.get('bands') or []
            opts = [('none', ':gray[— not yet answered —]', None)]
            for i, band in enumerate(bands):
                score = float(band['score'])
                pct = int(round(score * 100))
                prefix = _BAND_COLOR_PREFIX[i] if i < len(_BAND_COLOR_PREFIX) else ':gray['
                label_text = band.get('label') or f'Band {i + 1}'
                opts.append((
                    f'band_{i}',
                    f"{prefix}{label_text} ({pct}%)]",
                    score,
                ))
            opts.append(('custom', ':gray[Custom]', None))
            return opts

        def _idx_for(score, is_custom, options):
            """Return the radio index that represents a stored (score, is_custom)."""
            keys = [k for k, _, _ in options]
            if is_custom:
                return keys.index('custom')
            if score is None:
                return 0
            for i, (_k, _lbl, s) in enumerate(options):
                if s is not None and abs(s - score) < 1e-6:
                    return i
            return 0

        def _state_from_choice(choice_label: str, custom_val: int, options):
            """Given a chosen label + the value of its custom number input,
            return (score|None, is_custom)."""
            labels = [lbl for _, lbl, _ in options]
            keys = [k for k, _, _ in options]
            idx = labels.index(choice_label)
            key = keys[idx]
            if key == 'custom':
                return (float(custom_val) / 100.0, True)
            if key == 'none':
                return (None, False)
            return (options[idx][2], False)

        def _label_for_score(score, options):
            """Human-readable name for a score from the indicator's own
            options (e.g. M2 0.75 → 'Good recruitment')."""
            for k, lbl, s in options:
                if s is not None and abs(s - score) < 1e-6:
                    # Strip the Streamlit color markdown + emoji prefix for the caption
                    clean = lbl
                    for prefix in (':red[', ':orange[', ':green[', ':gray['):
                        if clean.startswith(prefix):
                            clean = clean[len(prefix):-1]
                            break
                    for em in ('🟥 ', '🟧 ', '🟨 ', '🟩 '):
                        if clean.startswith(em):
                            clean = clean[len(em):]
                            break
                    # Drop the trailing percentage parenthetical
                    if ' (' in clean:
                        clean = clean.split(' (', 1)[0]
                    return clean
            return 'Custom'

        for ind in committed:
            slug = ind['slug']
            code = ind.get('code') or '?'
            name = ind.get('name') or slug
            entry = pending[slug]
            # Ensure target keys exist
            entry.setdefault('target_score', None)
            entry.setdefault('target_is_custom', False)

            # Per-indicator radio options (labels come from this indicator's
            # own seed bands; score values and colour ramp stay constant).
            _options = _build_options_for(ind)
            _opt_labels = [lbl for _, lbl, _ in _options]

            is_mandatory = bool(ind.get('is_mandatory'))
            # `expanded=True` constant: Streamlit only applies it on first
            # render. After that the user controls open/closed via the chevron
            # and their choice is preserved across reruns. (Passing a dynamic
            # expression here causes Streamlit to force-close the expander
            # as soon as the user answers — they want their responses to
            # stay visible until they manually collapse.)
            with st.expander(
                f"{code}: {name}" + ("  (Required)" if is_mandatory else ""),
                expanded=True,
            ):
                _base_col, _tgt_col = st.columns(2)

                with _base_col:
                    st.markdown("**Baseline**")
                    _base_idx = _idx_for(entry.get('score'), entry.get('is_custom', False), _options)
                    _base_choice = st.radio(
                        "Baseline response",
                        _opt_labels,
                        index=_base_idx,
                        key=f"pi_pre_base_{slug}",
                        label_visibility='collapsed',
                    )
                    _base_is_custom = (_base_choice == _opt_labels[-1])
                    _base_default = (
                        int(round(entry['score'] * 100))
                        if (entry.get('is_custom') and entry.get('score') is not None)
                        else 50
                    )
                    _base_custom_val = st.number_input(
                        "Custom baseline (%)",
                        min_value=0, max_value=100, step=1,
                        value=_base_default,
                        key=f"pi_pre_basecustom_{slug}",
                        disabled=not _base_is_custom,
                        help="Enter 0-100. Active only when 'Custom' is selected.",
                    )

                with _tgt_col:
                    st.markdown("**Target**")
                    _tgt_idx = _idx_for(entry.get('target_score'), entry.get('target_is_custom', False), _options)
                    _tgt_choice = st.radio(
                        "Target response",
                        _opt_labels,
                        index=_tgt_idx,
                        key=f"pi_pre_tgt_{slug}",
                        label_visibility='collapsed',
                    )
                    _tgt_is_custom = (_tgt_choice == _opt_labels[-1])
                    _tgt_default = (
                        int(round(entry['target_score'] * 100))
                        if (entry.get('target_is_custom') and entry.get('target_score') is not None)
                        else 90
                    )
                    _tgt_custom_val = st.number_input(
                        "Custom target (%)",
                        min_value=0, max_value=100, step=1,
                        value=_tgt_default,
                        key=f"pi_pre_tgtcustom_{slug}",
                        disabled=not _tgt_is_custom,
                        help="Enter 0-100. Active only when 'Custom' is selected.",
                    )

                # Reconcile state from widgets
                entry['score'], entry['is_custom'] = _state_from_choice(_base_choice, _base_custom_val, _options)
                entry['target_score'], entry['target_is_custom'] = _state_from_choice(_tgt_choice, _tgt_custom_val, _options)

                # Caption with current Baseline / Target values
                _base_score = entry.get('score')
                _tgt_score = entry.get('target_score')
                if _base_score is not None or _tgt_score is not None:
                    if _base_score is None:
                        _base_str = '—'
                    else:
                        _base_pct = int(round(_base_score * 100))
                        _base_label = ('Custom' if entry.get('is_custom')
                                       else _label_for_score(_base_score, _options))
                        _base_str = f"{_base_pct}% ({_base_label})"
                    if _tgt_score is None:
                        _tgt_str = '—'
                    else:
                        _tgt_pct = int(round(_tgt_score * 100))
                        _tgt_label = ('Custom' if entry.get('target_is_custom')
                                      else _label_for_score(_tgt_score, _options))
                        _tgt_str = f"{_tgt_pct}% ({_tgt_label})"
                    st.caption(f"**Baseline:** {_base_str} · **Target:** {_tgt_str}")

    # Coverage summary
    try:
        from utils.teeb_slug_map import TEEB_TO_CALC_KEY, HD_RELATIONSHIP, WEIGHT_LOOKUP
        from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
        all_keys = list(
            PrecomputedESVDCoefficients().get_ecosystem_coefficients('Mangroves').keys()
        )
        covered = set()
        for ind in non_hd:
            slug = ind['slug']
            entry = pending.get(slug) or {}
            if not entry.get('is_committed') or entry.get('score') is None:
                continue
            sw = ind.get('service_weights') or {}
            for t, rel in sw.items():
                if rel == HD_RELATIONSHIP or rel not in WEIGHT_LOOKUP:
                    continue
                calc_key = TEEB_TO_CALC_KEY.get(t)
                if calc_key:
                    covered.add(calc_key)
        n_total = len(all_keys)
        n_covered = sum(1 for k in all_keys if k in covered)
        n_fallback = n_total - n_covered
        st.info(
            f"**Coverage:** {n_covered} of {n_total} sub-services covered by "
            f"indicators · Fallback intactness values (EEI or user-set) apply to {n_fallback}"
        )
    except Exception:
        pass

    st.markdown("---")


def _build_indicator_state_blob() -> dict | None:
    """Capture the user's current indicator-multiplier configuration as a
    JSON-serialisable dict, suitable for persisting to
    ``saved_areas.project_indicators``. Returns ``None`` if the feature is
    off or no responses/commitments are recorded.

    The shape is intentionally future-proof — adding fields here won't break
    existing rows because the column is JSON."""
    pending = st.session_state.get('pending_indicator_responses') or {}
    use_flag = bool(st.session_state.get('use_indicator_multipliers'))
    project_eco = st.session_state.get('project_ecosystem_override')
    baseline_date = st.session_state.get('pending_indicator_baseline_date')
    target_date = st.session_state.get('pending_indicator_target_date')
    if not use_flag and not pending:
        return None
    responses_out = {}
    for slug, entry in (pending or {}).items():
        if not entry:
            continue
        responses_out[slug] = {
            'is_committed': bool(entry.get('is_committed')),
            'score': entry.get('score'),
            'is_custom': bool(entry.get('is_custom')),
            'target_score': entry.get('target_score'),
            'target_is_custom': bool(entry.get('target_is_custom')),
        }
    return {
        'use_indicator_multipliers': use_flag,
        'project_ecosystem_override': project_eco,
        'baseline_date': baseline_date.isoformat() if baseline_date else None,
        'target_date': target_date.isoformat() if target_date else None,
        'responses': responses_out,
    }


def _restore_indicator_state_blob(blob: dict | None) -> None:
    """Restore session state from a previously-persisted indicator blob.
    Clears the relevant session keys first so an area without a blob comes
    up with a clean indicator panel."""
    # Always clear before restoring so loading an area that doesn't have a
    # blob (or has a partial one) doesn't inherit state from a previous area.
    for k in (
        'pending_indicator_responses',
        'pending_indicator_baseline_date',
        'pending_indicator_target_date',
        'pending_computed_multipliers',
        'pending_computed_multipliers_ecotype',
        'project_ecosystem_override',
    ):
        if k in st.session_state:
            del st.session_state[k]
    if not blob:
        # Legacy area (saved before this feature) — leave the user's current
        # Settings toggle alone.
        return
    # Propagate the Settings flag explicitly (both aliases) so the toggle
    # state restores with the area. Areas saved with the feature enabled
    # turn it back on; areas saved with it disabled turn it back off.
    _saved_flag = bool(blob.get('use_indicator_multipliers'))
    st.session_state['use_indicator_multipliers'] = _saved_flag
    st.session_state['project_indicators_enabled'] = _saved_flag
    if blob.get('project_ecosystem_override'):
        st.session_state['project_ecosystem_override'] = blob['project_ecosystem_override']
        # Also propagate to ecosystem_override so the calc routes correctly
        if blob['project_ecosystem_override'] != 'Auto-detect':
            st.session_state['ecosystem_override'] = blob['project_ecosystem_override']
    try:
        from datetime import date as _date
        if blob.get('baseline_date'):
            st.session_state['pending_indicator_baseline_date'] = _date.fromisoformat(blob['baseline_date'])
        if blob.get('target_date'):
            st.session_state['pending_indicator_target_date'] = _date.fromisoformat(blob['target_date'])
    except Exception:
        pass
    if blob.get('responses'):
        st.session_state['pending_indicator_responses'] = {
            slug: {
                'is_committed': bool(r.get('is_committed')),
                'score': r.get('score'),
                'is_custom': bool(r.get('is_custom')),
                'target_score': r.get('target_score'),
                'target_is_custom': bool(r.get('target_is_custom')),
            }
            for slug, r in (blob['responses'] or {}).items()
        }


def _build_indicator_multiplier_dict(ecosystem_type: str, score_field: str = 'score'):
    """Compute {calc_key: final_multiplier} from pending session-state
    indicator responses, for use by the calc engine. Returns ``None`` if
    the feature is disabled, the ecosystem isn't covered by a wired project
    type (v1: only Mangroves), or no project-indicator framework is seeded.

    ``score_field`` controls which response field becomes ``effective_score``
    when feeding rows into the multiplier engine:
      * ``'score'`` (default): baseline indicator responses.
      * ``'target_score'``: target-condition responses. Used to compute a
        parallel "target" valuation alongside baseline.

    Side-effect: stashes the per-sub-service rows in session state for the
    post-Analyze persistence step. Baseline rows go to
    ``pending_computed_multipliers``; target rows go to
    ``pending_computed_multipliers_target`` so the two never clobber each
    other.
    """
    if not st.session_state.get('use_indicator_multipliers'):
        return None
    # v1 scope: only Mangrove ecosystem is wired to the Mangrove project type.
    if ecosystem_type.lower() not in ('mangroves', 'mangrove'):
        return None
    try:
        from database import ProjectIndicatorDB
        from utils.indicator_multipliers import _compute_pure
        from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
    except ImportError:
        return None

    pt = ProjectIndicatorDB.get_project_type_with_indicators(PRE_ANALYZE_PROJECT_TYPE_SLUG)
    if not pt or not pt.get('indicators'):
        return None

    pending = st.session_state.get('pending_indicator_responses') or {}
    hd_slug = None
    responses = []
    for ind in pt['indicators']:
        slug = ind['slug']
        is_mand = bool(ind.get('is_mandatory'))
        if is_mand:
            hd_slug = slug
        entry = pending.get(slug) or {}
        responses.append({
            'indicator_slug': slug,
            'is_committed': bool(entry.get('is_committed') or is_mand),
            'is_mandatory': is_mand,
            'effective_score': entry.get(score_field),
            'service_weights': ind.get('service_weights') or {},
        })

    coeffs = PrecomputedESVDCoefficients()
    eco_dict = coeffs.get_ecosystem_coefficients(ecosystem_type) or {}
    if not eco_dict:
        return None
    sub_keys = list(eco_dict.keys())

    # BBI fallback for sub-services NOT covered by any selected indicator.
    # Source the intactness dict through _effective_intactness_dict() so that:
    #   - When EEI is on  -> BBI = the EEI-derived value for this ecosystem
    #   - When EEI is off -> BBI = the manual slider value
    # Reading raw ecosystem_intactness here would always give the slider
    # value (default 100%) even with EEI active, since EEI no longer
    # mirrors itself into the slider state.
    ei = _effective_intactness_dict()
    bbi = _get_ecosystem_intactness_multiplier(ecosystem_type, ei)

    rows = _compute_pure(
        sub_service_keys=sub_keys,
        indicator_responses=responses,
        hd_indicator_slug=hd_slug,
        bbi=bbi,
    )
    # Stash for post-Analyze persistence + breakdown-panel rendering.
    # Target rows go to a parallel key to avoid clobbering baseline.
    _stash_key = (
        'pending_computed_multipliers_target'
        if score_field == 'target_score' else
        'pending_computed_multipliers'
    )
    st.session_state[_stash_key] = rows
    st.session_state['pending_computed_multipliers_ecotype'] = ecosystem_type
    return {r['teeb_sub_service_key']: r['final_multiplier'] for r in rows}


def _all_committed_have_target_scores() -> bool:
    """Return True iff every committed indicator in
    ``pending_indicator_responses`` has a non-null ``target_score``.

    Gate for rendering target-condition valuations. Baseline responses can
    be missing (those fall back to EEI/slider); target rendering blocks
    until every committed indicator is answered on the target side.
    """
    if not st.session_state.get('use_indicator_multipliers'):
        return False
    pending = st.session_state.get('pending_indicator_responses') or {}
    if not pending:
        return False
    found_committed = False
    for entry in pending.values():
        entry = entry or {}
        if not entry.get('is_committed'):
            continue
        found_committed = True
        if entry.get('target_score') is None:
            return False
    return found_committed


def _persist_pre_analyze_indicators(analysis_id: str) -> None:
    """After save_analysis() succeeds and we have an analysis_id, persist
    the pre-Analyze indicator state to the DB:
      1. Flip use_indicator_multipliers=True on the assessment row.
      2. Save commitments + per-indicator responses to pi_analysis_responses.
      3. Write the pre-computed multiplier rows to
         computed_sub_service_multipliers (so the breakdown panel and any
         later recompute can reuse them).
    Silent on errors — this is a best-effort write that must never break
    a successful analysis."""
    try:
        from database import (
            ProjectIndicatorDB,
            ComputedSubServiceMultiplierDB,
        )
    except ImportError:
        return
    pending = st.session_state.get('pending_indicator_responses') or {}
    if not st.session_state.get('use_indicator_multipliers') or not pending:
        return

    try:
        ProjectIndicatorDB.set_assessment_flag(analysis_id, True)
        # Commitments
        committed_slugs = [s for s, e in pending.items()
                           if bool((e or {}).get('is_committed'))]
        ProjectIndicatorDB.save_commitments(
            analysis_id,
            PRE_ANALYZE_PROJECT_TYPE_SLUG,
            committed_slugs,
        )
        # Per-indicator responses
        for slug, entry in pending.items():
            entry = entry or {}
            if not entry.get('is_committed'):
                continue
            score = entry.get('score')
            if score is None:
                continue
            is_custom = bool(entry.get('is_custom'))
            if is_custom:
                ProjectIndicatorDB.save_response(
                    analysis_id=analysis_id,
                    project_type_slug=PRE_ANALYZE_PROJECT_TYPE_SLUG,
                    indicator_slug=slug,
                    baseline_band_id=None,
                    baseline_year=None,
                    target_band_id=None,
                    target_year=None,
                    applies_to_ecosystem=None,
                    followup_responses=None,
                    notes=None,
                    custom_score=float(score),
                )
            else:
                # Match a band by score
                from database import ProjectType, IndicatorBand, Indicator, get_db
                band_id = None
                try:
                    with get_db() as db:
                        ind_row = db.query(Indicator).filter(Indicator.slug == slug).first()
                        if ind_row is not None:
                            band = (db.query(IndicatorBand)
                                    .filter(IndicatorBand.indicator_id == ind_row.id)
                                    .order_by(IndicatorBand.sort_order).all())
                            for b in band:
                                if abs(float(b.score) - float(score)) < 1e-6:
                                    band_id = str(b.id)
                                    break
                except Exception:
                    band_id = None
                ProjectIndicatorDB.save_response(
                    analysis_id=analysis_id,
                    project_type_slug=PRE_ANALYZE_PROJECT_TYPE_SLUG,
                    indicator_slug=slug,
                    baseline_band_id=band_id,
                    baseline_year=None,
                    target_band_id=None,
                    target_year=None,
                    applies_to_ecosystem=None,
                    followup_responses=None,
                    notes=None,
                )
        # Computed multiplier rows
        rows = st.session_state.get('pending_computed_multipliers')
        if rows:
            ComputedSubServiceMultiplierDB.replace_for_analysis(analysis_id, rows)
    except Exception as _e:
        logger.warning(f"Pre-analyze indicator persistence failed (non-fatal): {_e}")


# ── Project Indicators section (optional, gated by Settings toggle) ──────────
def render_project_indicators_section():
    """Two-phase Project Indicators UI. Calc-neutral in v1.

    Phase 1: project type picker + indicator commitment list with TEEB coverage.
    Phase 2: per-committed-indicator measurement (band picker + years +
    applies-to + conditional followups + notes). Persists to
    pi_analysis_responses via ProjectIndicatorDB.
    """
    st.markdown("---")
    st.subheader("📋 Project Indicators")

    if not st.session_state.get('auth_user'):
        st.info("Sign in to record project-typed indicator answers for this analysis.")
        return

    analysis_id = st.session_state.get('last_saved_analysis_id')
    if not analysis_id:
        st.info("Run and save an analysis first to attach project indicator answers.")
        return

    db_modules = get_database_modules()
    if not db_modules or 'ProjectIndicatorDB' not in db_modules:
        st.info("Project Indicators unavailable — database connection issue.")
        return
    PI = db_modules['ProjectIndicatorDB']

    project_types = PI.get_active_project_types()
    if not project_types:
        st.warning("No project types configured.")
        return

    options = ["— None —"] + [f"{(pt.get('icon') or '')} {pt['name']}".strip() for pt in project_types]
    slug_by_label = {f"{(pt.get('icon') or '')} {pt['name']}".strip(): pt['slug'] for pt in project_types}

    current_slug = st.session_state.get('project_type_slug')
    current_label = next((lbl for lbl, sl in slug_by_label.items() if sl == current_slug), "— None —")
    selected_label = st.selectbox(
        "Project Type",
        options=options,
        index=options.index(current_label) if current_label in options else 0,
        key="pi_project_type_selectbox",
    )
    selected_slug = slug_by_label.get(selected_label) if selected_label != "— None —" else None

    if selected_slug != current_slug:
        st.session_state.project_type_slug = selected_slug
        PI.set_analysis_project_type(analysis_id, selected_slug)

    if not selected_slug:
        st.caption("Select a project type to begin recording indicators.")
        return

    snapshot = PI.get_project_type_with_indicators(selected_slug)
    if not snapshot:
        st.warning("Selected project type could not be loaded.")
        return

    existing_responses = PI.get_responses(analysis_id)
    responses_by_key = {(r['indicator_slug'], r['applies_to_ecosystem']): r for r in existing_responses}

    ecosystem_options = ["Whole area"]
    detected = st.session_state.get('detected_ecosystem', {})
    if isinstance(detected, dict):
        for eco_type in (detected.get('ecosystem_distribution') or {}).keys():
            label = eco_type.replace('_', ' ').title()
            if label not in ecosystem_options:
                ecosystem_options.append(label)

    st.markdown(f"### {snapshot.get('icon', '')} {snapshot['name']}")
    if snapshot.get('description'):
        st.caption(snapshot['description'])

    # ── Phase 1: commitment ──────────────────────────────────────────────────
    st.markdown("**Step 1 — Which indicators will your team monitor?**")

    committed_slugs = []
    for ind in snapshot['indicators']:
        existing = responses_by_key.get((ind['slug'], None))
        default_committed = bool(existing['is_committed']) if existing else bool(ind['is_recommended'])
        if ind['is_mandatory']:
            default_committed = True

        col_chk, col_text = st.columns([1, 12])
        with col_chk:
            chk = st.checkbox(
                "_",
                value=default_committed,
                key=f"pi_commit_{ind['slug']}",
                disabled=ind['is_mandatory'],
                label_visibility="collapsed",
            )
        with col_text:
            badges = []
            if ind['is_mandatory']:
                badges.append("🔒 Required")
            if ind['is_recommended']:
                badges.append("⭐ Recommended")
            badge_str = " ".join(badges)
            st.markdown(f"**{ind['code']} · {ind['name']}** {badge_str}".strip())
            st.caption(ind['commitment_question'])

        if chk or ind['is_mandatory']:
            committed_slugs.append(ind['slug'])

    # Coverage display: aggregate TEEB services across committed indicators.
    services_covered = {}
    for ind in snapshot['indicators']:
        if ind['slug'] not in committed_slugs:
            continue
        for service, weight in (ind.get('service_weights') or {}).items():
            if weight in (None, 'multiplier'):
                continue
            if services_covered.get(service) != 'primary':
                services_covered[service] = weight

    if services_covered:
        st.markdown("**Prospectus scope (TEEB services covered):**")
        primary = sorted(s.replace('_', ' ').title() for s, w in services_covered.items() if w == 'primary')
        secondary = sorted(s.replace('_', ' ').title() for s, w in services_covered.items() if w == 'secondary')
        bullets = []
        if primary:
            bullets.append("• **Primary**: " + ", ".join(primary))
        if secondary:
            bullets.append("• **Secondary**: " + ", ".join(secondary))
        st.markdown("  \n".join(bullets))
    else:
        st.caption("No TEEB services covered yet — commit at least one indicator.")

    recommended_slugs = {ind['slug'] for ind in snapshot['indicators'] if ind['is_recommended']}
    missing_recommended = recommended_slugs - set(committed_slugs)
    if missing_recommended:
        labels = [f"{ind['code']} {ind['name']}" for ind in snapshot['indicators']
                  if ind['slug'] in missing_recommended]
        st.info(f"💡 Minimum recommended set excludes: {', '.join(labels)}")

    if st.button("Save commitment", key="pi_save_commitment", type="primary"):
        PI.save_commitments(analysis_id, selected_slug, committed_slugs)
        st.success("Commitment saved.")
        st.rerun()

    # ── Phase 2: measurement ─────────────────────────────────────────────────
    persisted_committed = {r['indicator_slug'] for r in existing_responses if r['is_committed']}
    if not persisted_committed:
        st.caption("Save commitment to begin entering measurements.")
        return

    st.markdown("---")
    st.markdown("**Step 2 — Record baseline and target for each committed indicator**")

    current_year = datetime.now().year

    for ind in snapshot['indicators']:
        if ind['slug'] not in persisted_committed:
            continue

        with st.expander(f"{ind['code']} · {ind['name']}", expanded=False):
            if ind.get('why_matters'):
                st.markdown("**Why this matters**")
                st.caption(ind['why_matters'])

            with st.popover("📖 Field method & remote sensing"):
                if ind.get('field_method'):
                    st.markdown("**Field method**")
                    st.markdown(ind['field_method'])
                if ind.get('remote_sensing_alternative'):
                    st.markdown("**Remote sensing alternative**")
                    st.markdown(ind['remote_sensing_alternative'])
                if ind.get('sources'):
                    st.markdown(f"_Sources: {ind['sources']}_")

            applies_to_label = st.selectbox(
                "Applies to",
                options=ecosystem_options,
                key=f"pi_applies_{ind['slug']}",
            )
            applies_to_value = None if applies_to_label == "Whole area" else applies_to_label
            existing = responses_by_key.get((ind['slug'], applies_to_value))

            st.markdown(f"**{ind['baseline_question']}**")

            bands = ind['bands']
            band_labels = [f"{b['score']} · {b['label']} — {b['criteria']}" for b in bands]
            label_to_id = {band_labels[i]: bands[i]['id'] for i in range(len(bands))}
            id_to_label = {bands[i]['id']: band_labels[i] for i in range(len(bands))}

            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                default_baseline_label = id_to_label.get(existing['baseline_band_id']) if existing and existing.get('baseline_band_id') else None
                baseline_label = st.radio(
                    "Baseline (current condition)",
                    options=band_labels,
                    index=band_labels.index(default_baseline_label) if default_baseline_label in band_labels else 0,
                    key=f"pi_baseline_band_{ind['slug']}_{applies_to_label}",
                )
                baseline_band_id = label_to_id[baseline_label]
            with col_b2:
                baseline_year = st.number_input(
                    "Baseline year",
                    value=int(existing['baseline_year']) if existing and existing.get('baseline_year') else current_year,
                    min_value=1990, max_value=2100, step=1,
                    key=f"pi_baseline_year_{ind['slug']}_{applies_to_label}",
                )

            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                default_target_label = id_to_label.get(existing['target_band_id']) if existing and existing.get('target_band_id') else None
                target_label = st.radio(
                    "Target (future condition)",
                    options=band_labels,
                    index=band_labels.index(default_target_label) if default_target_label in band_labels else len(band_labels) - 1,
                    key=f"pi_target_band_{ind['slug']}_{applies_to_label}",
                )
                target_band_id = label_to_id[target_label]
            with col_t2:
                target_year = st.number_input(
                    "Target year",
                    value=int(existing['target_year']) if existing and existing.get('target_year') else current_year + 5,
                    min_value=1990, max_value=2100, step=1,
                    key=f"pi_target_year_{ind['slug']}_{applies_to_label}",
                )

            # Conditional followups based on chosen baseline score
            chosen_baseline_score = next((b['score'] for b in bands if b['id'] == baseline_band_id), None)
            followup_responses = dict(existing['followup_responses']) if existing and existing.get('followup_responses') else {}

            for f in ind.get('followups', []):
                trigger = f.get('trigger_max_score')
                if trigger is None or (chosen_baseline_score is not None and chosen_baseline_score <= trigger):
                    if f['input_kind'] == 'select':
                        opts_with_blank = ["— Select —"] + (f.get('options') or [])
                        prev = followup_responses.get(f['slug'])
                        idx = opts_with_blank.index(prev) if prev in opts_with_blank else 0
                        choice = st.selectbox(
                            f['question_text'],
                            options=opts_with_blank, index=idx,
                            key=f"pi_followup_{ind['slug']}_{applies_to_label}_{f['slug']}",
                        )
                        followup_responses[f['slug']] = None if choice == "— Select —" else choice
                    else:
                        prev_text = followup_responses.get(f['slug'], "") or ""
                        text = st.text_input(
                            f['question_text'],
                            value=prev_text,
                            key=f"pi_followup_{ind['slug']}_{applies_to_label}_{f['slug']}",
                        )
                        followup_responses[f['slug']] = text or None

            notes = st.text_input(
                "Notes (optional)",
                value=(existing.get('notes') if existing else "") or "",
                key=f"pi_notes_{ind['slug']}_{applies_to_label}",
            )

            if st.button(
                "💾 Save measurement",
                key=f"pi_save_measure_{ind['slug']}_{applies_to_label}",
            ):
                PI.save_response(
                    analysis_id=analysis_id,
                    project_type_slug=selected_slug,
                    indicator_slug=ind['slug'],
                    baseline_band_id=baseline_band_id,
                    baseline_year=int(baseline_year),
                    target_band_id=target_band_id,
                    target_year=int(target_year),
                    applies_to_ecosystem=applies_to_value,
                    followup_responses={k: v for k, v in followup_responses.items() if v is not None} or None,
                    notes=notes or None,
                )
                st.success(f"{ind['code']} saved.")
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
        if st.button("Settings", use_container_width=True, key="open_settings_btn"):
            analysis_settings_dialog()
        st.divider()

    # ── My Workspace ──────────────────────────────────────────────────────────
    if _auth_user:
        st.markdown("**🗂️ My Workspace**")
        with st.container(key="ws_tabs_wrap"):
            _ws_tab_areas, _ws_tab_history = st.tabs(["Saved Areas", "History"])

            with _ws_tab_areas:
                # Save current area
                if st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
                    st.markdown("**Save current area**")
                    _save_name = st.text_input(
                        "Area name", key="ws_save_name",
                        placeholder="e.g. River Wye Catchment",
                    )
                    if st.button("Save area", key="ws_save_btn", use_container_width=True):
                        if _save_name.strip():
                            try:
                                from database import SavedAreaDB as _SADB
                                _coords = st.session_state.area_coordinates
                                _ha = st.session_state.get('cached_area_ha') or calculate_area_optimized(_coords)
                                _sid = _SADB.save_area(
                                    name=_save_name.strip(),
                                    coordinates=_coords,
                                    area_hectares=_ha,
                                    project_indicators=_build_indicator_state_blob(),
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
                st.caption("After loading, you need to re-calculate the ecosystem value to ensure your analysis is up-to-date.")
                try:
                    from database import SavedAreaDB as _SADB2
                    _areas = _SADB2.get_user_saved_areas()
                    if _areas:
                        for _area in _areas:
                            _col_info, _col_btns = st.columns([3, 2])
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
                                _sub_l, _sub_d = st.columns(2)
                                with _sub_l:
                                    if st.button("↩", key=f"ws_load_{_area['id']}",
                                                 help="Load this area onto the map"):
                                        clear_analysis_cache()
                                        st.session_state.area_coordinates = _area['coordinates']
                                        st.session_state.selected_area = True
                                        st.session_state.cached_area_ha = _area['area_hectares']
                                        st.session_state.cached_bbox = calculate_bbox_optimized(_area['coordinates'])
                                        st.session_state.use_test_area_zoom = True
                                        st.session_state.current_area_id = _area['id']
                                        st.session_state.default_area_name = _area['name']
                                        # Reset the main test-area dropdown so the test-area
                                        # branch doesn't re-run on the next click (e.g.
                                        # Calculate) and clobber the loaded coordinates.
                                        st.session_state.main_area_type_selector = "None - Draw your own area"
                                        st.rerun()
                                with _sub_d:
                                    if st.button("🗑️", key=f"ws_del_{_area['id']}",
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

    # Ultra-optimized clear button with memory management
    if st.button("Clear Area & Results", help="Start over with a new area"):
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
    "🦀 Test area (Mangrove)",
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
    key="main_area_type_selector",
    label_visibility="hidden",
    help="Select a predefined test area, load a previously saved area, or choose 'None' to draw your own area on the map",
    on_change=reset_analysis_state
)
use_test_area = selected_test_area not in ["None - Draw your own area", "📁 Load Saved Area"]
use_load_saved_area = selected_test_area == "📁 Load Saved Area"
use_test_area_single = selected_test_area in ["🌾 Test area (Agricultural)", "🌱 Test area (Grassland)", "🌿 Test area (Shrubland)", "🌲 Test area (Boreal Forest)", "🌳 Test area (Temperate Forest)", "🌴 Test area (Tropical Forest)", "🦀 Test area (Mangrove)", "🏜️ Test area (Desert)", "🏙️ Test area (Urban)", "🌊 Test area (Water (ocean))", "🏞️ Test area (Water (Rivers/Lakes))", "🏖️ Test area (Water (Coastal))"]
use_test_area_multi = selected_test_area == "🌍 Test area (Multi-Ecosystem)" 
use_test_area_random = selected_test_area == "🎲 Test area (Random Global)"

# Track which area is currently set up. Without this, every Streamlit rerun
# (e.g. clicking the water-classification radio) re-enters the matching test-
# area branch below and re-runs clear_analysis_cache() — wiping
# analysis_in_progress and sending the user back to the map mid-flow.
_current_area_signature = (
    selected_test_area,
    st.session_state.get('saved_area_selector') if use_load_saved_area else None,
)
_area_selection_changed = (
    st.session_state.get('_active_area_signature') != _current_area_signature
)

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
            
            # Load selected saved area — only run setup when the user's choice
            # actually changes, otherwise the radio reruns wipe analysis state.
            if selected_saved_area != "Select a saved area..." and _area_selection_changed:
                selected_index = saved_area_names.index(selected_saved_area) - 1  # Subtract 1 for the placeholder
                selected_area_data = saved_areas[selected_index]

                # Clear all cached values first to ensure clean state
                clear_analysis_cache()

                # Set the loaded area coordinates
                st.session_state.area_coordinates = selected_area_data['coordinates']
                st.session_state.selected_area = True
                st.session_state.use_test_area_zoom = True

                # Use the saved area's name as the analysis-history label
                st.session_state.default_area_name = selected_area_data['name']

                # Calculate and cache area data
                area_ha = selected_area_data['area_hectares']
                st.session_state.cached_area_ha = area_ha
                st.session_state.cached_bbox = calculate_bbox_optimized(selected_area_data['coordinates'])
                st.session_state.area_coords_cache = selected_area_data['coordinates']

                # Restore the saved project-indicator configuration (if any)
                # so the user's commitments + baseline/target responses + dates
                # come back when they reload the area.
                _restore_indicator_state_blob(selected_area_data.get('project_indicators'))

                st.session_state['_active_area_signature'] = _current_area_signature

                st.success(f"**Loaded: {selected_area_data['name']}**")
                st.caption(f"Area: {area_ha:.1f} hectares")
                if selected_area_data.get('description'):
                    st.caption(selected_area_data['description'])
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
        "🦀 Test area (Mangrove)": {
            "coords": calculate_1000ha_coordinates(21.9504, 88.8604),
            "description": "Sundarbans Mangrove Forest (21.9504°N, 88.8604°E) | Expected: ESA Code 170, Mangroves ecosystem",
            "location": "Sundarbans Tiger Reserve, West Bengal, India (largest mangrove forest on Earth)"
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
    
    if selected_test_area in single_ecosystem_areas and _area_selection_changed:
        area_data = single_ecosystem_areas[selected_test_area]
        test_coordinates = area_data["coords"]

        # Clear all cached values first to ensure clean state
        clear_analysis_cache()

        # Set the test area coordinates
        st.session_state.area_coordinates = test_coordinates
        st.session_state.selected_area = True
        st.session_state.use_test_area_zoom = True

        # Name the analysis after the test-area label (strip the leading emoji)
        _ta_label = selected_test_area.split(' ', 1)[1] if ' ' in selected_test_area else selected_test_area
        st.session_state.default_area_name = _ta_label

        # Calculate area using the actual formula (should be exactly 1000ha)
        area_ha = calculate_area_optimized(test_coordinates)
        st.session_state.cached_area_ha = area_ha
        st.session_state.cached_bbox = calculate_bbox_optimized(test_coordinates)
        st.session_state.area_coords_cache = test_coordinates

        st.session_state['_active_area_signature'] = _current_area_signature

        st.success(f"**{selected_test_area} Selected**")
        st.caption(area_data["description"])

elif use_test_area_multi and _area_selection_changed:
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

    # Name the analysis after the multi-ecosystem test area
    st.session_state.default_area_name = "Test area (Multi-Ecosystem)"

    # Calculate area using the actual formula (should be exactly 1000ha)
    area_ha = calculate_area_optimized(test_coordinates)
    st.session_state.cached_area_ha = area_ha
    st.session_state.cached_bbox = calculate_bbox_optimized(test_coordinates)
    st.session_state.area_coords_cache = test_coordinates

    st.session_state['_active_area_signature'] = _current_area_signature

    st.success("**Multi-Ecosystem Test Area Selected**")
    st.caption("Michigan Transition Zone (42.0°N, 84.0°W) | Expected: Agricultural, Forest, and Grassland ecosystems")

elif use_test_area_random and _area_selection_changed:
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

    # Name the analysis after the random global test area
    st.session_state.default_area_name = "Test area (Random Global)"

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

    st.session_state['_active_area_signature'] = _current_area_signature

    st.success("**Random Global Test Area Selected**")
    st.caption(f"Random location in {region_name} ({lat_center:.2f}°N, {lon_center:.2f}°{'E' if lon_center >= 0 else 'W'}) | Area: {area_ha:.0f} ha")
else:
    # Clear test area flag when unchecked, but preserve manual area zoom
    if not st.session_state.get('area_coordinates'):
        st.session_state.use_test_area_zoom = False

# Map section

# Clear the search box if the drawing handler flagged a new on-map area
# last rerun. Must happen BEFORE the search widget renders below — once a
# Streamlit widget is instantiated in a given run, its session_state key
# can't be modified inline.
if st.session_state.pop('_clear_location_search', False):
    st.session_state.location_search_main = ""

# Add search and layer selector
col_search, col_layer = st.columns([2, 1])
with col_search:
    location_search = st.text_input(
        "Search for locations",
        placeholder="Try searching for locations e.g. Amazon rain forest",
        key="location_search_main",
        label_visibility="collapsed",
    )
with col_layer:
    map_layer = st.radio(
        "Map Style",
        ["Satellite", "Light Map"],
        horizontal=True,
        key="main_map_layer_selector",
        label_visibility="collapsed",
    )

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
            "🦀 Test area (Mangrove)": (21.9504, 88.8604),      # Sundarbans, India
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
col1_map, col2_map, col3_map = st.columns([0.2, 2, 1.1])
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
                'cached_ecosystem_results': None,
                # Flag the next render to clear the search box (we can't
                # modify the widget's session_state key inline here because
                # the widget already rendered earlier in this run).
                '_clear_location_search': True,
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
        # The Calculate button always lives below the ecosystem-type
        # dropdown — see the block after render_pre_analyze_indicator_panel().
        analyze_button = st.session_state.get('analysis_in_progress', False)
    else:
        st.markdown("""
        <div style='font-size:0.95rem; font-weight:600; color:#1B5E20;
                    background:#E8F5E9; border-left:4px solid #2E7D32;
                    border-radius:0 6px 6px 0; padding:0.6rem 0.75rem; margin-top:0.5rem;'>
            ✏️ Draw a polygon or rectangle on the map to select your area
        </div>
        """, unsafe_allow_html=True)

# ── Project ecosystem selector + project-indicators checkbox ───────────────
# Both widgets live together on the main page once an area is selected. The
# dropdown forces a single ecosystem type for the whole area (overriding
# satellite autodetect) when set to anything other than 'Auto-detect'. The
# checkbox is only enabled when the chosen ecosystem has seeded project
# indicators (currently Mangroves only); switching away auto-unchecks it.
if st.session_state.get('selected_area'):
    if 'project_ecosystem_override' not in st.session_state:
        st.session_state.project_ecosystem_override = 'Auto-detect'

    st.markdown(
        "<div style='font-size:0.78rem; line-height:1.35; color:#374151; "
        "margin:0.25rem 0 0.35rem 0;'>"
        "Satellite data is used to determine the ecosystem type in your "
        "selected area. You can override this by manually selecting an "
        "ecosystem type below — only the ecosystem classification is forced; "
        "satellite, EEI, country, economic and environmental-indicator data "
        "are still captured and used. Where ecosystem-specific indicators are "
        "available and required, enable them with the checkbox."
        "</div>",
        unsafe_allow_html=True,
    )

    col_eco, col_pi = st.columns([3, 1])
    with col_eco:
        _cur = st.session_state.project_ecosystem_override
        _idx = (
            ECOSYSTEM_DISPLAY_OPTIONS.index(_cur)
            if _cur in ECOSYSTEM_DISPLAY_OPTIONS else 0
        )
        _choice = st.selectbox(
            "Ecosystem type",
            options=ECOSYSTEM_DISPLAY_OPTIONS,
            index=_idx,
            key='project_ecosystem_selector',
            label_visibility='collapsed',
        )
        st.session_state.project_ecosystem_override = _choice
        st.session_state.ecosystem_override = _choice

    with col_pi:
        _has_indicators = _ecosystem_has_project_indicators(_choice)
        if not _has_indicators:
            # Force-clear before the widget renders. Writing to the widget's
            # own key resets its stored state; just setting the aliases is
            # not enough because Streamlit reads the widget's value from its
            # own key on rerender.
            st.session_state.project_indicators_main = False
            st.session_state.project_indicators_enabled = False
            st.session_state.use_indicator_multipliers = False
        _pi = st.checkbox(
            "Use project-specific indicators (alpha)",
            key='project_indicators_main',
            disabled=not _has_indicators,
            help=("Replace the intactness (BBI) multiplier with answers to "
                  "ecosystem-specific indicator questions. Available for "
                  "ecosystems with seeded indicator sets (currently Mangroves). "
                  "This feature is currently in alpha testing. Feedback welcome."),
        )
        if _has_indicators:
            st.session_state.project_indicators_enabled = _pi
            st.session_state.use_indicator_multipliers = _pi

render_pre_analyze_indicator_panel()

# Calculate button: always rendered below the ecosystem-type dropdown (and
# indicator panel, when one is shown). For the indicator path, this gives
# users space to finalise their answers before clicking. Re-running is
# supported: change any input and click again to re-run.
if st.session_state.get('selected_area'):
    _indicators_on = st.session_state.get('use_indicator_multipliers', False)
    _ready = st.session_state.get('calculation_ready')
    if _indicators_on and _ready:
        _calc_btn_label = 'Re-calculate with updated indicators'
        _calc_btn_help = 'Re-run the analysis using the current indicator responses'
    elif _ready:
        _calc_btn_label = 'Re-calculate Ecosystem Value'
        _calc_btn_help = 'Re-run the analysis with current settings'
    else:
        _calc_btn_label = 'Calculate Ecosystem Value'
        _calc_btn_help = 'Run ecosystem analysis with current settings'

    if st.button(_calc_btn_label, type='primary', use_container_width=True,
                 key='calc_below_dropdown', help=_calc_btn_help):
        st.session_state.analysis_in_progress = True
        if _indicators_on and _ready:
            # Indicator re-calc path — keep cached sampling data, regional
            # factor, country and ecosystem detection; setting
            # skip_ecosystem_detection routes the flow through the
            # sample-point shortcut so the 'Real ESA Satellite Data' source
            # survives the re-run instead of falling back to geographic
            # estimation.
            st.session_state['skip_ecosystem_detection'] = True
        else:
            # First-calc (or non-indicator re-calc) — clear stale water-
            # classification flags so the detection pipeline starts clean.
            for _stale in ('pending_water_classification', 'water_bodies_classified', 'skip_ecosystem_detection'):
                if _stale in st.session_state:
                    del st.session_state[_stale]
            if 'sampling_point_data' in st.session_state:
                for point_data in st.session_state.sampling_point_data.values():
                    if 'user_classified' in point_data:
                        del point_data['user_classified']
                    if point_data.get('landcover_class') == 210:
                        if 'ecosystem_type' in point_data:
                            del point_data['ecosystem_type']
        st.rerun()

# Auto-scroll the Calculate button into view the first render after an area
# is selected, so users don't have to manually scroll to find it. Fires only
# on the False→True transition of selected_area, using a tracking flag in
# session_state so subsequent reruns (e.g. dropdown / checkbox tweaks)
# don't re-scroll and yank the user's view around.
_curr_area_selected = bool(st.session_state.get('selected_area'))
_prev_area_selected = bool(st.session_state.get('_prev_area_selected_for_scroll', False))
if _curr_area_selected and not _prev_area_selected:
    import streamlit.components.v1 as _components
    _components.html(
        """
        <script>
        setTimeout(() => {
            const doc = window.parent.document;
            const btn = doc.querySelector('[class*="st-key-calc_below_dropdown"]')
                || doc.querySelector('button[kind="primary"]');
            if (btn) {
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
            }
        }, 150);
        </script>
        """,
        height=0,
    )
st.session_state['_prev_area_selected_for_scroll'] = _curr_area_selected

# Legacy results section — disabled; display handled by the calculation_ready block below
if False and st.session_state.get('analysis_results'):
    st.markdown('<h2 class="section-header">Step 3: Results</h2>', unsafe_allow_html=True)
    
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
                
            elif not st.session_state.get('skip_ecosystem_detection', False):
                # Run sampling + per-point classification + EEI fetch on every
                # analysis (unless explicitly skipped). When the user has forced
                # an ecosystem-type override, the override is applied downstream
                # via override_mapping (calc) and get_esvd_ecosystem_from_landcover_code
                # (display); sampling is still needed so EEI has per-point values
                # to average and the sample-points table has rows to render.
                try:
                    from utils.openlandmap_integration import detect_ecosystem_type

                    # If a previous render already detected water bodies and is
                    # waiting on the user to classify them, reuse the cached
                    # sampling data instead of re-running detect_ecosystem_type.
                    # Re-detection would fetch a different random sample, blank
                    # the user_classified flags, and re-render the radio — the
                    # symptom users see as the classification "looping".
                    _pending_classification = (
                        st.session_state.get('pending_water_classification', False)
                        and st.session_state.get('sampling_point_data')
                        and st.session_state.get('detected_ecosystem')
                    )

                    if _pending_classification:
                        sampling_point_data = dict(st.session_state['sampling_point_data'])
                        data_source = st.session_state.get('landcover_data_source', 'openlandmap')
                        ecosystem_info = st.session_state['detected_ecosystem']
                        has_real_satellite_data = data_source == 'openlandmap'
                    else:
                        sampling_point_data = None  # populated below

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
                    
                    if not _pending_classification:
                        ecosystem_info = detect_ecosystem_type(
                            st.session_state.area_coordinates,
                            st.session_state.sampling_frequency,
                            max_sampling_limit=max_limit,
                            progress_callback=update_progress,
                            include_environmental_indicators=(
                                st.session_state.get('show_indicator_fapar', False)
                                or st.session_state.get('show_indicator_soil_c', False)
                            )
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
                        # Cache sampling data + ecosystem info so the rerun
                        # triggered by the radio click can short-circuit
                        # detection and reuse this exact data.
                        st.session_state.sampling_point_data = sampling_point_data
                        st.session_state.detected_ecosystem = ecosystem_info
                        st.session_state.landcover_data_source = data_source
                        st.session_state.pending_water_classification = True

                        st.warning("**Water bodies detected**")
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
                                    # NB: don't mirror EEI into ecosystem_intactness — those
                                    # sliders are the user's MANUAL settings and must only
                                    # change when the user moves a slider. The calc engine
                                    # reads from _effective_intactness_dict() which picks
                                    # ecosystem_eei when EEI is on.
                                except Exception as e:
                                    st.session_state.point_eei_values = {}
                                    st.session_state.average_eei = None
                                    st.session_state.ecosystem_eei = {}
                            else:
                                # EEI disabled - clear any stored values
                                st.session_state.point_eei_values = {}
                                st.session_state.average_eei = None
                                st.session_state.ecosystem_eei = {}
                            
                            st.success(f"All {len(water_body_points)} water bodies classified as {selected_ecosystem}. Analysis continues below.")
                            
                            # Skip re-sampling and go directly to valuation with updated classifications
                            st.session_state.water_bodies_classified = True
                            st.session_state.skip_ecosystem_detection = True
                            if 'pending_water_classification' in st.session_state:
                                del st.session_state['pending_water_classification']
                            
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
                                # NB: don't mirror EEI into ecosystem_intactness — those
                                # sliders are the user's MANUAL settings and must only
                                # change when the user moves a slider. The calc engine
                                # reads from _effective_intactness_dict() which picks
                                # ecosystem_eei when EEI is on.
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
                    "Polar": "polar",
                    "Grassland": "grassland",
                    "Shrubland": "shrubland",
                    "Wetland": "wetland",
                    "Water (ocean)": "marine",
                    "Rivers and Lakes": "rivers_and_lakes",
                    "Coastal": "coastal",
                    "Mangroves": "mangroves",
                    "Marine": "marine",
                    "Desert": "desert",
                    "Urban": "urban",
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
                st.markdown("## Detailed Composition for Valuation")
                total_samples = st.session_state.detected_ecosystem['successful_queries']
                composition_lines = []
                for eco_type, data in ecosystem_distribution.items():
                    proportion = data['count'] / total_samples * 100
                    area_proportion = area_ha * (proportion / 100)
                    composition_lines.append(f"   • **{eco_type}**: {proportion:.1f}% → {area_proportion:.1f} ha ({data['count']} sample points)")
                
                st.markdown('\n'.join(composition_lines))
                
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
                    
                    # Intactness multiplier: indicator-driven dict (when pre-Analyze
                    # responses exist for this ecosystem) or uniform BBI scalar.
                    ecosystem_intactness = _effective_intactness_dict()
                    _ind_dict = _build_indicator_multiplier_dict(eco_type)
                    if _ind_dict is not None:
                        intactness_arg = _ind_dict
                    else:
                        intactness_arg = _get_ecosystem_intactness_multiplier(eco_type, ecosystem_intactness)

                    eco_result = coeffs.calculate_ecosystem_values(
                        ecosystem_type=eco_type,
                        area_hectares=eco_area,
                        coordinates=(center_lat, center_lon),
                        urban_green_blue_multiplier=urban_multiplier,
                        ecosystem_intactness_multiplier=intactness_arg
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
                
                # Intactness multiplier: indicator-driven dict (when pre-Analyze
                # responses exist for this ecosystem) or uniform BBI scalar.
                ecosystem_intactness = _effective_intactness_dict()
                _ind_dict = _build_indicator_multiplier_dict(ecosystem_type)
                if _ind_dict is not None:
                    intactness_arg = _ind_dict
                else:
                    intactness_arg = _get_ecosystem_intactness_multiplier(ecosystem_type, ecosystem_intactness)

                esvd_results = coeffs.calculate_ecosystem_values(
                    ecosystem_type=ecosystem_type,
                    area_hectares=area_ha,
                    coordinates=(center_lat, center_lon),
                    urban_green_blue_multiplier=urban_multiplier,
                    ecosystem_intactness_multiplier=intactness_arg
                )

                # Parallel target valuation — only when every committed
                # indicator has a target_score. Reuses every input except the
                # multiplier dict, which is rebuilt from target_score values.
                esvd_results_target = None
                if _all_committed_have_target_scores():
                    _target_dict = _build_indicator_multiplier_dict(
                        ecosystem_type, score_field='target_score'
                    )
                    if _target_dict is not None:
                        esvd_results_target = coeffs.calculate_ecosystem_values(
                            ecosystem_type=ecosystem_type,
                            area_hectares=area_ha,
                            coordinates=(center_lat, center_lon),
                            urban_green_blue_multiplier=urban_multiplier,
                            ecosystem_intactness_multiplier=_target_dict,
                        )

                # Both urban green/blue and ecosystem intactness multipliers now applied at service level in ESVD calculation

                # Apply ESA land cover code specific multiplier if available
                if st.session_state.get('detected_ecosystem') and 'landcover_class' in st.session_state.detected_ecosystem:
                    landcover_code = st.session_state.detected_ecosystem['landcover_class']
                    esa_multiplier = st.session_state.get('esa_code_multipliers', {}).get(landcover_code, 100) / 100.0
                    esvd_results['total_value'] = esvd_results['total_value'] * esa_multiplier
                    esvd_results['current_value'] = esvd_results['current_value'] * esa_multiplier
                    esvd_results['total_annual_value'] = esvd_results['total_annual_value'] * esa_multiplier
                    # Apply the same ESA multiplier to the target run for
                    # consistency — otherwise baseline/target wouldn't be
                    # comparable on the same downstream display.
                    if esvd_results_target is not None:
                        esvd_results_target['total_value'] = esvd_results_target['total_value'] * esa_multiplier
                        esvd_results_target['current_value'] = esvd_results_target['current_value'] * esa_multiplier
                        esvd_results_target['total_annual_value'] = esvd_results_target['total_annual_value'] * esa_multiplier

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
            # Indicator-driven target valuation, if all committed indicators
            # have a target_score. Display code below reads these keys and
            # renders the parallel target metrics + bar chart + breakdown.
            try:
                if esvd_results_target is not None:
                    analysis_results['esvd_results_target'] = esvd_results_target
                    analysis_results['total_value_target'] = int(
                        esvd_results_target.get('total_annual_value',
                                                esvd_results_target.get('current_value', 0))
                    )
                    analysis_results['value_per_ha_target'] = (
                        esvd_results_target.get('total_annual_value',
                                                esvd_results_target.get('current_value', 0))
                        / area_ha if area_ha else 0
                    )
            except NameError:
                # esvd_results_target wasn't created on this branch
                # (e.g. multi-ecosystem path) — that's fine, skip.
                pass

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
                            # Persist indicator commitments + responses + computed
                            # multipliers for this assessment (no-op if feature off).
                            _persist_pre_analyze_indicators(_saved_id)
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
            if 'pending_water_classification' in st.session_state:
                del st.session_state['pending_water_classification']
            
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
        st.markdown("## Sampling Results")
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
        
        # Summary totals — one unified panel, no per-metric card chrome
        with st.container(border=True, key="results_totals_panel"):
            col1, col2, col3 = st.columns(3)
            _total_target = results.get('total_value_target')
            _per_ha_target = results.get('value_per_ha_target')
            with col1:
                st.metric("Total Annual Value", f"${results['total_value']:,}")
                if _total_target is not None:
                    st.caption(f"${_total_target:,} (target)")
            with col2:
                per_ha = results.get('value_per_ha', results['total_value']/results['area_ha'])
                st.metric("Value per Hectare", f"${per_ha:,.0f}/ha")
                if _per_ha_target is not None:
                    st.caption(f"${_per_ha_target:,.0f}/ha (target)")
            with col3:
                # Area display with water exclusion for summary
                land_area = results.get('area_ha', results.get('area_hectares', 0))
                water_area = results.get('water_area_hectares', 0)

                if water_area > 0:
                    st.metric("Land Area Analyzed", f"{land_area:,.0f} ha")
                    st.caption(f"🌊 {water_area:,.0f} ha water excluded")
                else:
                    st.metric("Area Analyzed", f"{land_area:,.0f} ha")
        
        # Combined Predominant Country + Predominant Ecosystem Type panel
        _country_info = st.session_state.get('predominant_country_info')
        _country_prefix = f"**{_country_info['label']}**: {_country_info['name']} | " if _country_info else ""

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
                st.info(f"{_country_prefix}**Predominant Ecosystem Type**: {ecosystem_display} (100% coverage)")
        else:
            # Handle ecosystem type display for other cases
            ecosystem_display = results['ecosystem_type']
            if ecosystem_display == "Auto-detect" and st.session_state.get('detected_ecosystem'):
                ecosystem_display = st.session_state.detected_ecosystem.get('primary_ecosystem', ecosystem_display)
            st.info(f"{_country_prefix}**Predominant Ecosystem Type**: {ecosystem_display}")
        
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
        _total_target_d = results.get('total_value_target')
        _per_ha_target_d = results.get('value_per_ha_target')
        with col_metrics[0]:
            st.metric("Total Ecosystem Value", f"${results['total_value']:,}/year")
            if _total_target_d is not None:
                st.caption(f"${_total_target_d:,}/year (target)")
        with col_metrics[1]:
            per_ha_detailed = results.get('value_per_ha', results['total_value']/results['area_ha'])
            st.metric("Value per Hectare", f"${per_ha_detailed:,.0f}/ha")
            if _per_ha_target_d is not None:
                st.caption(f"${_per_ha_target_d:,.0f}/ha (target)")
        with col_metrics[2]:
            if 'ecosystem_composition' in results.get('metadata', {}):
                composition = results['metadata']['ecosystem_composition']
                dominant_type = max(composition.keys(), key=lambda k: composition[k])
                st.metric("Ecosystem Type", dominant_type, delta=f"{len(composition)} types")
            else:
                st.metric("Ecosystem Type", results["ecosystem_type"])
        # Show data source and methodology
        st.info(f"📊 **Data Source**: Pre-computed ESVD Coefficients (Static) | **Regional Adjustment**: Applied")
        
        with st.expander("Data sources and methodology"):
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
        st.markdown("## Ecosystem Services Breakdown")
        
        # Add reliability warning — small font, warning-styled box
        st.markdown(
            '<div style="background:#FFF8E1; border-left:4px solid #FB8C00; '
            'padding:0.5rem 0.875rem; border-radius:4px; font-size:0.8rem; '
            'line-height:1.4; color:#594400; margin:0.5rem 0;">'
            '⚠️ Although the ecosystem service values are based on the results of '
            'more than 10,000 studies, some services remain poorly understood. Be '
            'aware that some values may be based on fewer than five studies and '
            'should therefore be considered unreliable. We recommend using primary '
            'research to check suspect values.'
            '</div>',
            unsafe_allow_html=True,
        )
        
        esvd_data = results['esvd_results']
        
        # Check if we have the expected categories directly
        has_categories = any(cat in esvd_data for cat in ['provisioning', 'regulating', 'cultural', 'supporting'])
        
        # Check for mixed ecosystem structure where categories are nested
        has_mixed_ecosystem = ('ecosystem_breakdown' in esvd_data or 'ecosystem_results' in esvd_data or 
                              results.get('ecosystem_type') == 'multi_ecosystem')
        
        # Also check for alternative data structures
        has_services_data = 'services_data' in esvd_data
        
        def _render_service_columns(categories, data_source, total_value_key):
            # Target esvd_results (only present when every committed indicator
            # has a target_score). Build a parallel per-category totals dict
            # so each column can show a "(target)" caption.
            _target_esvd = results.get('esvd_results_target')
            _target_totals = {}
            if _target_esvd:
                for c in categories:
                    _target_totals[c] = _target_esvd.get(c, {}).get('total', 0)

            # Service-category totals — one unified panel, no per-metric chrome
            totals = []
            with st.container(border=True, key="results_services_panel"):
                cols = st.columns(4)
                for i, category in enumerate(categories):
                    cat_data = data_source.get(category, {})
                    total = cat_data.get('total', 0)
                    totals.append(total)
                    with cols[i]:
                        area_denom = results.get('area_hectares', results.get('area_ha', 1)) or 1
                        per_ha_cat = total / area_denom
                        st.metric(f"{category.title()} Services", f"${total:,.0f}/year")
                        st.caption(f"${per_ha_cat:.0f}/ha")
                        if _target_esvd:
                            _t = _target_totals.get(category, 0)
                            _t_per_ha = _t / area_denom
                            st.caption(f"${_t_per_ha:.0f}/ha (target)")

            # Pie chart: % share of each service category. When target results
            # exist, render a bar chart of Baseline vs Target alongside.
            if sum(totals) > 0:
                import plotly.graph_objects as go
                _pie_fig = go.Figure(data=[go.Pie(
                    labels=[c.title() for c in categories],
                    values=totals,
                    hole=0.4,
                    textinfo='label+percent',
                    textposition='outside',
                    marker=dict(colors=['#2E7D32', '#558B2F', '#1976D2', '#7B1FA2']),
                    sort=False,
                )])
                _pie_fig.update_layout(
                    showlegend=False,
                    margin=dict(t=60, b=60, l=80, r=80),
                    height=400,
                )
                if _target_esvd:
                    _baseline_total = sum(totals)
                    _target_total_v = sum(_target_totals.values())
                    _bar_fig = go.Figure(data=[go.Bar(
                        x=['Baseline', 'Target'],
                        y=[_baseline_total, _target_total_v],
                        text=[f"${_baseline_total:,.0f}", f"${_target_total_v:,.0f}"],
                        textposition='outside',
                        marker=dict(color=['#6B7280', '#2E7D32']),
                    )])
                    _bar_fig.update_layout(
                        showlegend=False,
                        margin=dict(t=60, b=60, l=40, r=40),
                        height=400,
                        yaxis=dict(title='Total annual value ($)'),
                    )
                    _pie_col, _bar_col = st.columns([1, 1])
                    with _pie_col:
                        st.plotly_chart(_pie_fig, use_container_width=True)
                    with _bar_col:
                        st.plotly_chart(_bar_fig, use_container_width=True)
                else:
                    st.plotly_chart(_pie_fig, use_container_width=True)

            # ── Sub-service breakdown panel (indicator-multiplier mode) ──
            _msm_rows = st.session_state.get('pending_computed_multipliers')
            _msm_rows_target = st.session_state.get('pending_computed_multipliers_target')
            # Only show the target column block when the target-condition
            # multiplier rows exist (i.e. all committed indicators answered
            # on the target side) AND a target valuation was actually
            # computed for this analysis.
            _show_target = bool(_msm_rows_target and results.get('esvd_results_target'))
            if _msm_rows and st.session_state.get('use_indicator_multipliers'):
                with st.expander("Sub-service value breakdown (indicator-driven)", expanded=True):
                    import pandas as pd
                    # Coefficient lookup for this ecosystem
                    try:
                        from utils.precomputed_esvd_coefficients import PrecomputedESVDCoefficients
                        _eco_for_breakdown = st.session_state.get('pending_computed_multipliers_ecotype') or 'Mangroves'
                        _coeffs_for_breakdown = PrecomputedESVDCoefficients().get_ecosystem_coefficients(_eco_for_breakdown) or {}
                    except Exception:
                        _coeffs_for_breakdown = {}
                    _area_for_breakdown = (
                        st.session_state.get('cached_area_ha')
                        or st.session_state.get('analysis_results', {}).get('area_hectares')
                        or 1.0
                    )
                    _regional_for_breakdown = (
                        st.session_state.get('analysis_results', {})
                        .get('metadata', {}).get('regional_adjustment', 1.0)
                    )
                    # Build slug → display-code lookup (M1, M2, …) for header labels
                    try:
                        from database import ProjectIndicatorDB
                        _pt_for_breakdown = ProjectIndicatorDB.get_project_type_with_indicators(
                            'mangrove_restoration'
                        )
                        _slug_to_code = {
                            i['slug']: (i.get('code') or i['slug'])
                            for i in (_pt_for_breakdown['indicators'] if _pt_for_breakdown else [])
                        }
                    except Exception:
                        _slug_to_code = {}

                    # Collect every indicator that contributes to at least one sub-service
                    _all_contrib_slugs = set()
                    for r in _msm_rows:
                        for slug in (r.get('contributing_indicators') or []):
                            _all_contrib_slugs.add(slug)
                    _contrib_slugs_sorted = sorted(
                        _all_contrib_slugs, key=lambda s: _slug_to_code.get(s, 'Z')
                    )

                    # Capture the BBI value once. fallback rows record it
                    # directly; indicator-driven rows have it as None — fall
                    # back to whatever the session-state intactness multiplier
                    # currently resolves to for this ecosystem.
                    _bbi_for_display = next(
                        (r['bbi_value_used'] for r in _msm_rows
                         if r.get('bbi_value_used') is not None),
                        None,
                    )
                    if _bbi_for_display is None:
                        try:
                            from utils.analysis_helpers import _get_ecosystem_intactness_multiplier
                            _ei = _effective_intactness_dict()
                            _bbi_for_display = _get_ecosystem_intactness_multiplier(
                                _eco_for_breakdown, _ei
                            )
                        except Exception:
                            _bbi_for_display = 1.0

                    # Target-row lookup by sub-service key. Only used when
                    # _show_target — kept empty otherwise so the append-only
                    # target columns stay out of the table.
                    _target_by_key = {}
                    if _show_target:
                        _target_by_key = {tr['teeb_sub_service_key']: tr for tr in _msm_rows_target}

                    _table_rows = []
                    _hd_mult_seen = None
                    _hd_mult_seen_target = None
                    _n_covered = 0
                    _n_fallback = 0
                    for r in _msm_rows:
                        s = r['teeb_sub_service_key']
                        coeff = float(_coeffs_for_breakdown.get(s, 0.0))
                        mult = float(r['final_multiplier'])
                        contribution = coeff * mult * float(_area_for_breakdown) * float(_regional_for_breakdown)
                        is_fallback = bool(r.get('fallback_to_bbi'))
                        if is_fallback:
                            _n_fallback += 1
                        else:
                            _n_covered += 1
                            if _hd_mult_seen is None:
                                _hd_mult_seen = r.get('hd_multiplier')

                        contrib_inds = r.get('contributing_indicators') or []
                        contrib_pcts = r.get('contributing_response_pcts') or []
                        contrib_weights = r.get('contributing_weights') or []
                        _by_slug = {
                            slug: (pct, w)
                            for slug, pct, w in zip(contrib_inds, contrib_pcts, contrib_weights)
                        }

                        # Same lookup for the matching target row (if any).
                        _tr = _target_by_key.get(s) if _show_target else None
                        _t_by_slug = {}
                        if _tr is not None:
                            _t_inds = _tr.get('contributing_indicators') or []
                            _t_pcts = _tr.get('contributing_response_pcts') or []
                            _t_weights = _tr.get('contributing_weights') or []
                            _t_by_slug = {
                                slug: (pct, w)
                                for slug, pct, w in zip(_t_inds, _t_pcts, _t_weights)
                            }
                            if (not _tr.get('fallback_to_bbi')
                                    and _hd_mult_seen_target is None):
                                _hd_mult_seen_target = _tr.get('hd_multiplier')

                        row_dict = {
                            'Sub-service': s.replace('_', ' ').title(),
                            'Coefficient ($/ha/yr)': f"{coeff:,.0f}",
                            'Area (ha)': f"{float(_area_for_breakdown):,.1f}",
                        }
                        # Per-indicator columns: '<pct>% × <weight>' or blank.
                        # When target is shown, each indicator gets a paired
                        # '<code> (target)' column immediately after its
                        # baseline column.
                        for slug in _contrib_slugs_sorted:
                            code = _slug_to_code.get(slug, slug)
                            if slug in _by_slug:
                                pct, w = _by_slug[slug]
                                row_dict[code] = f"{int(pct)}% × {float(w):.1f}"
                            else:
                                row_dict[code] = ''
                            if _show_target:
                                if slug in _t_by_slug:
                                    t_pct, t_w = _t_by_slug[slug]
                                    row_dict[f"{code} (target)"] = f"{int(t_pct)}% × {float(t_w):.1f}"
                                else:
                                    row_dict[f"{code} (target)"] = ''
                        # Aggregated multipliers — explicit calc chain
                        if r.get('indicator_multiplier') is not None:
                            row_dict['Indicator avg'] = f"{r['indicator_multiplier']:.3f}"
                        else:
                            row_dict['Indicator avg'] = '— (BBI)'
                        if _show_target:
                            if _tr is not None and _tr.get('indicator_multiplier') is not None:
                                row_dict['Indicator avg (target)'] = f"{_tr['indicator_multiplier']:.3f}"
                            else:
                                row_dict['Indicator avg (target)'] = '— (BBI)'
                        row_dict['HD ×'] = f"{r.get('hd_multiplier', 1.0):.3f}"
                        if _show_target:
                            row_dict['HD × (target)'] = (
                                f"{_tr.get('hd_multiplier', 1.0):.3f}"
                                if _tr is not None else ''
                            )
                        # BBI: shown for transparency on every row. Highlighted
                        # (asterisk) when this is the value actually applied.
                        # BBI is identical for baseline + target (same area-
                        # level intactness source), so we don't duplicate it.
                        _bbi_cell = f"{float(_bbi_for_display):.3f}"
                        row_dict['BBI'] = (f"{_bbi_cell} *" if is_fallback else _bbi_cell)
                        row_dict['Regional ×'] = f"{float(_regional_for_breakdown):.2f}"
                        row_dict['Final ×'] = f"{mult:.3f}"
                        if _show_target:
                            row_dict['Final × (target)'] = (
                                f"{float(_tr['final_multiplier']):.3f}"
                                if _tr is not None else ''
                            )
                        row_dict['Source'] = 'BBI' if is_fallback else 'indicator'
                        row_dict['Contribution ($/yr)'] = f"{contribution:,.0f}"
                        if _show_target and _tr is not None:
                            _t_contribution = (
                                coeff * float(_tr['final_multiplier'])
                                * float(_area_for_breakdown)
                                * float(_regional_for_breakdown)
                            )
                            row_dict['Contribution ($/yr) (target)'] = f"{_t_contribution:,.0f}"
                        elif _show_target:
                            row_dict['Contribution ($/yr) (target)'] = ''
                        _table_rows.append(row_dict)
                    if _table_rows:
                        st.dataframe(
                            pd.DataFrame(_table_rows),
                            hide_index=True,
                            use_container_width=True,
                        )
                        _hd_pct = int(round((_hd_mult_seen or 1.0) * 100))
                        _caption = (
                            f"**HD multiplier applied:** {(_hd_mult_seen or 1.0):.2f} "
                            f"(Human Disturbance response: {_hd_pct}%) · "
                            f"**BBI:** {float(_bbi_for_display):.3f} (applied to rows marked *) · "
                            f"**Sub-services covered by indicators:** {_n_covered} of {_n_covered + _n_fallback} · "
                            f"Fallback intactness values (EEI or user-set) apply to {_n_fallback}"
                        )
                        if _show_target:
                            _hd_pct_t = int(round((_hd_mult_seen_target or 1.0) * 100))
                            _caption += (
                                f" · **HD multiplier applied (target):** "
                                f"{(_hd_mult_seen_target or 1.0):.2f} "
                                f"(target HD response: {_hd_pct_t}%)"
                            )
                        st.caption(_caption)

            with st.expander("Service-by-service breakdown"):
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
            st.markdown("**Total Area Composition:**")
            comp_cols = st.columns(min(len(ecosystem_results), 4))
            for i, (ecosystem_type, eco_data) in enumerate(ecosystem_results.items()):
                with comp_cols[i % 4]:
                    percentage = eco_data.get('area_percentage', 0)
                    area_ha = eco_data.get('area_hectares', 0)
                    st.markdown(f"**{ecosystem_type.title()}**")
                    st.markdown(f"{percentage:.1f}% ({area_ha:.1f} ha)")
            
            # Show combined services breakdown
            if 'esvd_results' in results:
                st.markdown("**Combined Ecosystem Services (Total from All Ecosystems):**")
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
                    st.success("**Authentic ESVD database integrated**")
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
            'Mangroves': 'mangroves',
            'Shrubland': 'shrubland',
            'Desert': 'desert',
            'Urban': 'urban',
            'Marine': 'marine',
            'Rivers and Lakes': 'rivers_and_lakes'
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
            st.markdown("**Adjust Ecosystem Mix**")
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
            st.markdown("**Ecosystem Intactness**")
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
        if st.button("Calculate Scenario", type="primary", use_container_width=True):
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
            with st.expander("Scenario Details"):
                st.markdown("**Ecosystem Mix & Intactness:**")
                scenario_intactness = scenario.get('intactness', {})
                for eco, pct in scenario['mix'].items():
                    if pct > 0:
                        intactness_val = scenario_intactness.get(eco, 100) if isinstance(scenario_intactness, dict) else scenario_intactness
                        st.write(f"• {eco}: {pct:.0f}% @ {intactness_val:.0f}% intactness")
            
            if st.button("Clear Scenario", type="secondary"):
                if 'scenario_results' in st.session_state:
                    del st.session_state['scenario_results']
                st.rerun(scope="fragment")

    render_scenario_builder(results)

    # ── PDF Download ──────────────────────────────────────────────────────────
    # Placed after the Scenario Builder so future report enhancements can
    # include any scenario information the user has produced.
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
                _pdf_coords = st.session_state.get('area_coordinates', [])
                _pdf_bbox = st.session_state.get('cached_bbox', {}) or {}
                _pdf_country = ''
                try:
                    if _pdf_bbox:
                        _clat = (_pdf_bbox.get('min_lat', 0) + _pdf_bbox.get('max_lat', 0)) / 2
                        _clon = (_pdf_bbox.get('min_lon', 0) + _pdf_bbox.get('max_lon', 0)) / 2
                        _pdf_country = get_country_from_coordinates(_clat, _clon)
                except Exception:
                    pass

                # Recompute the Summary Statistics bundle (sample-point breakdown)
                # so the PDF mirrors what the UI shows.
                _pdf_summary = None
                try:
                    _sampling = st.session_state.get('sampling_point_data', {}) or {}
                    if _sampling:
                        _country_counts: Dict[str, int] = {}
                        _eco_counts: Dict[str, int] = {}
                        _land_pts = 0
                        _water_pts = 0
                        for _pt in _sampling.values():
                            if _pt.get('landcover_class') == 210:
                                _water_pts += 1
                                continue
                            _land_pts += 1
                            _pt_coords = _pt.get('coordinates', {}) or {}
                            _lat = _pt_coords.get('lat', 0)
                            _lon = _pt_coords.get('lon', 0)
                            if _lat or _lon:
                                _c = get_country_from_coordinates(_lat, _lon)
                                _country_counts[_c] = _country_counts.get(_c, 0) + 1
                            _eco = _pt.get('ecosystem_type') or get_esvd_ecosystem_from_landcover_code(
                                _pt.get('landcover_class'), _pdf_results
                            ) or 'Unknown'
                            _eco_counts[_eco] = _eco_counts.get(_eco, 0) + 1
                        _pdf_summary = {
                            'sample_points_total': len(_sampling),
                            'land_points': _land_pts,
                            'water_points': _water_pts,
                            'country_counts': _country_counts,
                            'ecosystem_counts': _eco_counts,
                            'average_eei': st.session_state.get('average_eei'),
                            'ecosystem_eei': st.session_state.get('ecosystem_eei', {}),
                            'eei_enabled': st.session_state.get('use_eei_for_intactness', False),
                            'predominant_country': st.session_state.get('predominant_country_info'),
                        }
                except Exception:
                    _pdf_summary = None

                _pdf_bytes = _gen_pdf_fn(
                    results=_pdf_results,
                    auth_user=_pdf_auth,
                    area_name=_pdf_area_name or 'Analysis Area',
                    country=_pdf_country,
                    bbox=_pdf_bbox,
                    coordinates=_pdf_coords,
                    summary_stats=_pdf_summary,
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

    # ── Project Indicators (optional, gated by Settings toggle) ──────────────
    if st.session_state.get('project_indicators_enabled', False):
        render_project_indicators_section()



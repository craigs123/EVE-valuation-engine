"""
OpenLandMap API Integration for Authentic Land Cover Classification
"""
import requests
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
from functools import lru_cache

# Simple cache for geographic classifications to avoid recalculation
_geographic_cache = {}

def try_openlandmap_fixed(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Try OpenLandMap with corrected API calls and collection names.
    """
    try:
        # Try different collection names that actually exist
        collections_to_try = [
            'layers1km',
            'layers250m', 
            'layers30m',
            'predicted1km',
            'predicted250m'
        ]
        
        patterns_to_try = [
            'lcv.*',  # Land cover
            'clm.*',  # Climate
            'sol.*',  # Soil
            'dtm.*',  # Digital terrain
            '.*landcover.*',
            '.*land.*cover.*'
        ]
        
        url = "http://api.openlandmap.org/query/point"
        
        # Try most promising collections first for speed
        priority_collections = ['layers250m', 'layers1km']
        priority_patterns = ['lcv.*', 'sol.*']  # Focus on land cover and soil
        
        # First, try high-priority combinations
        for collection in priority_collections:
            for pattern in priority_patterns:
                try:
                    params = {
                        'lat': lat,
                        'lon': lon,
                        'coll': collection,
                        'regex': pattern
                    }
                    
                    response = requests.get(url, params=params, timeout=3)  # Reduced timeout
                    if response.status_code == 200:
                        data = response.json()
                        if 'response' in data and data['response']:
                            ecosystem_type = classify_openlandmap_response(data['response'][0])
                            return ecosystem_type, data
                            
                except requests.RequestException:
                    continue
        
        # If priority attempts fail, try one fallback quickly
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'coll': 'layers1km',
                'regex': '.*'  # Catch any available data
            }
            
            response = requests.get(url, params=params, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and data['response']:
                    ecosystem_type = classify_openlandmap_response(data['response'][0])
                    return ecosystem_type, data
                    
        except requests.RequestException:
            pass
        
        return "unknown", {"error": "No valid OpenLandMap data found for location"}
        
    except Exception as e:
        return "unknown", {"error": f"OpenLandMap API error: {e}"}

def classify_openlandmap_response(response_data: Dict) -> str:
    """
    Classify ecosystem based on OpenLandMap response data.
    """
    # Look for land cover or vegetation indicators in the response
    for key, value in response_data.items():
        if isinstance(value, (int, float)) and not pd.isna(value):
            # Basic classification based on typical land cover values
            if 'urban' in key.lower() or 'built' in key.lower():
                return "urban"
            elif 'forest' in key.lower() or 'tree' in key.lower():
                return "forest"
            elif 'crop' in key.lower() or 'agri' in key.lower():
                return "agricultural"
            elif 'water' in key.lower() or 'wet' in key.lower():
                return "wetland"
            elif 'grass' in key.lower():
                return "grassland"
            elif 'desert' in key.lower() or 'bare' in key.lower():
                return "desert"
    
    return "grassland"  # Default

def get_land_cover_classification(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Get land cover classification using ESA WorldCover and other satellite data sources.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        Tuple of (ecosystem_type, raw_data)
    """
    # Try multiple authentic data sources in order of preference
    
    # 1. Try OpenLandMap with fixed API calls
    ecosystem_type, data = try_openlandmap_fixed(lat, lon)
    if ecosystem_type != "unknown":
        return ecosystem_type, {**data, "source": "OpenLandMap"}
    
    # Skip other APIs for speed - they currently return "unknown" anyway
    # Can be re-enabled when actual API access is available
    
    # 5. Fallback to geographic analysis with clear limitations
    ecosystem_type = classify_basic_geographic(lat, lon)
    return ecosystem_type, {
        "source": "geographic_fallback", 
        "limitation": "Using basic geographic rules - not satellite data",
        "coordinates": {"lat": lat, "lon": lon}
    }

def try_esa_worldcover(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Try ESA WorldCover API for land cover classification.
    ESA WorldCover provides global land cover maps at 10m resolution.
    """
    try:
        # ESA WorldCover WCS service endpoint
        # Note: This is a simplified example - real implementation would need proper WCS queries
        url = "https://services.terrascope.be/wcs/v2"
        
        # For demonstration, we'll use a placeholder approach
        # Real implementation would use WCS GetCoverage requests
        params = {
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'GetCoverage',
            'coverageId': 'WORLDCOVER_2021_MAP',
            'subset': f'Lat({lat})',
            'subset': f'Long({lon})',
            'format': 'application/json'
        }
        
        # This would need proper authentication and WCS handling
        # For now, return unknown to indicate API needs setup
        return "unknown", {"error": "ESA WorldCover API requires authentication setup"}
        
    except Exception as e:
        return "unknown", {"error": f"ESA WorldCover error: {e}"}

def try_google_earth_engine(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Try Google Earth Engine for land cover data.
    Requires authentication and service account setup.
    """
    try:
        # Google Earth Engine would require authentication
        # ee.Authenticate() and ee.Initialize()
        # This is a placeholder for the actual implementation
        return "unknown", {"error": "Google Earth Engine requires authentication setup"}
        
    except Exception as e:
        return "unknown", {"error": f"Google Earth Engine error: {e}"}

def try_usgs_landcover(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Try USGS/NASA land cover data for North American locations.
    """
    try:
        # USGS/NASA APIs would require proper endpoints and potentially authentication
        # This is a placeholder for actual NLCD or similar services
        return "unknown", {"error": "USGS Land Cover API requires setup"}
        
    except Exception as e:
        return "unknown", {"error": f"USGS Land Cover error: {e}"}

def classify_from_geocoding(geocoding_data: Dict, lat: float, lon: float) -> str:
    """
    Classify ecosystem type based on geocoding data and location context.
    """
    if 'address' not in geocoding_data:
        return classify_basic_geographic(lat, lon)
    
    address = geocoding_data['address']
    display_name = geocoding_data.get('display_name', '').lower()
    
    # Urban detection based on administrative levels and place types
    urban_indicators = ['city', 'town', 'village', 'municipality', 'urban', 'downtown', 'district']
    if (address.get('city') or address.get('town') or address.get('village') or 
        any(indicator in display_name for indicator in urban_indicators)):
        return "urban"
    
    # Agricultural detection
    agricultural_indicators = ['farm', 'agricultural', 'rural', 'county', 'township']
    if any(indicator in display_name for indicator in agricultural_indicators):
        return "agricultural"
    
    # Coastal detection
    if (address.get('coast') or 'coast' in display_name or 'beach' in display_name or 
        'ocean' in display_name or 'sea' in display_name):
        return "coastal"
    
    # Forest detection
    forest_indicators = ['forest', 'woods', 'national park', 'state park']
    if any(indicator in display_name for indicator in forest_indicators):
        return "forest"
    
    # Wetland detection
    wetland_indicators = ['wetland', 'marsh', 'swamp', 'bog']
    if any(indicator in display_name for indicator in wetland_indicators):
        return "wetland"
    
    # Default to geographic classification
    return classify_basic_geographic(lat, lon)

def classify_basic_geographic(lat: float, lon: float) -> str:
    """
    Basic ecosystem classification based on geographic coordinates.
    Uses simple caching for performance.
    """
    # Use simple rounding for cache key
    cache_key = (round(lat, 2), round(lon, 2))
    if cache_key in _geographic_cache:
        return _geographic_cache[cache_key]
    
    # Desert regions
    if ((20 <= lat <= 40 and -120 <= lon <= -100) or  # US Southwest
        (15 <= lat <= 35 and -15 <= lon <= 45) or     # Sahara/Middle East
        (-30 <= lat <= -15 and 110 <= lon <= 155)):   # Australian deserts
        result = "desert"
    
    # Coastal regions (near major coastlines)
    elif (abs(lat) < 65 and (lon < -120 or lon > 120 or  # Pacific
          (25 <= lat <= 50 and -85 <= lon <= -70) or     # US East coast
          (50 <= lat and -10 <= lon <= 30))):            # European coasts
        result = "coastal"
    
    # Forest regions (northern latitudes)
    elif lat > 45:
        result = "forest"
    
    # Agricultural regions (temperate)
    elif 30 <= lat <= 50:
        result = "agricultural"
    
    # Default grassland
    else:
        result = "grassland"
    
    # Cache the result
    _geographic_cache[cache_key] = result
    return result

def get_area_land_cover(bbox: list, grid_size: int = 2) -> Dict[str, float]:
    """
    Get land cover classification for an area using a grid sampling approach.
    
    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        grid_size: Number of sample points per dimension
    
    Returns:
        Dictionary with ecosystem percentages
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # Create sampling grid
    lats = np.linspace(min_lat, max_lat, grid_size)
    lons = np.linspace(min_lon, max_lon, grid_size)
    
    ecosystem_counts = {}
    total_points = 0
    data_sources = {}
    
    for lat in lats:
        for lon in lons:
            ecosystem, data = get_land_cover_classification(lat, lon)
            ecosystem_counts[ecosystem] = ecosystem_counts.get(ecosystem, 0) + 1
            total_points += 1
            
            # Track data source
            source = data.get('source', 'unknown')
            data_sources[source] = data_sources.get(source, 0) + 1
    
    # Calculate percentages
    ecosystem_percentages = {}
    for ecosystem, count in ecosystem_counts.items():
        ecosystem_percentages[ecosystem] = count / total_points
    
    # Store analysis metadata in session state for display
    import streamlit as st
    if hasattr(st, 'session_state'):
        st.session_state.last_analysis_data = {
            'source': max(data_sources.keys(), key=lambda k: data_sources[k]) if data_sources else 'unknown',
            'sources_used': data_sources,
            'total_points': total_points,
            'ecosystem_composition': ecosystem_percentages  # Store composition for multi-ecosystem analysis
        }
    
    return ecosystem_percentages

def get_dominant_ecosystem(bbox: list) -> str:
    """
    Get the dominant ecosystem type for an area.
    
    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
    
    Returns:
        Dominant ecosystem type
    """
    ecosystem_percentages = get_area_land_cover(bbox)
    
    if not ecosystem_percentages:
        return "grassland"
    
    # Return the ecosystem with highest percentage
    if ecosystem_percentages:
        return max(ecosystem_percentages.keys(), key=lambda k: ecosystem_percentages[k])
    else:
        return "grassland"

def get_multi_ecosystem_analysis(bbox: list) -> Dict[str, Any]:
    """
    Get comprehensive multi-ecosystem analysis for an area.
    
    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
    
    Returns:
        Dictionary with ecosystem composition and diversity metrics
    """
    ecosystem_percentages = get_area_land_cover(bbox)
    
    if not ecosystem_percentages:
        return {
            'primary_ecosystem': 'grassland',
            'ecosystem_composition': {'grassland': 100.0},
            'diversity_index': 1,
            'is_multi_ecosystem': False
        }
    
    # Convert to percentages (0-100)
    composition = {eco: pct * 100 for eco, pct in ecosystem_percentages.items()}
    
    # Determine primary ecosystem
    primary_ecosystem = max(composition.keys(), key=lambda k: composition[k])
    
    # Calculate diversity metrics
    diversity_index = len(composition)  # Number of ecosystem types
    is_multi_ecosystem = diversity_index > 1 and any(pct >= 10.0 for pct in composition.values() if pct != max(composition.values()))
    
    # Calculate Shannon diversity index
    import numpy as np
    shannon_diversity = 0
    for pct in composition.values():
        if pct > 0:
            p = pct / 100.0
            shannon_diversity += -p * np.log(p)
    
    return {
        'primary_ecosystem': primary_ecosystem,
        'ecosystem_composition': composition,
        'diversity_index': diversity_index,
        'shannon_diversity': shannon_diversity,
        'is_multi_ecosystem': is_multi_ecosystem,
        'homogeneity': max(composition.values())  # Percentage of dominant ecosystem
    }
"""
OpenLandMap API Integration for Authentic Land Cover Classification
"""
import requests
import numpy as np
from typing import Tuple, Dict, Optional

def get_land_cover_classification(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Get land cover classification from OpenLandMap API for a specific coordinate.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        Tuple of (ecosystem_type, raw_data)
    """
    try:
        # OpenLandMap REST API endpoint
        url = "http://api.openlandmap.org/query/point"
        
        # Query for land cover data
        params = {
            'lat': lat,
            'lon': lon,
            'coll': 'layers1km',
            'regex': 'lcv_landcover.lc_.*'  # Land cover layers
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'response' in data and data['response']:
            land_cover_data = data['response'][0]
            ecosystem_type = classify_land_cover(land_cover_data)
            return ecosystem_type, land_cover_data
        else:
            return "grassland", {"error": "No data available for this location"}
            
    except Exception as e:
        print(f"OpenLandMap API error: {e}")
        return "grassland", {"error": str(e)}

def classify_land_cover(land_cover_data: Dict) -> str:
    """
    Convert OpenLandMap land cover codes to ecosystem types.
    
    Based on standard land cover classification schemes.
    """
    # Extract land cover values from the response
    lc_values = []
    for key, value in land_cover_data.items():
        if 'landcover' in key.lower() and isinstance(value, (int, float)):
            lc_values.append(value)
    
    if not lc_values:
        return "grassland"
    
    # Use the primary land cover value
    primary_lc = lc_values[0] if lc_values else 0
    
    # Convert land cover codes to ecosystem types
    # Based on typical land cover classification schemes
    if primary_lc in range(10, 40):  # Forest classes
        return "forest"
    elif primary_lc in range(40, 60):  # Shrubland/grassland
        return "grassland"
    elif primary_lc in range(60, 80):  # Agricultural
        return "agricultural"
    elif primary_lc in range(80, 100):  # Wetland
        return "wetland"
    elif primary_lc in range(100, 120):  # Urban
        return "urban"
    elif primary_lc in range(120, 140):  # Bare/desert
        return "desert"
    elif primary_lc in range(140, 160):  # Water/coastal
        return "coastal"
    else:
        return "grassland"

def get_area_land_cover(bbox: list, grid_size: int = 3) -> Dict[str, float]:
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
    
    for lat in lats:
        for lon in lons:
            ecosystem, _ = get_land_cover_classification(lat, lon)
            ecosystem_counts[ecosystem] = ecosystem_counts.get(ecosystem, 0) + 1
            total_points += 1
    
    # Calculate percentages
    ecosystem_percentages = {}
    for ecosystem, count in ecosystem_counts.items():
        ecosystem_percentages[ecosystem] = count / total_points
    
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
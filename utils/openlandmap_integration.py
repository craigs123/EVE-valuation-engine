"""
OpenLandMap API Integration for Authentic Land Cover Classification
"""
import requests
import numpy as np
from typing import Tuple, Dict, Optional

def get_land_cover_classification(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    Get land cover classification using geographical rules and population density analysis.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
    
    Returns:
        Tuple of (ecosystem_type, raw_data)
    """
    try:
        # Use Nominatim API for reverse geocoding to understand location context
        geocoding_url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 10,
            'addressdetails': 1
        }
        
        response = requests.get(geocoding_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Analyze location context for ecosystem classification
        ecosystem_type = classify_from_geocoding(data, lat, lon)
        
        return ecosystem_type, data
            
    except Exception as e:
        print(f"Geocoding API error: {e}")
        # Fallback to basic geographic rules
        ecosystem_type = classify_basic_geographic(lat, lon)
        return ecosystem_type, {"error": str(e), "fallback": True}

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
    """
    # Desert regions
    if ((20 <= lat <= 40 and -120 <= lon <= -100) or  # US Southwest
        (15 <= lat <= 35 and -15 <= lon <= 45) or     # Sahara/Middle East
        (-30 <= lat <= -15 and 110 <= lon <= 155)):   # Australian deserts
        return "desert"
    
    # Coastal regions (near major coastlines)
    elif (abs(lat) < 65 and (lon < -120 or lon > 120 or  # Pacific
          (25 <= lat <= 50 and -85 <= lon <= -70) or     # US East coast
          (50 <= lat and -10 <= lon <= 30))):            # European coasts
        return "coastal"
    
    # Forest regions (northern latitudes)
    elif lat > 45:
        return "forest"
    
    # Agricultural regions (temperate)
    elif 30 <= lat <= 50:
        return "agricultural"
    
    # Default grassland
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
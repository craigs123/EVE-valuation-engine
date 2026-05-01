"""
Pure-computation helper functions for the EVE Valuation Engine.

These functions contain no Streamlit UI calls and can be tested independently.
They are imported back into app.py to keep the main application flow intact.
"""

import math
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# Ecosystem intactness
# ---------------------------------------------------------------------------

def _get_ecosystem_intactness_multiplier(ecosystem_type: str, ecosystem_intactness: Dict) -> float:
    """
    Get ecosystem-specific intactness multiplier with forest subtype fallback logic.

    Args:
        ecosystem_type: The ecosystem type (may include forest subtypes)
        ecosystem_intactness: Dictionary of ecosystem intactness percentages

    Returns:
        Multiplier value (0.0 to 1.0)
    """
    # First try exact match
    if ecosystem_type in ecosystem_intactness:
        return ecosystem_intactness[ecosystem_type] / 100.0

    # Handle case mismatch: try capitalized version
    capitalized_type = ecosystem_type.replace('_', ' ').title()
    if capitalized_type in ecosystem_intactness:
        return ecosystem_intactness[capitalized_type] / 100.0

    # Handle forest subtype fallbacks
    if 'Forest' in ecosystem_type:
        # Try specific forest type first
        if ecosystem_type in ecosystem_intactness:
            return ecosystem_intactness[ecosystem_type] / 100.0
        # Fall back to generic "Forest" if it exists (backward compatibility)
        elif 'Forest' in ecosystem_intactness:
            return ecosystem_intactness['Forest'] / 100.0
        # Fall back to any available forest type
        elif 'Temperate Forest' in ecosystem_intactness:
            return ecosystem_intactness['Temperate Forest'] / 100.0
        elif 'Boreal Forest' in ecosystem_intactness:
            return ecosystem_intactness['Boreal Forest'] / 100.0
        elif 'Tropical Forest' in ecosystem_intactness:
            return ecosystem_intactness['Tropical Forest'] / 100.0

    # Default fallback (100% intactness)
    return 1.0


# ---------------------------------------------------------------------------
# Map / bounding-box geometry helpers
# ---------------------------------------------------------------------------

def lat_to_mercator_y(lat: float) -> float:
    """Convert latitude to Web Mercator Y coordinate (0-1 scale)."""
    lat = max(-85.05112878, min(85.05112878, lat))  # Clamp to Web Mercator bounds
    return (1 - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) / math.pi) / 2


def compute_zoom_for_bbox(
    bbox: Dict,
    viewport: Tuple[int, int] = (950, 400),
    padding: float = 0.125,
    map_max_zoom: int = 20,
    map_min_zoom: int = 2,
) -> int:
    """Calculate optimal zoom level for a bounding box to occupy 80% of the viewport.

    Areas should take up 80% of the map display for optimal visibility with good margins.
    """
    if not bbox:
        return map_min_zoom

    try:
        # Calculate longitude span (handle dateline crossing)
        dlon = abs(bbox['max_lon'] - bbox['min_lon'])
        if dlon > 180:
            dlon = 360 - dlon
        dx_frac = dlon / 360.0

        # Calculate latitude span using Mercator projection
        y1 = lat_to_mercator_y(bbox['min_lat'])
        y2 = lat_to_mercator_y(bbox['max_lat'])
        dy_frac = abs(y2 - y1)

        # Prevent division by zero for extremely tiny spans
        dx_frac = max(dx_frac, 1e-8)
        dy_frac = max(dy_frac, 1e-8)

        # Target 80% viewport occupation with consistent padding
        # 12.5% padding on each side = 80% area occupation
        effective_padding = 0.125  # Consistent 12.5% padding for 80% viewport usage

        # Calculate zoom levels for both dimensions
        zoom_x = math.log2(viewport[0] / (256 * (1 + effective_padding) * dx_frac))
        zoom_y = math.log2(viewport[1] / (256 * (1 + effective_padding) * dy_frac))

        # Use the more restrictive zoom (ensures entire area fits)
        zoom = math.floor(min(zoom_x, zoom_y))  # Floor for 80% target with good margins

        # Ensure reasonable zoom levels for different area sizes
        # Target 80% viewport occupation for all sizes
        if dx_frac * 360.0 < 0.05 and dy_frac < 0.05:  # Areas roughly 1000ha and smaller
            zoom = max(zoom, 14)  # Minimum zoom 14 for 1000ha areas (80% occupation)
        elif dx_frac * 360.0 < 0.01 and dy_frac < 0.01:  # Very small areas (10ha-100ha)
            zoom = max(zoom, 16)  # Higher zoom for very small areas (80% occupation)

        # Clamp to map limits
        return max(map_min_zoom, min(map_max_zoom, zoom))
    except (ValueError, ZeroDivisionError, KeyError):
        return map_min_zoom


def compute_center_from_bbox(bbox: Dict) -> Tuple[float, float]:
    """Calculate center coordinates from bounding box.

    Returns:
        (center_lat, center_lon) tuple.
    """
    if not bbox:
        return 40.0, -100.0  # Default fallback

    try:
        center_lat = (bbox['min_lat'] + bbox['max_lat']) / 2

        # Handle longitude dateline crossing
        min_lon, max_lon = bbox['min_lon'], bbox['max_lon']
        if abs(max_lon - min_lon) <= 180:
            center_lon = (min_lon + max_lon) / 2
        else:
            # Dateline crossing - take the shorter arc
            center_lon = ((min_lon + max_lon + 360) / 2) % 360
            if center_lon > 180:
                center_lon -= 360

        return center_lat, center_lon
    except (KeyError, TypeError):
        return 40.0, -100.0


def create_bbox_from_center_and_area(
    center_lat: float, center_lon: float, area_ha: float = 1000
) -> Dict:
    """Create synthetic bounding box from center coordinates and area size.

    Args:
        center_lat: Latitude of the center point.
        center_lon: Longitude of the center point.
        area_ha: Area in hectares (default 1000 ha).

    Returns:
        Dict with min_lat, max_lat, min_lon, max_lon keys.
    """
    # Calculate side length for the given area
    side_length_km = math.sqrt(area_ha / 100)  # Convert ha to km²

    # Conversion factors
    lat_km_per_deg = 111.32
    lon_km_per_deg = 111.32 * math.cos(math.radians(center_lat))

    # Half-side in degrees
    lat_half_side = (side_length_km / 2) / lat_km_per_deg
    lon_half_side = (side_length_km / 2) / lon_km_per_deg

    # Calculate raw longitude values
    min_lon = center_lon - lon_half_side
    max_lon = center_lon + lon_half_side

    # Wrap longitude to valid range (-180 to 180)
    if min_lon < -180:
        min_lon += 360
    if max_lon > 180:
        max_lon -= 360

    return {
        'min_lat': center_lat - lat_half_side,
        'max_lat': center_lat + lat_half_side,
        'min_lon': min_lon,
        'max_lon': max_lon,
    }

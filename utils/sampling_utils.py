"""
Utility functions for working with sampling point data in the EVE Valuation Engine.
"""

from typing import List, Tuple


def extract_coordinates(sampling_point_data: dict) -> List[Tuple[str, float, float]]:
    """Returns list of (point_id, lat, lon) for all valid sampling points.

    A point is considered valid when it has a non-zero lat or lon value.

    Args:
        sampling_point_data: Dict mapping point_id to point data dicts.  Each
            point data dict is expected to contain a 'coordinates' sub-dict with
            'lat' and 'lon' keys.

    Returns:
        List of (point_id, lat, lon) tuples for every point that has valid
        (non-zero) coordinates.
    """
    results = []
    for point_id, point_data in sampling_point_data.items():
        coords = point_data.get('coordinates', {})
        if coords and isinstance(coords, dict):
            lat = coords.get('lat', 0)
            lon = coords.get('lon', 0)
            if lat != 0 or lon != 0:
                results.append((point_id, lat, lon))
    return results

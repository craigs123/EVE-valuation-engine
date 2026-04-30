"""
EEI (Ecosystem Ecological Integrity) API Client
Integrates with the EEI Explorer API to get ecosystem integrity metrics.

API Documentation: https://eei-explorer-1025191764754.us-central1.run.app/api
"""

import requests
import urllib3
from typing import List, Dict, Optional, Tuple
import logging
import google.auth.transport.requests
import google.oauth2.id_token

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

EEI_API_BASE_URL = "https://eei-explorer-1025191764754.us-central1.run.app"


def _get_headers() -> dict:
    try:
        auth_req = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, EEI_API_BASE_URL)
        return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    except Exception as e:
        logger.warning(f"Could not fetch identity token: {e}")
        return {"Content-Type": "application/json"}

def get_eei_batch(coordinates: List[Tuple[float, float]], timeout: int = 30) -> Dict:
    """
    Get EEI values for multiple coordinates (up to 10).
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        timeout: Request timeout in seconds
        
    Returns:
        Dict with 'results' (per-point values), 'averages', 'count', 'valid_count'
        or error dict on failure
    """
    if not coordinates:
        return {"error": "No coordinates provided", "results": [], "averages": None}
    
    if len(coordinates) > 10:
        coordinates = coordinates[:10]
        logger.warning(f"EEI API limited to 10 coordinates, truncating from {len(coordinates)}")
    
    payload = {
        "coordinates": [
            {"latitude": lat, "longitude": lon}
            for lat, lon in coordinates
        ]
    }
    
    try:
        response = requests.post(
            f"{EEI_API_BASE_URL}/api/eei-batch",
            json=payload,
            headers=_get_headers(),
            timeout=timeout,
            verify=False
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("EEI API request timed out")
        return {"error": "Request timed out", "results": [], "averages": None}
    except requests.exceptions.RequestException as e:
        logger.error(f"EEI API request failed: {e}")
        return {"error": str(e), "results": [], "averages": None}
    except Exception as e:
        logger.error(f"EEI API unexpected error: {e}")
        return {"error": str(e), "results": [], "averages": None}


def get_eei_single(latitude: float, longitude: float, timeout: int = 15) -> Dict:
    """
    Get EEI value for a single coordinate.
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        timeout: Request timeout in seconds
        
    Returns:
        Dict with 'values' containing eii, functional_integrity, structural_integrity, compositional_integrity
        or error dict on failure
    """
    payload = {
        "latitude": latitude,
        "longitude": longitude
    }
    
    try:
        response = requests.post(
            f"{EEI_API_BASE_URL}/api/eei-stats",
            json=payload,
            headers=_get_headers(),
            timeout=timeout,
            verify=False
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("EEI API request timed out")
        return {"error": "Request timed out", "values": None}
    except requests.exceptions.RequestException as e:
        logger.error(f"EEI API request failed: {e}")
        return {"error": str(e), "values": None}
    except Exception as e:
        logger.error(f"EEI API unexpected error: {e}")
        return {"error": str(e), "values": None}


def extract_eei_for_sample_points(sampling_point_data: Dict) -> Tuple[Dict[str, float], Optional[float]]:
    """
    Extract coordinates from sample points, call EEI API, and return per-point EEI values.
    
    Args:
        sampling_point_data: Dict of sample point data from EVE analysis
        
    Returns:
        Tuple of:
        - Dict mapping point_id to EEI value (0-1)
        - Average EEI value across all valid points (or None if no valid data)
    """
    coordinates = []
    point_ids = []
    
    for point_id, point_data in sampling_point_data.items():
        coords = point_data.get('coordinates', {})
        if coords and isinstance(coords, dict):
            lat = coords.get('lat', 0)
            lon = coords.get('lon', 0)
            if lat != 0 or lon != 0:
                coordinates.append((lat, lon))
                point_ids.append(point_id)
    
    if not coordinates:
        return {}, None
    
    eei_response = get_eei_batch(coordinates)
    
    if "error" in eei_response and eei_response.get("error"):
        logger.warning(f"EEI API returned error: {eei_response.get('error')}")
        return {}, None
    
    point_eei_values = {}
    results = eei_response.get('results', [])
    
    for i, result in enumerate(results):
        if i < len(point_ids):
            values = result.get('values', {})
            if values and values.get('eii') is not None:
                point_eei_values[point_ids[i]] = values.get('eii')
    
    averages = eei_response.get('averages', {})
    average_eei = averages.get('eii') if averages else None
    
    return point_eei_values, average_eei


def get_eei_per_ecosystem(sampling_point_data: Dict, point_eei_values: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate average EEI per ecosystem type from sample points.
    
    Args:
        sampling_point_data: Dict of sample point data from EVE analysis
        point_eei_values: Dict mapping point_id to EEI value
        
    Returns:
        Dict mapping ecosystem_type to average EEI value (0-1)
    """
    ecosystem_eei_sums = {}
    ecosystem_counts = {}
    
    for point_id, point_data in sampling_point_data.items():
        ecosystem_type = point_data.get('ecosystem_type', 'Unknown')
        eei_value = point_eei_values.get(point_id)
        
        if eei_value is not None:
            if ecosystem_type not in ecosystem_eei_sums:
                ecosystem_eei_sums[ecosystem_type] = 0
                ecosystem_counts[ecosystem_type] = 0
            ecosystem_eei_sums[ecosystem_type] += eei_value
            ecosystem_counts[ecosystem_type] += 1
    
    ecosystem_averages = {}
    for ecosystem_type, eei_sum in ecosystem_eei_sums.items():
        count = ecosystem_counts.get(ecosystem_type, 1)
        ecosystem_averages[ecosystem_type] = eei_sum / count if count > 0 else None
    
    return ecosystem_averages

"""
EEI (Ecosystem Ecological Integrity) API Client
Integrates with the EEI Explorer API to get ecosystem integrity metrics.

API Documentation: https://eve-solutions-482317.uc.r.appspot.com/api
"""

import requests
from typing import List, Dict, Optional, Tuple
import logging
import google.auth.transport.requests
import google.oauth2.id_token
from utils.sampling_utils import extract_coordinates

logger = logging.getLogger(__name__)

EEI_API_BASE_URL = "https://eve-solutions-482317.uc.r.appspot.com"


def _get_headers() -> dict:
    try:
        auth_req = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, EEI_API_BASE_URL)
        return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    except Exception as e:
        logger.warning(f"Could not fetch identity token: {e}")
        return {"Content-Type": "application/json"}


def _result_is_demo(result: Dict) -> bool:
    """
    Return True if a single per-point/region result is DEMO (fabricated) data.

    The EEI API can serve REAL Earth Engine data or fallback DEMO data
    (latitude-based estimates). The ONLY reliable demo signal is the explicit
    "demo_mode": true flag — the EEI service sets it on every fabricated
    result and never on a real Earth Engine response.

    A missing "source" field must NOT be treated as a demo signal: when the
    dataset has no pixel at a location (ocean / data gap) the EEI service
    returns a *real* "no data" response — values with null entries and a
    "message" — that legitimately carries neither "source" nor "demo_mode".
    Such a result is real (just empty), not demo.
    """
    if not isinstance(result, dict):
        return True
    return result.get("demo_mode") is True


def get_eei_batch(coordinates: List[Tuple[float, float]], timeout: int = 30) -> Dict:
    """
    Get EEI values for multiple coordinates (up to 100).

    Args:
        coordinates: List of (latitude, longitude) tuples
        timeout: Request timeout in seconds

    Returns:
        Dict with 'results' (per-point values), 'averages', 'count', 'valid_count'
        or error dict on failure
    """
    if not coordinates:
        return {"error": "No coordinates provided", "results": [], "averages": None}

    # The EEI API caps a batch at 100 coordinates. Truncate gracefully here
    # too so the request never trips the cap (the API would otherwise drop
    # the overflow itself). EVE's max sample count is 100, so this is a
    # belt-and-braces guard rather than a path normally hit.
    if len(coordinates) > 100:
        logger.warning(
            f"EEI batch capped at 100 coordinates, dropping "
            f"{len(coordinates) - 100} of {len(coordinates)}"
        )
        coordinates = coordinates[:100]

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
        )
        response.raise_for_status()
        data = response.json()
        # The API sets "truncated": true if it received >100 coordinates and
        # silently dropped the overflow. We pre-truncate above, so this should
        # not normally fire — but surface it if it ever does.
        if isinstance(data, dict) and data.get("truncated"):
            logger.warning("EEI API reported the batch was truncated server-side")
        return data
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
        )
        response.raise_for_status()
        data = response.json()
        # Annotate with a normalised demo flag so callers never mistake
        # fabricated fallback data for a real Earth Engine measurement.
        if isinstance(data, dict):
            data["is_demo"] = _result_is_demo(data)
            if data["is_demo"]:
                logger.warning(
                    f"EEI /api/eei-stats returned demo (fabricated) data for "
                    f"({latitude}, {longitude})"
                )
        return data
    except requests.exceptions.Timeout:
        logger.error("EEI API request timed out")
        return {"error": "Request timed out", "values": None}
    except requests.exceptions.RequestException as e:
        logger.error(f"EEI API request failed: {e}")
        return {"error": str(e), "values": None}
    except Exception as e:
        logger.error(f"EEI API unexpected error: {e}")
        return {"error": str(e), "values": None}


def extract_eei_for_sample_points(
    sampling_point_data: Dict,
) -> Tuple[Dict[str, float], Optional[float], Dict]:
    """
    Extract coordinates from sample points, call the EEI API, and return
    per-point EEI values — using REAL Earth Engine data only.

    DEMO (fabricated) results are detected per-point and discarded so that
    fake values can never flow into intactness defaults or the valuation.

    Args:
        sampling_point_data: Dict of sample point data from EVE analysis

    Returns:
        Tuple of:
        - Dict mapping point_id to EEI value (0-1), real non-null results only
        - Average EEI across the real non-null points (or None)
        - Status dict: keys 'total', 'real', 'demo', 'null', 'any_demo',
          'count_mismatch', 'error'
    """
    status = {
        "total": 0, "real": 0, "demo": 0, "null": 0,
        "any_demo": False, "count_mismatch": False, "error": None,
        "demo_point_ids": [],
    }

    valid_points = extract_coordinates(sampling_point_data)
    coordinates = [(lat, lon) for _, lat, lon in valid_points]
    point_ids = [point_id for point_id, _, _ in valid_points]
    status["total"] = len(point_ids)

    if not coordinates:
        return {}, None, status

    eei_response = get_eei_batch(coordinates)

    if eei_response.get("error"):
        logger.warning(f"EEI API returned error: {eei_response.get('error')}")
        status["error"] = eei_response.get("error")
        return {}, None, status

    results = eei_response.get('results', []) or []
    if len(results) != len(point_ids):
        logger.warning(
            f"EEI result count mismatch: sent {len(point_ids)}, "
            f"received {len(results)}"
        )
        status["count_mismatch"] = True

    # Top-level "demo_mode" only reflects whether Earth Engine initialised at
    # all. When it is true, EVERY result is demo. When it is false, an
    # individual result can STILL be a per-coordinate demo fallback, so each
    # result is also checked individually below.
    top_level_demo = eei_response.get("demo_mode") is True

    point_eei_values = {}
    for point_id, result in zip(point_ids, results):
        if top_level_demo or _result_is_demo(result):
            status["demo"] += 1
            status["demo_point_ids"].append(point_id)
            continue
        status["real"] += 1
        values = result.get('values', {}) or {}
        eii = values.get('eii')
        if eii is None:
            # Real data, but no dataset pixels at this location — not demo.
            status["null"] += 1
            continue
        point_eei_values[point_id] = eii

    status["any_demo"] = status["demo"] > 0

    # Average over REAL, non-null points only. The API's own top-level
    # "averages" block is deliberately NOT used: if any result was a demo
    # fallback it would silently fold fabricated values into the mean.
    if point_eei_values:
        average_eei = sum(point_eei_values.values()) / len(point_eei_values)
    else:
        average_eei = None

    if status["any_demo"]:
        logger.warning(
            f"EEI returned demo (fabricated) data for {status['demo']} of "
            f"{status['total']} points; demo values were discarded"
        )

    return point_eei_values, average_eei, status


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


# Conservative intactness (%) applied to an ecosystem whose EEI could not be
# measured because the service returned demo (fabricated) data. Used instead
# of the optimistic 100% default so demo coverage never inflates the valuation.
DEMO_FALLBACK_INTACTNESS_PCT = 50.0


def get_demo_affected_ecosystems(
    sampling_point_data: Dict,
    point_eei_values: Dict[str, float],
    demo_point_ids: List[str],
) -> List[str]:
    """
    Return the ecosystem types whose EEI could not be measured because the
    service returned demo (fabricated) data.

    An ecosystem qualifies only if it has at least one demo point AND no point
    with a real EEI value — i.e. there is no real EEI data to fall back on.
    Ecosystems that still have at least one real point keep their real
    (demo-free) average and are not included here.

    Args:
        sampling_point_data: Dict of sample point data from EVE analysis
        point_eei_values: Dict mapping point_id to REAL EEI value
        demo_point_ids: point_ids that returned demo data (eei_status)

    Returns:
        List of ecosystem_type names that should use the conservative
        demo-fallback intactness instead of the 100% default.
    """
    demo_set = set(demo_point_ids or [])
    eco_has_real = set()
    eco_has_demo = set()

    for point_id, point_data in sampling_point_data.items():
        ecosystem_type = point_data.get('ecosystem_type', 'Unknown')
        if point_id in point_eei_values:
            eco_has_real.add(ecosystem_type)
        elif point_id in demo_set:
            eco_has_demo.add(ecosystem_type)

    return sorted(eco_has_demo - eco_has_real)

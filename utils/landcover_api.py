"""
Backup landcover API client — calls the EEI Explorer app's
/api/landcover-batch endpoint, which wraps ESA WorldCover (10 m) via
Google Earth Engine.

Used **only** as a fallback when EVE's primary OpenLandMap STAC path is
unavailable. OpenLandMap is the free, default landcover source; GEE
calls cost money, so this client is wired behind the
_stac_asset_host_reachable() probe in utils/openlandmap_integration.py
and never fires when OpenLandMap is healthy.

The endpoint returns ESA CCI codes (server-side mapping from
WorldCover's native codes) so the response slots directly into EVE's
existing ecosystem-type taxonomy.
"""

import logging
from typing import List, Dict, Tuple, Optional

import requests
import google.auth.transport.requests
import google.oauth2.id_token

logger = logging.getLogger(__name__)

# Same App Engine host as the EEI API — landcover-batch is co-located.
LANDCOVER_API_BASE_URL = "https://eve-solutions-482317.uc.r.appspot.com"

# Endpoint cap — the EEI app truncates oversized batches but EVE never
# sends more than ~100 sample points anyway. Mirrors EEI's cap.
MAX_BATCH_COORDINATES = 100


def _get_headers() -> dict:
    """Identity-token auth, same pattern as utils/eei_api.py."""
    try:
        auth_req = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, LANDCOVER_API_BASE_URL)
        return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    except Exception as e:
        logger.warning(f"Could not fetch identity token for landcover-batch: {e}")
        return {"Content-Type": "application/json"}


def get_landcover_batch(
    coordinates: List[Tuple[float, float]],
    timeout: int = 30,
) -> Optional[Dict]:
    """Look up landcover for a batch of (lat, lon) coordinates.

    Args:
        coordinates: list of (latitude, longitude) tuples
        timeout: request timeout in seconds

    Returns:
        On success: dict with 'results' (per-coord landcover entries),
            'count', 'source'. Per-result keys: 'latitude', 'longitude',
            'worldcover_code', 'landcover_code' (ESA CCI), 'ecosystem_type'.
        On failure: None — callers fall through to the next backup tier
        (USGS / Copernicus / geographic). We return None rather than
        raise so the analysis pipeline keeps running.
    """
    if not coordinates:
        return None

    # Belt-and-braces — server also caps, but trim here so the wire payload
    # stays small and matches our internal sample-point limit.
    if len(coordinates) > MAX_BATCH_COORDINATES:
        logger.warning(
            f"Landcover batch capped at {MAX_BATCH_COORDINATES} coordinates, "
            f"dropping {len(coordinates) - MAX_BATCH_COORDINATES} of {len(coordinates)}"
        )
        coordinates = coordinates[:MAX_BATCH_COORDINATES]

    payload = {
        "coordinates": [
            {"latitude": lat, "longitude": lon}
            for lat, lon in coordinates
        ]
    }

    try:
        response = requests.post(
            f"{LANDCOVER_API_BASE_URL}/api/landcover-batch",
            json=payload,
            headers=_get_headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("truncated"):
            logger.warning("Landcover batch API reported server-side truncation")
        return data
    except requests.exceptions.Timeout:
        logger.error("Landcover batch API timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Landcover batch API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Landcover batch unexpected error: {e}")
        return None

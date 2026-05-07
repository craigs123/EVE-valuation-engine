"""
SoilGrids 2.0 REST API client (ISRIC).

API: https://rest.isric.org/soilgrids/v2.0/properties/query
Data: 250m global soil property maps, CC BY 4.0.

The API is in beta and subject to downtime. All public functions are
designed to fail soft: on any error, per-property values come back as
None and the caller renders a fallback string.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

SOILGRIDS_BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

PROPERTIES = ("phh2o", "soc", "bdod", "nitrogen")
DEPTH = "0-5cm"

# Display metadata for each property (used by the UI to format values).
PROPERTY_DISPLAY = {
    "phh2o":    {"label": "pH (H2O)",        "units": "",        "decimals": 1},
    "soc":      {"label": "SOC",             "units": "g/kg",    "decimals": 1},
    "bdod":     {"label": "Bulk Density",    "units": "g/cm³",   "decimals": 2},
    "nitrogen": {"label": "Nitrogen",        "units": "g/kg",    "decimals": 2},
}

REQUEST_TIMEOUT = 15
MAX_WORKERS = 5


def _round_coord(value: float) -> float:
    # SoilGrids has a 250m native resolution; rounding to 3 decimals (~110m)
    # collapses adjacent sample points to the same cache key without losing
    # spatial fidelity below the source resolution.
    return round(float(value), 3)


@lru_cache(maxsize=4096)
def _fetch_point_cached(lat_r: float, lon_r: float) -> Tuple[Tuple[str, Optional[float]], ...]:
    """Cached single-point fetch keyed on rounded coordinates.

    Returns a tuple of (property, value-in-natural-units-or-None) pairs so
    the result is hashable and lru_cache-friendly.
    """
    params: List[Tuple[str, str]] = [
        ("lon", f"{lon_r}"),
        ("lat", f"{lat_r}"),
        ("depth", DEPTH),
        ("value", "mean"),
    ]
    for prop in PROPERTIES:
        params.append(("property", prop))

    try:
        response = requests.get(SOILGRIDS_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.Timeout:
        logger.warning("SoilGrids timeout for (%s, %s)", lat_r, lon_r)
        return tuple((p, None) for p in PROPERTIES)
    except requests.exceptions.RequestException as e:
        logger.warning("SoilGrids request failed for (%s, %s): %s", lat_r, lon_r, e)
        return tuple((p, None) for p in PROPERTIES)
    except ValueError as e:
        logger.warning("SoilGrids returned invalid JSON for (%s, %s): %s", lat_r, lon_r, e)
        return tuple((p, None) for p in PROPERTIES)

    return tuple((p, _extract_value(payload, p)) for p in PROPERTIES)


def _extract_value(payload: dict, prop: str) -> Optional[float]:
    """Pull the 0-5cm mean for `prop` out of a SoilGrids response and
    convert from mapped units to natural units using the response's d_factor.
    """
    try:
        layers = payload.get("properties", {}).get("layers", []) or []
        for layer in layers:
            if layer.get("name") != prop:
                continue
            d_factor = layer.get("unit_measure", {}).get("d_factor") or 1
            for depth in layer.get("depths", []) or []:
                if depth.get("label") != DEPTH:
                    continue
                mean = depth.get("values", {}).get("mean")
                if mean is None:
                    return None
                return float(mean) / float(d_factor)
        return None
    except (TypeError, ValueError, AttributeError) as e:
        logger.warning("SoilGrids value extraction failed for %s: %s", prop, e)
        return None


def get_soil_properties(lat: float, lon: float) -> Dict[str, Optional[float]]:
    """Fetch the four soil properties at 0-5cm for one point.

    Returns a dict mapping property name to value in natural units, or to
    None for any property that could not be retrieved.
    """
    pairs = _fetch_point_cached(_round_coord(lat), _round_coord(lon))
    return dict(pairs)


def get_soil_properties_batch(
    coordinates: List[Tuple[float, float]],
) -> Dict[Tuple[float, float], Dict[str, Optional[float]]]:
    """Fetch soil properties for many points concurrently.

    Returns a dict keyed on the original (lat, lon) tuples. Missing points
    (all properties None) indicate the API was unavailable for that point.
    """
    if not coordinates:
        return {}

    results: Dict[Tuple[float, float], Dict[str, Optional[float]]] = {}
    workers = min(MAX_WORKERS, len(coordinates))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_coord = {
            executor.submit(get_soil_properties, lat, lon): (lat, lon)
            for lat, lon in coordinates
        }
        for future in as_completed(future_to_coord):
            coord = future_to_coord[future]
            try:
                results[coord] = future.result()
            except Exception as e:
                logger.warning("SoilGrids batch worker failed for %s: %s", coord, e)
                results[coord] = {p: None for p in PROPERTIES}
    return results


def format_value(prop: str, value: Optional[float]) -> str:
    """Format a single property value for table display."""
    if value is None:
        return "—"
    meta = PROPERTY_DISPLAY.get(prop, {"decimals": 2, "units": ""})
    decimals = meta["decimals"]
    units = meta["units"]
    formatted = f"{value:.{decimals}f}"
    return f"{formatted} {units}".strip() if units else formatted

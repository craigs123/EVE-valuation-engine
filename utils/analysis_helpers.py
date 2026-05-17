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


# ---------------------------------------------------------------------------
# Ecological Return on Investment (EROI)
# ---------------------------------------------------------------------------

# Appraisal horizon (years) for the discounted EROI metrics. Ecosystem-service
# uplift is treated as perpetual once a site reaches its target state; 30 years
# is the window over which NPV and the benefit-cost ratio are reported.
EROI_APPRAISAL_HORIZON_YEARS = 30


def _npv(rate: float, cashflows: list) -> float:
    """Net present value of ``cashflows``, where ``cashflows[t]`` falls at the
    end of year ``t`` (``cashflows[0]`` at t0, undiscounted)."""
    return sum(cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows))


def _irr(cashflows: list) -> "float | None":
    """Internal rate of return via bisection.

    ``cashflows[0]`` is the t0 outflow (negative); the rest are annual inflows.
    Returns None when the flows do not change sign or no root is bracketed.
    NPV is monotonic in the rate for this one-outflow/many-inflow shape, so
    bisection is robust.
    """
    if not cashflows:
        return None
    if all(cf >= 0 for cf in cashflows) or all(cf <= 0 for cf in cashflows):
        return None
    lo, hi = -0.9, 10.0
    f_lo = _npv(lo, cashflows)
    f_hi = _npv(hi, cashflows)
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    if f_lo * f_hi > 0:
        return None  # root not bracketed in the search range
    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = _npv(mid, cashflows)
        if abs(f_mid) < 1e-6 or (hi - lo) < 1e-12:
            return mid
        if f_lo * f_mid < 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0


def compute_eroi(baseline_value, target_value, cost, duration_years,
                 discount_rate, maintenance_cost: float = 0.0,
                 horizon: int = EROI_APPRAISAL_HORIZON_YEARS):
    """Flow-based Ecological Return on Investment metrics.

    Ecosystem-service valuations are annual *flows* (Int$/yr), not stocks. A
    restoration project lifts the annual flow from ``baseline_value`` to
    ``target_value``; the uplift ``U = target - baseline`` is a permanent
    annual flow once the target state is reached. ``duration_years`` is the
    linear ramp period (the gap between the baseline and target dates) over
    which the uplift grows from 0 to U; after the ramp it continues at U for
    the remainder of the appraisal ``horizon``.

    ``maintenance_cost`` is an optional ongoing annual cost that begins the
    year *after* the ramp completes (i.e. after the project has ended) — the
    upfront ``cost`` is assumed to cover the works during the project itself.

    Args:
        baseline_value:   baseline annual ecosystem-service value (Int$/yr)
        target_value:     target annual ecosystem-service value (Int$/yr)
        cost:             one-time capital cost (Int$), incurred at t0
        duration_years:   ramp years; None or 0 -> immediate full uplift
        discount_rate:    annual discount rate as a fraction (e.g. 0.035)
        maintenance_cost: ongoing annual maintenance cost (Int$/yr), applied
                          after the ramp ends; 0 to disable
        horizon:          appraisal horizon in years

    Returns:
        dict of metrics, or None when EROI does not apply (missing baseline or
        target valuation, cost <= 0, or no positive uplift).
    """
    if baseline_value is None or target_value is None:
        return None
    if not cost or cost <= 0:
        return None
    uplift = target_value - baseline_value
    if uplift <= 0:
        return None

    rate = discount_rate or 0.0
    horizon = int(horizon)
    ramp = duration_years if (duration_years and duration_years > 0) else 0.0
    maint = maintenance_cost or 0.0

    # Per-year uplift (midpoint of the year on the linear ramp, capped at the
    # full uplift) and maintenance (begins the year after the ramp ends; with
    # no ramp it applies from year 1).
    yearly_uplift = []
    yearly_maint = []
    for t in range(1, horizon + 1):
        frac = 1.0 if ramp <= 0 else min((t - 0.5) / ramp, 1.0)
        yearly_uplift.append(uplift * frac)
        yearly_maint.append(maint if t > ramp else 0.0)

    def _pv(stream):
        return sum(v / (1.0 + rate) ** (i + 1) for i, v in enumerate(stream))

    pv_benefits = _pv(yearly_uplift)
    pv_maintenance = _pv(yearly_maint)
    pv_costs = cost + pv_maintenance
    cum_benefit = sum(yearly_uplift)
    npv = pv_benefits - pv_costs
    bcr = pv_benefits / pv_costs                 # benefits / all costs
    net_annual = uplift - maint                  # mature net annual benefit
    annual_yield = net_annual / cost             # fraction per year

    # Undiscounted, ramp-aware payback on the NET stream (uplift - maintenance).
    payback_years = None
    running = 0.0
    for i in range(horizon):
        net_v = yearly_uplift[i] - yearly_maint[i]
        prev = running
        running += net_v
        if running >= cost:
            payback_years = (i + (cost - prev) / net_v) if net_v > 0 else float(i + 1)
            break

    irr = _irr([-cost] + [yearly_uplift[i] - yearly_maint[i]
                          for i in range(horizon)])

    return {
        'uplift': uplift,
        'maintenance_cost': maint,
        'net_annual': net_annual,
        'cost': cost,
        'duration_years': duration_years,
        'discount_rate': rate,
        'horizon_years': horizon,
        'pv_benefits': pv_benefits,
        'pv_maintenance': pv_maintenance,
        'pv_costs': pv_costs,
        'cum_benefit': cum_benefit,
        'npv': npv,
        'bcr': bcr,
        'annual_yield': annual_yield,
        'payback_years': payback_years,
        'irr': irr,
    }

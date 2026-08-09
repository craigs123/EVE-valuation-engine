"""
Pure-computation helper functions for the EVE Valuation Engine.

These functions contain no Streamlit UI calls and can be tested independently.
They are imported back into app.py to keep the main application flow intact.
"""

import math
import re
from typing import Dict, List, Optional, Sequence, Tuple


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
# User-entered polygon coordinates
# ---------------------------------------------------------------------------

# Users type/paste latitude first (the order coordinates are normally quoted in
# and the order the on-screen "Selected area" readout uses), but the rest of the
# engine works in GeoJSON [lon, lat] order — so these two helpers are the single
# conversion point between the two conventions.

_COORD_SPLIT_RE = re.compile(r'[\s,]+')

# Every coordinate the user types or reads is held to this many decimal places.
#
# 0.0001° is ~11.1 m of latitude, and 11.1 m down to ~5.6 m of longitude
# between the equator and 60°. That matches the 10 m ESA WorldCover backup —
# the finest layer EVE reads — and sits well inside the 250 m OpenLandMap
# pixels that drive a normal analysis, so a 5th decimal place cannot change
# which pixel gets sampled. It would only imply a precision the results do not
# have. `_get_ecosystem_type_cached` in utils/openlandmap_stac_api.py already
# quantises its cache key to the same 4 dp for exactly this reason.
COORD_DP = 4


def round_coord(value: float) -> float:
    """Snap one latitude or longitude to EVE's working precision (see COORD_DP)."""
    return round(float(value), COORD_DP)


def format_latlon(lat: float, lon: float, sep: str = ", ") -> str:
    """Render one (lat, lon) pair at EVE's working precision, latitude first."""
    return f"{float(lat):.{COORD_DP}f}{sep}{float(lon):.{COORD_DP}f}"


def format_points_as_text(points: Sequence[Sequence[float]]) -> str:
    """Render (lat, lon) points as the one-per-line text the entry box shows.

    Written at the same precision :func:`parse_coordinate_lines` reads back, so
    the entry box round-trips exactly: what a user sees is what is stored, and
    re-saving an untouched list cannot silently move the polygon.
    """
    return "\n".join(format_latlon(lat, lon) for lat, lon in points)


def parse_latlon_search(text: str) -> Tuple[Optional[Tuple[float, float]], Optional[str]]:
    """Interpret a search-box entry as a single 'latitude, longitude' pair.

    Lets the location search accept typed coordinates as well as place names.

    The result is held to :data:`COORD_DP` decimal places: longer entries are
    rounded to it, and shorter ones are taken at face value with the missing
    places read as zeros — ``51.5, -0.1`` means exactly ``51.5000, -0.1000``,
    not "somewhere in that band". Whole numbers are fine too.

    Rounding a long entry and rejecting a short one are different things, and
    only the first is wanted. Do not add a minimum-precision check here: a
    short entry is a valid point, just a coarser one, and refusing it would
    break a normal way of typing a rough location.

    Returns:
        ``(point, None)`` when the text is a usable coordinate pair;
        ``(None, hint)`` when it clearly means to be coordinates but is out of
        range, so the caller can explain rather than geocode nonsense; and
        ``(None, None)`` when it is not coordinates at all, which the caller
        should treat as a place name.
    """
    cleaned = (text or '').strip().strip('[]()').strip()
    if not cleaned:
        return None, None

    parts = [p for p in _COORD_SPLIT_RE.split(cleaned) if p]
    if len(parts) != 2:
        return None, None  # A place name, not a coordinate pair

    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        return None, None  # e.g. "New York" — two words, not two numbers

    if not -90.0 <= lat <= 90.0:
        # A reversed pair is the usual cause, and is worth naming: longitude
        # ranges beyond 90 while latitude cannot, so the swap is detectable.
        if -90.0 <= lon <= 90.0 and -180.0 <= lat <= 180.0:
            # Offered at working precision — it is a value to retype.
            return None, (
                f"Latitude must be between -90 and 90. Did you mean "
                f"{format_latlon(lon, lat)} — latitude first?"
            )
        return None, f"Latitude {lat} is outside the valid range -90 to 90."

    if not -180.0 <= lon <= 180.0:
        return None, f"Longitude {lon} is outside the valid range -180 to 180."

    return (round_coord(lat), round_coord(lon)), None


def parse_coordinate_lines(text: str) -> Tuple[List[Tuple[float, float]], Optional[str]]:
    """Parse 'lat, lon' lines into (lat, lon) points, with no minimum count.

    Lenient about formatting: accepts comma, semicolon or whitespace separators,
    blank lines, and surrounding brackets/parens, so a pasted ``[51.5, -0.12]``
    works as-is. As in :func:`parse_latlon_search`, points are held to
    :data:`COORD_DP` decimal places — longer entries rounded, shorter ones read
    with the missing places as zeros rather than rejected. This is the read
    half of the entry box's round trip; :func:`format_points_as_text` writes at
    the same precision so an untouched list re-saves unchanged. Used for the
    live preview, where a part-typed list is normal;
    :func:`parse_polygon_coordinates` adds the polygon-level rules on top.

    Args:
        text: Raw text from the coordinate entry box.

    Returns:
        ``(points, None)`` on success or ``([], error_message)`` on failure.
    """
    if not text or not text.strip():
        return [], None

    # Semicolons are treated as line breaks so single-line pastes also work.
    raw_lines = text.replace(';', '\n').splitlines()

    points: List[Tuple[float, float]] = []
    for line_no, raw_line in enumerate(raw_lines, start=1):
        cleaned = raw_line.strip().strip('[]()').strip()
        cleaned = cleaned.strip(',').strip()
        if not cleaned:
            continue

        parts = [p for p in _COORD_SPLIT_RE.split(cleaned) if p]
        if len(parts) != 2:
            return [], (
                f"Line {line_no}: expected 'latitude, longitude' "
                f"(two numbers), got '{raw_line.strip()}'."
            )

        try:
            lat = float(parts[0])
            lon = float(parts[1])
        except ValueError:
            return [], (
                f"Line {line_no}: '{raw_line.strip()}' is not a pair of numbers. "
                "Use decimal degrees, e.g. 51.5074, -0.1278."
            )

        if not -90.0 <= lat <= 90.0:
            return [], f"Line {line_no}: latitude {lat} is outside the valid range -90 to 90."
        if not -180.0 <= lon <= 180.0:
            return [], f"Line {line_no}: longitude {lon} is outside the valid range -180 to 180."

        points.append((round_coord(lat), round_coord(lon)))

    return points, None


def parse_polygon_coordinates(text: str) -> Tuple[List[List[float]], Optional[str]]:
    """Parse 'lat, lon' lines into a closed [lon, lat] GeoJSON ring.

    Args:
        text: Raw text from the coordinate entry box.

    Returns:
        ``(coordinates, None)`` on success, where coordinates is a list of
        ``[lon, lat]`` pairs with the first vertex repeated at the end, or
        ``([], error_message)`` on failure.
    """
    points, error = parse_coordinate_lines(text)
    if error:
        return [], error

    # A repeated final vertex is how a closed ring is normally written; drop it
    # before counting so "4 corners written as 5 lines" isn't over-counted.
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]

    if len(points) < 3:
        return [], (
            f"Need at least 3 corner points to make an area (got {len(points)})."
        )

    ring = [[lon, lat] for lat, lon in points]
    ring.append(ring[0])  # Close the ring, matching every other area source
    return ring, None


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
                 reversal_buffer_pct: float = 0.0,
                 horizon: int = EROI_APPRAISAL_HORIZON_YEARS):
    """Flow-based Ecological Return on Investment metrics.

    Ecosystem-service valuations are annual *flows* (Int$/yr), not stocks. A
    restoration project lifts the annual flow from ``baseline_value`` to
    ``target_value``; the uplift ``U = target - baseline`` is a permanent
    annual flow once the target state is reached. ``duration_years`` is the
    linear ramp period (the gap between the baseline and target dates) over
    which the uplift grows from 0 to U; after the ramp it continues at U for
    the remainder of the appraisal ``horizon``.

    The capital ``cost`` is spread evenly across the project duration (the
    ramp). ``maintenance_cost`` is an optional ongoing annual cost that begins
    the year *after* the ramp completes (i.e. after the project has ended).

    ``reversal_buffer_pct`` withholds a fraction of the annual uplift for
    permanence risk: every benefit metric uses the buffered uplift, while the
    capital and maintenance costs are left un-buffered.

    Args:
        baseline_value:    baseline annual ecosystem-service value (Int$/yr)
        target_value:      target annual ecosystem-service value (Int$/yr)
        cost:              total capital cost (Int$), spread over the ramp
        duration_years:    ramp years; None or 0 -> immediate full uplift
        discount_rate:     annual discount rate as a fraction (e.g. 0.035)
        maintenance_cost:  ongoing annual maintenance cost (Int$/yr), applied
                           after the ramp ends; 0 to disable
        reversal_buffer_pct: fraction of annual uplift withheld for permanence
                           risk (e.g. 0.20); 0 to disable
        horizon:           appraisal horizon in years

    Returns:
        dict of metrics, or None when EROI does not apply (missing baseline or
        target valuation, cost <= 0, or no positive uplift).
    """
    if baseline_value is None or target_value is None:
        return None
    if not cost or cost <= 0:
        return None
    uplift_gross = target_value - baseline_value
    if uplift_gross <= 0:
        return None
    # Reversal buffer: a fraction of the annual benefit withheld for permanence
    # risk. It scales the uplift only — capital and maintenance are not buffered.
    buffer = max(0.0, min(reversal_buffer_pct or 0.0, 1.0))
    uplift = uplift_gross * (1.0 - buffer)

    rate = discount_rate or 0.0
    horizon = int(horizon)
    ramp = duration_years if (duration_years and duration_years > 0) else 0.0
    maint = maintenance_cost or 0.0

    # Per-year streams over the appraisal horizon:
    #  - uplift: midpoint of the year on the linear ramp, capped at full U;
    #  - maintenance: begins the year after the ramp ends;
    #  - capital: the cost spread evenly across the project duration (the
    #    ramp). With no ramp/dates it falls in year 1. Installments sum to cost.
    yearly_uplift = []
    yearly_maint = []
    yearly_capital = []
    for t in range(1, horizon + 1):
        frac = 1.0 if ramp <= 0 else min((t - 0.5) / ramp, 1.0)
        yearly_uplift.append(uplift * frac)
        yearly_maint.append(maint if t > ramp else 0.0)
        if ramp > 0:
            # Slice of year t that lies within the [0, ramp] project window.
            yearly_capital.append(cost * (min(t, ramp) - min(t - 1, ramp)) / ramp)
        else:
            yearly_capital.append(cost if t == 1 else 0.0)

    def _pv(stream):
        return sum(v / (1.0 + rate) ** (i + 1) for i, v in enumerate(stream))

    pv_benefits = _pv(yearly_uplift)
    pv_maintenance = _pv(yearly_maint)
    pv_capital = _pv(yearly_capital)
    pv_costs = pv_capital + pv_maintenance
    # Counterfactual: the baseline annual value continues flat for the whole
    # horizon (no intervention). pv_with_project adds the buffered uplift PV;
    # pv_with_project - pv_counterfactual == pv_benefits.
    pv_counterfactual = _pv([baseline_value] * horizon)
    pv_with_project = pv_counterfactual + pv_benefits
    cum_benefit = sum(yearly_uplift)
    npv = pv_benefits - pv_costs
    bcr = pv_benefits / pv_costs                 # benefits / all costs
    net_annual = uplift - maint                  # mature net annual benefit
    annual_yield = net_annual / cost             # fraction per year on capital

    # Per-year net cash flow: benefit uplift, less maintenance, less the
    # capital installment for that year.
    yearly_net = [yearly_uplift[i] - yearly_maint[i] - yearly_capital[i]
                  for i in range(horizon)]

    # Undiscounted payback: first year the cumulative net cash flow turns
    # non-negative (the project has repaid its spread capital outlay).
    payback_years = None
    running = 0.0
    for i, net_v in enumerate(yearly_net):
        prev = running
        running += net_v
        if running >= 0:
            payback_years = (i + (-prev) / net_v) if net_v > 0 else float(i + 1)
            break

    irr = _irr([0.0] + yearly_net)

    return {
        'uplift': uplift,
        'uplift_gross': uplift_gross,
        'reversal_buffer_pct': buffer,
        'maintenance_cost': maint,
        'net_annual': net_annual,
        'cost': cost,
        'duration_years': duration_years,
        'discount_rate': rate,
        'horizon_years': horizon,
        'pv_benefits': pv_benefits,
        'pv_maintenance': pv_maintenance,
        'pv_capital': pv_capital,
        'pv_costs': pv_costs,
        'pv_counterfactual': pv_counterfactual,
        'pv_with_project': pv_with_project,
        'cum_benefit': cum_benefit,
        'npv': npv,
        'bcr': bcr,
        'annual_yield': annual_yield,
        'payback_years': payback_years,
        'irr': irr,
        'yearly_net': yearly_net,
    }


# ---------------------------------------------------------------------------
# Carbon revenue opportunity
# ---------------------------------------------------------------------------

# Social Cost of Carbon presets (Int$/tCO2e) used to back-calculate the
# implied physical sequestration from the ESVD climate-regulation value.
SCC_LOW = 100      # conservative, older literature
SCC_CENTRAL = 190  # US EPA 2023 interim figure
SCC_HIGH = 300     # high-damage scenario (Rennert et al. 2022, Nature)

# Published sequestration benchmarks (tCO2e/ha/yr) by ecosystem type.
# TODO: add tropical forest, freshwater wetland, peatland, grassland and
# seagrass benchmarks when EVE supplies them. Peatland sequestration is
# highly variable and site-specific — flag explicitly for peatland.
SEQ_BENCHMARKS = {
    'Mangroves': (6.0, 8.0),  # Hamilton & Friess (2018), Nature Climate Change
}


def compute_carbon_revenue(climate_reg_per_ha, regional_factor, assumed_scc,
                           carbon_price_low, carbon_price_high,
                           intervention_area_ha, ecosystem_type):
    """Potential carbon-credit revenue opportunity, back-calculated from the
    EEI-adjusted ESVD climate-regulation value.

    The ESVD climate-regulation value already carries EVE's regional GDP
    adjustment and EEI intactness multiplier. The regional adjustment is
    reversed to recover the global transfer value; dividing by the Social
    Cost of Carbon back-calculates the implied physical sequestration rate
    (still intactness-weighted). That tonnage is then valued across a
    voluntary carbon-market credit-price range to give a revenue range.

    Returns a dict of figures, or None when there is no climate-regulation
    value to work from.
    """
    if not climate_reg_per_ha or climate_reg_per_ha <= 0:
        return None
    rf = regional_factor if (regional_factor and regional_factor > 0) else 1.0
    scc = assumed_scc if (assumed_scc and assumed_scc > 0) else SCC_CENTRAL
    area = intervention_area_ha or 0.0

    climate_reg_global = climate_reg_per_ha / rf
    implied_seq_ha_yr = climate_reg_global / scc
    implied_seq_total_yr = implied_seq_ha_yr * area

    p_lo = max(0.0, carbon_price_low or 0.0)
    p_hi = max(0.0, carbon_price_high or 0.0)
    if p_hi < p_lo:
        p_lo, p_hi = p_hi, p_lo
    revenue_low = implied_seq_total_yr * p_lo
    revenue_high = implied_seq_total_yr * p_hi

    bench = SEQ_BENCHMARKS.get(ecosystem_type)
    if bench:
        b_lo, b_hi = bench
        # 'ok' within +/-30% of the published range; 'warning' well outside.
        consistency = ('ok' if b_lo * 0.7 <= implied_seq_ha_yr <= b_hi * 1.3
                       else 'warning')
    else:
        b_lo = b_hi = None
        consistency = 'na'  # no published benchmark for this ecosystem type

    return {
        'climate_reg_per_ha': climate_reg_per_ha,
        'climate_reg_global': climate_reg_global,
        'regional_factor': rf,
        'assumed_scc': scc,
        'implied_seq_ha_yr': implied_seq_ha_yr,
        'implied_seq_total_yr': implied_seq_total_yr,
        'carbon_price_low': p_lo,
        'carbon_price_high': p_hi,
        'revenue_low': revenue_low,
        'revenue_high': revenue_high,
        'benchmark_low': b_lo,
        'benchmark_high': b_hi,
        'consistency': consistency,
        'ecosystem_type': ecosystem_type,
    }

"""
Static map image for the PDF report.

Given the analysis bounding box (and optionally the drawn polygon vertices),
this fetches Esri World Imagery satellite tiles for the area, stitches them
into a single image, crops to the (padded) bounding box and draws the
selected-area outline on top. Returns JPEG bytes for embedding in the report
(JPEG keeps satellite imagery to a few hundred KB rather than ~2 MB as PNG).

Everything is best-effort: any failure (no network, tile server down, missing
Pillow) returns ``None`` so the PDF still builds without the image.
"""

import io
import math
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

TILE_SIZE = 256

# Esri World Imagery — public XYZ tile service, no API key required.
# Note the {z}/{y}/{x} ordering (row before column).
_ESRI_WORLD_IMAGERY = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
_ATTRIBUTION = "Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"

# Outline / fill for the drawn area — matches the on-screen draw colour (#2E8B57).
_OUTLINE_RGB = (46, 139, 87)
_FILL_RGBA = (46, 139, 87, 60)


def _lonlat_to_global_px(lon: float, lat: float, zoom: int):
    """Web-Mercator lon/lat -> global pixel coordinates at the given zoom."""
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    lat = max(min(lat, 85.05112878), -85.05112878)
    lat_rad = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * TILE_SIZE
    return x, y


def _choose_zoom(bbox: Dict[str, float], max_tiles_per_axis: int,
                 min_zoom: int, max_zoom: int) -> int:
    """Highest zoom at which the bbox still fits within max_tiles_per_axis."""
    for z in range(max_zoom, min_zoom - 1, -1):
        x0, y0 = _lonlat_to_global_px(bbox['min_lon'], bbox['max_lat'], z)
        x1, y1 = _lonlat_to_global_px(bbox['max_lon'], bbox['min_lat'], z)
        if (abs(x1 - x0) / TILE_SIZE <= max_tiles_per_axis and
                abs(y1 - y0) / TILE_SIZE <= max_tiles_per_axis):
            return z
    return min_zoom


def _pad_bbox(bbox: Dict[str, float], frac: float) -> Dict[str, float]:
    """Expand the bbox by a fraction of its span, with a minimum span so a
    tiny/point selection still produces a sensibly-zoomed image."""
    min_span = 0.002  # ~200 m, keeps very small areas from over-zooming
    lat_span = max(bbox['max_lat'] - bbox['min_lat'], min_span)
    lon_span = max(bbox['max_lon'] - bbox['min_lon'], min_span)
    lat_pad = lat_span * frac
    lon_pad = lon_span * frac
    c_lat = (bbox['min_lat'] + bbox['max_lat']) / 2
    c_lon = (bbox['min_lon'] + bbox['max_lon']) / 2
    half_lat = lat_span / 2 + lat_pad
    half_lon = lon_span / 2 + lon_pad
    return {
        'min_lat': c_lat - half_lat, 'max_lat': c_lat + half_lat,
        'min_lon': c_lon - half_lon, 'max_lon': c_lon + half_lon,
    }


def render_area_map_image(
    bbox: Optional[Dict[str, float]],
    coordinates: Optional[List] = None,
    padding_frac: float = 0.18,
    max_tiles_per_axis: int = 5,
    max_tiles_total: int = 36,
    min_zoom: int = 3,
    max_zoom: int = 18,
    timeout: float = 6.0,
) -> Optional[bytes]:
    """Build a satellite image of the selected area with its outline drawn on.

    Args:
        bbox:        dict with min_lat/max_lat/min_lon/max_lon.
        coordinates: polygon vertices as [lon, lat] pairs (GeoJSON order); the
                     outline is drawn if provided.
    Returns:
        JPEG bytes, or None on any failure.
    """
    if not bbox or not all(k in bbox for k in
                           ('min_lat', 'max_lat', 'min_lon', 'max_lon')):
        return None
    try:
        from PIL import Image, ImageDraw
        import requests
    except Exception as exc:  # pragma: no cover - dependency guard
        logger.warning("static_map: Pillow/requests unavailable (%s)", exc)
        return None

    try:
        padded = _pad_bbox(bbox, padding_frac)
        zoom = _choose_zoom(padded, max_tiles_per_axis, min_zoom, max_zoom)

        # Global pixel window for the padded bbox at the chosen zoom.
        left_px, top_px = _lonlat_to_global_px(padded['min_lon'], padded['max_lat'], zoom)
        right_px, bottom_px = _lonlat_to_global_px(padded['max_lon'], padded['min_lat'], zoom)
        left_px, right_px = sorted((left_px, right_px))
        top_px, bottom_px = sorted((top_px, bottom_px))

        x_tile_min = int(math.floor(left_px / TILE_SIZE))
        x_tile_max = int(math.floor((right_px - 1e-6) / TILE_SIZE))
        y_tile_min = int(math.floor(top_px / TILE_SIZE))
        y_tile_max = int(math.floor((bottom_px - 1e-6) / TILE_SIZE))

        n_tiles = (x_tile_max - x_tile_min + 1) * (y_tile_max - y_tile_min + 1)
        if n_tiles <= 0 or n_tiles > max_tiles_total:
            logger.warning("static_map: tile count %d out of range", n_tiles)
            return None

        mosaic_w = (x_tile_max - x_tile_min + 1) * TILE_SIZE
        mosaic_h = (y_tile_max - y_tile_min + 1) * TILE_SIZE
        mosaic = Image.new('RGB', (mosaic_w, mosaic_h), (60, 60, 60))

        session = requests.Session()
        session.headers.update({'User-Agent': 'EVE-Valuation-Engine/1.0'})
        max_idx = 2 ** zoom
        for tx in range(x_tile_min, x_tile_max + 1):
            for ty in range(y_tile_min, y_tile_max + 1):
                if not (0 <= tx < max_idx and 0 <= ty < max_idx):
                    continue
                url = _ESRI_WORLD_IMAGERY.format(z=zoom, x=tx, y=ty)
                try:
                    resp = session.get(url, timeout=timeout)
                    resp.raise_for_status()
                    tile = Image.open(io.BytesIO(resp.content)).convert('RGB')
                except Exception as exc:
                    logger.warning("static_map: tile fetch failed %s (%s)", url, exc)
                    continue
                mosaic.paste(
                    tile,
                    ((tx - x_tile_min) * TILE_SIZE, (ty - y_tile_min) * TILE_SIZE),
                )

        # Crop the mosaic to the padded-bbox pixel window.
        origin_x = x_tile_min * TILE_SIZE
        origin_y = y_tile_min * TILE_SIZE
        crop_box = (
            int(round(left_px - origin_x)),
            int(round(top_px - origin_y)),
            int(round(right_px - origin_x)),
            int(round(bottom_px - origin_y)),
        )
        crop = mosaic.crop(crop_box)
        if crop.width < 2 or crop.height < 2:
            return None

        # Draw the selected-area polygon (translucent fill + solid outline).
        if coordinates and len(coordinates) >= 3:
            poly_px = []
            for pt in coordinates:
                try:
                    lon, lat = float(pt[0]), float(pt[1])
                except (TypeError, ValueError, IndexError):
                    continue
                gx, gy = _lonlat_to_global_px(lon, lat, zoom)
                poly_px.append((gx - left_px, gy - top_px))
            if len(poly_px) >= 3:
                overlay = Image.new('RGBA', crop.size, (0, 0, 0, 0))
                odraw = ImageDraw.Draw(overlay)
                odraw.polygon(poly_px, fill=_FILL_RGBA)
                crop = Image.alpha_composite(crop.convert('RGBA'), overlay).convert('RGB')
                line_w = max(2, int(round(min(crop.size) / 200)))
                ImageDraw.Draw(crop).line(
                    poly_px + [poly_px[0]], fill=_OUTLINE_RGB, width=line_w,
                    joint='curve',
                )

        # Keep the embedded image a sensible size for the PDF.
        max_px = 1100
        if max(crop.size) > max_px:
            scale = max_px / max(crop.size)
            crop = crop.resize(
                (max(1, int(crop.width * scale)), max(1, int(crop.height * scale))),
                Image.LANCZOS,
            )

        out = io.BytesIO()
        crop.save(out, format='JPEG', quality=85, optimize=True)
        return out.getvalue()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("static_map: render failed (%s)", exc)
        return None


def attribution() -> str:
    """Tile-source attribution string for the report caption."""
    return _ATTRIBUTION

"""
Tests for polygon-clipped sample-point generation.

Verifies that OpenLandMapIntegrator._generate_sample_points():

  * places every sample point INSIDE the drawn polygon, not merely inside its
    bounding box;
  * returns EXACTLY the requested number of points, for every count the UI
    slider offers (the old bbox grid returned int(sqrt(n))**2, so 50 gave 49
    and 48 gave 36);
  * covers the area evenly — no part of a drawn polygon is further from its
    nearest sample than a true grid would leave it. This is what was wrong
    before: on non-rectangular polygons the old code densified the grid, then
    thinned it with linspace over a raster-ordered list, which is not a
    spatial operation and left holes. Rectangles were unaffected, which is
    why only polygons looked ragged;
  * is deterministic, so re-running an analysis reproduces the same points.

Containment is checked with an independent ray-casting implementation so we
are not validating matplotlib's point-in-polygon test with matplotlib itself.

Runnable without pytest:  ``python tests/test_sample_point_generation.py``
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from utils.openlandmap_integration import OpenLandMapIntegrator

_integ = OpenLandMapIntegrator()


# ── independent oracle ──────────────────────────────────────────────────────

def _dist_point_to_segment(px, py, ax, ay, bx, by):
    """Euclidean distance from point P to segment AB."""
    abx, aby = bx - ax, by - ay
    denom = abx * abx + aby * aby
    if denom == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * abx + (py - ay) * aby) / denom
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * abx, ay + t * aby
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _point_in_polygon(lon, lat, verts, eps=1e-9):
    """Ray-casting point-in-polygon. verts is a list of (lon, lat) WITHOUT the
    closing duplicate. Points lying on the boundary (within ``eps``) count as
    inside, matching matplotlib's contains_points boundary behaviour."""
    n = len(verts)
    for i in range(n):
        ax, ay = verts[i]
        bx, by = verts[(i + 1) % n]
        if _dist_point_to_segment(lon, lat, ax, ay, bx, by) <= eps:
            return True
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def _legacy_bbox_grid(coordinates, num_points):
    """Reproduction of the OLD implementation: a bbox grid with NO polygon
    clipping. Kept as a fixture check — it demonstrates both failures the
    current implementation fixes (points outside the polygon, and a count
    rounded down to a perfect square)."""
    coords = np.array(coordinates[:-1], dtype=np.float64)
    min_lon, min_lat = coords[:, 0].min(), coords[:, 1].min()
    max_lon, max_lat = coords[:, 0].max(), coords[:, 1].max()
    grid_size = int(np.sqrt(num_points)) or 1
    i_vals = np.arange(grid_size)
    lats = min_lat + (max_lat - min_lat) * (i_vals + 0.5) / grid_size
    lons = min_lon + (max_lon - min_lon) * (i_vals + 0.5) / grid_size
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    return list(zip(lat_grid.flatten(), lon_grid.flatten()))


# ── coverage measurement ────────────────────────────────────────────────────

def _to_metres(pts_latlon, lat0):
    """Project (lat, lon) pairs onto a local metric plane for distance work."""
    kx = 111320.0 * math.cos(math.radians(lat0))
    return np.array([[lon * kx, lat * 110574.0] for lat, lon in pts_latlon])


def _polygon_area_m2(verts, lat0):
    c = np.asarray(verts, dtype=float)
    x = c[:, 0] * 111320.0 * math.cos(math.radians(lat0))
    y = c[:, 1] * 110574.0
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def _worst_gap_ratio(coordinates, num_points, n_probe=120):
    """Largest distance from anywhere in the polygon to its nearest sample
    point, expressed in units of sqrt(area / n).

    An ideal square grid scores about 0.71 (half a cell diagonal). The old
    implementation reached ~1.5 on drawn polygons — twice the gap it should
    have left. The probe is an independent dense lattice over the polygon, not
    the one the implementation scores itself against.
    """
    verts = coordinates[:-1]
    lat0 = float(np.mean([v[1] for v in verts]))
    pts = _integ._generate_sample_points(coordinates, num_points=num_points)
    P = _to_metres(pts, lat0)

    lons = [v[0] for v in verts]
    lats = [v[1] for v in verts]
    probe = []
    for i in range(n_probe):
        for j in range(n_probe):
            lon = min(lons) + (max(lons) - min(lons)) * (i + 0.5) / n_probe
            lat = min(lats) + (max(lats) - min(lats)) * (j + 0.5) / n_probe
            if _point_in_polygon(lon, lat, verts):
                probe.append((lat, lon))
    Q = _to_metres(probe, lat0)

    d = np.linalg.norm(Q[:, None, :] - P[None, :, :], axis=-1).min(axis=1)
    ideal = math.sqrt(_polygon_area_m2(verts, lat0) / len(pts))
    return float(d.max() / ideal)


# ── fixtures ────────────────────────────────────────────────────────────────

# Closed rings in (lon, lat), matching app.py's area_coordinates convention.
RECTANGLE = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]

# L-shape: the [0,3]x[0,3] square with its top-right quadrant removed.
# Any bbox grid will drop points into the missing top-right corner.
L_SHAPE = [
    (0.0, 0.0), (3.0, 0.0), (3.0, 1.5),
    (1.5, 1.5), (1.5, 3.0), (0.0, 3.0), (0.0, 0.0),
]

# A right triangle occupying the lower-left half of the [0,4]x[0,4] bbox.
TRIANGLE = [(0.0, 0.0), (4.0, 0.0), (0.0, 4.0), (0.0, 0.0)]

# An irregular blob — the closest fixture to a hand-drawn area.
BLOB = [
    (0.0, 0.0), (2.4, 0.2), (3.4, 1.0), (3.0, 2.6),
    (1.4, 3.1), (-0.4, 1.8), (0.0, 0.0),
]

_SHAPES = [
    ("rectangle", RECTANGLE),
    ("L-shape", L_SHAPE),
    ("triangle", TRIANGLE),
    ("blob", BLOB),
]


# ── tests ───────────────────────────────────────────────────────────────────

def test_exact_count_every_slider_value():
    # The UI slider offers every integer from 9 to 100. Each must be honoured
    # exactly, on every shape — the old code silently rounded down to a
    # perfect square, so only 8 of the 92 values were delivered as asked.
    for name, shape in _SHAPES:
        for n in range(9, 101):
            pts = _integ._generate_sample_points(shape, num_points=n)
            assert len(pts) == n, f"{name}: asked {n}, got {len(pts)}"


def test_legacy_grid_did_not_honour_the_count():
    # Fixture sanity: the old method really did round the count down.
    assert len(_legacy_bbox_grid(RECTANGLE, 50)) == 49
    assert len(_legacy_bbox_grid(RECTANGLE, 48)) == 36


def test_all_points_inside_every_shape():
    for name, shape in _SHAPES:
        for n in (9, 16, 37, 64, 100):
            pts = _integ._generate_sample_points(shape, num_points=n)
            for lat, lon in pts:
                assert _point_in_polygon(lon, lat, shape[:-1]), (
                    f"{name} n={n}: point outside polygon: {(lat, lon)}"
                )


def test_l_shape_excludes_removed_corner():
    # No returned point may land in the removed top-right quadrant
    # (lon > 1.5 AND lat > 1.5).
    for n in (9, 16, 49):
        pts = _integ._generate_sample_points(L_SHAPE, num_points=n)
        for lat, lon in pts:
            assert not (lon > 1.5 and lat > 1.5), f"point in removed corner: {(lat, lon)}"


def test_old_method_would_have_leaked_outside():
    # Sanity check on the oracle + fixture: the OLD bbox grid DID place
    # points outside the L-shape — proving the clip is doing real work.
    legacy = _legacy_bbox_grid(L_SHAPE, 16)
    verts = L_SHAPE[:-1]
    leaked = [(lat, lon) for lat, lon in legacy if not _point_in_polygon(lon, lat, verts)]
    assert leaked, "fixture should produce out-of-polygon points under the old method"


def test_no_coverage_holes_on_polygons():
    # The headline guarantee. A true grid leaves a worst-case gap of about
    # 0.71; the old implementation reached ~1.5 on these shapes. Allow 1.15,
    # which is comfortably inside what the old code did and leaves room for
    # awkward geometry.
    for name, shape in _SHAPES:
        for n in (9, 49):
            ratio = _worst_gap_ratio(shape, n)
            assert ratio <= 1.15, f"{name} n={n}: worst gap {ratio:.2f} spacings"


def test_rectangle_coverage_is_grid_quality():
    # Rectangles were already even before this change and must stay that way:
    # they are the one shape the old bbox grid handled exactly.
    for n in (9, 49):
        ratio = _worst_gap_ratio(RECTANGLE, n)
        assert ratio <= 0.80, f"rectangle n={n}: worst gap {ratio:.2f} spacings"


def test_spacing_is_isotropic_on_the_ground():
    # Points are laid out in metres, so a bounding box that is far wider than
    # it is tall must not produce spacing that follows that aspect ratio.
    wide = [(0.0, 0.0), (4.0, 0.0), (4.0, 0.5), (0.0, 0.5), (0.0, 0.0)]
    pts = _integ._generate_sample_points(wide, num_points=36)
    lat0 = 0.25
    P = _to_metres(pts, lat0)
    d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=-1)
    np.fill_diagonal(d, np.inf)
    nn = d.min(axis=1)
    # Nearest-neighbour distances should be tightly clustered; an
    # aspect-following grid would spread them by the 8:1 box ratio.
    assert nn.max() / nn.min() < 2.0, (nn.min(), nn.max())


def test_deterministic():
    for name, shape in _SHAPES:
        a = _integ._generate_sample_points(shape, num_points=37)
        b = _integ._generate_sample_points(shape, num_points=37)
        assert a == b, f"{name}: sampling must be deterministic"


def test_completes_quickly_at_the_maximum_count():
    # The layout search runs on every analysis, so it has to stay cheap
    # relative to the per-point API calls that follow it.
    import time
    t0 = time.time()
    _integ._generate_sample_points(BLOB, num_points=100)
    elapsed = time.time() - t0
    assert elapsed < 3.0, f"took {elapsed:.2f}s for 100 points"


# ── runner ──────────────────────────────────────────────────────────────────

_TESTS = [
    ("exact count for every slider value 9-100", test_exact_count_every_slider_value),
    ("legacy grid did not honour the count (fixture)", test_legacy_grid_did_not_honour_the_count),
    ("all points inside, every shape", test_all_points_inside_every_shape),
    ("L-shape: removed corner excluded", test_l_shape_excludes_removed_corner),
    ("old method leaked outside (fixture sanity)", test_old_method_would_have_leaked_outside),
    ("no coverage holes on polygons", test_no_coverage_holes_on_polygons),
    ("rectangle keeps grid-quality coverage", test_rectangle_coverage_is_grid_quality),
    ("spacing is isotropic on the ground", test_spacing_is_isotropic_on_the_ground),
    ("deterministic output", test_deterministic),
    ("fast at the maximum point count", test_completes_quickly_at_the_maximum_count),
]


def main():
    print("Running sample-point generation tests\n")
    results = []
    for name, fn in _TESTS:
        try:
            fn()
            results.append((name, True))
            print(f"  PASS  {name}")
        except AssertionError as e:
            results.append((name, False))
            print(f"  FAIL  {name}: {e}")
        except Exception as e:
            import traceback
            results.append((name, False))
            print(f"  ERROR {name}: {e}")
            traceback.print_exc()
    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed} passed, {len(results) - passed} failed, {len(results)} total")
    return 1 if passed != len(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

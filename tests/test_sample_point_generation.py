"""
Tests for polygon-clipped sample-point generation.

Verifies that OpenLandMapIntegrator._generate_sample_points() places sample
points INSIDE the drawn polygon (not merely inside its bounding box), while
keeping rectangular selections bit-for-bit identical to the previous
bbox-grid behaviour.

Containment is checked with an independent ray-casting implementation so we
are not validating matplotlib's point-in-polygon test with matplotlib itself.

Runnable without pytest:  ``python tests/test_sample_point_generation.py``
"""

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
    # Boundary tolerance: a point on an edge/vertex is part of the area.
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
    clipping. Used to (a) reproduce the rectangle result and (b) prove the
    old method leaked points outside non-rectangular polygons."""
    coords = np.array(coordinates[:-1], dtype=np.float64)
    min_lon, min_lat = coords[:, 0].min(), coords[:, 1].min()
    max_lon, max_lat = coords[:, 0].max(), coords[:, 1].max()
    grid_size = int(np.sqrt(num_points)) or 1
    i_vals = np.arange(grid_size)
    lats = min_lat + (max_lat - min_lat) * (i_vals + 0.5) / grid_size
    lons = min_lon + (max_lon - min_lon) * (i_vals + 0.5) / grid_size
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    return list(zip(lat_grid.flatten(), lon_grid.flatten()))


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


# ── tests ───────────────────────────────────────────────────────────────────

def test_rectangle_matches_legacy_grid_exactly():
    pts = _integ._generate_sample_points(RECTANGLE, num_points=10)
    legacy = _legacy_bbox_grid(RECTANGLE, 10)
    assert len(pts) == len(legacy) == 9, (len(pts), len(legacy))
    for (a_lat, a_lon), (b_lat, b_lon) in zip(pts, legacy):
        assert abs(a_lat - b_lat) < 1e-9 and abs(a_lon - b_lon) < 1e-9, (
            (a_lat, a_lon), (b_lat, b_lon)
        )


def test_rectangle_points_all_inside():
    pts = _integ._generate_sample_points(RECTANGLE, num_points=10)
    verts = RECTANGLE[:-1]
    for lat, lon in pts:
        assert _point_in_polygon(lon, lat, verts), (lat, lon)


def test_l_shape_all_points_inside():
    pts = _integ._generate_sample_points(L_SHAPE, num_points=16)
    verts = L_SHAPE[:-1]
    assert len(pts) > 0
    for lat, lon in pts:
        assert _point_in_polygon(lon, lat, verts), f"point outside L-shape: {(lat, lon)}"


def test_l_shape_excludes_removed_corner():
    # No returned point may land in the removed top-right quadrant
    # (lon > 1.5 AND lat > 1.5).
    pts = _integ._generate_sample_points(L_SHAPE, num_points=16)
    for lat, lon in pts:
        assert not (lon > 1.5 and lat > 1.5), f"point in removed corner: {(lat, lon)}"


def test_old_method_would_have_leaked_outside():
    # Sanity check on the oracle + fixture: the OLD bbox grid DID place
    # points outside the L-shape — proving the clip is doing real work.
    legacy = _legacy_bbox_grid(L_SHAPE, 16)
    verts = L_SHAPE[:-1]
    leaked = [(lat, lon) for lat, lon in legacy if not _point_in_polygon(lon, lat, verts)]
    assert leaked, "fixture should produce out-of-polygon points under the old method"


def test_triangle_all_points_inside():
    pts = _integ._generate_sample_points(TRIANGLE, num_points=25)
    verts = TRIANGLE[:-1]
    assert len(pts) > 0
    for lat, lon in pts:
        assert _point_in_polygon(lon, lat, verts), f"point outside triangle: {(lat, lon)}"


def test_count_is_bounded_by_target():
    # Returned count should not exceed the native-grid target (grid_size**2)
    # and should be non-empty for a well-formed polygon.
    for n in (4, 10, 16, 25, 100):
        grid_size0 = int(np.sqrt(n)) or 1
        target = grid_size0 ** 2
        pts = _integ._generate_sample_points(L_SHAPE, num_points=n)
        assert 0 < len(pts) <= target, (n, len(pts), target)


def test_deterministic():
    a = _integ._generate_sample_points(L_SHAPE, num_points=16)
    b = _integ._generate_sample_points(L_SHAPE, num_points=16)
    assert a == b, "sampling must be deterministic"


# ── runner ──────────────────────────────────────────────────────────────────

_TESTS = [
    ("rectangle matches legacy grid exactly", test_rectangle_matches_legacy_grid_exactly),
    ("rectangle points all inside", test_rectangle_points_all_inside),
    ("L-shape: all points inside polygon", test_l_shape_all_points_inside),
    ("L-shape: removed corner excluded", test_l_shape_excludes_removed_corner),
    ("old method leaked outside (fixture sanity)", test_old_method_would_have_leaked_outside),
    ("triangle: all points inside", test_triangle_all_points_inside),
    ("count bounded by target", test_count_is_bounded_by_target),
    ("deterministic output", test_deterministic),
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

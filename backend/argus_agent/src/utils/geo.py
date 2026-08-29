"""Pure, stateless geometry helpers. No business logic."""

import math


def polygon_centroid(coordinates: list[list[float]]) -> tuple[float, float]:
    """Return (lat, lon) centroid of a [[lon, lat], ...] ring."""
    lons = [c[0] for c in coordinates]
    lats = [c[1] for c in coordinates]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def split_into_grid(
    coordinates: list[list[float]], cells_per_side: int = 2
) -> list[list[list[float]]]:
    """Split a bounding polygon into cells_per_side x cells_per_side sub-polygons."""
    lons = [c[0] for c in coordinates]
    lats = [c[1] for c in coordinates]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    lon_step = (max_lon - min_lon) / cells_per_side
    lat_step = (max_lat - min_lat) / cells_per_side

    cells = []
    for i in range(cells_per_side):
        for j in range(cells_per_side):
            lo0, lo1 = min_lon + i * lon_step, min_lon + (i + 1) * lon_step
            la0, la1 = min_lat + j * lat_step, min_lat + (j + 1) * lat_step
            cells.append([[lo0, la0], [lo1, la0], [lo1, la1], [lo0, la1], [lo0, la0]])
    return cells

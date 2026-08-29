"""Generate realistic dummy FortyGuard API responses and populate MongoDB cache.

This mimics actual FortyGuard heatmap (tcm, exceedance, persistence) responses for all 51 cities,
with realistic temperature ranges and structures, so the analysis pipeline can run without spending
API credits. Data is stored in fortyguard_cache collection, keyed by (path, payload) hash, exactly
as real API responses would be.
"""

import asyncio
import hashlib
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.constants import MONITORED_CITIES
from argus_agent.src.db.mongo import get_fortyguard_cache_collection
from argus_agent.src.db.models import FortyGuardCacheEntry


# Base temperature ranges for each city (realistic min/max in °C for a hot day)
CITY_TEMP_RANGES = {
    "birmingham-al": (28, 35),
    "anchorage-ak": (15, 22),
    "phoenix-az": (35, 42),
    "little-rock-ar": (27, 34),
    "los-angeles-ca": (25, 32),
    "denver-co": (24, 31),
    "hartford-ct": (22, 29),
    "wilmington-de": (23, 30),
    "miami-fl": (28, 33),
    "atlanta-ga": (27, 34),
    "honolulu-hi": (26, 30),
    "boise-id": (26, 33),
    "chicago-il": (25, 32),
    "indianapolis-in": (26, 33),
    "des-moines-ia": (25, 32),
    "wichita-ks": (28, 35),
    "louisville-ky": (26, 33),
    "new-orleans-la": (28, 34),
    "portland-me": (20, 27),
    "baltimore-md": (24, 31),
    "boston-ma": (22, 29),
    "detroit-mi": (24, 31),
    "minneapolis-mn": (23, 30),
    "jackson-ms": (28, 35),
    "kansas-city-mo": (27, 34),
    "billings-mt": (22, 29),
    "omaha-ne": (26, 33),
    "las-vegas-nv": (34, 41),
    "manchester-nh": (20, 27),
    "newark-nj": (24, 31),
    "albuquerque-nm": (30, 37),
    "new-york-ny": (24, 31),
    "charlotte-nc": (26, 33),
    "fargo-nd": (20, 27),
    "columbus-oh": (25, 32),
    "oklahoma-city-ok": (28, 35),
    "portland-or": (23, 30),
    "philadelphia-pa": (24, 31),
    "providence-ri": (22, 29),
    "columbia-sc": (27, 34),
    "sioux-falls-sd": (22, 29),
    "nashville-tn": (27, 34),
    "houston-tx": (29, 36),
    "salt-lake-city-ut": (27, 34),
    "burlington-vt": (20, 27),
    "virginia-beach-va": (25, 32),
    "seattle-wa": (21, 28),
    "charleston-wv": (25, 32),
    "milwaukee-wi": (24, 31),
    "cheyenne-wy": (22, 29),
    "washington-dc": (25, 32),
}


def generate_heatmap_tcm_response(city_id: str, polygon: list, cells_count: int = 9) -> dict:
    """Generate a realistic heatmap TCM (temperature) response."""
    min_temp_c, max_temp_c = CITY_TEMP_RANGES.get(city_id, (20, 30))

    # Generate per-cell temperatures
    temps_c = [
        round(random.uniform(min_temp_c, max_temp_c), 2)
        for _ in range(cells_count)
    ]

    mean_temp = sum(temps_c) / len(temps_c)
    min_temp = min(temps_c)
    max_temp = max(temps_c)

    # Create realistic GeoJSON features (one per grid cell)
    features = []
    for i, temp in enumerate(temps_c):
        lat, lon = polygon[i % len(polygon)][::-1]  # swap to (lat, lon)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - 0.005, lat - 0.005],
                    [lon + 0.005, lat - 0.005],
                    [lon + 0.005, lat + 0.005],
                    [lon - 0.005, lat + 0.005],
                    [lon - 0.005, lat - 0.005],
                ]],
            },
            "properties": {"average_temperature": temp},
        })

    return {
        "status": "completed",
        "result": {
            "stats_data": {
                "n_cells": cells_count,
                "temperature_stats": {
                    "mean": round(mean_temp, 2),
                    "minimum": min_temp,
                    "maximum": max_temp,
                },
            },
            "map_data": {"features": features},
        },
    }


def generate_exceedance_response(city_id: str, polygon: list, threshold_c: float = 30.0, cells_count: int = 9) -> dict:
    """Generate a realistic exceedance (hours above threshold) response."""
    # Some cells exceed, some don't
    hours_above = [
        round(random.uniform(0, 18), 1) if random.random() > 0.4 else 0
        for _ in range(cells_count)
    ]

    mean_hours = sum(hours_above) / len(hours_above) if hours_above else 0
    min_hours = min(hours_above) if hours_above else 0
    max_hours = max(hours_above) if hours_above else 0

    features = []
    for i, hours in enumerate(hours_above):
        lat, lon = polygon[i % len(polygon)][::-1]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - 0.005, lat - 0.005],
                    [lon + 0.005, lat - 0.005],
                    [lon + 0.005, lat + 0.005],
                    [lon - 0.005, lat + 0.005],
                    [lon - 0.005, lat - 0.005],
                ]],
            },
            "properties": {"value": hours},
        })

    return {
        "status": "completed",
        "result": {
            "stats_data": {
                "n_cells": cells_count,
                "mean": round(mean_hours, 1),
                "min": min_hours,
                "max": max_hours,
                "units": "hour",
            },
            "map_data": {"features": features},
        },
    }


def generate_persistence_response(city_id: str, polygon: list, threshold_c: float = 30.0, cells_count: int = 9) -> dict:
    """Generate a realistic persistence (longest streak above threshold) response."""
    # Longest consecutive hours above threshold
    hours_persistence = [
        round(random.uniform(0, 12), 1) if random.random() > 0.5 else 0
        for _ in range(cells_count)
    ]

    mean_hours = sum(hours_persistence) / len(hours_persistence) if hours_persistence else 0
    min_hours = min(hours_persistence) if hours_persistence else 0
    max_hours = max(hours_persistence) if hours_persistence else 0

    features = []
    for i, hours in enumerate(hours_persistence):
        lat, lon = polygon[i % len(polygon)][::-1]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - 0.005, lat - 0.005],
                    [lon + 0.005, lat - 0.005],
                    [lon + 0.005, lat + 0.005],
                    [lon - 0.005, lat + 0.005],
                    [lon - 0.005, lat - 0.005],
                ]],
            },
            "properties": {"value": hours},
        })

    return {
        "status": "completed",
        "result": {
            "stats_data": {
                "n_cells": cells_count,
                "mean": round(mean_hours, 1),
                "min": min_hours,
                "max": max_hours,
                "units": "hour",
            },
            "map_data": {"features": features},
        },
    }


def cache_key(path: str, payload: dict) -> str:
    """Same cache key logic as fortyguard_client.py."""
    canonical = json.dumps({"path": path, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def populate_cache_for_city(city: dict) -> int:
    """Generate and store dummy FortyGuard responses for one city. Returns count stored."""
    city_id = city["id"]
    polygon = city["polygon"]
    cache = get_fortyguard_cache_collection()
    count = 0
    now = datetime.now(UTC)

    # TCM (temperature snapshot)
    tcm_payload = {
        "polygon_aoi": {"type": "Polygon", "coordinates": [polygon]},
        "date_time": {"start_date": "2026-08-27", "filter_type": 3},
        "granularity": 100,
        "analytic_type": "tcm",
    }
    tcm_result = generate_heatmap_tcm_response(city_id, polygon)
    cache.replace_one(
        {"_id": cache_key("/v1/heatmap", tcm_payload)},
        FortyGuardCacheEntry(
            id=cache_key("/v1/heatmap", tcm_payload),
            label=f"DISCOVER {city_id} — tcm",
            city_id=city_id,
            path="/v1/heatmap",
            payload=tcm_payload,
            result=tcm_result,
            created_at=now,
            updated_at=now,
        ).to_mongo(),
        upsert=True,
    )
    count += 1

    # Exceedance (hours above 30°C)
    exceedance_payload = {
        "polygon_aoi": {"type": "Polygon", "coordinates": [polygon]},
        "date_time": {"start_date": "2026-08-27", "filter_type": 3},
        "granularity": 60,
        "analytic_type": "exceedance",
        "threshold": 30.0,
        "direction": "above",
    }
    exceedance_result = generate_exceedance_response(city_id, polygon, threshold_c=30.0)
    cache.replace_one(
        {"_id": cache_key("/v1/heatmap", exceedance_payload)},
        FortyGuardCacheEntry(
            id=cache_key("/v1/heatmap", exceedance_payload),
            label=f"INVESTIGATE {city_id} — exceedance",
            city_id=city_id,
            path="/v1/heatmap",
            payload=exceedance_payload,
            result=exceedance_result,
            created_at=now,
            updated_at=now,
        ).to_mongo(),
        upsert=True,
    )
    count += 1

    # Persistence (longest streak above 30°C)
    persistence_payload = {
        "polygon_aoi": {"type": "Polygon", "coordinates": [polygon]},
        "date_time": {"start_date": "2026-08-27", "filter_type": 3},
        "granularity": 60,
        "analytic_type": "persistence",
        "threshold": 30.0,
        "direction": "above",
    }
    persistence_result = generate_persistence_response(city_id, polygon, threshold_c=30.0)
    cache.replace_one(
        {"_id": cache_key("/v1/heatmap", persistence_payload)},
        FortyGuardCacheEntry(
            id=cache_key("/v1/heatmap", persistence_payload),
            label=f"INVESTIGATE {city_id} — persistence",
            city_id=city_id,
            path="/v1/heatmap",
            payload=persistence_payload,
            result=persistence_result,
            created_at=now,
            updated_at=now,
        ).to_mongo(),
        upsert=True,
    )
    count += 1

    return count


def main() -> None:
    """Load dummy data for all 51 cities into fortyguard_cache."""
    total_stored = 0
    failed_cities = []

    print(f"Populating dummy FortyGuard cache for {len(MONITORED_CITIES)} cities…\n")

    for i, city in enumerate(MONITORED_CITIES, start=1):
        city_id = city["id"]
        try:
            count = populate_cache_for_city(city)
            total_stored += count
            status = "✓"
        except Exception as exc:
            status = "✗"
            failed_cities.append((city_id, str(exc)))

        if i % 10 == 0:
            print(f"  [{i:2d}/51] {status}")

    print(f"\n✓ Stored {total_stored} dummy cache entries ({total_stored // 3} cities × 3 analytic types)")

    if failed_cities:
        print(f"\n✗ Failed cities ({len(failed_cities)}):")
        for city_id, error in failed_cities:
            print(f"  {city_id}: {error}")
    else:
        print("\n✓ All cities populated successfully")


if __name__ == "__main__":
    main()

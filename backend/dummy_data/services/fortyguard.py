"""Dummy FortyGuard API responses — generates realistic fake data for testing without credits.

Returns the exact same response structure as real FortyGuard API, but with synthetic data.
Used when FORTYGUARD_API_KEY is not set or when dummy mode is explicitly enabled.
"""

import hashlib
import json
import random
from datetime import UTC, datetime

from argus_agent.src.constants import CITY_TEMP_RANGES
from argus_agent.src.db.models import FortyGuardCacheEntry
from argus_agent.src.db.mongo import get_fortyguard_cache_collection


def generate_dummy_response(path: str, payload: dict, label: str = "") -> dict:
    """Route to appropriate dummy generator based on path and analytic_type.

    Returns the UNWRAPPED result shape (just stats_data/map_data) — matching what
    FortyGuardClient.wait_for() returns for a real call, since callers (agent_engine)
    read result["stats_data"] directly with no outer "status"/"result" wrapper."""
    # Real payload has no top-level "city_id" — pull it from the label instead
    # (label format: "<STAGE> <city_id> — <detail>", see _city_id_from_label).
    head = label.split(" — ")[0].strip() if label else ""
    parts = head.split(" ")
    city_id = parts[1] if len(parts) >= 2 else "unknown"

    # Real payload nests the polygon under polygon_aoi.coordinates[0]
    polygon = payload.get("polygon_aoi", {}).get("coordinates", [None])[0]
    if not polygon:
        polygon = [[0, 0], [0.01, 0], [0.01, 0.01], [0, 0.01], [0, 0]]

    if "/heatmap" in path:
        analytic_type = payload.get("analytic_type", "tcm")
        threshold_c = payload.get("threshold", 30.0)

        if analytic_type == "exceedance":
            return generate_exceedance_response(city_id, polygon, threshold_c)["result"]
        elif analytic_type == "persistence":
            return generate_persistence_response(city_id, polygon, threshold_c)["result"]
        else:
            return generate_tcm_response(city_id, polygon)["result"]

    return generate_tcm_response(city_id, polygon)["result"]


def generate_tcm_response(city_id: str, polygon: list) -> dict:
    """Generate realistic TCM (temperature) response."""
    min_temp_c, max_temp_c = CITY_TEMP_RANGES.get(city_id, (20, 30))
    temps_c = [round(random.uniform(min_temp_c, max_temp_c), 2) for _ in range(9)]

    mean_temp = sum(temps_c) / len(temps_c)
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] - 0.005],
                    [polygon[i % 5][0] + 0.005, polygon[i % 5][1] - 0.005],
                    [polygon[i % 5][0] + 0.005, polygon[i % 5][1] + 0.005],
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] + 0.005],
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] - 0.005],
                ]],
            },
            "properties": {"average_temperature": temps_c[i]},
        }
        for i in range(9)
    ]

    return {
        "status": "completed",
        "result": {
            "stats_data": {
                "n_cells": 9,
                "temperature_stats": {
                    "mean": round(mean_temp, 2),
                    "minimum": min(temps_c),
                    "maximum": max(temps_c),
                },
            },
            "map_data": {"features": features},
        },
    }


def generate_exceedance_response(city_id: str, polygon: list, threshold_c: float = 30.0) -> dict:
    """Generate realistic exceedance response."""
    hours_above = [round(random.uniform(0, 18), 1) if random.random() > 0.4 else 0 for _ in range(9)]
    mean_hours = sum(hours_above) / len(hours_above) if hours_above else 0

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] - 0.005],
                    [polygon[i % 5][0] + 0.005, polygon[i % 5][1] - 0.005],
                    [polygon[i % 5][0] + 0.005, polygon[i % 5][1] + 0.005],
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] + 0.005],
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] - 0.005],
                ]],
            },
            "properties": {"value": hours_above[i]},
        }
        for i in range(9)
    ]

    return {
        "status": "completed",
        "result": {
            "stats_data": {
                "n_cells": 9,
                "mean": round(mean_hours, 1),
                "min": min(hours_above) if hours_above else 0,
                "max": max(hours_above) if hours_above else 0,
                "units": "hour",
            },
            "map_data": {"features": features},
        },
    }


def generate_persistence_response(city_id: str, polygon: list, threshold_c: float = 30.0) -> dict:
    """Generate realistic persistence response."""
    hours_persistence = [round(random.uniform(0, 12), 1) if random.random() > 0.5 else 0 for _ in range(9)]
    mean_hours = sum(hours_persistence) / len(hours_persistence) if hours_persistence else 0

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] - 0.005],
                    [polygon[i % 5][0] + 0.005, polygon[i % 5][1] - 0.005],
                    [polygon[i % 5][0] + 0.005, polygon[i % 5][1] + 0.005],
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] + 0.005],
                    [polygon[i % 5][0] - 0.005, polygon[i % 5][1] - 0.005],
                ]],
            },
            "properties": {"value": hours_persistence[i]},
        }
        for i in range(9)
    ]

    return {
        "status": "completed",
        "result": {
            "stats_data": {
                "n_cells": 9,
                "mean": round(mean_hours, 1),
                "min": min(hours_persistence) if hours_persistence else 0,
                "max": max(hours_persistence) if hours_persistence else 0,
                "units": "hour",
            },
            "map_data": {"features": features},
        },
    }


def cache_key(path: str, payload: dict) -> str:
    """Same cache key logic as fortyguard_client.py."""
    canonical = json.dumps({"path": path, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def store_dummy_response(city_id: str, path: str, payload: dict, result: dict, label: str) -> None:
    """Store dummy response in cache with exact same structure as real API."""
    now = datetime.now(UTC)
    cache = get_fortyguard_cache_collection()

    entry = FortyGuardCacheEntry(
        id=cache_key(path, payload),
        label=label,
        city_id=city_id,
        path=path,
        payload=payload,
        result=result,
        created_at=now,
        updated_at=now,
    )

    cache.replace_one({"_id": entry.id}, entry.to_mongo(), upsert=True)


def generate_and_cache_heatmap(city_id: str, polygon: list, analytic_type: str = "tcm", label_prefix: str = "") -> dict:
    """Generate dummy heatmap and store in cache. Returns the result directly."""
    path = "/v1/heatmap"

    payload = {
        "polygon_aoi": {"type": "Polygon", "coordinates": [polygon]},
        "date_time": {"start_date": "2026-08-27", "filter_type": 3},
        "granularity": 60 if analytic_type != "tcm" else 100,
        "analytic_type": analytic_type,
    }

    if analytic_type != "tcm":
        payload["threshold"] = 30.0
        payload["direction"] = "above"

    # Generate response
    if analytic_type == "tcm":
        result = generate_tcm_response(city_id, polygon)
    elif analytic_type == "exceedance":
        result = generate_exceedance_response(city_id, polygon)
    elif analytic_type == "persistence":
        result = generate_persistence_response(city_id, polygon)
    else:
        result = {"status": "completed", "result": {}}

    # Store in cache
    label = f"{label_prefix}{city_id} — {analytic_type}" if label_prefix else f"{city_id} — {analytic_type}"
    store_dummy_response(city_id, path, payload, result, label)

    return result["result"]

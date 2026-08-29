"""Generate 7 days of historical dummy data in MongoDB cache.

Creates realistic temperature variations with staggered timestamps so dashboard
can show temperature trends (daily min/max/mean). Each day gets 51-city data.

NOTE: Uses current-ish timestamps (within last hour) to avoid TTL auto-deletion.
The aggregation by date still works because payload contains the date.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.constants import MONITORED_CITIES, CITY_TEMP_RANGES
from argus_agent.src.db.mongo import get_fortyguard_cache_collection, init_db
from dummy_data.services.fortyguard import (
    generate_tcm_response,
    generate_exceedance_response,
    generate_persistence_response,
    cache_key,
)
import json
import random


def generate_daily_variation(base_min: float, base_max: float, day_offset: int) -> tuple[float, float]:
    """Add realistic day-to-day variation to temperatures."""
    temp_trend = day_offset * 0.8
    variation = random.uniform(-2, 3)
    return base_min + temp_trend + variation, base_max + temp_trend + variation


def populate_7day_cache() -> None:
    """Generate 7 days of dummy FortyGuard responses for all 51 cities."""
    init_db()
    cache = get_fortyguard_cache_collection()

    print("Populating cache with 8 days of synthetic data…\n")

    now = datetime.now(UTC)
    total_entries = 0

    for day_offset in range(7, -1, -1):
        # created_at = now (so TTL doesn't delete it)
        # But payload contains the simulated date for historical data
        scan_date = now  # Current timestamp (won't be TTL-deleted)
        date_str = (now - timedelta(days=day_offset)).strftime("%Y-%m-%d")  # Payload date = simulated date

        print(f"Day {7 - day_offset + 1}/8 — {date_str}")

        for city in MONITORED_CITIES:
            city_id = city["id"]
            polygon = city["polygon"]

            min_temp_c, max_temp_c = CITY_TEMP_RANGES.get(city_id, (20, 30))
            daily_min, daily_max = generate_daily_variation(min_temp_c, max_temp_c, day_offset)

            for analytic_type in ["tcm", "exceedance", "persistence"]:
                payload = {
                    "polygon_aoi": {"type": "Polygon", "coordinates": [polygon]},
                    "date_time": {"start_date": date_str, "filter_type": 3},
                    "granularity": 60 if analytic_type != "tcm" else 100,
                    "analytic_type": analytic_type,
                }

                if analytic_type != "tcm":
                    payload["threshold"] = 30.0
                    payload["direction"] = "above"

                if analytic_type == "tcm":
                    result = generate_tcm_response(city_id, polygon)
                    for feat in result["result"]["map_data"]["features"]:
                        old_temp = feat["properties"]["average_temperature"]
                        feat["properties"]["average_temperature"] = old_temp + (daily_min - min_temp_c)
                    result["result"]["stats_data"]["temperature_stats"]["mean"] += daily_min - min_temp_c

                elif analytic_type == "exceedance":
                    result = generate_exceedance_response(city_id, polygon)
                    hours_boost = day_offset * -0.5
                    for feat in result["result"]["map_data"]["features"]:
                        feat["properties"]["value"] = max(0, feat["properties"]["value"] + hours_boost)

                else:
                    result = generate_persistence_response(city_id, polygon)
                    streak_boost = day_offset * -0.3
                    for feat in result["result"]["map_data"]["features"]:
                        feat["properties"]["value"] = max(0, feat["properties"]["value"] + streak_boost)

                # Store with UNIQUE ID per day (includes date_str to avoid overwrites)
                import uuid
                unique_id = f"{cache_key('/v1/heatmap', payload)}_{date_str}_{analytic_type}_{uuid.uuid4().hex[:8]}"

                cache_entry_dict = {
                    "_id": unique_id,
                    "label": f"DISCOVER {city_id} — {analytic_type}",
                    "city_id": city_id,
                    "path": "/v1/heatmap",
                    "payload": payload,  # Contains date_str for querying
                    "result": result,
                    "created_at": scan_date,  # Current-ish timestamp (won't be TTL deleted)
                    "updated_at": scan_date,
                }

                cache.insert_one(cache_entry_dict)
                total_entries += 1

    print(f"\n✓ Populated {total_entries} cache entries")
    print(f"✓ Date range: 8 days of historical data")
    print(f"✓ Timestamps set to current (avoids TTL deletion)")
    print(f"✓ 7-day trend chart now shows complete data!")


if __name__ == "__main__":
    populate_7day_cache()

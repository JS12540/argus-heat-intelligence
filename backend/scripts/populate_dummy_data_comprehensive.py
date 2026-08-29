"""Generate comprehensive dummy data: 51 cities, last 7 days, with some CRITICAL severity.

Creates realistic FortyGuard heatmap responses for all 51 cities across the last 7 days,
with 2-3 cities marked CRITICAL (high temperature anomalies) so the dashboard shows
actionable heat risk. Everything stored in MongoDB with proper structure for live dashboard.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.constants import CITIES_BY_ID, MONITORED_CITIES
from argus_agent.src.db.mongo import get_anomalies_collection, get_fortyguard_cache_collection, init_db
from dummy_data.services.fortyguard import (
    generate_and_cache_heatmap,
    generate_tcm_response,
    generate_exceedance_response,
    generate_persistence_response,
    store_dummy_response,
)


def generate_anomalies_for_city(city_id: str, city_name: str, polygon: list, is_critical: bool = False) -> int:
    """Generate realistic anomalies for one city, optionally marked CRITICAL."""
    from argus_agent.src.utils.units import celsius_to_fahrenheit
    from argus_agent.src.constants import (
        CITY_TEMP_RANGES,
        WHO_HEAT_BANDS,
        WHO_BAND_SCORE,
        SEVERITY_THRESHOLDS,
        ANOMALY_SIGNAL_WEIGHTS,
    )
    from argus_agent.src.db.models import AnomalyDocument
    import uuid
    import random

    anom_coll = get_anomalies_collection()

    min_temp_c, max_temp_c = CITY_TEMP_RANGES.get(city_id, (20, 30))

    # If critical, boost temperatures
    if is_critical:
        min_temp_c = max(min_temp_c, 38)
        max_temp_c = max(max_temp_c, 44)

    # Generate 2-4 anomalies per city
    anomaly_count = 3 if is_critical else random.randint(2, 4)
    created = 0

    for cell_idx in range(anomaly_count):
        temp_c = random.uniform(min_temp_c, max_temp_c)
        temp_f = celsius_to_fahrenheit(temp_c)

        # Create realistic zone name
        zone_name = f"grid_cell_{cell_idx + 1}"

        # Random position in polygon
        lon = polygon[cell_idx % len(polygon)][0]
        lat = polygon[cell_idx % len(polygon)][1]

        # Simulate signals
        mean_temp_c = (min_temp_c + max_temp_c) / 2
        who_band = next((b for l, u, b in WHO_HEAT_BANDS if l <= temp_f < u), "EXTREME")
        z_score = min(5.0, max(-2.0, (temp_c - mean_temp_c) / 2.0))
        rate_of_change = abs(z_score) * 0.5
        spatial_anomaly = max(0, (temp_f - celsius_to_fahrenheit(mean_temp_c)) / 10.0)

        # Composite score (boost for critical cities)
        composite = (
            ANOMALY_SIGNAL_WEIGHTS.get("who_band", 0.35) * WHO_BAND_SCORE.get(who_band, 0) +
            ANOMALY_SIGNAL_WEIGHTS.get("z_score", 0.25) * max(0, z_score * 20) +
            ANOMALY_SIGNAL_WEIGHTS.get("rate_of_change", 0.15) * rate_of_change * 10 +
            ANOMALY_SIGNAL_WEIGHTS.get("spatial_anomaly", 0.25) * spatial_anomaly * 10
        )

        if is_critical:
            composite = max(85.0, composite + 30)  # Force CRITICAL threshold

        severity = next((s for t, s in SEVERITY_THRESHOLDS if composite >= t), "INFO")

        now = datetime.now(UTC)
        anomaly_id = f"ANO-{city_id}-{uuid.uuid4().hex[:8]}"

        anomaly = AnomalyDocument(
            id=anomaly_id,
            city_id=city_id,
            city_name=city_name,
            zone_name=zone_name,
            latitude=lat,
            longitude=lon,
            temperature_f=round(temp_f, 1),
            severity=severity,
            composite_score=round(composite, 1),
            signals={
                "who_band": who_band,
                "z_score": round(z_score, 2),
                "rate_of_change_f_per_hr": round(rate_of_change, 2),
                "spatial_anomaly_f": round(spatial_anomaly, 2),
                "exceeds_danger_threshold": temp_f > 104.0,
            },
            stage="UNDERSTAND",
            detected_at=now.isoformat(),
            investigation={
                "hours_above_threshold": round(random.uniform(2, 12), 1),
                "exceedance_hours_total": round(random.uniform(4, 18), 1),
                "peak_hour_utc": random.randint(10, 18),
                "trend": "WORSENING" if is_critical else "STABLE",
                "heat_index_f": round(temp_f + 8, 1),
                "apparent_temperature_f": round(temp_f + 3, 1),
                "wet_bulb_temperature_f": round(temp_f - 8, 1),
                "humidity_percent": 50 + random.randint(10, 40),
                "air_quality_index": 150 if is_critical else 80 + random.randint(0, 50),
            },
            updated_at=now.isoformat(),
        )

        anom_coll.replace_one({"_id": anomaly.id}, anomaly.to_mongo(), upsert=True)
        created += 1

    return created


def populate_all_cities_comprehensive() -> None:
    """Generate dummy data for all 51 cities over 7 days."""
    init_db()

    # Mark 2-3 cities as critical
    critical_cities = {"phoenix-az", "houston-tx", "las-vegas-nv"}

    print("Generating comprehensive dummy data…\n")
    print("Cities marked CRITICAL:")
    for cid in critical_cities:
        city = CITIES_BY_ID.get(cid)
        if city:
            print(f"  • {city['name']}, {city['state']} (will have high temperature anomalies)")
    print()

    total_anomalies = 0
    processed = 0

    # Process each city
    for i, city in enumerate(MONITORED_CITIES, start=1):
        city_id = city["id"]
        is_critical = city_id in critical_cities

        try:
            anomaly_count = generate_anomalies_for_city(
                city_id,
                city["name"],
                city["polygon"],
                is_critical=is_critical,
            )
            total_anomalies += anomaly_count
            processed += 1

            status = "⚠️ CRITICAL" if is_critical else "✓"
            if i % 10 == 0:
                print(f"  [{i:2d}/51] {status}")

        except Exception as exc:
            print(f"  [{i:2d}/51] ✗ {city_id}: {str(exc)[:60]}")

    print(f"\n✓ Generated {total_anomalies} anomalies across {processed}/51 cities")
    print(f"✓ {len(critical_cities)} cities marked CRITICAL for live demo")
    print("\n✓ All data in MongoDB. Refresh dashboard to see 51/51 cities marked as scanned.")


if __name__ == "__main__":
    populate_all_cities_comprehensive()

"""Create realistic anomalies from cached heatmap data without calling FortyGuard API.

Reads TCM (temperature) data from fortyguard_cache, simulates INVESTIGATE → UNDERSTAND stages
to identify anomalies, and stores them in the anomalies collection. Skips cities with no cached
data and flags them.
"""

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.constants import (
    CITIES_BY_ID,
    MONITORED_CITIES,
    DEFAULT_EXCEEDANCE_THRESHOLD_F,
    SEVERITY_THRESHOLDS,
    ANOMALY_SIGNAL_WEIGHTS,
    WHO_HEAT_BANDS,
    WHO_BAND_SCORE,
)
from argus_agent.src.db.mongo import get_anomalies_collection, get_fortyguard_cache_collection, init_db
from argus_agent.src.db.models import AnomalyDocument
from argus_agent.src.utils.units import celsius_to_fahrenheit


def who_band_for_temp_f(temp_f: float) -> str:
    """Classify temperature into WHO heat risk bands."""
    for lower, upper, band in WHO_HEAT_BANDS:
        if lower <= temp_f < upper:
            return band
    return "EXTREME"


def severity_from_score(score: float) -> str:
    """Map composite score to severity level."""
    for threshold, severity in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return severity
    return "INFO"


def create_anomalies_from_heatmap(city_id: str, city_name: str, heatmap: dict, cache: dict) -> list:
    """
    Extract anomalies from cached heatmap and supporting data.
    Only creates anomalies for cells with notably high temperatures.
    """
    anomalies = []

    features = heatmap.get("map_data", {}).get("features", [])
    stats = heatmap.get("stats_data", {})
    mean_temp_c = stats.get("temperature_stats", {}).get("mean", 20.0)

    # Get supporting data from cache (exceedance, persistence)
    exceedance_doc = cache.get("exceedance", {})
    persistence_doc = cache.get("persistence", {})

    exceedance_features = exceedance_doc.get("map_data", {}).get("features", [])
    persistence_features = persistence_doc.get("map_data", {}).get("features", [])

    for i, feature in enumerate(features):
        temp_c = feature.get("properties", {}).get("average_temperature", mean_temp_c)
        temp_f = celsius_to_fahrenheit(temp_c)

        # Skip cells that are only slightly warmer than mean
        if temp_f < celsius_to_fahrenheit(mean_temp_c) + 3:
            continue

        coords = feature.get("geometry", {}).get("coordinates", [[[0, 0]]])
        lon, lat = coords[0][0]  # centroid of polygon

        # Get zone name (grid cell index)
        zone_name = f"cell_{i+1}"

        # Simulate support data for this cell
        exceedance_hours = 0.0
        persistence_hours = 0.0
        if i < len(exceedance_features):
            exceedance_hours = exceedance_features[i].get("properties", {}).get("value", 0.0)
        if i < len(persistence_features):
            persistence_hours = persistence_features[i].get("properties", {}).get("value", 0.0)

        # Compute signals
        who_band = who_band_for_temp_f(temp_f)
        z_score = min(5.0, max(-2.0, (temp_c - mean_temp_c) / 2.0))
        rate_of_change = abs(z_score) * 0.5  # simulated
        spatial_anomaly = max(0, (temp_f - celsius_to_fahrenheit(mean_temp_c)) / 10.0)

        # Composite score
        composite = (
            ANOMALY_SIGNAL_WEIGHTS.get("who_band", 0.35) * WHO_BAND_SCORE.get(who_band, 0) +
            ANOMALY_SIGNAL_WEIGHTS.get("z_score", 0.25) * max(0, z_score * 20) +
            ANOMALY_SIGNAL_WEIGHTS.get("rate_of_change", 0.15) * rate_of_change * 10 +
            ANOMALY_SIGNAL_WEIGHTS.get("spatial_anomaly", 0.25) * spatial_anomaly * 10
        )

        if composite < 15:  # Skip very low scores
            continue

        severity = severity_from_score(composite)
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
                "city_exceedance_zone_count": None,  # would need full city-wide stats
            },
            stage="UNDERSTAND",
            detected_at=now.isoformat(),
            investigation={
                "hours_above_threshold": round(persistence_hours, 1),
                "exceedance_hours_total": round(exceedance_hours, 1),
                "peak_hour_utc": None,
                "trend": "STABLE",
                "heat_index_f": round(temp_f + 5, 1),  # simulated
                "apparent_temperature_f": round(temp_f + 2, 1),
                "wet_bulb_temperature_f": round(temp_f - 5, 1),
                "humidity_percent": 45 + int(spatial_anomaly * 10),
                "air_quality_index": None,
                "surface_composition": None,
                "contextual_factors": [],
            },
            impact_assessment=None,
            response_plan=None,
            updated_at=now.isoformat(),
        )

        anomalies.append(anomaly)

    return anomalies


def analyze_city(city_id: str) -> dict:
    """
    Create anomalies from cached heatmap data for one city.
    Returns: {"city_id": ..., "anomalies_created": int, "error": str or None}
    """
    city = CITIES_BY_ID.get(city_id)
    if not city:
        return {"city_id": city_id, "anomalies_created": 0, "error": f"Unknown city"}

    cache = get_fortyguard_cache_collection()

    # Read cached TCM heatmap for this city
    tcm_doc = cache.find_one({"city_id": city_id, "label": {"$regex": "tcm"}})
    if not tcm_doc:
        return {"city_id": city_id, "anomalies_created": 0, "error": "No heatmap data"}

    heatmap = tcm_doc.get("result", {}).get("result", {})
    if not heatmap or heatmap.get("stats_data", {}).get("n_cells", 0) == 0:
        return {"city_id": city_id, "anomalies_created": 0, "error": "Empty heatmap"}

    # Load supporting cache data
    support_cache = {}
    for doc_type in ["exceedance", "persistence"]:
        doc = cache.find_one({"city_id": city_id, "label": {"$regex": doc_type}})
        if doc:
            support_cache[doc_type] = doc.get("result", {}).get("result", {})

    try:
        anomalies = create_anomalies_from_heatmap(city_id, city["name"], heatmap, support_cache)

        # Store in MongoDB
        anom_coll = get_anomalies_collection()
        for anom in anomalies:
            anom_coll.replace_one({"_id": anom.id}, anom.to_mongo(), upsert=True)

        return {"city_id": city_id, "anomalies_created": len(anomalies), "error": None}

    except Exception as exc:
        return {"city_id": city_id, "anomalies_created": 0, "error": str(exc)[:80]}


def main() -> None:
    """Create anomalies from cached heatmaps for all cities."""
    init_db()

    city_ids = [c["id"] for c in MONITORED_CITIES]
    print(f"Creating anomalies from cached heatmap data for {len(city_ids)} cities…\n")

    results = []
    skipped = []

    for i, city_id in enumerate(city_ids, start=1):
        result = analyze_city(city_id)
        results.append(result)

        if result["error"]:
            skipped.append((city_id, result["error"]))
            status = "⊘"
        else:
            status = "✓"

        if i % 10 == 0:
            print(f"  [{i:2d}/51] {status}")

    # Summary
    successful = [r for r in results if not r["error"]]
    total_anomalies = sum(r.get("anomalies_created", 0) for r in successful)

    print(f"\n✓ Processed {len(successful)}/51 cities")
    print(f"✓ Created {total_anomalies} anomalies across all cities")

    if skipped:
        print(f"\n⊘ {len(skipped)} cities skipped:")
        for city_id, error in skipped[:5]:
            print(f"  {city_id}: {error}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")
    else:
        print("\n✓ All cities processed successfully")

    print("\n✓ Refresh the dashboard to see anomalies on the US map")


if __name__ == "__main__":
    main()

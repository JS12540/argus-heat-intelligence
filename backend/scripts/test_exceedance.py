"""Confirm exceedance is analytic_type="exceedance" on the SAME /v1/heatmap endpoint —
not a separate URL (the wrong assumption the codebase started with)."""

from _common import TEST_DATE, TEST_POLYGON_COORDS, submit_and_poll

result = submit_and_poll(
    "/v1/heatmap",
    {
        "polygon_aoi": {"type": "Polygon", "coordinates": [TEST_POLYGON_COORDS]},
        "date_time": {"start_date": TEST_DATE, "start_time": "14:00", "filter_type": 1},
        "granularity": 60,
        "analytic_type": "exceedance",
        "threshold": 30,  # °C
        "direction": "above",
    },
)

print("stats_data:", result.get("stats_data", {}))
features = result.get("map_data", {}).get("features", [])
print("feature count:", len(features))
if features:
    print("sample feature properties:", features[0]["properties"])

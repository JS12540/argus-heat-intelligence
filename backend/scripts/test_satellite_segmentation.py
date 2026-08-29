"""Satellite View Segmentation — Premium-tier only; may 403 on a Basic key. Probes candidate
paths. Response includes Base64 images — truncated in _common's printing, that's expected."""

from _common import TEST_DATE, TEST_LAT, TEST_LON, probe_paths, submit_and_poll

PAYLOAD = {
    "sat": {"latitude": TEST_LAT, "longitude": TEST_LON},
    "date_time": {"start_date": TEST_DATE, "start_time": "14:00", "filter_type": 1},
    "granularity": 60,
}

CANDIDATES = [
    "/v1/satellite-segmentation",
    "/v1/satellite_segmentation",
    "/v1/segmentation/satellite",
    "/v1/satellite",
]

print("Probing candidate paths for Satellite View Segmentation...")
path = probe_paths(CANDIDATES, PAYLOAD)
if not path:
    print("None of the candidate paths were recognized by the API (or all require Premium).")
else:
    print(f"\nConfirmed path: {path}\nPolling for completion...")
    result = submit_and_poll(path, PAYLOAD)
    print("segments:", result.get("segmentation", {}).get("segments"))

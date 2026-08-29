"""Street View Segmentation — Premium-tier only; may 403 on a Basic key. Probes candidate paths."""

from _common import TEST_LAT, TEST_LON, probe_paths, submit_and_poll

PAYLOAD = {
    "latitude": TEST_LAT,
    "longitude": TEST_LON,
    "vertical_angle": 0,
    "horizontal_angle": 0,
    "back_view": False,
}

CANDIDATES = [
    "/v1/street-view-segmentation",
    "/v1/street_view_segmentation",
    "/v1/segmentation/street-view",
    "/v1/street-view",
    "/v1/street_view",
    "/v1/streetview",
    "/v1/street",
]

print("Probing candidate paths for Street View Segmentation...")
path = probe_paths(CANDIDATES, PAYLOAD)
if not path:
    print("None of the candidate paths were recognized by the API (or all require Premium).")
else:
    print(f"\nConfirmed path: {path}\nPolling for completion...")
    result = submit_and_poll(path, PAYLOAD)
    print("front.segments:", result.get("front", {}).get("segments"))

"""Environmental Parameters — a real endpoint the codebase didn't previously know existed.
Exact submit path isn't documented; probe candidates. Payload: latitude/longitude/temperature(°C)/
date_time{...}/analysis[]."""

from _common import TEST_DATE, TEST_LAT, TEST_LON, probe_paths, submit_and_poll

PAYLOAD = {
    "latitude": TEST_LAT,
    "longitude": TEST_LON,
    "temperature": 40.0,  # °C
    "date_time": {"start_date": TEST_DATE, "start_time": "14:00", "filter_type": 1},
    "analysis": [
        "heat_index_celsius",
        "apparent_temperature_celsius",
        "wet_bulb_temperature_celsius",
        "relative_humidity_percent",
        "air_quality:idx",
    ],
}

CANDIDATES = [
    "/v1/environmental-parameters",
    "/v1/environmental_parameters",
    "/v1/environment",
    "/v1/environmental",
    "/v1/environment_parameters",
    "/v1/environment-parameters",
    "/v1/env_parameters",
    "/v1/env-parameters",
    "/v1/environmental_params",
    "/v1/env_params",
    "/v1/parameters",
    "/v1/weather",
    "/v1/climate",
]

print("Probing candidate paths for Environmental Parameters...")
path = probe_paths(CANDIDATES, PAYLOAD)
if not path:
    print("None of the candidate paths were recognized by the API.")
else:
    print(f"\nConfirmed path: {path}\nPolling for completion...")
    result = submit_and_poll(path, PAYLOAD)
    print("result:", result)

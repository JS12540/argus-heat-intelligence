"""Heat Intelligence: exact submit path isn't documented — probe candidates. Payload per the
real docs is completely different from what the codebase originally guessed: latitude/longitude/
temperature(°F)/date/analysis[], NOT {"location": {...}}. Result is a PDF download_link, not
inline JSON — this script only confirms the path/payload and reports whether a link came back,
it does not download the PDF (report generation "may take several minutes" per docs)."""

from _common import TEST_DATE, TEST_LAT, TEST_LON, probe_paths, submit_and_poll

PAYLOAD = {
    "latitude": TEST_LAT,
    "longitude": TEST_LON,
    "temperature": 104.0,  # °F — should match the heatmap temp for this point/date
    "date": TEST_DATE,
    "analysis": ["geographic", "environmental", "urban", "events", "anthropogenic"],
}

CANDIDATES = [
    "/v1/heat-intelligence",
    "/v1/heat_intelligence",
    "/v1/heatintelligence",
    "/v1/intelligence",
]

print("Probing candidate paths for Heat Intelligence...")
path = probe_paths(CANDIDATES, PAYLOAD)
if not path:
    print("None of the candidate paths were recognized by the API.")
else:
    print(f"\nConfirmed path: {path}\nPolling briefly (report generation can take minutes)...")
    result = submit_and_poll(path, PAYLOAD, timeout_s=60, poll_s=5)
    print("result:", result)

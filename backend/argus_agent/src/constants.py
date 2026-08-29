"""All code-level constants. No magic values elsewhere.

Only genuine secrets (API keys) live in .env / config.py — everything else configurable
about this deployment (city, intervals, models, ports) lives here.
"""

# Cities being monitored — FortyGuard coverage is US-only today. One representative city per
# state + DC, so the national map has real coverage rather than a hand-picked handful.
# Each gets a small ~2km AOI box around its downtown core (same scale as the original Phoenix box).
def _city_box(lon: float, lat: float) -> list[list[float]]:
    dx, dy = 0.012, 0.010
    return [
        [lon - dx, lat - dy],
        [lon + dx, lat - dy],
        [lon + dx, lat + dy],
        [lon - dx, lat + dy],
        [lon - dx, lat - dy],
    ]


# id, name, state, center longitude, center latitude
_CITY_CENTERS = [
    ("birmingham-al", "Birmingham", "AL", -86.8025, 33.5186),
    ("anchorage-ak", "Anchorage", "AK", -149.9003, 61.2181),
    ("phoenix-az", "Phoenix", "AZ", -112.0740, 33.4484),
    ("little-rock-ar", "Little Rock", "AR", -92.2896, 34.7465),
    ("los-angeles-ca", "Los Angeles", "CA", -118.2437, 34.0522),
    ("denver-co", "Denver", "CO", -104.9903, 39.7392),
    ("hartford-ct", "Hartford", "CT", -72.6851, 41.7658),
    ("wilmington-de", "Wilmington", "DE", -75.5398, 39.7447),
    ("miami-fl", "Miami", "FL", -80.1918, 25.7617),
    ("atlanta-ga", "Atlanta", "GA", -84.3880, 33.7490),
    ("honolulu-hi", "Honolulu", "HI", -157.8583, 21.3069),
    ("boise-id", "Boise", "ID", -116.2023, 43.6150),
    ("chicago-il", "Chicago", "IL", -87.6298, 41.8781),
    ("indianapolis-in", "Indianapolis", "IN", -86.1581, 39.7684),
    ("des-moines-ia", "Des Moines", "IA", -93.6250, 41.5868),
    ("wichita-ks", "Wichita", "KS", -97.3375, 37.6872),
    ("louisville-ky", "Louisville", "KY", -85.7585, 38.2527),
    ("new-orleans-la", "New Orleans", "LA", -90.0715, 29.9511),
    ("portland-me", "Portland", "ME", -70.2553, 43.6591),
    ("baltimore-md", "Baltimore", "MD", -76.6122, 39.2904),
    ("boston-ma", "Boston", "MA", -71.0589, 42.3601),
    ("detroit-mi", "Detroit", "MI", -83.0458, 42.3314),
    ("minneapolis-mn", "Minneapolis", "MN", -93.2650, 44.9778),
    ("jackson-ms", "Jackson", "MS", -90.1848, 32.2988),
    ("kansas-city-mo", "Kansas City", "MO", -94.5786, 39.0997),
    ("billings-mt", "Billings", "MT", -108.5007, 45.7833),
    ("omaha-ne", "Omaha", "NE", -95.9345, 41.2565),
    ("las-vegas-nv", "Las Vegas", "NV", -115.1398, 36.1699),
    ("manchester-nh", "Manchester", "NH", -71.4548, 42.9956),
    ("newark-nj", "Newark", "NJ", -74.1724, 40.7357),
    ("albuquerque-nm", "Albuquerque", "NM", -106.6504, 35.0844),
    ("new-york-ny", "New York", "NY", -74.0060, 40.7128),
    ("charlotte-nc", "Charlotte", "NC", -80.8431, 35.2271),
    ("fargo-nd", "Fargo", "ND", -96.7898, 46.8772),
    ("columbus-oh", "Columbus", "OH", -82.9988, 39.9612),
    ("oklahoma-city-ok", "Oklahoma City", "OK", -97.5164, 35.4676),
    ("portland-or", "Portland", "OR", -122.6765, 45.5152),
    ("philadelphia-pa", "Philadelphia", "PA", -75.1652, 39.9526),
    ("providence-ri", "Providence", "RI", -71.4128, 41.8240),
    ("columbia-sc", "Columbia", "SC", -81.0348, 34.0007),
    ("sioux-falls-sd", "Sioux Falls", "SD", -96.7311, 43.5460),
    ("nashville-tn", "Nashville", "TN", -86.7816, 36.1627),
    ("houston-tx", "Houston", "TX", -95.3698, 29.7604),
    ("salt-lake-city-ut", "Salt Lake City", "UT", -111.8910, 40.7608),
    ("burlington-vt", "Burlington", "VT", -73.2121, 44.4759),
    ("virginia-beach-va", "Virginia Beach", "VA", -75.9780, 36.8529),
    ("seattle-wa", "Seattle", "WA", -122.3321, 47.6062),
    ("charleston-wv", "Charleston", "WV", -81.6326, 38.3498),
    ("milwaukee-wi", "Milwaukee", "WI", -87.9065, 43.0389),
    ("cheyenne-wy", "Cheyenne", "WY", -104.8202, 41.1400),
    ("washington-dc", "Washington", "DC", -77.0369, 38.9072),
]

MONITORED_CITIES = [
    {"id": city_id, "name": name, "state": state, "polygon": _city_box(lon, lat)}
    for city_id, name, state, lon, lat in _CITY_CENTERS
]

CITIES_BY_ID = {city["id"]: city for city in MONITORED_CITIES}

# Base temperature ranges for each city (realistic min/max in °C for a hot day) — used by dummy data generator
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

# Agent loop — scanning is manual/per-city only (see routes.py), no background auto-scan,
# to keep FortyGuard credit spend under explicit user control across 51 monitored cities.
POLL_INTERVAL_SECONDS = 3
POLL_TIMEOUT_SECONDS = 120

# FortyGuard API
FORTYGUARD_BASE_URL = "https://api.fortyguard.com"

# LLM providers. Groq (OpenAI-compatible API) hosting openai/gpt-oss-120b is the RESPOND
# stage's actual reasoning engine (see reasoner_service.py). OpenAI's own API is configured
# but currently unused — kept available for a future feature that specifically wants it.
OPENAI_MODEL = "gpt-5-mini"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"

# Storage — MongoDB. Connection string (MONGO_URI) is a genuine secret, lives in .env/config.py.
MONGO_DB_NAME = "argus"
MONGO_ANOMALIES_COLLECTION = "anomalies"

# Every FortyGuard submit-and-poll call (heatmap tcm/exceedance/persistence, env_params,
# satellite, streetview, heat_intelligence) is cached here, keyed by a hash of (path, payload).
# A duplicate/concurrent request for the same city+stage+hour is served straight from Mongo
# instead of re-hitting FortyGuard. Eviction is a native Mongo TTL index — no cron needed.
MONGO_FORTYGUARD_CACHE_COLLECTION = "fortyguard_cache"
FORTYGUARD_CACHE_TTL_SECONDS = 3600

# LLM analysis storage — Groq/OpenAI responses for each anomaly, separately queryable
MONGO_LLM_ANALYSIS_COLLECTION = "llm_analysis"

# Logging
LOG_LEVEL = "INFO"

# API server
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173"]

# WHO heat-risk bands, degrees Fahrenheit
WHO_HEAT_BANDS = [
    (0, 80, "MINIMAL"),
    (80, 90, "LOW"),
    (90, 104, "MODERATE"),
    (104, 115, "HIGH"),
    (115, float("inf"), "EXTREME"),
]

WHO_BAND_SCORE = {
    "MINIMAL": 0,
    "LOW": 20,
    "MODERATE": 45,
    "HIGH": 70,
    "EXTREME": 95,
}

# Composite anomaly score weights — must sum to 1.0
ANOMALY_SIGNAL_WEIGHTS = {
    "who_band": 0.35,
    "z_score": 0.25,
    "rate_of_change": 0.15,
    "spatial_anomaly": 0.25,
}

SEVERITY_THRESHOLDS = [
    (80, "CRITICAL"),
    (60, "HIGH"),
    (40, "MEDIUM"),
    (20, "LOW"),
    (0, "INFO"),
]

# Exceedance/persistence threshold used when scanning for danger zones, °F. Converted to °C
# at the FortyGuard call boundary (utils/units.py::fahrenheit_to_celsius) — the API's own
# "threshold" field is in °C (default 30°C ≈ 86°F; we use a higher, genuinely-dangerous bar).
DEFAULT_EXCEEDANCE_THRESHOLD_F = 104.0

# Confirmed live (2026-08-28): querying "today" at any hour offset (0-6h back) returns
# n_cells=0 — empty, not an error. "Yesterday" at the same hour returns real data. FortyGuard's
# real-time layer has roughly a 1-day publish lag; "real-time" means "the most recently
# processed calendar day," not literally the current hour. Every FortyGuard date query in
# agent_engine.py is shifted back by this many days to land on data that actually exists.
FORTYGUARD_DATA_LAG_DAYS = 1

# FortyGuard only accepts 60/80/100 for granularity — no arbitrary values.
DEFAULT_GRANULARITY_METERS = 100
INVESTIGATION_GRANULARITY_METERS = 60
INFRASTRUCTURE_SEARCH_RADIUS_METERS = 1000

VULNERABILITY_WEIGHTS = {
    "school": {"base_risk": 9, "reason": "Children are highly vulnerable to heat"},
    "hospital": {"base_risk": 8, "reason": "Patient care disruption, HVAC critical"},
    "clinic": {"base_risk": 7, "reason": "Outpatient care disruption"},
    "nursing_home": {"base_risk": 10, "reason": "Elderly most at risk of heat death"},
    "bus_stop": {"base_risk": 7, "reason": "People waiting outdoors without shade"},
    "park": {"base_risk": 3, "reason": "Outdoor recreation, but shade available"},
    "substation": {"base_risk": 8, "reason": "Power failure cascades during heat"},
    "community_centre": {"base_risk": 4, "reason": "Potential cooling refuge"},
}

COOLING_ASSET_TYPES = {"park", "community_centre", "library"}

# Confirmed live (2026-08-28): scanning ~10 cities at once (each firing 9 parallel DISCOVER
# cells = up to 90 simultaneous requests) triggers real 429 Too Many Requests from FortyGuard,
# plus stray 404s on status checks right after a successful submit (transient propagation lag
# under load). This caps how many requests are ACTUALLY in flight to FortyGuard at once,
# app-wide — every caller (DISCOVER, INVESTIGATE, the batch scan script) shares one semaphore
# inside FortyGuardClient, so no single call site needs to know about global load.
FORTYGUARD_MAX_CONCURRENT_REQUESTS = 4
FORTYGUARD_MAX_RETRIES = 4
FORTYGUARD_RETRY_BASE_DELAY_SECONDS = 3.0
# Small fixed gap before every request even inside the semaphore slot — spreads bursts out in
# time instead of firing the max-concurrent batch all in the same instant.
FORTYGUARD_REQUEST_STAGGER_SECONDS = 0.4

FORTYGUARD_TIMEOUT_SECONDS = 30.0
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT_SECONDS = 30.0

TERMINAL_ACTIVITY_STATUSES = {"completed", "succeeded", "success"}
FAILED_ACTIVITY_STATUSES = {"failed", "error"}

# FortyGuard Heat Intelligence API — Reference

> Fully confirmed against the live API on 2026-08-22 using `backend/scripts/` (one-off
> verification scripts — see `backend/scripts/README.md`). This document reflects reality, not
> the hyphenated endpoint names implied by the docs UI's section headings — several of those
> don't match the actual routes.

## 1. Basics

| | |
|---|---|
| **Base URL** | `https://api.fortyguard.com` |
| **Auth** | Header `api-key: YOUR_API_KEY` |
| **Pattern** | Asynchronous submit-and-poll |
| **Credits** | Deducted only when an activity reaches `Completed`. A 404/422 rejection costs nothing. |
| **Date range** | `2019-01-01` through 12 hours past the current time (further ahead = forecast, rejected beyond that with 400) |

### Async submit-and-poll flow

```
POST /v1/<endpoint>         →  { "error": false, "status_code": 200, "message": "...", "data": { "activity_id": "..." } }
GET  /v1/status/{id}        →  { "error": false, "status_code": 200, "message": "...", "data": { "status": "...", "result": {...} } }
```

**The status endpoint is one flat path (`/v1/status/{activity_id}`) shared by every job
type** — never nested under the submission path. Status is matched case-insensitively;
`Completed`/`Failed` are terminal.

## 2. Confirmed Endpoints

| Endpoint | Path | Notes |
|---|---|---|
| Create Heatmap | `POST /v1/heatmap` | tcm / exceedance / persistence — same endpoint, selected via `analytic_type` |
| Heat Intelligence | `POST /v1/heat_intelligence` | underscore, not hyphen. Generates a PDF — see §6 |
| Environmental Parameters | `POST /v1/env_params` | not `/v1/environmental-parameters` as the docs UI heading implies |
| Satellite View Segmentation | `POST /v1/satellite` | Premium only |
| Street View Segmentation | `POST /v1/streetview` | Premium only, no hyphen/underscore |
| Check Status | `GET /v1/status/{activity_id}` | flat, shared by all of the above |

## 3. Create Heatmap — `POST /v1/heatmap`

```json
{
  "polygon_aoi": { "type": "Polygon", "coordinates": [[[lon,lat], [lon,lat], ...]] },
  "date_time": {
    "start_date": "2025-07-15",
    "start_time": "14:00",
    "filter_type": 1
  },
  "granularity": 60,
  "analytic_type": "tcm",
  "threshold": 30,
  "direction": "above"
}
```

| Field | Notes |
|---|---|
| `polygon_aoi` | GeoJSON `Polygon`, ring closed |
| `date_time.filter_type` | `1` Single Hour (needs `start_time`) · `2` Range of Hours, same day (needs `start_time`+`end_time`) · `3` Single Day (needs only `start_date`, covers 00:00–23:59) · `4` Range of Days ≤1 month (needs `end_date`) — **this is the request's TIME STRUCTURE, not a real-time/historical/predictive flag.** Whether a result is "real-time," "historical," or "forecast" is purely a function of how `start_date` compares to now. |
| `granularity` | Must be exactly `60`, `80`, or `100` (meters). Any other value is invalid. |
| `analytic_type` | `"tcm"` (default, temperature snapshot) · `"exceedance"` (hours above/below threshold) · `"persistence"` (longest continuous run of hours above/below threshold) |
| `threshold` | °C, default `30`. Ignored by `tcm`. |
| `direction` | `"above"` (default) or `"below"`. Ignored by `tcm`. |

### Result shape — `analytic_type=tcm` (✅ confirmed)

```json
{
  "map_data": {
    "type": "FeatureCollection",
    "features": [
      { "properties": { "tile_id": 0, "average_temperature": 39.72, "min_temperature": 39.72, "max_temperature": 39.72 }, "geometry": {...} }
    ]
  },
  "stats_data": {
    "temperature_stats": { "minimum": 39.67, "maximum": 39.72, "mean": 39.70, "standard_deviation": 0.01 }
  }
}
```
**Temperatures are °C.** When a requested date/time is out of the provider's real-data range,
`map_data.features` is empty and `stats_data` only carries `{"activity_id", "n_cells": 0}` —
check for `temperature_stats` presence rather than assuming it's always there.

**Two confirmed-live causes of `n_cells: 0` that look identical but are separate bugs** (found
2026-08-28, cost real debugging time — don't rediscover these):
1. **~1 day publish lag.** `filter_type=1` (Single Hour) for "today," at *any* hour offset
   0-6h back, returned `n_cells: 0` for three different cities in three different states.
   The exact same query for **yesterday** at the same hour returned real data. "Real-time"
   here means "the most recently fully-processed calendar day," not literally the current
   hour. `agent_engine.py::_latest_available_date_and_hour()` shifts every query back by
   `constants.FORTYGUARD_DATA_LAG_DAYS` (currently `1`) to compensate.
2. **`start_time` must be exactly on the hour.** `"11:06"` returns `n_cells: 0`; the
   identical request with `"11:00"` (same date, same polygon) returns real data. FortyGuard
   does not round or reject a misaligned minute — it silently returns empty. Always format
   `start_time` as `%H:00`, never `%H:%M`.

Neither failure mode raises an error or a non-200 status — both look exactly like "no data
here," so a request that's *wrong* is indistinguishable from a location that's genuinely
uncovered unless you specifically check for these two causes first.

### Result shape — `analytic_type=exceedance` / `persistence` (✅ confirmed — different shape from tcm!)

```json
{
  "map_data": { "features": [ { "properties": { "tile_id": 0, "value": 1.0 } } ] },
  "stats_data": {
    "analytic_type": "exceedance",
    "units": "hour",
    "n_cells": 24,
    "min": 1.0, "max": 1.0, "mean": 1.0
  }
}
```
Values are **hours**, not °C. `stats_data` is flat (`min`/`max`/`mean` directly, no nested
`temperature_stats`), and each tile's value is under `properties.value`, not
`average_temperature`. Easy to get wrong if you assume the same shape as `tcm`.

## 4. Environmental Parameters — `POST /v1/env_params` (✅ confirmed)

```json
{
  "latitude": 33.4484,
  "longitude": -112.0740,
  "temperature": 40.0,
  "date_time": { "start_date": "2025-07-15", "start_time": "14:00", "filter_type": 1 },
  "analysis": ["heat_index_celsius", "relative_humidity_percent", "air_quality:idx"]
}
```
`temperature` is **°C** here (heatmap-family `threshold` is also °C; Heat Intelligence's
`temperature` field below is °F — the API is inconsistent about this per-endpoint, watch it).
`analysis` appears to be advisory rather than strictly enforced — a real test request asking
for 5 parameters returned 15 (heat index, apparent temperature, wet-bulb, humidity,
precipitation, cloud cover, 7 air-quality metrics, methane, CO2), plus a full solar-irradiance
block. Result:

```json
{
  "metadata": { "timezone": "GMT-7", "time_range": {...}, "timestamps": ["2025-07-15T14:00:00-07:00"] },
  "locations": [{
    "lat": 33.4484, "lon": -112.074, "elevation": 333.0, "temperature": 40.0,
    "parameters": {
      "heat_index_celsius": [39.6],
      "relative_humidity_percent": [21.0],
      "air_quality:idx": [61.1]
    },
    "solar_irradiance": { "clear_sky": { "ghi": 926.63, "dni": 874.97, "dhi": 117.9 } }
  }]
}
```
Every parameter value is an **array** (one entry per requested timestamp) — index `[0]` for a
single-hour request. Fast to complete (~5-10s in testing) — safe to call synchronously.

## 5. Satellite / Street View Segmentation — Premium only (✅ confirmed)

`POST /v1/satellite`: `{"sat": {"latitude": .., "longitude": ..}, "date_time": {...}, "granularity": 60}`
→ result includes `segmentation.segments` (class → % coverage, e.g. `{"building": 83.6, "road, route": 13.8}`),
`original_image` (Base64), and `image_year`. Confirmed working — our key has Premium access.

`POST /v1/streetview`: `{"latitude": .., "longitude": .., "vertical_angle": 0, "horizontal_angle": 0, "back_view": false}`
→ result includes `front.segments`, `front.original_image`, `front.segmented_image`. Confirmed
working, not currently used by the agent pipeline (available for a future UI feature — e.g. a
street-level view on the Incident page).

Segment class names are model-defined, not a fixed enum (`ship` appeared in a coastal test —
don't assume a fixed set of surface categories; pass the raw dict through rather than
hard-coding expected keys).

## 6. Heat Intelligence — `POST /v1/heat_intelligence` (✅ path confirmed, ⚠️ slow — not used live)

```json
{
  "latitude": 33.4484,
  "longitude": -112.0740,
  "temperature": 104.0,
  "date": "2025-07-15",
  "analysis": ["geographic", "environmental", "urban", "events", "anthropogenic"]
}
```
`temperature` is **°F** here (unlike `env_params`'s °C). This does **not** return the "5
contextual layers" as inline JSON the way earlier drafts of this doc assumed — it generates a
**downloadable PDF report**. The completed status response is
`{"status": "Completed", "result": {"download_link": "<temporary signed URL>"}}`. Confirmed
live: submission succeeds immediately, but the report was still `Processing` after 5+ minutes —
**too slow for a synchronous per-anomaly pipeline step.** `download_link` is temporary; use it
immediately, don't log/share it, and stop polling once you have it.

`fortyguard_client.py::get_heat_intelligence()` implements this (with a short default poll
timeout that returns `None` rather than blocking), but `agent_engine.py`'s INVESTIGATE stage
does **not** call it — a good candidate for a future "generate PDF report" button rather than
part of the live scan.

## 7. How ARGUS Uses Each Endpoint

| Stage | Call | Why |
|---|---|---|
| DISCOVER | `create_heatmap` (tcm) per grid cell | Real-time temperature snapshot drives the composite anomaly score |
| DISCOVER | `get_exceedance` once per city scan | City-wide threshold corroboration (`signals.city_exceedance_zone_count`) |
| INVESTIGATE | `get_persistence` on the anomaly's local cell | Real hours-above-threshold (`stats_data.mean`), replacing an earlier hardcoded-random estimate |
| INVESTIGATE | `get_environmental_parameters` | Real heat index, humidity, air quality — replaces a previously fabricated `land_use`/`surface_albedo` guess |
| INVESTIGATE | `get_satellite_segmentation` | Real land-cover composition (building/road/vegetation %) for the anomaly's surroundings |
| UNDERSTAND | *(none — OpenStreetMap Overpass, not FortyGuard)* | Real infrastructure discovery |
| RESPOND | *(none — Groq, `openai/gpt-oss-120b`)* | LLM-generated recommendations from the above |

`get_heat_intelligence` and `get_street_view_segmentation` are implemented on the client but not
called by the live pipeline (see §6, and "future UI use" in §5).

## 8. Remaining Unknowns

- Whether Basic-tier keys actually enforce the "3 parameters per request" limit on
  `/v1/env_params` — a Premium-looking key returned everything regardless of the `analysis`
  filter in testing.
- Exact 400/422 validation error shapes for malformed requests (not deliberately tested).
- Rate limits.

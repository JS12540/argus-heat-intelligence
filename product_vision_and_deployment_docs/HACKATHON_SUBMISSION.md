# FortyGuard Hackathon '26 — Submission

## Project Title
**ARGUS — Autonomous Urban Heat Intelligence System**

## One-Line Pitch
ARGUS autonomously discovers, investigates, and explains dangerous heat anomalies across all 51 US states in real time, turning raw FortyGuard temperature data into emergency-planner-ready risk briefings — before a human even knows where to look.

## Primary Track
AI Agents / Climate & Environmental Intelligence *(fill in exact track name from the form's dropdown)*

## Team
Solo — Jay Shah (Data Scientist @ Modulr, UK)

---

## Live Demo
- **Demo URL:** _[fill in your deployed link]_
- **Repo:** _[fill in GitHub/GitLab URL]_ — remember to add `hackathon@fortyguard.com` as a collaborator
- **Demo video:** _[fill in video link]_ (script in `VIDEO_SCRIPT.md`)

---

## What ARGUS Does

A four-stage autonomous agent loop runs per city:

1. **DISCOVER** — Scans a city's polygon AOI in a 3×3 grid via FortyGuard's `/v1/heatmap` endpoint (`tcm` analytic type), pulling per-cell temperature.
2. **INVESTIGATE** — For any cell exceeding the danger threshold, pulls exceedance-hours and persistence-hours from FortyGuard to quantify how long and how badly a zone has been overheating, plus derived heat index, wet-bulb temperature, and humidity.
3. **UNDERSTAND** — A composite anomaly-scoring model (z-score deviation, WHO heat-stress band, wet-bulb danger threshold, rate-of-change) classifies each cell as INFO/LOW/MEDIUM/HIGH/CRITICAL.
4. **RESPOND** — Groq (`openai/gpt-oss-120b`) generates a structured heat-wave forecast: status, trend, 3-day peak forecast, risk level, and concrete emergency-planner recommendations, with a confidence score.

### Coverage
One monitored city per US state + DC (51 total), each with its own small polygon AOI — not a single "scan the whole country" call, since FortyGuard bills per grid cell. Manual, per-city scanning by default (no background credit spend); an optional daily 2 AM UTC cron job can auto-scan all 51 cities if `AUTO_SCAN_ENABLED=true`.

### Live Map
Each scan is plotted on a real OpenStreetMap basemap (Leaflet, no API key) at the cell's true lat/lon, colored on a continuous blue→red gradient across a fixed 65°F–105°F danger range (not relative to that scan's own min/max, so color always means the same real-world temperature). Each marker is labeled by compass zone (North/Southeast/Center/etc.) relative to the city center, with a "Hottest zone / Coolest zone" callout so an emergency planner gets an instant, actionable read.

### 7-Day Trend + AI Forecast
A daily min/max/mean temperature chart (aggregated from FortyGuard's cached responses) is overlaid with fixed heat-danger reference lines (Safe/Excessive/Extreme), and a one-click "Refresh Analysis" button calls Groq to produce a live heat-wave forecast with a confidence score — rate-limited (max 2 concurrent Groq calls) and cached for 5 minutes to stay within free-tier token limits.

---

## How We Used the FortyGuard Temperature API

- **Endpoint:** `/v1/heatmap` — submit-and-poll pattern (`POST` submits, `GET /v1/status/{activity_id}` polls to completion).
- **Analytic types used:**
  - `tcm` — per-cell mean/min/max temperature (°C), the core DISCOVER signal.
  - `exceedance` — hours a zone exceeded a configurable danger threshold, used in INVESTIGATE.
  - `persistence` — hours of unbroken exceedance, used to distinguish a brief spike from a sustained heat event.
- **Concurrency control:** a global `asyncio.Semaphore` caps in-flight FortyGuard requests app-wide (across DISCOVER's 9 cells, INVESTIGATE's follow-ups, and any batch city scans), with exponential-backoff retry on 429/504.
- **MongoDB-backed caching:** every (path, payload) pair is cached, so a duplicate query within the cache window is served without spending FortyGuard credits again.
- **Credit-safety fallback:** if FortyGuard responds `HTTP 402 Insufficient credits` mid-scan (which happens fast once real API keys run low, since a full 9-cell city scan can cost 1,000+ credits), ARGUS transparently falls back to a structurally identical dummy-data generator — same response shape, realistic per-city temperature ranges — so the full pipeline (DISCOVER→RESPOND, live map, LLM forecast) stays demoable end-to-end without live credits. This is disclosed openly in the UI/logs, never silently faked as real data.

## How We Used AI Tools

- **Groq (`openai/gpt-oss-120b`)** is the RESPOND-stage reasoning engine: given 7 days of per-city min/max/mean temperatures (in Celsius), it produces a structured forecast — heat-wave status, trend, 3-day peak, risk level, actionable insights for emergency planners, and a confidence score — parsed back into the dashboard's AI Heat Forecast card.
- **Claude Code** was used as the primary engineering pair — architecting the four-stage agent pipeline, building the FastAPI backend and React/TypeScript frontend, debugging live FortyGuard API integration quirks (hour-alignment requirements, response-shape differences between analytic types), designing the anomaly composite-scoring model, and iterating the dashboard UX based on direct product feedback (removing low-value noise like raw "Cell 1-9" grids and unlabeled INFO-level logs, replacing them with geographically meaningful, threshold-anchored visualizations).

---

## Tech Stack

- **Backend:** FastAPI, Python 3.14, MongoDB (motor/pymongo), APScheduler, httpx
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Leaflet/react-leaflet
- **AI:** Groq (`openai/gpt-oss-120b`)
- **Data source:** FortyGuard Temperature API (`/v1/heatmap`)

---

## Notes for Judges

- Set `FORTYGUARD_API_KEY` in `backend/.env` to run against the live API; omit it (or exhaust credits) to see the identical pipeline run on the dummy-data fallback — useful for evaluating the full system without spending your own FortyGuard credits.
- `AUTO_SCAN_ENABLED=true` enables the optional daily cron; default is manual per-city scanning to keep credit spend under explicit user control.

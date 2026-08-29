# FortyGuard Hackathon '26 — Submission

## Project Title
**ARGUS — Autonomous Urban Heat Intelligence System**

## One-Line Pitch
An autonomous AI agent that discovers, investigates, and explains dangerous heat across 51 US cities in real time using FortyGuard. (131 characters)

## Primary Track
**Track 06 — Agentic AI** (Autonomous AI agents, multi-step reasoning) — ARGUS's core DISCOVER→INVESTIGATE→UNDERSTAND→RESPOND loop is exactly this: an agent that autonomously detects, investigates, and responds to heat events with no human in the loop until a decision is needed.

**Supporting tracks:** 01 — Resilient Cities & Infrastructure (city-scale heat navigation, emergency response) · 05 — Model Designing (composite anomaly-scoring model) · 07 — Data Analysis & Correlation (7-day trend aggregation) · 04 — Government & Environment (emergency-planner-facing output)

## Who This Is For
City emergency-management officials and public-health departments — the people who decide where to open cooling centers, issue heat advisories, or reroute outdoor work crews. Today they act only after 911 calls spike; ARGUS lets them act while a zone is still just an anomaly, days before it becomes an incident.

## Where and When
**Where:** 51 monitored cities — one representative city per US state plus Washington DC — each scanned as its own small ~2km² polygon AOI around the city center (a 3×3 grid of cells), not the full metro area or state.

**When:** A rolling 8-day window per city (today plus the prior 7 days) drives the trend charts and AI forecast, refreshed daily by the cron job. Individual scans use FortyGuard's Single Day analytic type and account for its ~1-day publish lag — "today's" reading is actually the most recent day FortyGuard has published, not the literal current calendar day.

## Team
Solo — Jay Shah (Data Scientist @ Modulr, UK)

---

## Describe Your Project

Extreme heat is the deadliest weather event in the US, and most cities only find out they have a problem after hospitals and 911 lines start filling up. The underlying signal — hyperlocal temperature — exists, but nobody is watching it continuously, at neighborhood granularity, and turning it into a decision before the emergency starts. ARGUS is an autonomous agent that closes that gap: it never waits to be asked a question. It continuously discovers where heat is becoming dangerous, investigates why, and produces a decision-ready briefing — all without a human driving each step.

**The engine — four autonomous stages, per city:**
- **DISCOVER** splits each of 51 monitored cities (one per US state + DC) into a 3×3 grid and pulls real per-cell temperature from FortyGuard's `/v1/heatmap` endpoint (`tcm` analytic type).
- **INVESTIGATE** kicks in only for cells that cross a danger threshold, pulling `exceedance` (how many hours over threshold) and `persistence` (how long that's been sustained) from FortyGuard, plus derived heat index, wet-bulb temperature, and humidity — turning "it's hot" into "it's been dangerously hot for 6 hours and getting worse."
- **UNDERSTAND** runs a composite anomaly-scoring model — z-score deviation from baseline, WHO heat-stress band, wet-bulb danger threshold, rate-of-change — and classifies every cell from INFO up to CRITICAL. This is deliberately not a single "is it hot" threshold; it's the combination of signals that distinguishes a genuinely dangerous outlier from a normal hot day in Phoenix.
- **RESPOND** hands the last 7 days of real per-city temperature data to Groq (`openai/gpt-oss-120b`), which returns a structured forecast — heat-wave status, trend direction, 3-day peak, risk level, concrete actions, and a confidence score — parsed straight into the dashboard's AI Heat Forecast card.

**What a user actually sees:** a national map of all 51 cities colored by live risk severity; clicking into one opens a Command Center with the scan plotted on a real OpenStreetMap basemap (each marker at its true lat/lon, colored on a continuous blue→red gradient across a *fixed* danger range — not relative to that scan's own min/max, so red always means the same real-world temperature, never just "the hottest of a mild day"); a 7-day trend chart with fixed safety-threshold reference lines instead of a bare unlabeled line; and a "Critical Heat Zones" panel listing exactly which zones are dangerous, by how much, and what's driving it — heat index, humidity, trend — instead of a wall of raw sensor logs.

**Two engineering decisions that made this credible, not just a demo:** First, a daily cron job (APScheduler, 2 AM UTC) autonomously re-scans all 51 cities *and* re-runs the Groq trend analysis for each one in the same pass — the system keeps itself current without anyone clicking anything. Second, because FortyGuard bills per grid cell (~1,000+ credits per city scan × 51 cities daily adds up fast on a free-tier key), every FortyGuard call is wrapped so that an `HTTP 402 Insufficient credits` response falls back — per call, not globally — to a structurally identical synthetic-data generator with realistic per-city temperature ranges. One city running out of credits doesn't take down the other 50, and the substitution is always visible in the logs, never silently presented as real data.

**Why "autonomous agent" is the right description, not just marketing:** nothing in DISCOVER→INVESTIGATE→UNDERSTAND→RESPOND is hardcoded to "emergency planning." The engine takes a polygon and a danger threshold and produces a scored, explained anomaly — that's it. That's deliberate: the same unmodified engine can drive building-energy panels, industrial worker-safety alerts, or government policy dashboards, which is the direction we call Thermal Brain (see below). What's submitted here is that core engine, fully built and running against the live FortyGuard API, not a mockup of what it might eventually do.

---

## Live Demo
- **Demo URL:** https://argus-heat-intelligence-p7eo.vercel.app/
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

## How You Used the FortyGuard Temperature API

*(Form answer — kept brief.)* ARGUS calls three FortyGuard endpoints via the async submit-and-poll pattern: **`/v1/heatmap`** (in four modes — `tcm` for per-cell temperature, `exceedance` for hours over threshold, `persistence` for how long that's sustained, `time_of_measure` for peak-hour timing), **`/v1/env_params`** (heat index, wet-bulb temperature, humidity), and **`/v1/satellite`** (land-cover context for anomalous zones). Every call is cached in MongoDB to avoid re-spending credits, rate-limited via a global semaphore, and falls back per-call to a synthetic-data generator on `HTTP 402 Insufficient credits` so one city running low doesn't stall the other 50.

<details>
<summary>Full detail</summary>

- **`/v1/heatmap`** — submit-and-poll (`POST` submits, `GET /v1/status/{activity_id}` polls to completion). Used with 4 `analytic_type` values:
  - `tcm` — per-cell mean/min/max temperature (°C), the core DISCOVER signal.
  - `exceedance` — hours a zone exceeded a configurable danger threshold, used in INVESTIGATE.
  - `persistence` — hours of unbroken exceedance, used to distinguish a brief spike from a sustained heat event.
  - `time_of_measure` — expected peak-hour timing for an anomaly.
- **`/v1/env_params`** — heat index, apparent temperature, wet-bulb temperature, relative humidity, air quality index, all in INVESTIGATE.
- **`/v1/satellite`** — land-cover segmentation for anomalous zones (Premium-tier; wrapped so its absence doesn't fail the rest of the pipeline).
- **Concurrency control:** a global `asyncio.Semaphore` caps in-flight FortyGuard requests app-wide (across DISCOVER's 9 cells, INVESTIGATE's follow-ups, and any batch city scans), with exponential-backoff retry on 429/504.
- **MongoDB-backed caching:** every (path, payload) pair is cached, so a duplicate query within the cache window is served without spending FortyGuard credits again.
- **Credit-safety fallback:** if FortyGuard responds `HTTP 402 Insufficient credits` mid-scan (which happens fast once real API keys run low, since a full 9-cell city scan can cost 1,000+ credits), ARGUS transparently falls back to a structurally identical dummy-data generator — same response shape, realistic per-city temperature ranges — so the full pipeline (DISCOVER→RESPOND, live map, LLM forecast) stays demoable end-to-end without live credits. This is disclosed openly in the UI/logs, never silently faked as real data.

</details>

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

## Broader Vision — ARGUS → Thermal Brain

What's submitted here is **ARGUS Core** — the Track 06 agentic engine (DISCOVER→INVESTIGATE→UNDERSTAND→RESPOND) fully built and running against the live FortyGuard API across 51 cities. The engine is deliberately domain-agnostic: it takes a polygon, a danger threshold, and produces a scored, investigated, LLM-explained anomaly — nothing about it is hardcoded to "emergency planner."

That's the seed of a broader idea we call **Thermal Brain**: the same engine, unchanged, driving domain-specific panels for every other track —
- **Buildings & Energy (02):** which buildings are absorbing the most heat, HVAC load prediction, pre-cooling schedules
- **Industrial & Enterprise (03):** OSHA-threshold worker-safety alerts, equipment thermal risk, shift optimization
- **Government & Environment (04):** public-health-by-neighborhood dashboards, policy "what-if" modeling, environmental-justice heat-burden mapping
- **Model Designing (05) / Data Analysis (07):** the composite anomaly model and 7-day trend aggregation already built here become the training/validation substrate for custom UHI-prediction and heat-correlation models

ARGUS Core proves the engine works end-to-end on real data; Thermal Brain is that same engine wearing a different domain's lens — not a rebuild.

---

## Notes for Judges

- Set `FORTYGUARD_API_KEY` in `backend/.env` to run against the live API; omit it (or exhaust credits) to see the identical pipeline run on the dummy-data fallback — useful for evaluating the full system without spending your own FortyGuard credits.
- `AUTO_SCAN_ENABLED=true` enables the optional daily cron; default is manual per-city scanning to keep credit spend under explicit user control.

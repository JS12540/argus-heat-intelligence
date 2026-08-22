# ARGUS → Thermal Brain — Full Product Vision

> **Chief Product Officer Blueprint**
> From autonomous heat intelligence to a city-wide heat operating system.
> Built step-by-step. Every feature mapped. Every API call defined.

---

## Table of Contents

1. [Product Identity](#1-product-identity)
2. [Architecture Overview](#2-architecture-overview)
3. [FortyGuard API — Complete Integration Map](#3-fortyguard-api--complete-integration-map)
4. [ARGUS Core — The Agentic Engine](#4-argus-core--the-agentic-engine)
5. [Stage 1: DISCOVER](#5-stage-1-discover)
6. [Stage 2: INVESTIGATE](#6-stage-2-investigate)
7. [Stage 3: UNDERSTAND](#7-stage-3-understand)
8. [Stage 4: RESPOND](#8-stage-4-respond)
9. [Thermal Brain — The Expansion Layer](#9-thermal-brain--the-expansion-layer)
10. [Frontend — What to Show](#10-frontend--what-to-show)
11. [Backend — Python Architecture](#11-backend--python-architecture)
12. [Data Pipeline & External Data Sources](#12-data-pipeline--external-data-sources)
13. [AI/ML Components](#13-aiml-components)
14. [Real-World Impact & Use Cases](#14-real-world-impact--use-cases)
15. [Demo Script — What Judges See](#15-demo-script--what-judges-see)
16. [Tech Stack Summary](#16-tech-stack-summary)
17. [Build Timeline — Day by Day](#17-build-timeline--day-by-day)
18. [File & Folder Structure](#18-file--folder-structure)

---

## 1. Product Identity

| Field | Value |
|---|---|
| **Product Name** | **ARGUS** — Autonomous Urban Heat Intelligence System |
| **Evolution** | ARGUS Core → Thermal Brain (City Heat Operating System) |
| **GitHub Repo** | `argus-heat-intelligence` |
| **Tagline** | Discovers thermal risks before humans know where to look |
| **One-Line Pitch** | ARGUS is an autonomous urban heat intelligence system that discovers thermal risks before humans know where to look, investigates why they matter, and recommends what cities should do next. |
| **Primary Track** | 06 — Agentic AI |
| **Supporting Tracks** | 01 (Resilient Cities) · 05 (Model Designing) · 07 (Data Analysis) · 04 (Government) |
| **Expansion Tracks** | 02 (Buildings & Energy) · 03 (Industrial & Enterprise) |
| **Builder** | Solo |
| **Backend** | Python (FastAPI) |
| **Frontend** | React (Next.js) or HTML/JS with Mapbox/Deck.gl |
| **AI Layer** | Claude API / OpenAI API for reasoning + custom anomaly detection |

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React / Next.js)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Live Map │  │ Agent    │  │ Incident │  │ Thermal  │            │
│  │ + Heatmap│  │ Activity │  │ Reports  │  │ Brain    │            │
│  │ (Mapbox) │  │ Feed     │  │ Detail   │  │ Dashboard│            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                         ▼ WebSocket + REST                          │
├──────────────────────────────────────────────────────────────────────┤
│                        BACKEND (FastAPI / Python)                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    ARGUS AGENT ENGINE                        │   │
│  │  ┌──────────┐  ┌─────────────┐  ┌───────────┐  ┌─────────┐ │   │
│  │  │ DISCOVER │→ │ INVESTIGATE │→ │ UNDERSTAND│→ │ RESPOND │ │   │
│  │  └──────────┘  └─────────────┘  └───────────┘  └─────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ FortyGuard │  │ Anomaly    │  │ LLM        │  │ External   │   │
│  │ API Client │  │ Detector   │  │ Reasoner   │  │ Data APIs  │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │          DATABASE (SQLite/PostgreSQL) + CACHE (Redis)          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
           ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│  FortyGuard API  │ │  OpenStreetMap   │ │  LLM API (Claude/GPT)   │
│  Temperature     │ │  Overpass API    │ │  Reasoning + Reports     │
│  Intelligence    │ │  Infrastructure  │ │  Natural Language        │
└──────────────────┘ └──────────────────┘ └──────────────────────────┘
```

---

## 3. FortyGuard API — Complete Integration Map

**Base URL:** `https://api.fortyguard.com`

**Authentication:** Header `api-key: YOUR_API_KEY`

**Pattern:** Asynchronous submit-and-poll. You POST a request, get an `activity_id`, then poll until the result is ready.

### 3.1 — Endpoint Map

| # | Endpoint | Method | Purpose | ARGUS Stage |
|---|---|---|---|---|
| 1 | `/v1/heatmap` | POST | Submit a heatmap generation request for a polygon area | DISCOVER |
| 2 | `/v1/heatmap/status/{activity_id}` | GET | Poll processing status of a submitted job | ALL (polling) |
| 3 | `/v1/heatmap/snapshot` | GET/POST | Point-in-time temperature grid — "what's the temp NOW" | DISCOVER |
| 4 | `/v1/heatmap/exceedance` | GET/POST | Where does temperature exceed a threshold — "where is it dangerously hot" | DISCOVER + INVESTIGATE |
| 5 | `/v1/heatmap/persistence` | GET/POST | How long has extreme heat persisted — "how many hours above danger level" | INVESTIGATE |
| 6 | `/v1/heat-intelligence` | POST | Point-specific intelligence report with 5 contextual layers | INVESTIGATE + UNDERSTAND |

### 3.2 — Heatmap Request Payload

```python
{
    "polygon_aoi": {
        "type": "Polygon",
        "coordinates": [[
            [lon1, lat1],
            [lon2, lat2],
            [lon3, lat3],
            [lon4, lat4],
            [lon1, lat1]  # close the polygon
        ]]
    },
    "date_time": {
        "start_date": "2026-08-22",   # YYYY-MM-DD
        "start_time": "14:00",        # HH:MM (24h)
        "filter_type": 1              # 1=real-time, 2=historical, 3=predictive
    },
    "granularity": 100                # spatial resolution (meters per grid cell)
}
```

### 3.3 — filter_type Values

| filter_type | Mode | Description | Use Case |
|---|---|---|---|
| `1` | **Real-time** | Current/near-real-time temperature data | Live monitoring, anomaly detection |
| `2` | **Historical** | Past temperature patterns | Trend analysis, baseline computation |
| `3` | **Predictive** | AI-forecasted future heat distribution | Early warning, proactive planning |

### 3.4 — Response Pattern (Async)

```python
# Step 1: Submit
response = requests.post(
    "https://api.fortyguard.com/v1/heatmap",
    headers={"api-key": API_KEY, "Content-Type": "application/json"},
    json=payload
)
activity_id = response.json()["data"]["activity_id"]

# Step 2: Poll
while True:
    status = requests.get(
        f"https://api.fortyguard.com/v1/heatmap/status/{activity_id}",
        headers={"api-key": API_KEY}
    )
    result = status.json()
    if result["data"]["status"] == "completed":
        heatmap_data = result["data"]["result"]
        break
    time.sleep(2)  # wait before next poll
```

### 3.5 — Analysis Layer Selection (Critical)

From Fawad Shah's mentor session — **choosing the wrong layer gives confident wrong answers.**

| Question You're Asking | Correct Layer | Wrong Layer |
|---|---|---|
| "How hot is it right now across this zone?" | **Snapshot** | Exceedance (tells you where it's hot, not how hot) |
| "Where is it dangerously hot (above threshold)?" | **Exceedance** | Snapshot (gives raw temps, no threshold context) |
| "How long has this been going on?" | **Persistence** | Snapshot (only shows current moment) |
| "What's the full story of this specific location?" | **Heat Intelligence** | Heatmap (gives grid, not point-level depth) |
| "What will tomorrow look like?" | **Snapshot (filter_type=3)** | Historical (shows past, not future) |

### 3.6 — Heat Intelligence Report — 5 Contextual Layers

When you call `/v1/heat-intelligence` for a specific coordinate, you get:

1. **Temperature Data** — Current, historical, and predicted temperature at that point
2. **Land Use Context** — What type of urban environment surrounds this point
3. **Surface Analysis** — Material composition, albedo, vegetation density
4. **Risk Assessment** — Heat risk level, vulnerability indicators
5. **Comparative Context** — How this point compares to surrounding areas

### 3.7 — API Usage in ARGUS (Per Stage)

| ARGUS Stage | API Calls | Purpose |
|---|---|---|
| **DISCOVER** | `POST /v1/heatmap` (snapshot, real-time) | Scan city grid for current temperatures |
| **DISCOVER** | `POST /v1/heatmap` (exceedance) | Find zones exceeding danger thresholds |
| **INVESTIGATE** | `POST /v1/heatmap` (persistence) | Check how long anomalies have persisted |
| **INVESTIGATE** | `POST /v1/heatmap` (historical) | Compare current to historical baseline |
| **INVESTIGATE** | `POST /v1/heat-intelligence` | Deep-dive single point with 5 layers |
| **UNDERSTAND** | `POST /v1/heat-intelligence` | Get land use, surface, risk context |
| **RESPOND** | `POST /v1/heatmap` (predictive) | Forecast whether conditions will worsen |

---

## 4. ARGUS Core — The Agentic Engine

### What Makes ARGUS Agentic (Track 06)

Traditional dashboards: Human sees data → human decides what's important → human investigates → human acts.

**ARGUS:** AI detects anomaly → AI decides it's important → AI investigates automatically → AI recommends action → AI monitors the outcome.

### The Agent Loop

```
          ┌───────────────────────────────────────┐
          │                                       │
          ▼                                       │
    ┌──────────┐    ┌─────────────┐    ┌────────────────┐    ┌─────────┐
    │ DISCOVER │───→│ INVESTIGATE │───→│  UNDERSTAND    │───→│ RESPOND │
    │          │    │             │    │                │    │         │
    │ Scan     │    │ Deep-dive   │    │ Connect to     │    │ Rank    │
    │ Detect   │    │ Analyze     │    │ infrastructure │    │ Recommend│
    │ Anomalies│    │ Persistence │    │ Assess risk    │    │ Monitor │
    └──────────┘    └─────────────┘    └────────────────┘    └────┬────┘
                                                                  │
                                                                  │ Loop back
                                                                  │
          ┌───────────────────────────────────────────────────────┘
          │
          ▼
    ┌──────────────┐
    │   MONITOR    │
    │              │
    │ Did it get   │
    │ better or    │
    │ worse?       │
    │              │
    │ Re-enter     │
    │ DISCOVER if  │
    │ conditions   │
    │ change       │
    └──────────────┘
```

---

## 5. Stage 1: DISCOVER

### Purpose
Continuously scan the city for thermal anomalies that require attention.

### What It Does

1. **Grid Scan** — Divide the city into polygon zones, submit snapshot heatmap for each
2. **Threshold Detection** — Run exceedance analysis to find zones above danger thresholds
3. **Statistical Anomaly Detection** — Compare current readings against historical baselines
4. **Pattern Recognition** — Identify unusual clustering, rapid temperature spikes, UHI hotspots

### API Calls

```python
# Scan city grid with real-time snapshot
snapshot_payload = {
    "polygon_aoi": city_zone_polygon,
    "date_time": {
        "start_date": today,
        "start_time": current_hour,
        "filter_type": 1  # real-time
    },
    "granularity": 100
}
# Submit and poll for each zone
```

```python
# Find danger zones with exceedance
exceedance_payload = {
    "polygon_aoi": city_zone_polygon,
    "date_time": {
        "start_date": today,
        "start_time": current_hour,
        "filter_type": 1
    },
    "granularity": 100,
    # threshold parameters for exceedance analysis
}
```

### Anomaly Detection Algorithm

```python
class AnomalyDetector:
    """Multi-signal anomaly detection for urban heat."""

    def detect(self, current_data, historical_baseline):
        signals = []

        # Signal 1: Absolute Heat Level (WHO heat-risk bands)
        # < 27°C = minimal, 27-32°C = low, 32-40°C = moderate,
        # 40-46°C = high, > 46°C = extreme
        signals.append(self.who_heat_band(current_data.temperature))

        # Signal 2: Statistical Outlier (z-score vs 24h baseline)
        z_score = (current_data.temperature - historical_baseline.mean) / historical_baseline.std
        signals.append(self.z_score_signal(z_score))

        # Signal 3: Rate of Change (rapid spike detection)
        rate = current_data.temperature - current_data.temperature_1h_ago
        signals.append(self.rate_of_change_signal(rate))

        # Signal 4: Spatial Anomaly (hotter than neighbors)
        neighbor_diff = current_data.temperature - current_data.neighbor_avg
        signals.append(self.spatial_anomaly_signal(neighbor_diff))

        # Composite score 0-100
        composite = self.weighted_composite(signals)

        return AnomalyResult(
            score=composite,
            severity=self.classify_severity(composite),
            signals=signals,
            location=current_data.location,
            timestamp=current_data.timestamp
        )

    def classify_severity(self, score):
        if score >= 80: return "CRITICAL"
        if score >= 60: return "HIGH"
        if score >= 40: return "MEDIUM"
        if score >= 20: return "LOW"
        return "INFO"
```

### DISCOVER Output

```json
{
    "anomalies_found": 3,
    "scan_area": "Phoenix Downtown, AZ",
    "scan_time": "2026-08-22T14:00:00Z",
    "anomalies": [
        {
            "id": "ANO-001",
            "location": {"lat": 33.4484, "lon": -112.0740},
            "zone": "Zone A3 — Central Business District",
            "temperature_f": 118,
            "severity": "CRITICAL",
            "composite_score": 87,
            "signals": {
                "who_band": "EXTREME",
                "z_score": 2.4,
                "rate_of_change": "+5°F/hr",
                "spatial_anomaly": "+8°F vs neighbors"
            },
            "status": "PENDING_INVESTIGATION"
        }
    ]
}
```

### Features in DISCOVER

- **Auto-Scheduling:** Agent runs scans every 30 min / 1 hour automatically
- **Priority Queue:** Anomalies ranked by severity for investigation order
- **Historical Comparison:** Each scan compared against same-time-yesterday and 7-day average
- **Predictive Pre-Scan:** Uses filter_type=3 to check if tomorrow will be worse
- **Multi-City Support:** Configure multiple city polygons for parallel scanning
- **Alert Thresholds:** Configurable per-city danger thresholds

---

## 6. Stage 2: INVESTIGATE

### Purpose
Deep-dive into detected anomalies to understand their nature, duration, and trajectory.

### What It Does

1. **Persistence Analysis** — How long has this anomaly been active?
2. **Temporal Analysis** — Is it getting worse, stable, or improving?
3. **Historical Context** — Has this happened before at this location?
4. **Heat Intelligence Report** — Pull full 5-layer contextual report for the anomaly center
5. **Expand Search Radius** — Check surrounding areas for spreading heat

### API Calls

```python
# Check persistence — how many hours above threshold
persistence_payload = {
    "polygon_aoi": anomaly_zone_polygon,  # tight polygon around anomaly
    "date_time": {
        "start_date": today,
        "start_time": "00:00",  # check full day
        "filter_type": 1
    },
    "granularity": 50  # higher resolution for investigation
}
```

```python
# Pull Heat Intelligence Report for anomaly center point
intelligence_payload = {
    "location": {
        "latitude": anomaly.lat,
        "longitude": anomaly.lon
    }
}
response = requests.post(
    "https://api.fortyguard.com/v1/heat-intelligence",
    headers=headers,
    json=intelligence_payload
)
```

```python
# Compare to historical baseline (same date last week / last year)
historical_payload = {
    "polygon_aoi": anomaly_zone_polygon,
    "date_time": {
        "start_date": "2026-08-15",  # last week
        "start_time": "14:00",
        "filter_type": 2  # historical
    },
    "granularity": 100
}
```

### INVESTIGATE Output

```json
{
    "anomaly_id": "ANO-001",
    "investigation": {
        "persistence": {
            "hours_above_threshold": 6,
            "started_at": "2026-08-22T08:00:00Z",
            "trend": "WORSENING",
            "peak_expected": "2026-08-22T15:30:00Z"
        },
        "historical_comparison": {
            "same_time_last_week": 112,
            "current": 118,
            "deviation": "+6°F",
            "is_unusual": true,
            "historical_frequency": "occurs 3 times per summer"
        },
        "heat_intelligence": {
            "land_use": "commercial_dense",
            "surface_albedo": 0.15,
            "vegetation_density": "very_low",
            "risk_assessment": "EXTREME",
            "contextual_factors": [
                "Large parking lot with dark asphalt surface",
                "Minimal tree canopy (<5% coverage)",
                "High building density trapping heat",
                "Limited nighttime cooling potential"
            ]
        },
        "spatial_analysis": {
            "anomaly_radius": "0.8 km",
            "spreading": true,
            "spread_direction": "northeast",
            "affected_area_km2": 2.01
        }
    },
    "recommendation": "ESCALATE_TO_UNDERSTAND"
}
```

### Features in INVESTIGATE

- **Auto-Depth:** Agent decides how deep to investigate based on severity
- **Persistence Tracking:** Tracks consecutive hours above threshold
- **Trend Projection:** Simple ML model to predict next 6 hours
- **Spreading Detection:** Compares anomaly boundaries over time
- **Root Cause Hypothesis:** LLM reasons about contextual factors
- **Comparison Engine:** Side-by-side with similar historical events

---

## 7. Stage 3: UNDERSTAND

### Purpose
Connect the thermal anomaly to real-world infrastructure, populations, and assets at risk.

### What It Does

1. **Infrastructure Mapping** — Find schools, hospitals, transit stops, power lines within the heat zone
2. **Population Vulnerability** — Identify elderly care facilities, outdoor worker zones, homeless shelters
3. **Asset Risk Assessment** — Roads, bridges, rail lines, data centers, power substations
4. **Impact Scoring** — Rank everything by exposure severity and vulnerability

### External Data Sources (Free/Open)

| Data Source | What It Provides | API/Method |
|---|---|---|
| **OpenStreetMap (Overpass API)** | Schools, hospitals, parks, roads, buildings, transit | `https://overpass-api.de/api/interpreter` |
| **US Census / ACS** | Population density, demographics, vulnerability indicators | Public datasets |
| **EPA Environmental Data** | Air quality, environmental justice screening | `https://enviro.epa.gov/` |
| **NOAA Weather** | Official weather warnings, NWS alerts | `https://api.weather.gov/` |
| **WHO Heat-Health Guidelines** | Heat risk thresholds, health impact data | Published guidelines |
| **Open Data Portals** | City-specific data (parks, fire stations, shelters) | Varies by city |

### Overpass API — Finding Infrastructure Near Anomalies

```python
import requests

def find_infrastructure_near(lat, lon, radius_m=1000):
    """Find vulnerable infrastructure near a heat anomaly."""

    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json][timeout:30];
    (
      // Schools
      node["amenity"="school"](around:{radius_m},{lat},{lon});
      way["amenity"="school"](around:{radius_m},{lat},{lon});

      // Hospitals and clinics
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      node["amenity"="clinic"](around:{radius_m},{lat},{lon});

      // Elderly care
      node["amenity"="nursing_home"](around:{radius_m},{lat},{lon});
      node["social_facility"="nursing_home"](around:{radius_m},{lat},{lon});

      // Public transit stops
      node["highway"="bus_stop"](around:{radius_m},{lat},{lon});
      node["railway"="station"](around:{radius_m},{lat},{lon});

      // Parks and cooling centers
      way["leisure"="park"](around:{radius_m},{lat},{lon});
      node["amenity"="community_centre"](around:{radius_m},{lat},{lon});

      // Power infrastructure
      node["power"="substation"](around:{radius_m},{lat},{lon});
      way["power"="line"](around:{radius_m},{lat},{lon});
    );
    out body;
    """

    response = requests.post(overpass_url, data={"data": query})
    return response.json()
```

### Risk Scoring Matrix

```python
VULNERABILITY_WEIGHTS = {
    "school": {"base_risk": 9, "reason": "Children are highly vulnerable to heat"},
    "hospital": {"base_risk": 8, "reason": "Patient care disruption, HVAC critical"},
    "nursing_home": {"base_risk": 10, "reason": "Elderly most at risk of heat death"},
    "bus_stop": {"base_risk": 7, "reason": "People waiting outdoors without shade"},
    "park": {"base_risk": 3, "reason": "Outdoor recreation, but shade available"},
    "substation": {"base_risk": 8, "reason": "Power failure cascades during heat"},
    "construction_site": {"base_risk": 9, "reason": "Outdoor workers, heavy equipment"},
    "data_center": {"base_risk": 7, "reason": "Cooling system stress, outage risk"},
}

def calculate_impact_score(infrastructure_item, anomaly_severity, distance_m):
    """Calculate impact score for infrastructure near a heat anomaly."""
    base = VULNERABILITY_WEIGHTS[infrastructure_item.type]["base_risk"]
    severity_multiplier = anomaly_severity / 100  # 0-1
    distance_decay = max(0, 1 - (distance_m / 1000))  # closer = higher risk
    return base * severity_multiplier * distance_decay * 10  # 0-100
```

### UNDERSTAND Output

```json
{
    "anomaly_id": "ANO-001",
    "impact_assessment": {
        "total_infrastructure_at_risk": 12,
        "total_population_exposure": "~15,000 people",
        "risk_ranking": [
            {
                "rank": 1,
                "type": "nursing_home",
                "name": "Sunrise Senior Living",
                "distance_m": 320,
                "impact_score": 92,
                "risk": "CRITICAL",
                "reason": "Elderly residents, 320m from anomaly center, high heat-death risk"
            },
            {
                "rank": 2,
                "type": "school",
                "name": "Roosevelt Elementary School",
                "distance_m": 480,
                "impact_score": 78,
                "risk": "HIGH",
                "reason": "450 students, outdoor recess scheduled, limited shade structures"
            },
            {
                "rank": 3,
                "type": "bus_stop",
                "name": "Central Ave & McDowell Rd",
                "distance_m": 150,
                "impact_score": 71,
                "risk": "HIGH",
                "reason": "High-traffic transit stop, no shade structure, avg wait 12 min"
            }
        ],
        "cooling_assets_nearby": [
            {"type": "park", "name": "Hance Park", "distance_m": 800, "shade_coverage": "moderate"},
            {"type": "library", "name": "Burton Barr Central Library", "distance_m": 1200, "ac": true}
        ]
    }
}
```

### Features in UNDERSTAND

- **Infrastructure Discovery:** Auto-query OSM for all relevant infrastructure within heat zone
- **Vulnerability Scoring:** Weighted risk scores based on type, distance, and severity
- **Population Estimation:** Rough population exposure based on census/density data
- **Cooling Asset Mapping:** Find nearby parks, libraries, community centers as relief points
- **Cascading Risk Analysis:** Power substations → grid failure → AC loss → compound risk
- **Temporal Vulnerability:** Schools during school hours vs. weekend, construction sites during work hours

---

## 8. Stage 4: RESPOND

### Purpose
Generate actionable, prioritized recommendations and continue monitoring outcomes.

### What It Does

1. **Action Generation** — LLM-powered recommendations based on investigation + understanding
2. **Priority Ranking** — Rank actions by urgency, impact, and feasibility
3. **Report Generation** — Auto-generate incident reports for city officials
4. **Continuous Monitoring** — Track whether conditions improve after response
5. **Re-escalation** — If conditions worsen, re-enter DISCOVER loop

### LLM-Powered Action Generation

```python
def generate_recommendations(anomaly, investigation, impact_assessment):
    """Use LLM to generate contextual, actionable recommendations."""

    prompt = f"""
    You are an urban heat emergency response advisor.

    HEAT ANOMALY:
    - Location: {anomaly.zone}
    - Temperature: {anomaly.temperature_f}°F
    - Severity: {anomaly.severity}
    - Duration: {investigation.persistence.hours_above_threshold} hours
    - Trend: {investigation.persistence.trend}

    INFRASTRUCTURE AT RISK:
    {json.dumps(impact_assessment.risk_ranking, indent=2)}

    COOLING ASSETS NEARBY:
    {json.dumps(impact_assessment.cooling_assets_nearby, indent=2)}

    Generate 5-7 specific, actionable recommendations ranked by urgency.
    Each recommendation must include:
    - Action (what to do)
    - Target (who should do it)
    - Urgency (immediate / within 1 hour / within 4 hours / next day)
    - Expected impact (what this prevents or mitigates)

    Format as JSON array.
    """

    response = llm_client.complete(prompt)
    return parse_recommendations(response)
```

### RESPOND Output

```json
{
    "anomaly_id": "ANO-001",
    "response_plan": {
        "generated_at": "2026-08-22T14:15:00Z",
        "total_actions": 6,
        "actions": [
            {
                "rank": 1,
                "action": "Issue heat alert to Sunrise Senior Living — activate emergency cooling protocol",
                "target": "Facility management + EMS",
                "urgency": "IMMEDIATE",
                "expected_impact": "Prevents heat-related illness in ~80 elderly residents"
            },
            {
                "rank": 2,
                "action": "Cancel outdoor recess at Roosevelt Elementary, move to indoor activities",
                "target": "School administration",
                "urgency": "IMMEDIATE",
                "expected_impact": "Protects 450 children from extreme heat exposure"
            },
            {
                "rank": 3,
                "action": "Deploy emergency shade structures at Central Ave & McDowell bus stop",
                "target": "City transit authority",
                "urgency": "WITHIN_1_HOUR",
                "expected_impact": "Reduces heat exposure for ~200 daily transit riders"
            },
            {
                "rank": 4,
                "action": "Open Burton Barr Library as designated cooling center, extend hours",
                "target": "Library services + Emergency management",
                "urgency": "WITHIN_1_HOUR",
                "expected_impact": "Provides cooling refuge for surrounding neighborhood"
            },
            {
                "rank": 5,
                "action": "Monitor power substation on 7th Ave for overload — pre-position repair crew",
                "target": "Utility company",
                "urgency": "WITHIN_4_HOURS",
                "expected_impact": "Prevents cascading power failure affecting 3,000 homes"
            },
            {
                "rank": 6,
                "action": "Schedule reflective pavement treatment for parking lot at anomaly center",
                "target": "City public works",
                "urgency": "NEXT_DAY",
                "expected_impact": "Long-term: reduces surface temperature by 10-15°F"
            }
        ],
        "monitoring": {
            "next_scan": "2026-08-22T14:45:00Z",
            "escalation_threshold": "If temperature exceeds 120°F or persistence exceeds 8 hours",
            "de_escalation_threshold": "If temperature drops below 110°F for 2 consecutive hours"
        }
    }
}
```

### Features in RESPOND

- **LLM-Generated Actions:** Context-aware, specific to the anomaly and infrastructure at risk
- **Priority Matrix:** Urgency × Impact × Feasibility scoring
- **Auto-Reporting:** Generate PDF/HTML incident reports for city officials
- **Monitoring Loop:** Agent continues scanning the anomaly area every 30 min
- **Outcome Tracking:** Did temperature drop? Did infrastructure report issues?
- **Re-escalation Logic:** If conditions worsen, agent re-enters the pipeline
- **Historical Learning:** Store all incidents for pattern recognition over time

---

## 9. Thermal Brain — The Expansion Layer

Thermal Brain is NOT a separate product. It's ARGUS applied across every domain.

### Thermal Brain = ARGUS Engine + Domain Panels

```
┌──────────────────────────────────────────────────────────────┐
│                    THERMAL BRAIN DASHBOARD                    │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ CITY       │  │ BUILDINGS  │  │ INDUSTRIAL │             │
│  │ Track 01   │  │ Track 02   │  │ Track 03   │             │
│  │            │  │            │  │            │             │
│  │ Urban heat │  │ Building   │  │ Workforce  │             │
│  │ islands    │  │ energy     │  │ safety     │             │
│  │ Emergency  │  │ HVAC load  │  │ Equipment  │             │
│  │ response   │  │ efficiency │  │ thermal    │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ GOVERNMENT │  │ MODELS     │  │ DATA       │             │
│  │ Track 04   │  │ Track 05   │  │ Track 07   │             │
│  │            │  │            │  │            │             │
│  │ Policy     │  │ Prediction │  │ Correlation│             │
│  │ decisions  │  │ accuracy   │  │ discovery  │             │
│  │ Public     │  │ Custom     │  │ Hidden     │             │
│  │ health     │  │ models     │  │ patterns   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │            ARGUS AGENTIC ENGINE              │           │
│  │        DISCOVER → INVESTIGATE →              │           │
│  │        UNDERSTAND → RESPOND                  │           │
│  │            (Track 06 - Core)                 │           │
│  └──────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

### Track 02 — Buildings & Energy Panel

| Feature | Description | Data Source |
|---|---|---|
| **Building Heat Stress** | Which buildings are absorbing most heat | FortyGuard heatmap + OSM building footprints |
| **HVAC Load Prediction** | Predict cooling demand spikes | Temperature forecast + building type |
| **Energy Optimization** | Recommend pre-cooling schedules | Persistence data + predictive API |
| **Cool Roof Assessment** | Which buildings benefit most from reflective roofing | Surface albedo from Heat Intelligence |

### Track 03 — Industrial & Enterprise Panel

| Feature | Description | Data Source |
|---|---|---|
| **Worker Safety Alerts** | Auto-alert when outdoor work zones exceed OSHA thresholds | Exceedance API + OSM construction sites |
| **Equipment Thermal Risk** | Flag equipment in extreme heat zones | Heatmap + asset location data |
| **Shift Optimization** | Recommend shifting outdoor work to cooler hours | Predictive API + persistence |
| **Supply Chain Heat Risk** | Flag logistics routes through extreme heat | Snapshot API + route data |

### Track 04 — Government & Environment Panel

| Feature | Description | Data Source |
|---|---|---|
| **Public Health Dashboard** | Heat-health risk by neighborhood | Heat Intelligence + census data |
| **Emergency Response Prioritization** | Where to deploy resources first | ARGUS RESPOND output |
| **Policy Impact Modeling** | "What if we added 1000 trees here?" | Historical vs. predicted comparison |
| **Environmental Justice** | Heat burden on disadvantaged communities | Temperature + EPA EJ data |

### Track 05 — Model Designing Panel

| Feature | Description | Data Source |
|---|---|---|
| **Custom Anomaly Model** | ML model trained on FortyGuard historical data | Historical API + scikit-learn |
| **UHI Prediction** | Predict urban heat island intensity from features | Historical + OSM land use |
| **Thermal Inertia Model** | How fast does a zone cool after sunset? | Persistence + time series |
| **Validation Dashboard** | Compare ARGUS predictions to actual | Predicted vs. real-time |

### Track 07 — Data Analysis & Correlation Panel

| Feature | Description | Data Source |
|---|---|---|
| **Heat × Health Correlation** | Temperature vs. hospital admissions | Historical API + health data |
| **Heat × Energy Correlation** | Temperature vs. power consumption | Historical API + energy data |
| **Heat × Crime Correlation** | Temperature vs. incident reports | Historical API + crime data |
| **Spatial Autocorrelation** | Moran's I for heat clustering | Snapshot API + spatial statistics |
| **Thermal Fingerprinting** | Unique heat behavior per neighborhood | Historical time series |

---

## 10. Frontend — What to Show

### Recommended Frontend Stack

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| **React + Next.js** | Full framework, great for complex UI | Setup time | Best for full product |
| **React (Vite)** | Fast, simple, component-based | No SSR | Good for hackathon speed |
| **HTML + Vanilla JS** | Zero setup, deploy anywhere | Harder to scale | Fastest to start |
| **Streamlit (Python)** | Python-native, rapid prototyping | Limited customization | Fastest demo, looks less polished |

**Recommendation for hackathon:** **React (Vite) + Tailwind CSS + Mapbox GL JS**

If speed is critical: **Streamlit** for backend demo + simple React frontend for map.

### Frontend Pages & Components

#### Page 1: ARGUS Command Center (Main Dashboard)

```
┌─────────────────────────────────────────────────────────────────┐
│  ARGUS — Autonomous Urban Heat Intelligence         [Live] 🔴   │
├──────────────────────────────┬──────────────────────────────────┤
│                              │                                  │
│     INTERACTIVE HEATMAP      │     AGENT ACTIVITY FEED          │
│     (Mapbox GL + Deck.gl)    │                                  │
│                              │  14:15 — CRITICAL anomaly        │
│     [City zone overlay]      │  detected in Zone A3             │
│     [Anomaly markers]        │                                  │
│     [Infrastructure pins]    │  14:12 — Investigation complete  │
│     [Risk heatmap layer]     │  for ANO-001: 6hr persistence    │
│                              │                                  │
│     [Click anomaly to        │  14:10 — Scanning Downtown       │
│      see investigation]      │  Phoenix... 3 anomalies found    │
│                              │                                  │
│                              │  14:05 — Predictive scan:        │
│                              │  tomorrow peak 120°F expected    │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│   ANOMALY QUEUE              │   METRICS                        │
│   ┌─────────────────────┐    │   Active Anomalies: 3            │
│   │ 🔴 ANO-001 CRITICAL │    │   Under Investigation: 1         │
│   │ Zone A3 — 118°F     │    │   Actions Recommended: 6         │
│   │ 6hr persistence     │    │   Infrastructure at Risk: 12     │
│   ├─────────────────────┤    │   Population Exposed: ~15,000    │
│   │ 🟠 ANO-002 HIGH     │    │   Last Scan: 2 min ago           │
│   │ Zone B1 — 114°F     │    │   Next Scan: in 28 min           │
│   ├─────────────────────┤    │                                  │
│   │ 🟡 ANO-003 MEDIUM   │    │   API Credits Used: 47           │
│   │ Zone C4 — 108°F     │    │   API Credits Remaining: 952     │
│   └─────────────────────┘    │                                  │
└──────────────────────────────┴──────────────────────────────────┘
```

#### Page 2: Incident Detail (Click on Anomaly)

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back    ANO-001 — Zone A3 Central Business District          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STAGE: ████████████████░░░░ RESPOND                           │
│         DISCOVER → INVESTIGATE → UNDERSTAND → RESPOND           │
│                                                                 │
├──────────────────────────────┬──────────────────────────────────┤
│                              │                                  │
│  ANOMALY MAP (zoomed in)     │  INVESTIGATION SUMMARY           │
│  [Tight polygon view]        │                                  │
│  [Infrastructure markers]    │  Temperature: 118°F              │
│  [Heatmap overlay]           │  Severity: CRITICAL (87/100)     │
│  [Cooling assets shown]      │  Persistence: 6 hours            │
│                              │  Trend: WORSENING                │
│                              │  Peak Expected: 3:30 PM          │
│                              │  Surface: Dark asphalt, low veg  │
│                              │  Historical: Unusual (+6°F)      │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│                              │                                  │
│  INFRASTRUCTURE AT RISK      │  RECOMMENDED ACTIONS             │
│                              │                                  │
│  🔴 Sunrise Senior Living    │  1. 🔴 IMMEDIATE                 │
│     320m — Score 92          │     Alert senior facility         │
│  🔴 Roosevelt Elementary     │  2. 🔴 IMMEDIATE                 │
│     480m — Score 78          │     Cancel outdoor recess         │
│  🟠 Central Ave Bus Stop     │  3. 🟠 WITHIN 1 HOUR             │
│     150m — Score 71          │     Deploy shade structures       │
│  🟢 Hance Park               │  4. 🟠 WITHIN 1 HOUR             │
│     800m — Cooling asset     │     Open cooling center           │
│                              │  5. 🟡 WITHIN 4 HOURS            │
│                              │     Monitor power substation     │
│                              │                                  │
├─────────────────────────────────────────────────────────────────┤
│  TEMPERATURE TIMELINE (24h chart)                               │
│  ▁▂▃▅▆▇█████████▇▆▅▃▂▁                                        │
│  12am    6am    12pm   NOW   6pm    12am                        │
│                              ↑ peak                             │
└─────────────────────────────────────────────────────────────────┘
```

#### Page 3: Thermal Brain Dashboard (Expansion)

```
┌─────────────────────────────────────────────────────────────────┐
│  THERMAL BRAIN — City Heat Operating System        Phoenix, AZ  │
├─────────────────────────────────────────────────────────────────┤
│  [CITY] [BUILDINGS] [INDUSTRIAL] [GOVERNMENT] [MODELS] [DATA]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  (Tab content changes based on selected domain panel)           │
│                                                                 │
│  Currently active: CITY                                         │
│  Showing: ARGUS Command Center (same as Page 1)                │
│                                                                 │
│  Switch to BUILDINGS:                                           │
│  → Building heat stress map                                    │
│  → HVAC load predictions                                       │
│  → Energy optimization recommendations                        │
│                                                                 │
│  Switch to GOVERNMENT:                                         │
│  → Public health risk by neighborhood                          │
│  → Emergency resource deployment map                           │
│  → Environmental justice heat burden overlay                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Libraries

| Library | Purpose | Install |
|---|---|---|
| **Mapbox GL JS** | Interactive map with heatmap layers | `npm install mapbox-gl` |
| **Deck.gl** | High-performance heatmap rendering | `npm install @deck.gl/core` |
| **Recharts** | Temperature timeline charts | `npm install recharts` |
| **Tailwind CSS** | Rapid styling | `npm install tailwindcss` |
| **Framer Motion** | Agent activity animations | `npm install framer-motion` |
| **Socket.io Client** | Real-time agent feed | `npm install socket.io-client` |

---

## 11. Backend — Python Architecture

### Core Python Packages

```
# requirements.txt
fastapi==0.115.0
uvicorn==0.30.0
httpx==0.27.0          # async HTTP client for FortyGuard API
pydantic==2.9.0        # data validation
sqlalchemy==2.0.35     # database ORM
celery==5.4.0          # background task queue (agent loop)
redis==5.1.0           # cache + celery broker
python-socketio==5.11  # real-time updates to frontend
anthropic==0.35.0      # Claude API for LLM reasoning
openai==1.45.0         # alternative LLM (GPT-4o)
shapely==2.0.6         # polygon geometry operations
geopandas==1.0.1       # geospatial data handling
scikit-learn==1.5.2    # anomaly detection ML
numpy==2.1.1           # numerical computing
pandas==2.2.2          # data analysis
matplotlib==3.9.2      # chart generation for reports
reportlab==4.2.2       # PDF report generation
jinja2==3.1.4          # HTML template rendering
python-dotenv==1.0.1   # environment variables
```

### Backend Module Structure

```python
# app/fortyguard_client.py — API Client
class FortyGuardClient:
    """Async client for FortyGuard Temperature API."""

    BASE_URL = "https://api.fortyguard.com"

    async def create_heatmap(self, polygon, date_time, granularity=100):
        """Submit heatmap request and return activity_id."""

    async def poll_status(self, activity_id, timeout=120):
        """Poll until job completes, return result data."""

    async def get_snapshot(self, polygon, date_time, granularity=100):
        """Get point-in-time temperature grid."""

    async def get_exceedance(self, polygon, date_time, threshold, granularity=100):
        """Get areas exceeding temperature threshold."""

    async def get_persistence(self, polygon, date_time, threshold, granularity=100):
        """Get duration of extreme heat persistence."""

    async def get_heat_intelligence(self, latitude, longitude):
        """Get full intelligence report for a single point."""
```

```python
# app/agent.py — The ARGUS Agent
class ArgusAgent:
    """Autonomous heat intelligence agent."""

    def __init__(self, fortyguard: FortyGuardClient, detector: AnomalyDetector):
        self.fortyguard = fortyguard
        self.detector = detector
        self.state = AgentState()

    async def run_cycle(self):
        """Execute one full DISCOVER → INVESTIGATE → UNDERSTAND → RESPOND cycle."""
        anomalies = await self.discover()
        for anomaly in anomalies:
            investigation = await self.investigate(anomaly)
            if investigation.warrants_action:
                impact = await self.understand(anomaly, investigation)
                response = await self.respond(anomaly, investigation, impact)
                await self.monitor(anomaly, response)

    async def discover(self) -> list[Anomaly]: ...
    async def investigate(self, anomaly: Anomaly) -> Investigation: ...
    async def understand(self, anomaly, investigation) -> ImpactAssessment: ...
    async def respond(self, anomaly, investigation, impact) -> ResponsePlan: ...
    async def monitor(self, anomaly, response) -> MonitoringResult: ...
```

```python
# app/anomaly_detector.py — Multi-Signal Detection
class AnomalyDetector:
    """Detect thermal anomalies using multiple signals."""

    def detect(self, grid_data, historical_baseline) -> list[Anomaly]: ...
    def who_heat_band(self, temp_f) -> Signal: ...
    def z_score_signal(self, z) -> Signal: ...
    def rate_of_change_signal(self, rate) -> Signal: ...
    def spatial_anomaly_signal(self, diff) -> Signal: ...
    def weighted_composite(self, signals) -> float: ...
```

```python
# app/infrastructure.py — OSM Infrastructure Discovery
class InfrastructureDiscovery:
    """Find and score infrastructure near heat anomalies."""

    async def find_near(self, lat, lon, radius_m=1000) -> list[Infrastructure]: ...
    def score_vulnerability(self, item, severity, distance) -> float: ...
    def rank_risks(self, items) -> list[RankedRisk]: ...
```

```python
# app/reasoner.py — LLM-Powered Reasoning
class HeatReasoner:
    """Generate investigation insights and action recommendations."""

    async def analyze_anomaly(self, anomaly, investigation) -> AnalysisReport: ...
    async def generate_recommendations(self, anomaly, investigation, impact) -> list[Action]: ...
    async def generate_incident_report(self, full_context) -> str: ...
```

### API Endpoints (FastAPI)

```python
# app/main.py

# Agent Control
POST /api/agent/start          # Start the ARGUS agent loop
POST /api/agent/stop           # Stop the agent loop
GET  /api/agent/status         # Current agent state
POST /api/agent/scan           # Trigger immediate scan

# Anomalies
GET  /api/anomalies            # List all detected anomalies
GET  /api/anomalies/{id}       # Get anomaly detail
GET  /api/anomalies/{id}/investigation   # Investigation results
GET  /api/anomalies/{id}/impact          # Impact assessment
GET  /api/anomalies/{id}/response        # Response plan

# City Configuration
GET  /api/cities               # List configured cities
POST /api/cities               # Add a city to monitor
GET  /api/cities/{id}/zones    # Get zone polygons

# Reports
GET  /api/reports              # List generated reports
GET  /api/reports/{id}/pdf     # Download PDF report
GET  /api/reports/{id}/html    # View HTML report

# Thermal Brain (expansion)
GET  /api/brain/buildings      # Building heat stress data
GET  /api/brain/industrial     # Industrial risk data
GET  /api/brain/government     # Public health dashboard data
GET  /api/brain/models         # Model performance data
GET  /api/brain/correlations   # Data correlation results

# Real-time
WS   /ws/feed                  # WebSocket for agent activity feed
```

---

## 12. Data Pipeline & External Data Sources

### Data Flow

```
FortyGuard API ─────────────────────────────────────┐
  (Temperature snapshots, exceedance,               │
   persistence, heat intelligence)                   │
                                                     │
OpenStreetMap Overpass API ──────────────────────────┼──→ ARGUS ENGINE ──→ Database
  (Schools, hospitals, transit,                      │        │               │
   buildings, parks, infrastructure)                 │        │               │
                                                     │        ▼               │
NOAA/NWS API ───────────────────────────────────────┤    LLM Reasoner        │
  (Weather warnings, official alerts)                │        │               │
                                                     │        ▼               │
US Census / ACS ────────────────────────────────────┤    Frontend            │
  (Population density, demographics)                 │    (via WebSocket      │
                                                     │     + REST API)        │
Open Data Portals ──────────────────────────────────┘                        │
  (City-specific datasets)                                                    │
                                                                             │
                                                     ┌───────────────────────┘
                                                     ▼
                                              Reports (PDF/HTML)
```

### External APIs Summary

| API | Base URL | Auth | Free? | Used For |
|---|---|---|---|---|
| FortyGuard Temperature | `https://api.fortyguard.com` | API key | Hackathon credits | Core temperature data |
| OpenStreetMap Overpass | `https://overpass-api.de/api/interpreter` | None | Yes | Infrastructure discovery |
| NOAA Weather | `https://api.weather.gov` | None | Yes | Official weather alerts |
| US Census Geocoder | `https://geocoding.geo.census.gov` | None | Yes | Population data |
| Nominatim (OSM) | `https://nominatim.openstreetmap.org` | None | Yes | Geocoding city names |

---

## 13. AI/ML Components

### Component 1: Anomaly Detection Model (Track 05)

- **Type:** Unsupervised anomaly detection
- **Method:** Isolation Forest + Z-score ensemble
- **Training Data:** FortyGuard historical API (filter_type=2)
- **Features:** Temperature, time of day, day of week, season, location cluster
- **Output:** Anomaly score 0-100, severity classification

### Component 2: Trend Projection

- **Type:** Time series forecasting
- **Method:** Simple ARIMA or Prophet on temperature time series
- **Input:** Last 24-48 hours of temperature readings
- **Output:** Next 6-hour temperature forecast per zone

### Component 3: LLM Reasoning Agent (Track 06)

- **Type:** Agentic AI with tool use
- **LLM:** Claude Sonnet or GPT-4o
- **Tools Available to Agent:**
  - `scan_city(polygon)` → calls FortyGuard snapshot
  - `check_exceedance(polygon, threshold)` → calls FortyGuard exceedance
  - `check_persistence(polygon)` → calls FortyGuard persistence
  - `get_intelligence(lat, lon)` → calls FortyGuard heat intelligence
  - `find_infrastructure(lat, lon, radius)` → calls Overpass API
  - `get_weather_alerts(zone)` → calls NOAA API
  - `generate_report(context)` → creates incident report
- **Loop:** Agent autonomously decides which tool to call next based on findings

### Component 4: Spatial Analysis (Track 07)

- **Spatial Autocorrelation:** Moran's I statistic for heat clustering
- **Hotspot Detection:** Getis-Ord Gi* for statistically significant hot spots
- **Kernel Density Estimation:** Smooth anomaly density surfaces
- **Cross-Correlation:** Temperature vs. infrastructure density, vegetation, albedo

---

## 14. Real-World Impact & Use Cases

### Impact Story 1: Protecting Vulnerable Populations

> ARGUS detects a 118°F anomaly in Downtown Phoenix at 2pm. Within 60 seconds, it identifies a nursing home with 80 elderly residents 320m from the center. It generates an immediate alert to activate emergency cooling protocols. Without ARGUS, no one would have known that specific facility was in a danger zone until someone collapsed.

### Impact Story 2: Preventing Infrastructure Failure

> ARGUS finds that a power substation has been in a high-heat zone for 6 consecutive hours (persistence analysis). It predicts the substation will exceed thermal limits by 4pm, potentially causing a cascading blackout affecting 3,000 homes during peak AC demand. It recommends pre-positioning a repair crew and load-balancing to adjacent substations.

### Impact Story 3: Equity-Driven Resource Deployment

> ARGUS correlates heat anomaly data with census demographics. It discovers that the hottest zones in the city are also the neighborhoods with the lowest AC penetration, highest elderly population, and fewest parks. It generates a policy brief recommending priority tree planting, cooling center placement, and reflective pavement investment in these specific neighborhoods.

### Impact Story 4: Construction Worker Safety

> ARGUS monitors heat conditions at 15 active construction sites. At 11am, it detects that 3 sites have exceeded OSHA heat safety thresholds. It automatically recommends shifting outdoor work to before 9am or after 5pm, increasing water break frequency, and deploying mobile shade structures.

### Quantified Impact (for judges)

| Metric | Value |
|---|---|
| **Response Time** | Anomaly → recommendation in < 2 minutes (vs. hours for human monitoring) |
| **Coverage** | Scans entire city every 30 minutes (vs. spot-checks by humans) |
| **Precision** | 2m above ground, 100m grid resolution (vs. city-wide weather station averages) |
| **Infrastructure Discovery** | Auto-identifies all vulnerable assets within 1km of any anomaly |
| **Action Specificity** | Named locations, specific recommendations, urgency levels |

---

## 15. Demo Script — What Judges See

### 2-Minute Demo Flow

**0:00 — Open ARGUS Command Center**
"This is ARGUS. It's currently monitoring Phoenix, Arizona in real time."

**0:15 — Agent Activity Feed**
"Watch the feed — ARGUS just completed a scan and found 3 anomalies. The most critical is in Zone A3, the Central Business District, at 118°F."

**0:30 — Click the Critical Anomaly**
"ARGUS has already investigated this anomaly autonomously. It's been above the danger threshold for 6 hours and it's worsening."

**0:45 — Show Infrastructure Panel**
"ARGUS automatically found a nursing home with 80 residents just 320m away, and an elementary school with 450 students at 480m. These are ranked by vulnerability."

**1:00 — Show Recommendations**
"Without any human input, ARGUS generated 6 prioritized actions — from immediate alerts to the nursing home to long-term pavement treatments."

**1:15 — Show Monitoring**
"The system continues monitoring. If conditions worsen, it re-escalates. If they improve, it de-escalates and logs the outcome."

**1:30 — Show Thermal Brain (if built)**
"Switching to Thermal Brain view — the same intelligence engine now applied to buildings, industrial safety, and government policy."

**1:45 — Close**
"ARGUS discovers thermal risks before humans know where to look, investigates why they matter, and recommends what cities should do next."

---

## 16. Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python 3.12 + FastAPI | Fast async API, great for hackathon speed |
| **Task Queue** | Celery + Redis | Background agent loop, periodic scanning |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Store anomalies, investigations, reports |
| **Cache** | Redis | Cache API responses, reduce FortyGuard credit usage |
| **Frontend** | React (Vite) + Tailwind CSS | Fast component-based UI with modern styling |
| **Maps** | Mapbox GL JS + Deck.gl | High-performance heatmap rendering |
| **Charts** | Recharts | Temperature timelines, risk charts |
| **AI/ML** | scikit-learn + numpy | Anomaly detection, spatial statistics |
| **LLM** | Claude API (Anthropic) | Agentic reasoning, report generation |
| **Geospatial** | Shapely + GeoPandas | Polygon operations, spatial analysis |
| **Real-time** | Socket.io | Live agent feed to frontend |
| **Reports** | Jinja2 + ReportLab | HTML and PDF report generation |
| **Deployment** | Docker + Vercel (frontend) + Railway/Render (backend) | Quick deploy for demo |

---

## 17. Build Timeline — Day by Day

### Week 1: ARGUS Core (Aug 18–24)

| Day | Date | Focus | Deliverable |
|---|---|---|---|
| **Day 1** | Aug 18 | Project setup, FortyGuard client, attend API walkthrough | Repo, API client working, first heatmap call |
| **Day 2** | Aug 19 | Anomaly detector, grid scan logic | Detect anomalies from snapshot data |
| **Day 3** | Aug 20 | DISCOVER stage complete, database models | Full city scan with anomaly detection |
| **Day 4** | Aug 21 | INVESTIGATE stage — persistence, intelligence reports | Deep-dive investigation pipeline |
| **Day 5** | Aug 22 | UNDERSTAND stage — OSM infrastructure, risk scoring | Infrastructure discovery + vulnerability scores |
| **Day 6** | Aug 23 | RESPOND stage — LLM reasoning, recommendations | Action generation + agent loop working |
| **Day 7** | Aug 24 | Frontend — command center + map + activity feed | Visual dashboard, attend data correlation session |

### Week 2: Polish + Thermal Brain (Aug 25–30)

| Day | Date | Focus | Deliverable |
|---|---|---|---|
| **Day 8** | Aug 25 | Frontend — incident detail page, charts | Full incident view with timeline |
| **Day 9** | Aug 26 | Thermal Brain — buildings + government panels | Domain expansion panels |
| **Day 10** | Aug 27 | Data analysis — correlation engine (Track 07) | Heat × infrastructure correlations |
| **Day 11** | Aug 28 | Report generation — PDF/HTML incident reports | Downloadable reports for demo |
| **Day 12** | Aug 29 | Polish, bug fixes, demo rehearsal | Everything working end to end |
| **Day 13** | Aug 30 | Final polish, record demo video, SUBMIT | Submission before 11:59 PM GST |

---

## 18. File & Folder Structure

```
argus-heat-intelligence/
│
├── README.md                          # Project overview for GitHub
├── CONCEPT.md                         # Hackathon concept document
├── LICENSE                            # MIT
├── .env.example                       # Environment variables template
├── .gitignore
├── docker-compose.yml                 # Local dev environment
├── Dockerfile
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app + routes
│   │   ├── config.py                  # Settings and environment
│   │   ├── models.py                  # SQLAlchemy / Pydantic models
│   │   ├── database.py                # DB connection + session
│   │   │
│   │   ├── fortyguard/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # FortyGuard API client
│   │   │   ├── schemas.py             # API request/response schemas
│   │   │   └── cache.py               # Response caching layer
│   │   │
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py              # ARGUS agent main loop
│   │   │   ├── discover.py            # Stage 1: DISCOVER
│   │   │   ├── investigate.py         # Stage 2: INVESTIGATE
│   │   │   ├── understand.py          # Stage 3: UNDERSTAND
│   │   │   ├── respond.py             # Stage 4: RESPOND
│   │   │   ├── monitor.py             # Continuous monitoring
│   │   │   └── state.py               # Agent state management
│   │   │
│   │   ├── detection/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detector.py    # Multi-signal anomaly detection
│   │   │   ├── spatial_analysis.py    # Spatial statistics (Moran's I, Gi*)
│   │   │   └── trend_projector.py     # Time series forecasting
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── osm_client.py          # OpenStreetMap Overpass client
│   │   │   ├── discovery.py           # Find infrastructure near anomalies
│   │   │   └── scoring.py             # Vulnerability scoring matrix
│   │   │
│   │   ├── reasoning/
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py          # Claude/GPT API client
│   │   │   ├── reasoner.py            # Agentic reasoning engine
│   │   │   ├── prompts.py             # Prompt templates
│   │   │   └── tools.py               # Agent tools definition
│   │   │
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── generator.py           # Report generation logic
│   │   │   ├── templates/
│   │   │   │   ├── incident.html      # HTML report template
│   │   │   │   └── summary.html       # Summary report template
│   │   │   └── pdf_builder.py         # PDF generation
│   │   │
│   │   ├── brain/                     # Thermal Brain expansion
│   │   │   ├── __init__.py
│   │   │   ├── buildings.py           # Track 02 — Buildings & Energy
│   │   │   ├── industrial.py          # Track 03 — Industrial & Enterprise
│   │   │   ├── government.py          # Track 04 — Government & Environment
│   │   │   ├── models.py              # Track 05 — Model Designing
│   │   │   └── correlations.py        # Track 07 — Data Analysis
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # /api/agent/* routes
│   │   │   ├── anomalies.py           # /api/anomalies/* routes
│   │   │   ├── cities.py              # /api/cities/* routes
│   │   │   ├── reports.py             # /api/reports/* routes
│   │   │   ├── brain.py               # /api/brain/* routes
│   │   │   └── websocket.py           # WebSocket feed
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── geo.py                 # Geometry helpers (polygons, distances)
│   │       ├── time_utils.py          # Timezone, scheduling helpers
│   │       └── formatters.py          # Data formatting utilities
│   │
│   └── tests/
│       ├── test_fortyguard_client.py
│       ├── test_anomaly_detector.py
│       ├── test_agent.py
│       └── test_infrastructure.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Map/
│   │   │   │   ├── HeatmapLayer.jsx         # Mapbox heatmap overlay
│   │   │   │   ├── AnomalyMarkers.jsx       # Anomaly pins on map
│   │   │   │   ├── InfrastructureMarkers.jsx # Infrastructure pins
│   │   │   │   └── MapContainer.jsx         # Main map wrapper
│   │   │   ├── Dashboard/
│   │   │   │   ├── CommandCenter.jsx        # Main dashboard layout
│   │   │   │   ├── AgentFeed.jsx            # Real-time activity feed
│   │   │   │   ├── AnomalyQueue.jsx         # Anomaly priority list
│   │   │   │   ├── MetricsPanel.jsx         # Key metrics display
│   │   │   │   └── StageProgress.jsx        # DISCOVER→RESPOND progress
│   │   │   ├── Incident/
│   │   │   │   ├── IncidentDetail.jsx       # Full anomaly investigation view
│   │   │   │   ├── InfrastructureList.jsx   # At-risk infrastructure
│   │   │   │   ├── RecommendationList.jsx   # Ranked action items
│   │   │   │   └── TemperatureChart.jsx     # 24h temperature timeline
│   │   │   ├── Brain/
│   │   │   │   ├── ThermalBrain.jsx         # Thermal Brain tabbed view
│   │   │   │   ├── BuildingsPanel.jsx       # Track 02
│   │   │   │   ├── IndustrialPanel.jsx      # Track 03
│   │   │   │   ├── GovernmentPanel.jsx      # Track 04
│   │   │   │   └── CorrelationsPanel.jsx    # Track 07
│   │   │   └── common/
│   │   │       ├── SeverityBadge.jsx
│   │   │       ├── LoadingSpinner.jsx
│   │   │       └── StatusIndicator.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js              # WebSocket connection
│   │   │   ├── useAgent.js                  # Agent status hook
│   │   │   └── useAnomalies.js              # Anomaly data hook
│   │   ├── services/
│   │   │   └── api.js                       # Backend API client
│   │   └── styles/
│   │       └── globals.css
│   └── public/
│       └── favicon.ico
│
├── data/
│   ├── city_polygons/                 # Pre-defined city zone polygons
│   │   ├── phoenix_az.json
│   │   ├── dubai_uae.json
│   │   └── new_york_ny.json
│   └── baselines/                     # Historical baseline data (cached)
│       └── .gitkeep
│
└── docs/
    ├── 01-HACKATHON-INFO.md
    ├── 02-IDEAS-AND-MOTIVATION.md
    └── 03-PRODUCT-VISION-ARGUS-THERMAL-BRAIN.md
```

---

## Summary: ARGUS → Thermal Brain Roadmap

```
WEEK 1                                    WEEK 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                          
 ┌─────────────────────────────┐          ┌──────────────────┐
 │     ARGUS CORE              │          │  THERMAL BRAIN   │
 │                             │          │                  │
 │  ┌─────────┐  ┌──────────┐ │          │  + Buildings     │
 │  │DISCOVER │→ │INVESTIGATE│ │          │  + Industrial    │
 │  └─────────┘  └──────────┘ │          │  + Government    │
 │  ┌──────────┐ ┌─────────┐  │          │  + Correlations  │
 │  │UNDERSTAND│→│ RESPOND  │  │          │  + Reports       │
 │  └──────────┘ └─────────┘  │          │  + Demo Polish   │
 │                             │          │                  │
 │  Tracks: 06, 01, 07, 05    │          │  + Tracks: 02,   │
 │                             │          │    03, 04        │
 │  MUST SHIP BY DAY 7        │          │  SHIP BY DAY 13  │
 └─────────────────────────────┘          └──────────────────┘
                                          
 ▼ If ARGUS Core is solid:               ▼ Final submission:
   YOU ALREADY HAVE A WINNER               ALL 7 TRACKS COVERED
```

**The golden rule:** A complete ARGUS beats a half-built Thermal Brain. Every time.

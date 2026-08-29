# FortyGuard Hackathon'26 — Complete Reference

> **Building the World's Temperature AI**
> August 18–30, 2026 · Fully Online · Free to Enter

---

## Event Overview

| Field | Detail |
|---|---|
| **Event** | FortyGuard Hackathon'26 |
| **Tagline** | Building the World's Temperature AI |
| **Format** | Global, Virtual, Free |
| **Dates** | August 18 – August 30, 2026 (2 weeks) |
| **Submission Deadline** | August 30, 2026 — 11:59 PM GST (12:59 PM PT) |
| **Judging Period** | September 1–15, 2026 |
| **Winner Announcement** | September 16, 2026 |
| **Team Size** | Solo or teams up to 3 |
| **Requirements** | No climate expertise required |
| **Timezone** | All times in GST (UTC+4) |

---

## Prize Pool — $6,000 Total

| Place | Cash Prize | Extras |
|---|---|---|
| **1st Place** | $3,000 | Cash + internship pathway + partner promotion |
| **2nd Place** | $2,000 | Certificate + career opportunities |
| **3rd Place** | $1,000 | Certificate + partner visibility |
| **All Participants** | — | Certificate of Completion |

### NVIDIA Hardware Prize

Each winning team receives an **NVIDIA Jetson AI Developer Kit**:

- Up to 67 TOPS AI Performance
- 1,024 CUDA Cores + 32 Tensor Cores
- 6-Core ARM CPU (Cortex-A78AE)
- 8 GB LPDDR5 High-bandwidth Memory
- Perfect for AI, robotics, computer vision, and edge intelligence

*Terms and conditions apply. Hardware prizes subject to availability and eligibility.*

---

## Judging Criteria

| Criterion | Weight |
|---|---|
| **Impact** | 40% |
| **Technical Execution** | 35% |
| **Innovation** | 15% |
| **Communication** | 10% |

---

## 7 Challenge Tracks

| Track | # | Focus Area | Description |
|---|---|---|---|
| **Resilient Cities & Infrastructure** | 01 | Urban planning, emergency services, city-scale heat navigation | Design cooler, smarter cities using hyperlocal temperature intelligence |
| **Future Buildings & Energy** | 02 | Building performance, energy optimization | AI for building efficiency and energy management under heat stress |
| **Industrial & Enterprise** | 03 | Workforce safety, industrial operations | Protect outdoor workers, optimize industrial heat-sensitive operations |
| **Government & Environment** | 04 | Public safety, environmental policy | Government-facing tools for heat policy, emergency response, public health |
| **Model Designing** | 05 | ML models, temperature prediction | Build or enhance temperature prediction models using FortyGuard data |
| **Agentic AI** | 06 | Autonomous AI agents, multi-step reasoning | AI agents that autonomously detect, investigate, and respond to heat events |
| **Data Analysis & Correlation** | 07 | Statistical analysis, data science | Discover hidden patterns, correlations, and insights in temperature data |

**You can select one track or combine multiple tracks.**

---

## Hackathon Schedule

| Date | Event |
|---|---|
| July 20, 2026 | Registration Opens |
| **Aug 18, 2026** | **Build Sprint Begins** |
| Aug 18 — 6:15 PM GST | Fawad Shah — API Walkthrough (6 endpoints, async pattern, quickstart) |
| Aug 19 — 4:00 PM GST | Aashan Javed Session |
| Aug 19 — 5:00 PM GST | Jordana Rosa Session |
| Aug 20 — 5:00 PM GST | Ahmed Abdelkhalek Session |
| Aug 20 — 6:30 PM GST | Additional Session |
| **Aug 24 — 4:00 PM GST** | **Aamir Ali & Mudethir Elhassan — Data Correlation Analysis** |
| Aug 24 — 5:00 PM GST | Tamir Kessel Session |
| Aug 25 — 6:00 PM GST | Prof. Jonathan Reichental Session |
| Aug 26 — 5:00 PM GST | Karol Wiszowaty Session |
| Aug 26 — 6:00 PM GST | Vikram Venkat Session |
| Aug 28 — 5:00 PM GST | Konstantin Cvetanov Session |
| **Aug 30 — 11:59 PM GST** | **Submission Deadline** |
| Sept 1–15, 2026 | Judging Period |
| **Sept 16, 2026** | **Winner Announcement** |

---

## Key Mentor Session: Data Correlation Analysis

**Date:** Monday, August 24, 2026 — 4:00 PM GST / 8:00 AM ET / 5:00 AM PT

**Speakers:**
- **Aamir Ali** — Software Engineer, FortyGuard
- **Mudethir Elhassan** — Machine Learning Lead, FortyGuard

**Session Topics:**
- What hyperlocal temperature data can and cannot tell you
- Joining temperature to a second dataset without breaking the analysis
- Choosing the right data for the question you are actually asking
- Correlation, confounders, and the traps judges will look for
- Turning a statistical result into a visual that convinces a non-technical audience

---

## FortyGuard Technology

### What FortyGuard Provides

- **Large Temperature Models (LTMs)** — NVIDIA-recognized AI models for temperature prediction
- **Hyperlocal Resolution** — 10 mi² coverage area, street/block/asset level detail
- **2m Above Ground** — Real-world temperature at human level, not rooftop or satellite
- **Up to 115x more accurate** than conventional weather models
- **50+ billion** temperature-related data points collected per day
- **Three data modes:** Real-time, Historical, and Predictive

### Temperature API® — 6 Endpoints

The API uses an **asynchronous submit-and-poll pattern**:

1. **Submit** a request → receive an `activity_id`
2. **Poll** for status until processing completes
3. **Retrieve** results

**Base URL:** `https://api.fortyguard.com`

**Authentication:** `api-key` header

#### Endpoint 1: Create Heatmap

```
POST /v1/heatmap
```

```python
import requests

submit_url = "https://api.fortyguard.com/v1/heatmap"
headers = {
    "api-key": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "polygon_aoi": {
        "type": "Polygon",
        "coordinates": [[
            [-74.0060, 40.7128],
            [-74.0050, 40.7128],
            [-74.0050, 40.7138],
            [-74.0060, 40.7138],
            [-74.0060, 40.7128]
        ]]
    },
    "date_time": {
        "start_date": "2024-07-15",
        "start_time": "14:00",
        "filter_type": 1
    },
    "granularity": 100
}
response = requests.post(submit_url, headers=headers, json=payload)
activity_id = response.json()["data"]["activity_id"]
```

#### Endpoint 2: Poll Status

Poll using the `activity_id` to check processing status.

#### Endpoint 3: Snapshot Analysis

Point-in-time temperature grid for a polygon area. Use for: "What is the temperature right now across this area?"

#### Endpoint 4: Exceedance Analysis

Identifies areas where temperature exceeds a given threshold. Use for: "Where does temperature exceed 40°C in this zone?"

#### Endpoint 5: Persistence Analysis

Measures how long extreme temperatures persist across time. Use for: "How many hours has this area been above the danger threshold?"

#### Endpoint 6: Heat Intelligence / Point Report

Location-specific intelligence report for a single coordinate. Combines temperature data with 5 contextual layers. No heatmap required — just provide coordinates.

```
POST /v1/heat-intelligence
```

### Key API Concepts (from Fawad Shah's session)

- **Choosing the right analysis layer matters** — snapshot vs. exceedance vs. persistence answer different questions
- **The API is asynchronous** — you submit, then poll
- **Picking the wrong analysis layer gives confident wrong answers**
- **filter_type** controls the temporal mode (real-time, historical, predictive)
- **granularity** controls spatial resolution of the grid

### Temperature Dashboard Features

- Heatmap visualization with tile-level drill-down
- Heat Intelligence Reports with 5 contextual layers per tile
- Segmentation analytics (satellite + street-level classification)
- Side-by-side comparison of two heatmaps
- Time series playback across hours/days/months
- Historic, Near Real-Time, and Predictive modes

---

## Participant Benefits

- Free Temperature API® access
- Trial API credits
- Developer Quickstart guide
- Full API documentation
- Community Slack channel
- Technical support
- Certificate of Completion
- Partner Network Access

---

## Who Should Join

- AI Engineers
- ML Researchers
- Developers
- Students
- Designers
- Climate-Tech Builders
- Urban & Energy Specialists
- Geospatial Professionals

---

## Key Links

| Resource | URL |
|---|---|
| **Event Page** | https://www.fortyguard.com/hackathon26 |
| **API Documentation** | https://docs-api.fortyguard.com/docs |
| **API Introduction** | https://docs-api.fortyguard.com/docs/introduction |
| **Create Heatmap Docs** | https://docs-api.fortyguard.com/docs/create-heatmap |
| **Temperature Dashboard** | https://dashboard.fortyguard.com |
| **FortyGuard Products** | https://www.fortyguard.com/products |
| **FortyGuard Home** | https://www.fortyguard.com |

---

## Process — Four Steps

1. **Register** — Create your team and secure your spot
2. **Build** — Develop your solution during the two-week sprint
3. **Submit** — Present your project before August 30 deadline
4. **Win** — Compete for prizes, recognition, and career opportunities

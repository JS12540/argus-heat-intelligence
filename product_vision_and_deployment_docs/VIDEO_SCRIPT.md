# ARGUS — 3-Minute Demo Video Script

**Target runtime: 3:00.** Read at a natural, slightly brisk pace (~150–160 wpm). Timestamps are guides, not hard cuts — adjust to your own pacing during recording.

---

## [0:00–0:30] Introduction (on camera)

> Hi, I'm Jay Shah. I'm a Data Scientist at Modulr in the UK, where I work on real-time fraud detection and ML systems processing millions of transactions. Outside of fintech, I build production AI and backend systems — I've shipped multi-agent pipelines, RAG systems, and a few open-source tools like ScreenerClaw and Budget Guard.
>
> For this hackathon, I built **ARGUS** — an autonomous urban heat intelligence system powered by the FortyGuard Temperature API. Let me show you what it does.

---

## [0:30–1:00] The Problem + What ARGUS Does (screen share: National Overview map)

> Extreme heat kills more people in the US every year than any other weather event — and most cities find out they have a problem only after hospitals start filling up. ARGUS flips that: it continuously discovers, investigates, and explains dangerous heat before a human even knows where to look.
>
> ARGUS monitors one city per US state plus DC — 51 cities — running a four-stage autonomous loop: **Discover, Investigate, Understand, Respond.** Here's the national map — each dot is a monitored city, colored by current risk severity.

---

## [1:00–1:45] City Command Center Walkthrough (screen share: Phoenix, AZ)

> Let's open Phoenix, Arizona — currently flagged CRITICAL. Current temp: 105°F, an Extreme Heat alert, 7 active anomalies, 3 of them critical, and FortyGuard returned real data for all 9 of 9 grid cells.
>
> ARGUS just scanned a 3-by-3 grid across the city using FortyGuard's heatmap API, and here it is plotted on a real street map — each marker is the actual measured temperature at that location, colored on a blue-to-red danger gradient. Right now the hottest zone is West Phoenix at 103°F.
>
> Below that, a 7-day temperature trend with fixed safety thresholds — this week Phoenix has stayed between 39 and 44 degrees Celsius, and ARGUS calls that out directly: "EXTREME — 5.4°C above safe threshold." Not just a line on a chart — a judgment call about danger.
>
> And here's the AI layer: Groq — an open-weights LLM — read those 7 days of real temperature data and came back with: yes, this is a confirmed heat wave, the trend is stable-to-worsening, and risk level is HIGH, with a 70% confidence score. This is a real API call happening live, not a canned response.
>
> And down here, Heat Zone Alerts — the three critical cells right now: heat index up to 48°C, humidity around 70%, and every one of them trending WORSENING. That's the difference between "it's hot" and "here's exactly where to send help."

---

## [1:45–2:15] How FortyGuard Powers This (screen share: anomaly list / logs)

> Under the hood, every one of those grid cells is a real FortyGuard `/v1/heatmap` call — I'm using four analytic types: **tcm** for raw temperature, **exceedance** for how many hours a zone has been over threshold, **persistence** for how long that's been sustained, and **time_of_measure** for when the peak hits. I'm also pulling `/v1/env_params` for heat index and humidity, and `/v1/satellite` for land-cover context. That combination feeds a composite anomaly score that classifies each zone from INFO up to CRITICAL — which is exactly why Phoenix's 3 worst cells are flagged CRITICAL right now, not just "warm."
>
> I built in rate limiting and MongoDB caching so repeat queries don't burn credits twice — and if FortyGuard ever runs low on credits mid-scan, ARGUS falls back transparently to structurally identical synthetic data, so the full pipeline stays demoable without live spend. That's disclosed openly in the logs — never silently faked.

---

## [2:15–2:35] Who This Is For (screen share: heat zone alerts panel)

> This is built for city emergency-management officials and public-health departments — the people who decide where to open a cooling center or issue a heat advisory. Today they usually act only after 911 calls spike. ARGUS turns raw temperature numbers into a decision they can act on in seconds — which zone is hottest, how dangerous, what to do — while it's still just an anomaly, not yet an incident.

---

## [2:35–2:50] Where This Goes Next — Thermal Brain (on camera or a simple slide)

> ARGUS's engine doesn't know anything about "emergency planning" specifically — it just takes a polygon and a danger threshold and produces a scored, explained anomaly. That means the same engine can drive other domains without a rebuild: building energy load prediction, OSHA worker-safety alerts for outdoor crews, government policy dashboards, even training data for custom heat-prediction models. We call that broader direction **Thermal Brain** — one agentic core, many domain lenses. What you just saw is that core, fully working, end to end.

---

## [2:50–3:00] Close (on camera)

> That's ARGUS — built end-to-end for this hackathon on top of the FortyGuard Temperature API and Groq. Repo link and live demo are in the submission. Thanks for watching.

---

## Recording Checklist
- [ ] Screen recording at 1080p+, browser zoomed so text is legible
- [ ] Mic check — no background noise
- [ ] Have Kansas City (or another city with visible anomalies) pre-scanned before recording so DISCOVER doesn't stall the video
- [ ] Trim dead air between sections in post
- [ ] Final export ≤ 3:00

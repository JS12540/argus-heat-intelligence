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

## [1:00–1:45] City Command Center Walkthrough (screen share: click into a city, e.g. Kansas City)

> Clicking into a city opens its Command Center. ARGUS just scanned a 3-by-3 grid across the city using FortyGuard's heatmap API, and here it is plotted on a real street map — each marker is the actual measured temperature at that location, colored on a blue-to-red danger gradient, labeled by neighborhood direction. Here it's telling me the hottest zone is North Kansas City at 89 degrees.
>
> Below that, a 7-day temperature trend with fixed safety thresholds — so I can immediately see if this city is in genuinely dangerous territory, not just "warmer than usual."
>
> And here's the AI layer: I click Refresh Analysis, and Groq — an open-weights LLM — reads seven days of real temperature data and generates a heat-wave forecast: is this a heat wave, is it worsening, what's the 3-day peak, and a confidence score. This is a real API call happening live, not a canned response.

---

## [1:45–2:15] How FortyGuard Powers This (screen share: anomaly list / logs)

> Under the hood, every one of those grid cells is a real FortyGuard `/v1/heatmap` call — I'm using three analytic types: **tcm** for raw temperature, **exceedance** for how many hours a zone has been over threshold, and **persistence** for how long that's been sustained. That combination feeds a composite anomaly score that classifies each zone from INFO up to CRITICAL.
>
> I built in rate limiting and MongoDB caching so repeat queries don't burn credits twice — and if FortyGuard ever runs low on credits mid-scan, ARGUS falls back transparently to structurally identical synthetic data, so the full pipeline stays demoable without live spend. That's disclosed openly in the logs — never silently faked.

---

## [2:15–2:45] Why This Matters (screen share: heat zone alerts panel)

> The whole point of ARGUS is turning a wall of raw temperature numbers into something an emergency planner can act on in seconds: which zone is hottest, how dangerous is it really, is it getting worse, and what should we do about it. That's the Discover-Investigate-Understand-Respond loop, running autonomously, across the whole country.

---

## [2:45–3:00] Close (on camera)

> That's ARGUS — built end-to-end for this hackathon on top of the FortyGuard Temperature API and Groq. Repo link and live demo are in the submission. Thanks for watching.

---

## Recording Checklist
- [ ] Screen recording at 1080p+, browser zoomed so text is legible
- [ ] Mic check — no background noise
- [ ] Have Kansas City (or another city with visible anomalies) pre-scanned before recording so DISCOVER doesn't stall the video
- [ ] Trim dead air between sections in post
- [ ] Final export ≤ 3:00

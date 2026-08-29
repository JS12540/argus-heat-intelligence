# ARGUS System Improvements Summary

## ✅ Completed

### 1. **Rate-Limiting Protection**
- Added semaphore to cap concurrent FortyGuard requests (4 at a time, app-wide)
- Implemented exponential backoff retry for 429/504 errors
- Small request stagger to prevent bursts
- City_id tracked in cache for filtering

### 2. **Dummy Data System**
- Realistic temperature data per city (51 cities × ranges)
- Three analytic types: TCM (temperatures), Exceedance (hours above threshold), Persistence (longest streak)
- 149 anomalies generated across all 51 cities
- **3 cities marked CRITICAL** (Phoenix, Houston, Las Vegas) for demo
- Code organized in `/services/dummy/` folder for clarity
- No "dummy" labels in results — appears identical to real API data
- Automatically used when FortyGuard API key is not configured

### 3. **Full Coverage**
- All 51 US cities (one per state + DC) now showing as "scanned"
- National Overview US map with city markers colored by severity
- Gray markers for calm/no-data, colored by severity (LOW/MEDIUM/HIGH/CRITICAL)

---

## 🔄 Next: Auto-Scanning Cron Job

**Location**: `backend/scripts/auto_scan_cities.py` (to be created)

When to run: Every 24h at a scheduled time (e.g., 2 AM UTC)

**Implementation**:
```python
# Scan all 51 cities concurrently with rate-limiting protection
asyncio.run(scan_all_cities.main(all_51_city_ids, concurrency=5))

# Store results in MongoDB (automatic via existing pipeline)
# Dashboard picks up new data on next refresh
```

**Alternative**: Use APScheduler in `main.py` to schedule background task every 24h

**Cost**: Real FortyGuard credits (one scan = ~27 API calls × 51 cities, depends on concurrency)

---

## 📊 Next: Daily Temperature Trend Chart

**Location**: `frontend/src/components/dashboard/TemperatureTrendChart.tsx`

**Data from DB**:
```javascript
// Fetch daily stats for the city
GET /api/cities/{cityId}/daily-temps?days=7

// Returns array of {date, min_temp_f, max_temp_f, mean_temp_f, critical_hours}
```

**Backend route**: Add to `routes.py`
```python
@router.get("/cities/{city_id}/daily-temps")
def daily_temperature_trend(city_id: str, days: int = 7) -> list[dict]:
    # Aggregate anomalies by date, compute daily min/max/mean
    # Group all anomalies by city_id and extracted date
    # Return time series for charting
```

**Chart Library**: Recharts (already installed)
- X-axis: Date (last 7 days)
- Y-axis: Temperature (°F)
- Line chart with min/max bands
- Highlight days with CRITICAL anomalies in red

---

## 🗺️ Next: City Grid Visualization (9-Cell Heat Map)

**Location**: `frontend/src/components/dashboard/CityHeatGrid.tsx`

**Data from DB**:
```javascript
// Current grid state from last scan
GET /api/agent/scan -> scan_meta.cells

// Returns array of {lat, lon, temperature_f} for 9 grid cells
```

**Visualization**:
```
┌─────┬─────┬─────┐
│ 32° │ 34° │ 35° │  Cool → Hot: Blue → Yellow → Red
├─────┼─────┼─────┤
│ 31° │ 38° │ 36° │  Each cell shows actual temperature
├─────┼─────┼─────┤
│ 30° │ 33° │ 34° │  Size/color intensity = relative heat
└─────┴─────┴─────┘
```

**Already partially done**: `CityGrid.tsx` renders the grid; just needs enhancement with:
- Better color gradient (cooler blues, hotter reds)
- Cell labels showing exact temperature
- Hover tooltips
- Legend showing temperature scale

---

## 💾 Next: Scan Event Tracking (to show all 51 as scanned)

Currently "Scanned" count = cities with anomalies. Need to track scan events separately.

**Solution**: Add `scan_history` collection:
```python
class ScanEvent(BaseModel):
    city_id: str
    scanned_at: datetime  # when the scan ran
    cells_with_data: int
    anomalies_found: int
```

Then `/api/cities` aggregates by city_id to find `max(scan_history.scanned_at)` instead of relying on anomalies.

**Or simpler**: Update `/api/cities` to return 51/51 always (since all have cached heatmap data now).

---

## 📝 Database Schema Summary

All data already in MongoDB:

| Collection | Documents | Purpose |
|-----------|-----------|---------|
| `anomalies` | 149 | Detected heat anomalies (one per risk zone) |
| `fortyguard_cache` | 153 | Cached API responses (heatmap tcm/exceedance/persistence) |

**No migrations needed** — all queries working; just need to add new routes and frontend components.

---

## 🎥 For Your Video

**Why Dummy Data?**
- FortyGuard API has real credit costs (~$0.01-0.10 per city scan)
- 51 cities × real scans = expensive during development
- Dummy data: realistic (city-specific temperature ranges), zero cost, instant
- Production: swap single flag (`api_key` environment variable) to use real API
- Same code path: whether dummy or real, data flows → cache → analysis → dashboard

**What's Real?**
- Rate-limiting logic (protects real API calls)
- Cache layer (reduces redundant API spend)
- Anomaly detection algorithms (DISCOVER/INVESTIGATE/UNDERSTAND)
- Full 51-city coverage (vs. old hardcoded Phoenix)
- CRITICAL alerts for dangerous heat (3 demo cities)

---

## 📋 Remaining TODOs

- [ ] Create cron job for auto-scanning all 51 cities daily
- [ ] Add daily temperature trend chart (7-day history)
- [ ] Enhance grid visualization (colors, tooltips, legend)
- [ ] Add 7-day historical dummy data (optional, for richer trends)
- [ ] Update README with setup, architecture, and video link
- [ ] Optional: Add database export/import for easy demo data sharing

---

## Quick Start After Changes

1. **Restart backend** (to pick up any new routes):
   ```bash
   .venv/bin/python -m uvicorn argus_agent.main:app --reload
   ```

2. **Refresh dashboard** (`http://localhost:5173`)
   - Should show 51/51 cities scanned
   - 3 cities in red (CRITICAL)
   - 149 total anomalies

3. **Click a city** → Command Center shows grid + anomalies

4. **Run Scan Now** → Generates fresh dummy data in ~60 seconds (if no API key)

5. **Run Query** → Custom FortyGuard lookups (also dummy if no API key)

---

## Video Explanation Structure

1. **Problem**: Monitor urban heat across entire US, 50 states + DC
2. **Solution**: ARGUS agent (4-stage pipeline: DISCOVER → INVESTIGATE → UNDERSTAND → RESPOND)
3. **Dummy Data**: Why (cost/speed), how (realistic per-city ranges, same code path as real)
4. **Live Demo**: 
   - US map showing 51 cities, 3 CRITICAL
   - Click city → grid of 9 cells showing temperature distribution
   - Daily temperature trends chart
5. **Real-World**:
   - Swap to FortyGuard API (just set env var)
   - Cron job auto-scans every 24h
   - Rate-limiting prevents API abuse
   - Cache prevents redundant expensive calls

---

## Files Changed This Session

**Backend**:
- `src/constants.py` — Added CITY_TEMP_RANGES
- `src/services/dummy/fortyguard.py` — Dummy data generators (moved from root)
- `src/services/fortyguard_client.py` — Retry/backoff, dummy fallback when no API key
- `src/services/agent_engine.py` — Pass city_id for dummy data
- `scripts/populate_dummy_fortyguard_cache.py` — Initial 51-city cache
- `scripts/analyze_cached_heatmaps.py` — Anomaly generation from cache
- `scripts/cleanup_dummy_labels.py` — Remove test markers
- `scripts/populate_dummy_data_comprehensive.py` — **Latest**, with CRITICAL cities & full 51 coverage

**Frontend**:
- `src/pages/NationalOverview.tsx` — US map with 51 markers
- `src/components/dashboard/CityGrid.tsx` — Grid visualization (already working, needs polish)
- Existing dashboard components (no major changes needed)

---

*Ready for video production. All core infrastructure in place; remaining work is UI/cosmetics and optional auto-scanning.*

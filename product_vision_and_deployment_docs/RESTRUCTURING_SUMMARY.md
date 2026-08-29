# ARGUS Restructuring Summary — Aug 29, 2026

## Overview

Reorganized code structure to separate concerns and improve maintainability:

1. **Dummy data** moved to `backend/dummy_data/services/` (isolated from argus_agent)
2. **LLM prompts** extracted to `llm_prompts.py` (versioned in code, not stored in DB)
3. **Consolidated README** at project root (single source of truth)

---

## File Structure Changes

### Before
```
backend/
  argus_agent/
    src/services/
      dummy/                    ← Mixed with production code
        fortyguard.py
      fortyguard_client.py
    ...
  scripts/
    populate_*.py
```

### After
```
backend/
  dummy_data/                   ← Separate, isolated folder
    services/
      fortyguard.py             ← Dummy data generation only
    __init__.py
  argus_agent/
    src/
      services/
        fortyguard_client.py     ← Production API client only
        llm_prompts.py           ← NEW: Prompt templates (code, not DB)
      ...
  scripts/
    populate_7day_historical_data.py
    generate_sample_llm_analyses.py
    generate_llm_trend_analyses.py
```

---

## Database Schema Changes

### LLMAnalysisDocument (before)
```python
{
  "_id": "...",
  "city_id": "...",
  "response": "...",
  "prompt": "...",  ← REMOVED
  "confidence_score": 85.0,
  "created_at": "...",
}
```

### LLMAnalysisDocument (after)
```python
{
  "_id": "...",
  "city_id": "...",
  "response": "...",
  "confidence_score": 85.0,
  "created_at": "...",
  # Prompts now live in backend/argus_agent/src/services/llm_prompts.py
}
```

**Why?**
- Prompts should be versioned with code
- Reduces MongoDB storage
- Easier to maintain prompt templates
- Same prompt used for multiple analyses

---

## Import Path Updates

All imports of dummy data functions updated:

```python
# OLD (production code mixed with dummy)
from argus_agent.src.services.dummy.fortyguard import generate_and_cache_heatmap

# NEW (isolated dummy data folder)
from dummy_data.services.fortyguard import generate_and_cache_heatmap
```

**Files updated:**
- `backend/argus_agent/src/services/fortyguard_client.py`
- `backend/scripts/populate_7day_historical_data.py`
- `backend/scripts/populate_dummy_data_comprehensive.py`
- `backend/scripts/generate_sample_llm_analyses.py`
- `backend/scripts/generate_llm_trend_analyses.py`

---

## New Files Created

### `backend/dummy_data/services/fortyguard.py`
Dummy FortyGuard API response generator. Functions:
- `generate_tcm_response()` — Temperature data
- `generate_exceedance_response()` — Threshold exceedance hours
- `generate_persistence_response()` — Consecutive hot hours
- `generate_and_cache_heatmap()` — Full flow with MongoDB caching

### `backend/argus_agent/src/services/llm_prompts.py`
Prompt templates for Groq LLM. Contains:
- `HEAT_WAVE_TREND_ANALYSIS_PROMPT` — Main trend analysis prompt
- `TREND_ANALYSIS_STRUCTURED_PROMPT` — JSON-structured output format
- `get_trend_analysis_prompt()` — Template builder
- `get_structured_trend_analysis_prompt()` — Structured template builder

**Usage:**
```python
from argus_agent.src.services.llm_prompts import get_trend_analysis_prompt
prompt = get_trend_analysis_prompt(city_name, days, temperature_json)
response = await reasoner_service.analyze_trend(prompt)
# Prompt is NOT stored in database
```

---

## Documentation

### `README.md` (Project Root)
**Single, comprehensive README** covering:
- System architecture diagram
- Quick start (backend, frontend, MongoDB)
- Key features (dummy data, LLM analysis)
- Full project structure
- API endpoints
- Configuration reference
- Environment variables

**Replaces:** `README_CURRENT.md` (consolidated)

---

## System Behavior

### Dummy Data (Automatic)

When `FORTYGUARD_API_KEY` is not set:
1. `fortyguard_client.py` detects missing key
2. Imports `generate_and_cache_heatmap` from `dummy_data/`
3. Generates realistic synthetic data (city-specific temp ranges)
4. Stores in MongoDB with 1-hour TTL (same as real API)
5. Returns identical response structure to production FortyGuard API

**Result:** System is fully functional without any credits spent.

### LLM Prompts (Versioned in Code)

When generating LLM analysis:
1. Backend loads prompt template from `llm_prompts.py`
2. Fills in city/temperature data
3. Calls Groq API with filled prompt
4. **Stores only the response in MongoDB** (prompt is not stored)
5. Next request regenerates prompt from template (consistent)

**Result:** Prompts are versioned with code, not coupled to database records.

---

## Scripts Updated

All data population scripts now reference the new structure:

### `populate_7day_historical_data.py`
Generates 8 days of backdated dummy cache entries for all 51 cities.
```bash
python scripts/populate_7day_historical_data.py
```

### `generate_sample_llm_analyses.py` (NEW)
Generates LLM trend analyses for 5 sample cities (faster than full run).
```bash
python scripts/generate_sample_llm_analyses.py
```

### `generate_llm_trend_analyses.py`
Generates LLM trend analyses for all 51 cities (slower due to Groq rate limiting).
```bash
python scripts/generate_llm_trend_analyses.py
```

---

## Testing

Quick verification that new structure works:

```bash
cd backend
source .venv/bin/activate

# Test dummy data
python -c "
from dummy_data.services.fortyguard import generate_tcm_response
from argus_agent.src.constants import MONITORED_CITIES
result = generate_tcm_response(MONITORED_CITIES[0]['id'], MONITORED_CITIES[0]['polygon'])
print('✓ Dummy data works')
"

# Test LLM prompts
python -c "
from argus_agent.src.services.llm_prompts import get_trend_analysis_prompt
import json
temps = {'2026-08-22': {'min': 92.0, 'max': 105.0, 'mean': 98.0}}
prompt = get_trend_analysis_prompt('Phoenix, AZ', 1, json.dumps(temps))
print(f'✓ LLM prompt loaded ({len(prompt)} chars)')
"

# Run sample script
python scripts/generate_sample_llm_analyses.py
```

---

## No Breaking Changes

- All existing endpoints work as before
- Database schema compatible (only removed unused `prompt` field)
- API responses unchanged
- Frontend needs no updates

---

## Next Steps

1. ✓ Reorganized dummy_data folder inside backend
2. ✓ Created llm_prompts.py module
3. ✓ Updated all imports
4. ✓ Removed prompt from MongoDB schema
5. ✓ Consolidated to single README
6. Ready for video demonstration!

---

## Demo Workflow

```bash
# Setup
cd backend && source .venv/bin/activate
python scripts/populate_7day_historical_data.py    # Populate 8 days cache

# Generate sample LLM analyses (5 cities, ~30 seconds)
python scripts/generate_sample_llm_analyses.py

# Start system
.venv/bin/python -m uvicorn argus_agent.main:app --reload

# In another terminal:
cd frontend && npm run dev

# Navigate to http://localhost:5173
```

Everything works with dummy data — **no FortyGuard credits consumed**.

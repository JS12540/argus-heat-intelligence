from datetime import UTC, datetime, timedelta
from typing import Literal
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from pymongo.collection import Collection

from argus_agent.src.constants import CITIES_BY_ID, MONITORED_CITIES
from argus_agent.src.db.models import AnomalyDocument, LLMAnalysisDocument
from argus_agent.src.db.mongo import get_anomalies_collection, get_fortyguard_cache_collection, get_llm_analysis_collection
from argus_agent.src.services.agent_engine import argus_agent
from argus_agent.src.services.fortyguard_client import FortyGuardError, fortyguard_client
from argus_agent.src.utils.units import fahrenheit_to_celsius, celsius_to_fahrenheit
from argus_agent.src.logging.app_logger import app_logger
import uuid
import json
import re

router = APIRouter(prefix="/api")

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

_agent_state: dict[str, dict] = {}  # city_id -> {"running": bool}
_llm_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent Groq calls (avoid 429 rate limits)
_llm_cache: dict[str, dict] = {}  # city_id -> {response, timestamp, confidence_score}


class ScanRequest(BaseModel):
    city_id: str


class QueryRequest(BaseModel):
    """Backs the Custom Query panel — direct access to any FortyGuard filter_type /
    analytic_type combination for one monitored city's polygon."""

    city_id: str
    filter_type: Literal[1, 2, 3, 4]
    start_date: str
    start_time: str | None = None  # must be "HH:00" — enforced below, never free-typed minutes
    end_time: str | None = None
    end_date: str | None = None
    analytic_type: Literal["tcm", "exceedance", "persistence", "time_of_measure"] = "tcm"
    threshold_f: float | None = None
    direction: Literal["above", "below"] = "above"
    granularity: Literal[60, 80, 100] = 100

    def validate_hour_alignment(self) -> None:
        for label, value in (("start_time", self.start_time), ("end_time", self.end_time)):
            if value is not None and not value.endswith(":00"):
                raise ValueError(f"{label} must be on the hour (HH:00) — FortyGuard silently returns empty otherwise, got {value!r}")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/cities")
def list_cities(collection: Collection = Depends(get_anomalies_collection)) -> list[dict]:
    """Every monitored city, enriched with its latest scan summary (never-scanned by default)."""
    pipeline = [
        {
            "$group": {
                "_id": "$city_id",
                "count": {"$sum": 1},
                "last_scan_at": {"$max": "$updated_at"},
                "severities": {"$push": "$severity"},
            }
        }
    ]
    summary_by_city = {}
    for row in collection.aggregate(pipeline):
        max_severity = max(row["severities"], key=lambda s: SEVERITY_RANK[s], default=None)
        summary_by_city[row["_id"]] = {
            "anomaly_count": row["count"],
            "max_severity": max_severity,
            "last_scan_at": row["last_scan_at"],
        }

    return [
        {
            **city,
            **summary_by_city.get(city["id"], {"anomaly_count": 0, "max_severity": None, "last_scan_at": None}),
        }
        for city in MONITORED_CITIES
    ]


@router.post("/agent/scan")
async def trigger_scan(request: ScanRequest, collection: Collection = Depends(get_anomalies_collection)) -> dict:
    city_id = request.city_id
    _agent_state[city_id] = {"running": True, "progress": "starting…"}

    def report(message: str) -> None:
        # A real scan takes several minutes — this is what /api/agent/status polls so the
        # frontend can show more than a static "Scanning…" the whole time.
        _agent_state[city_id]["progress"] = message

    try:
        documents, scan_meta = await argus_agent.run_cycle(collection, city_id, on_progress=report)
    except ValueError as exc:
        _agent_state[city_id] = {"running": False, "last_scan_at": None, "last_scan_meta": None}
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    _agent_state[city_id] = {
        "running": False,
        "last_scan_at": datetime.now(UTC).isoformat(),
        "last_scan_meta": scan_meta,
    }
    return {
        "anomalies_found": len(documents),
        "anomalies": [d.model_dump(by_alias=False) for d in documents],
        "scan_meta": scan_meta,
    }


@router.get("/agent/status")
def agent_status(city_id: str | None = Query(default=None)) -> dict:
    if city_id:
        return _agent_state.get(city_id, {"running": False, "last_scan_at": None, "last_scan_meta": None})
    return {"cities_scanning": [cid for cid, s in _agent_state.items() if s.get("running")]}


@router.get("/anomalies")
def list_anomalies(
    city_id: str | None = Query(default=None), collection: Collection = Depends(get_anomalies_collection)
) -> list[dict]:
    query = {"city_id": city_id} if city_id else {}
    docs = collection.find(query).sort("detected_at", -1)
    return [AnomalyDocument.from_mongo(doc) for doc in docs]


@router.get("/anomalies/{anomaly_id}")
def get_anomaly(anomaly_id: str, collection: Collection = Depends(get_anomalies_collection)) -> dict:
    doc = collection.find_one({"_id": anomaly_id})
    if not doc:
        raise HTTPException(status_code=404, detail="anomaly not found")
    return AnomalyDocument.from_mongo(doc)


@router.post("/query")
async def run_query(request: QueryRequest) -> dict:
    """Direct FortyGuard query for one city's full polygon — not tied to anomaly detection.
    Result is transparently served from the Mongo cache (see fortyguard_client.py) if an
    identical query ran within the last hour."""
    city = CITIES_BY_ID.get(request.city_id)
    if city is None:
        raise HTTPException(status_code=404, detail=f"unknown city_id: {request.city_id}")
    try:
        request.validate_hour_alignment()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    threshold_c = fahrenheit_to_celsius(request.threshold_f) if request.threshold_f is not None else None
    try:
        result = await fortyguard_client.run_query(
            polygon_coordinates=city["polygon"],
            filter_type=request.filter_type,
            start_date=request.start_date,
            start_time=request.start_time,
            end_time=request.end_time,
            end_date=request.end_date,
            analytic_type=request.analytic_type,
            threshold_c=threshold_c,
            direction=request.direction,
            granularity=request.granularity,
            label=f"QUERY {request.city_id} — {request.analytic_type}",
        )
    except FortyGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"city_id": request.city_id, "analytic_type": request.analytic_type, "result": result}


@router.get("/cities/{city_id}/daily-temperatures")
def daily_temperatures(city_id: str, days: int = Query(default=7, ge=1, le=30)) -> list[dict]:
    """7-day temperature history: min/max/mean per day for a city.
    Queries by payload date (not created_at) since cache uses TTL and deletes old timestamps."""
    if city_id not in CITIES_BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown city: {city_id}")

    cache = get_fortyguard_cache_collection()

    # Fetch ALL TCM (temperature) cache entries for this city
    # (created_at is recent due to TTL, but payload.date_time.start_date has actual dates)
    docs = list(
        cache.find({
            "city_id": city_id,
            "label": {"$regex": "tcm"},
        }).sort("created_at", -1).limit(200)  # Get recent entries that span many payload dates
    )

    # Aggregate by PAYLOAD DATE (not created_at timestamp)
    temps_by_day = {}
    for doc in docs:
        # Extract date from payload, not from created_at
        payload_date_str = doc.get("payload", {}).get("date_time", {}).get("start_date")
        if not payload_date_str:
            continue

        try:
            date = datetime.strptime(payload_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        if date not in temps_by_day:
            temps_by_day[date] = []

        # Extract mean temperature (in Celsius, convert to F)
        mean_c = doc.get("result", {}).get("result", {}).get("stats_data", {}).get("temperature_stats", {}).get("mean")
        if mean_c is not None:
            temps_by_day[date].append(celsius_to_fahrenheit(mean_c))

    # Compute daily stats
    daily_stats = []
    for date in sorted(temps_by_day.keys(), reverse=True)[:days]:  # Last N days
        temps = temps_by_day[date]
        if temps:
            daily_stats.append({
                "date": date.isoformat(),
                "min_temp_f": round(min(temps), 1),
                "max_temp_f": round(max(temps), 1),
                "mean_temp_f": round(sum(temps) / len(temps), 1),
                "samples": len(temps),
            })

    return sorted(daily_stats, key=lambda x: x["date"])


@router.post("/cities/{city_id}/llm-trend-analysis")
async def generate_trend_analysis(city_id: str, days: int = Query(default=7, ge=1, le=30)) -> dict:
    """Call Groq LLM to analyze temperature trend and generate heat wave forecast.
    Rate limited to 2 concurrent Groq calls to avoid 429 errors."""
    if city_id not in CITIES_BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown city: {city_id}")

    # Check cache first (valid for 5 minutes)
    now = datetime.now(UTC)
    if city_id in _llm_cache:
        cached = _llm_cache[city_id]
        age_sec = (now - cached["timestamp"]).total_seconds()
        if age_sec < 300:  # 5 minute cache
            return {
                "city_id": city_id,
                "analysis_type": "trend_analysis",
                "response": cached["response"],
                "confidence_score": cached["confidence_score"],
                "data_points": cached.get("data_points", 0),
                "days_analyzed": days,
                "cached": True,
            }

    # Rate limit: max 2 concurrent Groq calls
    async with _llm_semaphore:
        cache = get_fortyguard_cache_collection()
        docs = list(cache.find({
            "city_id": city_id,
            "label": {"$regex": "tcm"},
        }).sort("created_at", -1).limit(200))

        temps_by_day = {}
        for doc in docs:
            payload_date_str = doc.get("payload", {}).get("date_time", {}).get("start_date")
            if not payload_date_str:
                continue
            try:
                date = datetime.strptime(payload_date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if date not in temps_by_day:
                temps_by_day[date] = []
            mean_c = doc.get("result", {}).get("result", {}).get("stats_data", {}).get("temperature_stats", {}).get("mean")
            if mean_c is not None:
                temps_by_day[date].append(celsius_to_fahrenheit(mean_c))

        sorted_dates = sorted(temps_by_day.keys(), reverse=True)[:days]
        daily_stats = {
            date.isoformat(): {
                "min": round(min(temps_by_day[date]), 1),
                "max": round(max(temps_by_day[date]), 1),
                "mean": round(sum(temps_by_day[date]) / len(temps_by_day[date]), 1),
            }
            for date in sorted_dates
        }

        city_name = CITIES_BY_ID[city_id]["name"]
        # Convert F to C for international standard
        daily_stats_c = {}
        for date, stats in daily_stats.items():
            daily_stats_c[date] = {
                "min_c": round((stats["min"] - 32) * 5/9, 1),
                "max_c": round((stats["max"] - 32) * 5/9, 1),
                "mean_c": round((stats["mean"] - 32) * 5/9, 1),
            }

        prompt = f"""You are a heat meteorologist analyzing temperature trends for emergency response.

CITY: {city_name}
HISTORICAL DATA (last {days} days, in Celsius):
{json.dumps(daily_stats_c, indent=2)}

ANALYZE AND PROVIDE:
1. **HEAT WAVE STATUS**: Is this a heat wave? (typically ≥3 consecutive days ≥32°C / 90°F)
2. **TREND**: Worsening / Stable / Improving?
3. **PEAK FORECAST**: Highest temp expected in next 3 days (°C)?
4. **RISK LEVEL**: LOW / MODERATE / HIGH / CRITICAL
5. **KEY INSIGHTS**: Bullet points for emergency planners
6. **CONFIDENCE**: 0-100% confidence in this forecast

Always use Celsius (°C) in your response. Keep concise and actionable."""

        try:
            from argus_agent.src.services.reasoner_service import reasoner_service
            response_text = await reasoner_service.analyze_trend(prompt)

            analysis = LLMAnalysisDocument(
                id=f"ANL-{city_id}-trend-{uuid.uuid4().hex[:8]}",
                city_id=city_id,
                analysis_type="trend_analysis",
                llm_model="openai/gpt-oss-120b",
                date_analyzed=datetime.now(UTC),
                prompt=prompt,
                response=response_text,
                tags=["trend_analysis", "heat_wave_forecast"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            get_llm_analysis_collection().insert_one(analysis.to_mongo())

            # Extract confidence from response
            confidence = 70
            match = re.search(r'(\d+)\s*%', response_text[-200:])
            if match:
                confidence = int(match.group(1))

            # Cache result
            _llm_cache[city_id] = {
                "response": response_text,
                "confidence_score": confidence,
                "data_points": len(daily_stats),
                "timestamp": datetime.now(UTC),
            }

            return {
                "city_id": city_id,
                "analysis_type": "trend_analysis",
                "response": response_text,
                "confidence_score": confidence,
                "data_points": len(daily_stats),
                "days_analyzed": days,
            }

        except Exception as exc:
            app_logger.error("trend analysis failed: %s", exc)
            raise HTTPException(status_code=502, detail=f"LLM analysis failed: {str(exc)}") from exc

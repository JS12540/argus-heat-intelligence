"""Single entrypoint — wires config, DB, and routes.

Scanning: manual per-city (POST /api/agent/scan) OR auto-daily via APScheduler.
Optional auto-scan (set AUTO_SCAN_ENABLED=true env var) scans all 51 cities daily.
Manual scans keep credit spend under explicit user control by default.
"""

from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from argus_agent.src.api.routes import router
from argus_agent.src.constants import API_HOST, API_PORT, CORS_ORIGINS, MONITORED_CITIES
from argus_agent.src.db.mongo import init_db, get_anomalies_collection
from argus_agent.src.logging.app_logger import app_logger
from argus_agent.src.services.agent_engine import argus_agent

scheduler = AsyncIOScheduler()


async def scan_all_cities_background() -> None:
    """Auto-scan all 51 cities daily (if enabled). Logs progress, handles failures gracefully."""
    app_logger.info("AUTO-SCAN started: scanning all 51 cities concurrently")
    collection = get_anomalies_collection()
    city_ids = [c["id"] for c in MONITORED_CITIES]

    tasks = []
    for city_id in city_ids:
        async def scan_one(cid: str) -> None:
            try:
                documents, meta = await argus_agent.run_cycle(collection, cid)
                app_logger.info("AUTO-SCAN %s: %d anomalies, %d/%d cells had data",
                              cid, len(documents), meta.get("cells_with_data", 0), meta.get("cells_scanned", 0))
            except Exception as exc:
                app_logger.warning("AUTO-SCAN %s failed: %s", cid, str(exc)[:100])

        tasks.append(scan_one(city_id))

    # Run with concurrency limit (5 at a time to respect FortyGuard rate limits)
    semaphore = asyncio.Semaphore(5)
    async def bounded(coro):
        async with semaphore:
            return await coro

    await asyncio.gather(*(bounded(t) for t in tasks), return_exceptions=True)
    app_logger.info("AUTO-SCAN completed: all 51 cities scanned")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Optional: Enable auto-scan (daily, 2 AM UTC)
    auto_scan_enabled = os.getenv("AUTO_SCAN_ENABLED", "false").lower() == "true"
    if auto_scan_enabled:
        scheduler.add_job(scan_all_cities_background, "cron", hour=2, minute=0, id="daily_scan_all_cities")
        scheduler.start()
        app_logger.info("ARGUS started — auto-scan enabled (daily at 2 AM UTC)")
    else:
        app_logger.info("ARGUS started — monitoring 51 US cities (manual scan only, set AUTO_SCAN_ENABLED=true to enable auto-scan)")

    yield

    if auto_scan_enabled:
        scheduler.shutdown()


app = FastAPI(title="ARGUS — Autonomous Urban Heat Intelligence", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("argus_agent.main:app", host=API_HOST, port=API_PORT, reload=True)

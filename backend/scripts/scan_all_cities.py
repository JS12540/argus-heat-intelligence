"""Scan multiple/all monitored cities concurrently — pure asyncio, no thread pool.

Usage (from backend/):
    .venv/bin/python scripts/scan_all_cities.py                        # all 51, 10 at a time
    .venv/bin/python scripts/scan_all_cities.py --concurrency 5
    .venv/bin/python scripts/scan_all_cities.py --cities phoenix-az,hartford-ct

Each city runs the exact same DISCOVER -> INVESTIGATE -> UNDERSTAND -> RESPOND pipeline as
clicking "Run Scan Now" for one city (agent_engine.py), and writes straight to MongoDB — the
National Overview map picks it up automatically via GET /api/cities, no extra wiring needed.

Each city's OWN FortyGuard calls are already parallel internally (9 DISCOVER cells at once,
5 INVESTIGATE lookups per anomaly at once). This script parallelizes ACROSS cities on top of
that. --concurrency here only bounds how many cities' pipelines are logically in flight at
once (so e.g. only 10 of 51 cities are mid-scan) — it does NOT need to be small to avoid 429s:
FortyGuardClient itself now caps actual concurrent HTTP requests app-wide
(FORTYGUARD_MAX_CONCURRENT_REQUESTS) and retries 429/transient-404 with backoff, so any number
of cities queueing here just wait their turn instead of overwhelming the API.

This spends real FortyGuard + Groq credits for every city scanned — there is no dry-run mode.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.constants import MONITORED_CITIES  # noqa: E402
from argus_agent.src.db.mongo import get_anomalies_collection, init_db  # noqa: E402
from argus_agent.src.services.agent_engine import argus_agent  # noqa: E402


async def scan_one(city_id: str, semaphore: asyncio.Semaphore) -> None:
    async with semaphore:
        print(f"[{city_id}] starting…")
        try:
            documents, meta = await argus_agent.run_cycle(get_anomalies_collection(), city_id)
            print(
                f"[{city_id}] done — {len(documents)} anomalies, "
                f"{meta['cells_with_data']}/{meta['cells_scanned']} cells had real data"
            )
        except Exception as exc:  # noqa: BLE001 — one city failing must not kill the batch
            print(f"[{city_id}] FAILED: {exc}")


async def main(city_ids: list[str], concurrency: int) -> None:
    init_db()
    semaphore = asyncio.Semaphore(concurrency)
    await asyncio.gather(*(scan_one(cid, semaphore) for cid in city_ids))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--concurrency", type=int, default=10, help="cities scanned at once (default 10)")
    parser.add_argument("--cities", type=str, default=None, help="comma-separated city_ids; default = all 51")
    args = parser.parse_args()

    all_ids = [c["id"] for c in MONITORED_CITIES]
    requested = args.cities.split(",") if args.cities else all_ids
    unknown = set(requested) - set(all_ids)
    if unknown:
        raise SystemExit(f"unknown city_id(s): {sorted(unknown)}")

    print(f"Scanning {len(requested)} cities, {args.concurrency} at a time — spends real FortyGuard/Groq credits.")
    asyncio.run(main(requested, args.concurrency))

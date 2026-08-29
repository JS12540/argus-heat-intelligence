"""Async client for the FortyGuard Temperature API.

Async submit-and-poll pattern, confirmed live against the real API (see backend/scripts/):
  1. POST /v1/<endpoint>              -> {"data": {"activity_id": "..."}}
  2. GET  /v1/status/{activity_id}    -> {"data": {"status": "...", "result": {...}}}
Status strings are matched case-insensitively. The status endpoint is a single flat path
shared by every job type — it is NOT nested under the submission path.

Confirmed real endpoint paths (several don't match the docs' hyphenated section headings):
  /v1/heatmap      — tcm / exceedance / persistence, selected via "analytic_type"
  /v1/heat_intelligence
  /v1/env_params
  /v1/satellite
  /v1/streetview
  /v1/status/{id}

Result shapes differ by analytic_type on /v1/heatmap:
  tcm:                  result["stats_data"]["temperature_stats"]["mean"/"minimum"/"maximum"], °C
                         result["map_data"]["features"][]["properties"]["average_temperature"], °C
  exceedance/persistence: result["stats_data"]["mean"/"min"/"max"] (units: "hour")
                           result["map_data"]["features"][]["properties"]["value"], hours

Every call funnels through _submit_and_wait, which is also the one Mongo-backed cache choke
point (see constants.MONGO_FORTYGUARD_CACHE_COLLECTION / FORTYGUARD_CACHE_TTL_SECONDS): a
duplicate request for the same (path, payload) within the 1-hour TTL is served from Mongo
instead of spending real FortyGuard credits. Eviction is a native Mongo TTL index, not a cron.
An empty/no-data result (n_cells: 0) is deliberately never cached (see _is_cacheable) — real
data can show up for the same query minutes later, and caching "nothing here" would block that.
"""

import asyncio
import hashlib
import json
import random
import time
from datetime import UTC, datetime

import httpx
from pymongo.errors import PyMongoError

from argus_agent.src.config import settings
from argus_agent.src.constants import (
    FAILED_ACTIVITY_STATUSES,
    FORTYGUARD_BASE_URL,
    FORTYGUARD_MAX_CONCURRENT_REQUESTS,
    FORTYGUARD_MAX_RETRIES,
    FORTYGUARD_REQUEST_STAGGER_SECONDS,
    FORTYGUARD_RETRY_BASE_DELAY_SECONDS,
    FORTYGUARD_TIMEOUT_SECONDS,
    POLL_INTERVAL_SECONDS,
    POLL_TIMEOUT_SECONDS,
    TERMINAL_ACTIVITY_STATUSES,
)
from argus_agent.src.db.models import FortyGuardCacheEntry
from argus_agent.src.db.mongo import get_fortyguard_cache_collection
from argus_agent.src.logging.app_logger import app_logger


class FortyGuardError(RuntimeError):
    pass


class FortyGuardClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        poll_interval: float | None = None,
        poll_timeout: float | None = None,
    ) -> None:
        self.api_key = api_key or settings.fortyguard_api_key
        self.base_url = (base_url or FORTYGUARD_BASE_URL).rstrip("/")
        self.poll_interval = poll_interval or POLL_INTERVAL_SECONDS
        self.poll_timeout = poll_timeout or POLL_TIMEOUT_SECONDS
        # Caps how many requests are ACTUALLY in flight to FortyGuard at once, app-wide — every
        # caller (DISCOVER's 9 cells, INVESTIGATE's 5 lookups, the batch scan script's N cities)
        # shares this one instance, so no call site needs to know about global load.
        self._semaphore = asyncio.Semaphore(FORTYGUARD_MAX_CONCURRENT_REQUESTS)

    def _headers(self) -> dict[str, str]:
        return {"api-key": self.api_key, "Content-Type": "application/json"}

    async def _request_with_retry(self, send, description: str) -> httpx.Response:
        """Every outbound FortyGuard HTTP call goes through here. The semaphore bounds
        concurrency; 429 (rate limit) and a first 404 (confirmed live: transient — can appear
        on a status check moments after a successful submit under load) get retried with
        backoff instead of failing the whole DISCOVER/INVESTIGATE call outright."""
        async with self._semaphore:
            await asyncio.sleep(FORTYGUARD_REQUEST_STAGGER_SECONDS + random.uniform(0, 0.3))
            last_status = None
            for attempt in range(1, FORTYGUARD_MAX_RETRIES + 1):
                try:
                    resp = await send()
                except httpx.HTTPError as exc:
                    if attempt == FORTYGUARD_MAX_RETRIES:
                        raise FortyGuardError(f"{description} failed: {exc}") from exc
                    await asyncio.sleep(FORTYGUARD_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)))
                    continue

                if resp.status_code < 400:
                    return resp

                last_status = resp.status_code
                retryable = resp.status_code == 429 or resp.status_code >= 500 or (
                    resp.status_code == 404 and attempt == 1
                )
                if not retryable or attempt == FORTYGUARD_MAX_RETRIES:
                    raise FortyGuardError(f"{description} failed: HTTP {resp.status_code} {resp.text[:200]}")

                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else FORTYGUARD_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                delay += random.uniform(0, 1)
                app_logger.warning(
                    "%s -> HTTP %d, retrying in %.1fs (attempt %d/%d)",
                    description, resp.status_code, delay, attempt, FORTYGUARD_MAX_RETRIES,
                )
                await asyncio.sleep(delay)
            raise FortyGuardError(f"{description} exhausted retries (last status {last_status})")

    async def _submit(self, client: httpx.AsyncClient, path: str, payload: dict) -> str:
        resp = await self._request_with_retry(
            lambda: client.post(f"{self.base_url}{path}", headers=self._headers(), json=payload),
            description=f"POST {path}",
        )
        return resp.json()["data"]["activity_id"]

    async def get_status(self, client: httpx.AsyncClient, activity_id: str) -> dict:
        resp = await self._request_with_retry(
            lambda: client.get(f"{self.base_url}/v1/status/{activity_id}", headers=self._headers()),
            description=f"status check for {activity_id}",
        )
        return resp.json()["data"]

    async def wait_for(self, client: httpx.AsyncClient, activity_id: str, timeout: float | None = None) -> dict:
        elapsed = 0.0
        deadline = timeout if timeout is not None else self.poll_timeout
        while elapsed < deadline:
            data = await self.get_status(client, activity_id)
            status = str(data.get("status", "")).lower()
            if status in TERMINAL_ACTIVITY_STATUSES:
                return data.get("result", {})
            if status in FAILED_ACTIVITY_STATUSES:
                raise FortyGuardError(f"activity {activity_id} failed: {data}")
            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise FortyGuardError(f"activity {activity_id} timed out after {deadline}s")

    async def _submit_and_wait(
        self, path: str, payload: dict, timeout: float | None = None, label: str | None = None
    ) -> dict:
        """Every FortyGuard call funnels through here — one choke point for the Mongo-backed
        cache, and the one place that logs what's actually happening (label identifies WHICH
        call this is, e.g. "DISCOVER burlington-vt cell 3/9" — without it every call just says
        "POST /v1/heatmap" and you can't tell them apart in the log). A duplicate/concurrent
        request for the same (path, payload) within the TTL window is served straight from
        Mongo instead of re-hitting FortyGuard. Cache errors degrade to a real API call, never
        fail the request. HTTP 402 (insufficient credits) falls back to dummy data."""
        label = label or path

        cache_key = self._cache_key(path, payload)
        cached = self._get_cached_result(cache_key)
        if cached is not None:
            app_logger.info("%s — cache hit, no FortyGuard call made", label)
            return cached

        app_logger.info("%s — request sent to FortyGuard (%s)", label, path)
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=FORTYGUARD_TIMEOUT_SECONDS) as client:
                activity_id = await self._submit(client, path, payload)
                result = await self.wait_for(client, activity_id, timeout=timeout)
        except FortyGuardError as exc:
            # HTTP 402: Insufficient credits — fall back to dummy data
            if "402" in str(exc):
                app_logger.warning("%s — FortyGuard out of credits, using dummy data", label)
                from dummy_data.services.fortyguard import generate_dummy_response
                result = generate_dummy_response(path, payload, label)
            else:
                raise

        elapsed = time.monotonic() - start

        n_cells = result.get("stats_data", {}).get("n_cells")
        empty_note = " — EMPTY (n_cells: 0)" if n_cells == 0 else ""
        app_logger.info("%s — response received after %.1fs%s", label, elapsed, empty_note)

        if self._is_cacheable(result):
            self._store_cached_result(cache_key, path, payload, result, label)
        return result

    @staticmethod
    def _is_cacheable(result: dict) -> bool:
        """Don't cache an empty/no-data result (e.g. n_cells: 0) — FortyGuard may have real
        data for the same query minutes later, and caching the empty response for a full hour
        would keep serving "nothing here" instead of letting a retry find real data."""
        if not result:
            return False
        stats = result.get("stats_data")
        if isinstance(stats, dict) and stats.get("n_cells") == 0:
            return False
        map_data = result.get("map_data")
        if isinstance(map_data, dict) and not map_data.get("features"):
            return False
        return True

    @staticmethod
    def _cache_key(path: str, payload: dict) -> str:
        canonical = json.dumps({"path": path, "payload": payload}, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _get_cached_result(cache_key: str) -> dict | None:
        try:
            doc = get_fortyguard_cache_collection().find_one({"_id": cache_key})
        except PyMongoError as exc:
            app_logger.warning("fortyguard cache lookup failed, calling API directly: %s", exc)
            return None
        return doc["result"] if doc else None

    @staticmethod
    def _city_id_from_label(label: str) -> str | None:
        """Labels are always "<STAGE> <city_id> — <detail>" (e.g. "DISCOVER burlington-vt —
        cell 7/9") — pull city_id out so cache entries are filterable by city directly,
        instead of only being greppable inside the free-text label."""
        head = label.split(" — ")[0].strip()
        parts = head.split(" ")
        return parts[1] if len(parts) >= 2 else None

    @staticmethod
    def _store_cached_result(cache_key: str, path: str, payload: dict, result: dict, label: str) -> None:
        now = datetime.now(UTC)
        entry = FortyGuardCacheEntry(
            id=cache_key,
            label=label,
            city_id=FortyGuardClient._city_id_from_label(label),
            path=path,
            payload=payload,
            result=result,
            created_at=now,
            updated_at=now,
        )
        try:
            get_fortyguard_cache_collection().replace_one({"_id": cache_key}, entry.to_mongo(), upsert=True)
        except PyMongoError as exc:
            app_logger.warning("fortyguard cache write failed (non-fatal): %s", exc)

    @staticmethod
    def _date_time_payload(
        start_date: str,
        start_time: str | None,
        filter_type: int,
        end_time: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        payload = {"start_date": start_date, "filter_type": filter_type}
        if start_time is not None:
            payload["start_time"] = start_time
        if end_time is not None:
            payload["end_time"] = end_time
        if end_date is not None:
            payload["end_date"] = end_date
        return payload

    async def _heatmap_request(
        self,
        polygon_coordinates: list[list[float]],
        start_date: str,
        start_time: str | None,
        filter_type: int,
        granularity: int,
        analytic_type: str = "tcm",
        threshold_c: float | None = None,
        direction: str = "above",
        end_time: str | None = None,
        end_date: str | None = None,
        label: str | None = None,
        city_id: str | None = None,
    ) -> dict:
        """POST /v1/heatmap — tcm/exceedance/persistence/time_of_measure are all this ONE
        endpoint, selected via analytic_type. threshold/direction are ignored by the API for
        tcm and time_of_measure (only exceedance/persistence use a threshold).

        If no API key is set, generates realistic dummy data instead of calling FortyGuard."""

        # Use dummy data when API key not configured
        if not self.api_key:
            from dummy_data.services.fortyguard import generate_and_cache_heatmap as gen_heatmap

            app_logger.info("%s — using dummy data (no API key configured)", label or analytic_type)
            await asyncio.sleep(1)  # Simulate API delay
            return gen_heatmap(
                city_id or "unknown",
                polygon_coordinates,
                analytic_type=analytic_type,
                label_prefix=label.split(" — ")[0] + " " if label else "",
            )

        payload = {
            "polygon_aoi": {"type": "Polygon", "coordinates": [polygon_coordinates]},
            "date_time": self._date_time_payload(start_date, start_time, filter_type, end_time, end_date),
            "granularity": granularity,
            "analytic_type": analytic_type,
        }
        if analytic_type not in ("tcm", "time_of_measure"):
            payload["threshold"] = threshold_c if threshold_c is not None else 30.0
            payload["direction"] = direction
        return await self._submit_and_wait("/v1/heatmap", payload, label=label or f"heatmap:{analytic_type}")

    async def create_heatmap(
        self,
        polygon_coordinates: list[list[float]],
        start_date: str,
        start_time: str | None,
        filter_type: int,
        granularity: int,
        label: str | None = None,
        city_id: str | None = None,
    ) -> dict:
        """Plain temperature snapshot (analytic_type=tcm). Result temps are in °C."""
        return await self._heatmap_request(
            polygon_coordinates,
            start_date,
            start_time,
            filter_type,
            granularity,
            analytic_type="tcm",
            label=label,
            city_id=city_id,
        )

    async def get_exceedance(
        self,
        polygon_coordinates: list[list[float]],
        start_date: str,
        start_time: str | None,
        filter_type: int,
        threshold_c: float,
        granularity: int,
        direction: str = "above",
        label: str | None = None,
        city_id: str | None = None,
    ) -> dict:
        """Hours above/below threshold per tile. Result values are in HOURS, not °C."""
        return await self._heatmap_request(
            polygon_coordinates,
            start_date,
            start_time,
            filter_type,
            granularity,
            analytic_type="exceedance",
            threshold_c=threshold_c,
            direction=direction,
            label=label,
            city_id=city_id,
        )

    async def get_persistence(
        self,
        polygon_coordinates: list[list[float]],
        start_date: str,
        start_time: str | None,
        filter_type: int,
        threshold_c: float,
        granularity: int,
        direction: str = "above",
        label: str | None = None,
        city_id: str | None = None,
    ) -> dict:
        """Longest continuous run of hours above/below threshold per tile, in HOURS."""
        return await self._heatmap_request(
            polygon_coordinates,
            start_date,
            start_time,
            filter_type,
            granularity,
            analytic_type="persistence",
            threshold_c=threshold_c,
            direction=direction,
            label=label,
            city_id=city_id,
        )

    async def get_time_of_measure(
        self,
        polygon_coordinates: list[list[float]],
        start_date: str,
        start_time: str | None,
        filter_type: int,
        granularity: int,
        label: str | None = None,
    ) -> dict:
        """Hour of day (0-23 UTC) the peak temperature occurred per tile — not a threshold
        comparison, no threshold/direction needed."""
        return await self._heatmap_request(
            polygon_coordinates,
            start_date,
            start_time,
            filter_type,
            granularity,
            analytic_type="time_of_measure",
            label=label,
        )

    async def run_query(
        self,
        polygon_coordinates: list[list[float]],
        filter_type: int,
        start_date: str,
        start_time: str | None = None,
        end_time: str | None = None,
        end_date: str | None = None,
        analytic_type: str = "tcm",
        threshold_c: float | None = None,
        direction: str = "above",
        granularity: int = 100,
        label: str | None = None,
    ) -> dict:
        """General-purpose entry point exposing every filter_type/analytic_type combination
        directly — backs the Custom Query UI. The pipeline-specific convenience methods above
        (create_heatmap/get_exceedance/get_persistence) stay as-is for DISCOVER/INVESTIGATE,
        which never need date ranges or time_of_measure."""
        return await self._heatmap_request(
            polygon_coordinates,
            start_date,
            start_time,
            filter_type,
            granularity,
            analytic_type=analytic_type,
            threshold_c=threshold_c,
            direction=direction,
            end_time=end_time,
            end_date=end_date,
            label=label or "custom query",
        )

    async def get_environmental_parameters(
        self,
        latitude: float,
        longitude: float,
        temperature_c: float,
        start_date: str,
        start_time: str,
        filter_type: int,
        analysis: list[str] | None = None,
        label: str | None = None,
    ) -> dict:
        """Heat index, humidity, air quality, solar irradiance, etc. for one point. Fast
        (~5-10s) — safe to call synchronously in the INVESTIGATE stage."""
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "temperature": temperature_c,
            "date_time": self._date_time_payload(start_date, start_time, filter_type),
        }
        if analysis:
            payload["analysis"] = analysis
        return await self._submit_and_wait("/v1/env_params", payload, label=label or "env_params")

    async def get_satellite_segmentation(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        start_time: str,
        filter_type: int,
        granularity: int,
        label: str | None = None,
    ) -> dict:
        """Land-cover class coverage (% building/road/vegetation/etc.) from satellite imagery.
        Premium-tier only — raises FortyGuardError if the key doesn't have access."""
        payload = {
            "sat": {"latitude": latitude, "longitude": longitude},
            "date_time": self._date_time_payload(start_date, start_time, filter_type),
            "granularity": granularity,
        }
        return await self._submit_and_wait("/v1/satellite", payload, label=label or "satellite")

    async def get_street_view_segmentation(
        self,
        latitude: float,
        longitude: float,
        vertical_angle: float = 0,
        horizontal_angle: float = 0,
        back_view: bool = False,
        label: str | None = None,
    ) -> dict:
        """Ground-level segmentation (building facades, vegetation, road surface). Premium-tier
        only. Not currently called by the agent pipeline — available for future UI use."""
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "vertical_angle": vertical_angle,
            "horizontal_angle": horizontal_angle,
            "back_view": back_view,
        }
        return await self._submit_and_wait("/v1/streetview", payload, label=label or "streetview")

    async def get_heat_intelligence(
        self,
        latitude: float,
        longitude: float,
        temperature_f: float,
        date: str,
        analysis: list[str] | None = None,
        wait_timeout: float = 30.0,
        label: str | None = None,
    ) -> dict | None:
        """Generates a downloadable PDF report (result["download_link"]) — NOT inline JSON
        data. Report generation can take several minutes (confirmed live), far too slow for
        the synchronous per-anomaly INVESTIGATE step, so this is NOT called by agent_engine.py.
        Kept here for a future "generate report" feature. Only waits `wait_timeout` seconds by
        default and returns None rather than raising if it's not done yet — the caller decides
        whether to poll longer."""
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "temperature": temperature_f,
            "date": date,
            "analysis": analysis or ["geographic", "environmental", "urban", "events", "anthropogenic"],
        }
        try:
            return await self._submit_and_wait(
                "/v1/heat_intelligence", payload, timeout=wait_timeout, label=label or "heat_intelligence"
            )
        except FortyGuardError:
            return None


fortyguard_client = FortyGuardClient()

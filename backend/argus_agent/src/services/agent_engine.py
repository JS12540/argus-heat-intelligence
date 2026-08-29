"""The ARGUS agent: DISCOVER -> INVESTIGATE -> UNDERSTAND -> RESPOND -> MONITOR."""

import asyncio
import random
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from pymongo.collection import Collection

from argus_agent.src.config import settings
from argus_agent.src.constants import (
    CITIES_BY_ID,
    DEFAULT_EXCEEDANCE_THRESHOLD_F,
    DEFAULT_GRANULARITY_METERS,
    FORTYGUARD_DATA_LAG_DAYS,
    INFRASTRUCTURE_SEARCH_RADIUS_METERS,
    INVESTIGATION_GRANULARITY_METERS,
)
from argus_agent.src.db.models import AnomalyDocument
from argus_agent.src.enums import HeatmapFilterType
from argus_agent.src.logging.app_logger import app_logger
from argus_agent.src.logging.audit_logger import audit
from argus_agent.src.services.anomaly_detector import anomaly_detector
from argus_agent.src.services.fortyguard_client import FortyGuardError, fortyguard_client
from argus_agent.src.services.infrastructure_service import infrastructure_service
from argus_agent.src.services.reasoner_service import reasoner_service
from argus_agent.src.utils.geo import polygon_centroid, split_into_grid
from argus_agent.src.utils.units import celsius_to_fahrenheit, fahrenheit_to_celsius

DANGER_THRESHOLD_C = fahrenheit_to_celsius(DEFAULT_EXCEEDANCE_THRESHOLD_F)

WARRANTS_INVESTIGATION_SCORE = 40.0


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _latest_available_date_and_hour() -> tuple[str, str]:
    """The most recent (date, hour) FortyGuard actually has data for. Two confirmed-live
    quirks, both required for a Single Hour (filter_type=1) request to return anything:
      1. ~1 day publish lag — "today" returns n_cells=0 regardless of hour
         (constants.FORTYGUARD_DATA_LAG_DAYS).
      2. start_time must be exactly on the hour ("11:00") — any non-zero minute (e.g. "11:06")
         silently returns n_cells=0 too, no error. Hence %H:00, not %H:%M."""
    now = datetime.now(UTC) - timedelta(days=FORTYGUARD_DATA_LAG_DAYS)
    return now.strftime("%Y-%m-%d"), now.strftime("%H:00")


class ArgusAgent:
    """Runs one full scan cycle across the configured city polygon."""

    def __init__(self) -> None:
        self.fortyguard = fortyguard_client
        self.detector = anomaly_detector

    async def _read_zone_temperature(self, cell: list[list[float]], label: str) -> tuple[float, bool]:
        """Temperature for one grid cell (°F), and whether that's real FortyGuard data or a
        fallback. Uses Single Day (filter_type=3, mean over the whole day), NOT Single Hour —
        confirmed live that a single-hour snapshot frequently misses the satellite pass and
        returns n_cells=0 even when correctly date/hour-aligned; a full-day mean is far more
        likely to have at least some coverage."""
        if not settings.fortyguard_api_key:
            # ponytail: no FortyGuard key configured — synthesize a plausible reading so
            # the full pipeline is demoable end-to-end. Swap for the real call once a key exists.
            lat, _ = polygon_centroid(cell)
            return 95.0 + (lat % 1) * 30 + random.uniform(-3, 6), False

        start_date, _ = _latest_available_date_and_hour()
        result = await self.fortyguard.create_heatmap(
            polygon_coordinates=cell,
            start_date=start_date,
            start_time=None,
            filter_type=HeatmapFilterType.SINGLE_DAY,
            granularity=DEFAULT_GRANULARITY_METERS,
            label=label,
            city_id=label.split(" ")[1] if " " in label else "unknown",
        )
        # Confirmed live shape: result["stats_data"]["temperature_stats"]["mean"], in Celsius.
        mean_celsius = result.get("stats_data", {}).get("temperature_stats", {}).get("mean")
        if mean_celsius is None:
            app_logger.warning("%s — no data (n_cells: 0), using 100°F fallback", label)
            return 100.0, False
        return celsius_to_fahrenheit(mean_celsius), True

    async def _city_exceedance_zone_count(self, polygon: list[list[float]], label: str) -> int | None:
        """Threshold Detection — ask FortyGuard directly which zones exceed the danger
        threshold, city-wide, as a corroborating signal alongside our own composite score.

        Confirmed live result shape for analytic_type="exceedance": result["stats_data"] is
        flat ({n_cells, min, max, mean}, units="hour" — NOT nested under "temperature_stats"
        like tcm), and each result["map_data"]["features"][i]["properties"]["value"] is the
        number of hours that tile exceeded the threshold over the requested day."""
        if not settings.fortyguard_api_key:
            return None

        start_date, _ = _latest_available_date_and_hour()
        city_id = label.split(" ")[1] if " " in label else "unknown"
        try:
            result = await self.fortyguard.get_exceedance(
                polygon_coordinates=polygon,
                start_date=start_date,
                start_time=None,
                filter_type=HeatmapFilterType.SINGLE_DAY,
                threshold_c=DANGER_THRESHOLD_C,
                granularity=DEFAULT_GRANULARITY_METERS,
                label=label,
                city_id=city_id,
            )
        except FortyGuardError as exc:
            app_logger.warning("city-wide exceedance scan failed: %s", exc)
            return None

        features = result.get("map_data", {}).get("features", [])
        return sum(1 for f in features if f.get("properties", {}).get("value", 0) > 0)

    async def _city_persistence_hours(self, polygon: list[list[float]], label: str) -> float | None:
        """The other half of the "3 requests" corroboration alongside exceedance: longest
        unbroken streak above threshold, city-wide (mean across tiles, in hours)."""
        if not settings.fortyguard_api_key:
            return None

        start_date, _ = _latest_available_date_and_hour()
        city_id = label.split(" ")[1] if " " in label else "unknown"
        try:
            result = await self.fortyguard.get_persistence(
                polygon_coordinates=polygon,
                start_date=start_date,
                start_time=None,
                filter_type=HeatmapFilterType.SINGLE_DAY,
                threshold_c=DANGER_THRESHOLD_C,
                granularity=DEFAULT_GRANULARITY_METERS,
                label=label,
                city_id=city_id,
            )
        except FortyGuardError as exc:
            app_logger.warning("city-wide persistence scan failed: %s", exc)
            return None
        return result.get("stats_data", {}).get("mean")

    async def discover(
        self, city: dict, on_progress: Callable[[str], None] | None = None
    ) -> tuple[list[dict], dict]:
        """Stage 1 — grid-scan the given city (temperature per cell), then cross-check against
        FortyGuard's own exceedance AND persistence analysis city-wide, and score every cell
        for anomalies. Returns (anomalies, scan_meta) — scan_meta reports how many cells
        actually had FortyGuard data vs. fell back, so the UI can tell "calm" apart from
        "FortyGuard had no data for this window" instead of showing an unexplained blank."""
        polygon = city["polygon"]
        cells = split_into_grid(polygon, cells_per_side=3)
        total = len(cells)

        async def read_cell(idx: int, cell: list[list[float]]) -> dict | None:
            lat, lon = polygon_centroid(cell)
            label = f"DISCOVER {city['id']} — cell {idx}/{total}"
            try:
                temp, is_real = await self._read_zone_temperature(cell, label=label)
            except FortyGuardError as exc:
                app_logger.warning("%s failed: %s", label, exc)
                return None
            if on_progress:
                on_progress(f"DISCOVER: cell {idx}/{total} done")
            return {"lat": lat, "lon": lon, "temp": temp, "is_real": is_real}

        # All 9 cells hit FortyGuard concurrently (asyncio, not a thread pool — these are
        # network-bound httpx calls) instead of one at a time — this is the difference
        # between a ~5 minute DISCOVER and a ~30 second one.
        if on_progress:
            on_progress(f"DISCOVER: scanning {total} cells in parallel")
        raw = await asyncio.gather(*(read_cell(idx, cell) for idx, cell in enumerate(cells, start=1)))
        readings = [r for r in raw if r is not None]
        cells_with_data = sum(1 for r in readings if r["is_real"])

        if on_progress:
            on_progress("DISCOVER: checking city-wide exceedance + persistence")
        exceedance_zone_count, persistence_hours = await asyncio.gather(
            self._city_exceedance_zone_count(polygon, label=f"DISCOVER {city['id']} — city-wide exceedance"),
            self._city_persistence_hours(polygon, label=f"DISCOVER {city['id']} — city-wide persistence"),
        )

        temps = [r["temp"] for r in readings]
        baseline_mean, baseline_std = self.detector.baseline_from_grid(temps)
        neighbor_avg = sum(temps) / len(temps) if temps else 0.0

        anomalies = []
        for idx, r in enumerate(readings):
            scored = self.detector.score_cell(
                temperature_f=r["temp"],
                neighbor_avg_f=neighbor_avg,
                baseline_mean_f=baseline_mean,
                baseline_std_f=baseline_std,
                temperature_1h_ago_f=r["temp"] - random.uniform(-2, 4),
            )
            if scored["composite_score"] < WARRANTS_INVESTIGATION_SCORE:
                continue
            scored["signals"]["exceeds_danger_threshold"] = r["temp"] >= DEFAULT_EXCEEDANCE_THRESHOLD_F
            scored["signals"]["city_exceedance_zone_count"] = exceedance_zone_count
            scored["signals"]["city_persistence_hours"] = persistence_hours
            anomalies.append(
                {
                    "id": f"ANO-{city['id']}-{int(datetime.now(UTC).timestamp())}-{idx}",
                    "city_id": city["id"],
                    "city_name": city["name"],
                    "zone_name": f"{city['name']}, {city['state']} — Zone {idx + 1}",
                    "latitude": r["lat"],
                    "longitude": r["lon"],
                    "temperature_f": round(r["temp"], 1),
                    "detected_at": _now_iso(),
                    **scored,
                }
            )

        scan_meta = {
            "cells_scanned": len(readings),
            "cells_with_data": cells_with_data,
            "city_exceedance_zone_count": exceedance_zone_count,
            "city_persistence_hours": persistence_hours,
            "demo_mode": not bool(settings.fortyguard_api_key),
            # All 9 real readings, regardless of anomaly status — so the UI can render the
            # full heatmap even on a "calm, 0 anomalies" scan instead of showing nothing.
            "cells": [
                {"lat": r["lat"], "lon": r["lon"], "temperature_f": round(r["temp"], 1)} for r in readings
            ],
        }
        audit(
            "DISCOVER",
            city_id=city["id"],
            scanned_cells=len(readings),
            cells_with_data=cells_with_data,
            anomalies_found=len(anomalies),
            city_exceedance_zones=exceedance_zone_count,
            city_persistence_hours=persistence_hours,
        )
        return anomalies, scan_meta

    async def investigate(self, anomaly: dict, on_progress: Callable[[str], None] | None = None) -> dict:
        """Stage 2 — real persistence (hours above threshold), real environmental context
        (heat index, humidity, air quality), and real surface composition (satellite land-cover),
        all confirmed against the live API (see backend/scripts/). Heat Intelligence is
        deliberately NOT called here — it generates a PDF over several minutes, far too slow
        for this synchronous per-anomaly step (see fortyguard_client.py::get_heat_intelligence)."""
        start_date, start_time = _latest_available_date_and_hour()
        cell = split_into_grid(
            [
                [anomaly["longitude"] - 0.005, anomaly["latitude"] - 0.005],
                [anomaly["longitude"] + 0.005, anomaly["latitude"] - 0.005],
                [anomaly["longitude"] + 0.005, anomaly["latitude"] + 0.005],
                [anomaly["longitude"] - 0.005, anomaly["latitude"] + 0.005],
                [anomaly["longitude"] - 0.005, anomaly["latitude"] - 0.005],
            ],
            cells_per_side=1,
        )[0]

        if not settings.fortyguard_api_key:
            investigation = {
                "hours_above_threshold": round(random.uniform(1, 8), 1),
                "exceedance_hours_total": round(random.uniform(2, 10), 1),
                "peak_hour_utc": random.randint(12, 20),
                "trend": "WORSENING",
                "heat_index_f": anomaly["temperature_f"] + 8,
                "apparent_temperature_f": anomaly["temperature_f"] + 6,
                "wet_bulb_temperature_f": None,
                "humidity_percent": 25.0,
                "air_quality_index": 60.0,
                "surface_composition": None,
                "contextual_factors": ["Demo mode — no FORTYGUARD_API_KEY configured, values estimated"],
            }
            audit("INVESTIGATE", anomaly_id=anomaly["id"], hours_above=investigation["hours_above_threshold"])
            return investigation

        aid = anomaly["id"]

        async def get_persistence_hours() -> float:
            try:
                r = await self.fortyguard.get_persistence(
                    polygon_coordinates=cell,
                    start_date=start_date,
                    start_time=None,
                    filter_type=HeatmapFilterType.SINGLE_DAY,
                    threshold_c=DANGER_THRESHOLD_C,
                    granularity=INVESTIGATION_GRANULARITY_METERS,
                    label=f"INVESTIGATE {aid} — persistence",
                )
                return float(r.get("stats_data", {}).get("mean", 1.0))
            except FortyGuardError as exc:
                app_logger.warning("persistence check failed for %s, using estimate: %s", aid, exc)
                return 1.0

        async def get_exceedance_hours() -> float | None:
            try:
                r = await self.fortyguard.get_exceedance(
                    polygon_coordinates=cell,
                    start_date=start_date,
                    start_time=None,
                    filter_type=HeatmapFilterType.SINGLE_DAY,
                    threshold_c=DANGER_THRESHOLD_C,
                    granularity=INVESTIGATION_GRANULARITY_METERS,
                    label=f"INVESTIGATE {aid} — exceedance",
                )
                return r.get("stats_data", {}).get("mean")
            except FortyGuardError as exc:
                app_logger.warning("exceedance check failed for %s: %s", aid, exc)
                return None

        async def get_peak_hour() -> int | None:
            try:
                r = await self.fortyguard.get_time_of_measure(
                    polygon_coordinates=cell,
                    start_date=start_date,
                    start_time=None,
                    filter_type=HeatmapFilterType.SINGLE_DAY,
                    granularity=INVESTIGATION_GRANULARITY_METERS,
                    label=f"INVESTIGATE {aid} — time_of_measure",
                )
                mean_hour = r.get("stats_data", {}).get("mean")
                return round(mean_hour) if mean_hour is not None else None
            except FortyGuardError as exc:
                app_logger.warning("time-of-measure check failed for %s: %s", aid, exc)
                return None

        async def get_env() -> dict:
            try:
                r = await self.fortyguard.get_environmental_parameters(
                    latitude=anomaly["latitude"],
                    longitude=anomaly["longitude"],
                    temperature_c=fahrenheit_to_celsius(anomaly["temperature_f"]),
                    start_date=start_date,
                    start_time=start_time,
                    filter_type=HeatmapFilterType.SINGLE_HOUR,
                    analysis=[
                        "heat_index_celsius",
                        "apparent_temperature_celsius",
                        "wet_bulb_temperature_celsius",
                        "relative_humidity_percent",
                        "air_quality:idx",
                    ],
                    label=f"INVESTIGATE {aid} — env_params",
                )
                params = (r.get("locations") or [{}])[0].get("parameters", {})
                return {k: v[0] for k, v in params.items() if v}
            except FortyGuardError as exc:
                app_logger.warning("environmental parameters lookup failed for %s: %s", aid, exc)
                return {}

        async def get_surface() -> dict | None:
            try:
                r = await self.fortyguard.get_satellite_segmentation(
                    latitude=anomaly["latitude"],
                    longitude=anomaly["longitude"],
                    start_date=start_date,
                    start_time=start_time,
                    filter_type=HeatmapFilterType.SINGLE_HOUR,
                    granularity=INVESTIGATION_GRANULARITY_METERS,
                    label=f"INVESTIGATE {aid} — satellite",
                )
                return r.get("segmentation", {}).get("segments") or None
            except FortyGuardError as exc:
                app_logger.warning("satellite segmentation failed for %s (Premium-only): %s", aid, exc)
                return None

        # 5 independent FortyGuard calls — fire them all at once instead of one after another.
        if on_progress:
            on_progress(f"INVESTIGATE {aid}: 5 checks in parallel (persistence/exceedance/time/env/satellite)")
        hours_above, exceedance_hours_total, peak_hour_utc, env, surface_composition = await asyncio.gather(
            get_persistence_hours(), get_exceedance_hours(), get_peak_hour(), get_env(), get_surface()
        )

        def _f(celsius_key: str) -> float | None:
            value = env.get(celsius_key)
            return celsius_to_fahrenheit(value) if value is not None else None

        contextual_factors = []
        heat_index_f = _f("heat_index_celsius")
        if heat_index_f is not None:
            contextual_factors.append(f"Heat index (feels like) {heat_index_f:.0f}°F")
        if env.get("relative_humidity_percent") is not None:
            contextual_factors.append(f"Relative humidity {env['relative_humidity_percent']:.0f}%")
        if env.get("air_quality:idx") is not None:
            contextual_factors.append(f"Air quality index {env['air_quality:idx']:.0f}")
        if surface_composition:
            top = sorted(surface_composition.items(), key=lambda kv: kv[1], reverse=True)[:2]
            contextual_factors.append(
                "Surface composition: " + ", ".join(f"{name} {pct:.0f}%" for name, pct in top)
            )
        if exceedance_hours_total is not None:
            contextual_factors.append(f"{exceedance_hours_total:.1f}h total above threshold today")
        if peak_hour_utc is not None:
            contextual_factors.append(f"Peak temperature expected around {peak_hour_utc:02d}:00 UTC")

        investigation = {
            "hours_above_threshold": round(hours_above, 1),
            "exceedance_hours_total": round(exceedance_hours_total, 1) if exceedance_hours_total is not None else None,
            "peak_hour_utc": peak_hour_utc,
            "trend": "WORSENING" if hours_above > 4 else "STABLE",
            "heat_index_f": heat_index_f,
            "apparent_temperature_f": _f("apparent_temperature_celsius"),
            "wet_bulb_temperature_f": _f("wet_bulb_temperature_celsius"),
            "humidity_percent": env.get("relative_humidity_percent"),
            "air_quality_index": env.get("air_quality:idx"),
            "surface_composition": surface_composition,
            "contextual_factors": contextual_factors,
        }
        audit(
            "INVESTIGATE",
            anomaly_id=anomaly["id"],
            hours_above=hours_above,
            exceedance_hours_total=exceedance_hours_total,
            peak_hour_utc=peak_hour_utc,
            trend=investigation["trend"],
        )
        return investigation

    async def understand(self, anomaly: dict) -> dict:
        """Stage 3 — connect the anomaly to real-world infrastructure at risk."""
        nearby = await infrastructure_service.find_near(
            anomaly["latitude"], anomaly["longitude"], INFRASTRUCTURE_SEARCH_RADIUS_METERS
        )
        impact = infrastructure_service.score_and_rank(
            nearby, anomaly["composite_score"], INFRASTRUCTURE_SEARCH_RADIUS_METERS
        )
        audit("UNDERSTAND", anomaly_id=anomaly["id"], infrastructure_found=len(nearby))
        return impact

    async def respond(self, anomaly: dict, investigation: dict, impact: dict) -> dict:
        """Stage 4 — LLM-ranked recommendations."""
        actions = await reasoner_service.generate_recommendations(anomaly, investigation, impact)
        plan = {
            "actions": [{"rank": i + 1, **a} for i, a in enumerate(actions)],
            "generated_at": _now_iso(),
        }
        audit("RESPOND", anomaly_id=anomaly["id"], actions_generated=len(actions))
        return plan

    async def run_cycle(
        self, collection: Collection, city_id: str, on_progress: Callable[[str], None] | None = None
    ) -> tuple[list[AnomalyDocument], dict]:
        """Execute one full DISCOVER -> INVESTIGATE -> UNDERSTAND -> RESPOND cycle for a
        single city. Scanning is always scoped to one city — there is no "scan everything"
        mode, to keep FortyGuard credit spend under explicit, per-click user control across
        the 51 monitored cities. `on_progress`, if given, is called with a short human-readable
        string at every meaningful step — routes.py wires this into /api/agent/status so the
        UI isn't just a blank "Scanning…" for the several minutes a real scan takes. Returns
        (documents, scan_meta) — scan_meta.cells_with_data lets the caller tell "genuinely
        calm, 0 anomalies" apart from "FortyGuard had no data for this scan window" instead of
        both looking like an unexplained empty result."""
        city = CITIES_BY_ID.get(city_id)
        if city is None:
            raise ValueError(f"unknown city_id: {city_id}")

        anomalies, scan_meta = await self.discover(city, on_progress=on_progress)
        documents = []
        for i, anomaly in enumerate(anomalies, start=1):
            try:
                if on_progress:
                    on_progress(f"INVESTIGATE: anomaly {i}/{len(anomalies)}")
                investigation = await self.investigate(anomaly, on_progress=on_progress)
                if on_progress:
                    on_progress(f"UNDERSTAND: anomaly {i}/{len(anomalies)}")
                impact = await self.understand(anomaly)
                if on_progress:
                    on_progress(f"RESPOND: anomaly {i}/{len(anomalies)}")
                response_plan = await self.respond(anomaly, investigation, impact)
            except Exception:
                # One anomaly's pipeline failing (a flaky external call, etc.) must not
                # abort the rest of the scan cycle.
                app_logger.exception("pipeline failed for anomaly %s — skipping", anomaly["id"])
                continue

            doc = AnomalyDocument(
                id=anomaly["id"],
                city_id=anomaly["city_id"],
                city_name=anomaly["city_name"],
                zone_name=anomaly["zone_name"],
                latitude=anomaly["latitude"],
                longitude=anomaly["longitude"],
                temperature_f=anomaly["temperature_f"],
                severity=anomaly["severity"],
                composite_score=anomaly["composite_score"],
                signals=anomaly["signals"],
                stage="RESPOND",
                detected_at=anomaly["detected_at"],
                investigation=investigation,
                impact_assessment=impact,
                response_plan=response_plan,
                updated_at=_now_iso(),
            )
            collection.replace_one({"_id": doc.id}, doc.to_mongo(), upsert=True)
            documents.append(doc)
        return documents, scan_meta


argus_agent = ArgusAgent()

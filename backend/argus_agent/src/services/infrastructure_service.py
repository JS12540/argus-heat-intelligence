"""Find and score real-world infrastructure near a heat anomaly via OpenStreetMap Overpass."""

import httpx

from argus_agent.src.constants import (
    COOLING_ASSET_TYPES,
    OVERPASS_TIMEOUT_SECONDS,
    OVERPASS_URL,
    VULNERABILITY_WEIGHTS,
)
from argus_agent.src.enums import Severity
from argus_agent.src.logging.app_logger import app_logger
from argus_agent.src.utils.geo import haversine_m

_OSM_TAGS = {
    "school": ('amenity', 'school'),
    "hospital": ('amenity', 'hospital'),
    "clinic": ('amenity', 'clinic'),
    "nursing_home": ('amenity', 'nursing_home'),
    "bus_stop": ('highway', 'bus_stop'),
    "park": ('leisure', 'park'),
    "substation": ('power', 'substation'),
    "community_centre": ('amenity', 'community_centre'),
}


def _build_query(lat: float, lon: float, radius_m: int) -> str:
    clauses = "\n".join(
        f'node["{k}"="{v}"](around:{radius_m},{lat},{lon});'
        for k, v in _OSM_TAGS.values()
    )
    return f"[out:json][timeout:{int(OVERPASS_TIMEOUT_SECONDS)}];\n(\n{clauses}\n);\nout center;"


class InfrastructureService:
    async def find_near(self, lat: float, lon: float, radius_m: int) -> list[dict]:
        query = _build_query(lat, lon, radius_m)
        try:
            async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT_SECONDS) as client:
                # Overpass rejects the default httpx user-agent with 406.
                resp = await client.post(
                    OVERPASS_URL,
                    data={"data": query},
                    headers={"User-Agent": "ARGUS-HeatIntelligence/0.1 (hackathon research tool)"},
                )
                resp.raise_for_status()
                elements = resp.json().get("elements", [])
        except httpx.HTTPError as exc:
            app_logger.warning("overpass query failed: %s", exc)
            return []

        results = []
        for el in elements:
            tags = el.get("tags", {})
            osm_type = next(
                (name for name, (k, v) in _OSM_TAGS.items() if tags.get(k) == v),
                None,
            )
            if not osm_type:
                continue
            el_lat, el_lon = el.get("lat"), el.get("lon")
            if el_lat is None or el_lon is None:
                continue
            results.append(
                {
                    "type": osm_type,
                    "name": tags.get("name", osm_type.replace("_", " ").title()),
                    "latitude": el_lat,
                    "longitude": el_lon,
                    "distance_m": round(haversine_m(lat, lon, el_lat, el_lon), 0),
                }
            )
        return results

    def score_and_rank(self, items: list[dict], anomaly_severity_score: float, radius_m: int) -> dict:
        severity_multiplier = min(1.0, anomaly_severity_score / 100)
        scored = []
        cooling_assets = []
        for item in items:
            weight = VULNERABILITY_WEIGHTS.get(item["type"])
            distance_decay = max(0.0, 1 - (item["distance_m"] / radius_m))

            if item["type"] in COOLING_ASSET_TYPES:
                cooling_assets.append(
                    {
                        "type": item["type"],
                        "name": item["name"],
                        "distance_m": item["distance_m"],
                        "impact_score": 0.0,
                        "risk": Severity.INFO,
                        "reason": "Nearby cooling / relief asset",
                    }
                )
                continue
            if not weight:
                continue

            impact = weight["base_risk"] * severity_multiplier * distance_decay * 10
            scored.append(
                {
                    "type": item["type"],
                    "name": item["name"],
                    "distance_m": item["distance_m"],
                    "impact_score": round(impact, 1),
                    "risk": _impact_to_severity(impact),
                    "reason": weight["reason"],
                }
            )

        scored.sort(key=lambda r: r["impact_score"], reverse=True)
        return {
            "total_infrastructure_at_risk": len(scored),
            "risk_ranking": scored,
            "cooling_assets_nearby": cooling_assets,
        }


def _impact_to_severity(impact: float) -> Severity:
    if impact >= 70:
        return Severity.CRITICAL
    if impact >= 50:
        return Severity.HIGH
    if impact >= 25:
        return Severity.MEDIUM
    return Severity.LOW


infrastructure_service = InfrastructureService()

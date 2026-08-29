from pydantic import BaseModel

from argus_agent.src.enums import AgentStage, Severity


class Anomaly(BaseModel):
    id: str
    city_id: str
    city_name: str
    zone_name: str
    latitude: float
    longitude: float
    temperature_f: float
    severity: Severity
    composite_score: float
    signals: dict
    stage: AgentStage = AgentStage.DISCOVER
    detected_at: str


class Investigation(BaseModel):
    """See fortyguard_heat_intelligence_api.md — persistence, exceedance, and time_of_measure
    (all /v1/heatmap, analytic_type varies), environmental parameters (/v1/env_params), and
    satellite segmentation (/v1/satellite, Premium) are the confirmed real data sources here.
    Heat Intelligence is deliberately excluded — it returns a PDF over several minutes, too
    slow for this synchronous step."""

    hours_above_threshold: float  # persistence: longest unbroken streak
    exceedance_hours_total: float | None = None  # exceedance: total hours over threshold
    peak_hour_utc: int | None = None  # time_of_measure: hour of day (0-23) peak temp occurred
    trend: str
    heat_index_f: float | None = None
    apparent_temperature_f: float | None = None
    wet_bulb_temperature_f: float | None = None
    humidity_percent: float | None = None
    air_quality_index: float | None = None
    surface_composition: dict[str, float] | None = None
    contextual_factors: list[str] = []


class RiskedInfrastructure(BaseModel):
    type: str
    name: str
    distance_m: float
    impact_score: float
    risk: Severity
    reason: str


class ImpactAssessment(BaseModel):
    total_infrastructure_at_risk: int
    risk_ranking: list[RiskedInfrastructure]
    cooling_assets_nearby: list[RiskedInfrastructure] = []


class RecommendedAction(BaseModel):
    rank: int
    action: str
    target: str
    urgency: str
    expected_impact: str


class ResponsePlan(BaseModel):
    actions: list[RecommendedAction]
    generated_at: str

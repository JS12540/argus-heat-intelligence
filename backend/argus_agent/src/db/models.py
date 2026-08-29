"""Document models for the MongoDB collections. Mongo is schemaless — this is what keeps
the document shape honest and typed at the boundary (build one, dump one)."""

from datetime import datetime

from pydantic import BaseModel, Field


class AnomalyDocument(BaseModel):
    """One document per detected anomaly, carrying every stage's output as it fills in.
    The anomaly's own id (e.g. "ANO-phoenix-az-...") is used directly as Mongo's `_id` —
    no separate auto-generated id."""

    model_config = {"populate_by_name": True}

    id: str = Field(alias="_id")
    city_id: str
    city_name: str
    zone_name: str
    latitude: float
    longitude: float
    temperature_f: float
    severity: str
    composite_score: float
    signals: dict
    stage: str = "DISCOVER"
    detected_at: str

    investigation: dict | None = None
    impact_assessment: dict | None = None
    response_plan: dict | None = None

    updated_at: str = ""

    def to_mongo(self) -> dict:
        """Dict ready to pass to a pymongo insert/replace call (`_id` populated)."""
        return self.model_dump(by_alias=True)

    @staticmethod
    def from_mongo(doc: dict) -> dict:
        """A raw Mongo document -> an API response dict (`_id` renamed back to `id`)."""
        doc = dict(doc)
        doc["id"] = doc.pop("_id")
        return doc


class FortyGuardCacheEntry(BaseModel):
    """One document per distinct FortyGuard call (path + payload hash). `_id` is that hash.
    A TTL index on `created_at` (see db/mongo.py) evicts entries after
    constants.FORTYGUARD_CACHE_TTL_SECONDS — Mongo does this natively, no cron job.
    `created_at` MUST be a real datetime (BSON Date), not a string — Mongo's TTL monitor
    only acts on Date-typed fields."""

    model_config = {"populate_by_name": True}

    id: str = Field(alias="_id")
    label: str  # e.g. "DISCOVER burlington-vt — cell 7/9" — city/context, for readability in Mongo
    city_id: str | None = None  # parsed out of label, so cache entries are filterable by city directly
    path: str
    payload: dict
    result: dict
    created_at: datetime
    updated_at: datetime

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True)


class LLMAnalysisDocument(BaseModel):
    """LLM-generated insights for an anomaly or city-wide heat event.
    Stores Groq/Claude reasoning outputs separately so they can be versioned,
    retrieved independently, and used to train future models.
    Prompts are stored in llm_prompts.py module, not in the database."""

    model_config = {"populate_by_name": True}

    id: str = Field(alias="_id")
    city_id: str
    anomaly_id: str | None = None  # if tied to specific anomaly, else null for city-wide
    analysis_type: str  # "response_plan", "risk_assessment", "trend_analysis", etc.
    llm_model: str  # "openai/gpt-oss-120b" (Groq), "gpt-5-mini", etc.
    temperature_f: float | None = None  # what was the temp when analysis was made
    date_analyzed: datetime  # when the analysis was generated
    response: str  # the LLM's response text
    reasoning_steps: list[str] = []  # structured reasoning if available
    confidence_score: float | None = None  # 0-100, LLM's confidence in its response
    tags: list[str] = []  # e.g. ["infrastructure_risk", "vulnerable_population", "urgent"]
    created_at: datetime
    updated_at: datetime

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True)

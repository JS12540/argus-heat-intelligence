"""MongoDB connection — one shared pymongo client for the process's lifetime."""

from pymongo import MongoClient
from pymongo.collection import Collection

from argus_agent.src.config import settings
from argus_agent.src.constants import (
    FORTYGUARD_CACHE_TTL_SECONDS,
    MONGO_ANOMALIES_COLLECTION,
    MONGO_DB_NAME,
    MONGO_FORTYGUARD_CACHE_COLLECTION,
    MONGO_LLM_ANALYSIS_COLLECTION,
)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client


def get_anomalies_collection() -> Collection:
    return get_client()[MONGO_DB_NAME][MONGO_ANOMALIES_COLLECTION]


def get_fortyguard_cache_collection() -> Collection:
    return get_client()[MONGO_DB_NAME][MONGO_FORTYGUARD_CACHE_COLLECTION]


def get_llm_analysis_collection() -> Collection:
    return get_client()[MONGO_DB_NAME][MONGO_LLM_ANALYSIS_COLLECTION]


def init_db() -> None:
    """Ensure required indexes exist. Called once at startup."""
    anomalies = get_anomalies_collection()
    anomalies.create_index("city_id")
    anomalies.create_index("detected_at")

    cache = get_fortyguard_cache_collection()
    # Use regular index (no TTL) to prevent auto-deletion of historical data
    cache.create_index("created_at")
    cache.create_index("city_id")

    llm_analysis = get_llm_analysis_collection()
    llm_analysis.create_index("city_id")
    llm_analysis.create_index("anomaly_id")
    llm_analysis.create_index("date_analyzed")

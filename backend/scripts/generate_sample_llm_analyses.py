"""Generate LLM trend analyses for 5 sample cities using Groq (faster sample).

Prompt templates are in llm_prompts.py — no prompts stored in database.
"""

import sys
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.constants import CITIES_BY_ID
from argus_agent.src.db.mongo import (
    get_fortyguard_cache_collection,
    get_llm_analysis_collection,
    init_db,
)
from argus_agent.src.services.reasoner_service import reasoner_service
from argus_agent.src.services.llm_prompts import get_trend_analysis_prompt
from argus_agent.src.utils.units import celsius_to_fahrenheit


async def generate_sample_llm_analyses() -> None:
    """Generate LLM analyses for 5 sample cities (fast demo)."""
    init_db()
    cache = get_fortyguard_cache_collection()
    llm_coll = get_llm_analysis_collection()

    # Sample cities: 2 critical + 3 others
    sample_city_ids = [
        "phoenix-az",      # CRITICAL
        "houston-tx",      # CRITICAL
        "denver-co",       # Normal
        "burlington-vt",   # Normal
        "miami-fl",        # Normal
    ]

    print("Generating LLM trend analyses for 5 sample cities…\n")

    successful = 0
    failed = 0

    for i, city_id in enumerate(sample_city_ids, start=1):
        city = CITIES_BY_ID.get(city_id)
        if not city:
            continue

        city_name = city["name"]

        # Fetch 7 days of TCM data
        docs = list(
            cache.find({
                "city_id": city_id,
                "label": {"$regex": "tcm"},
            }).sort("created_at", 1).limit(8)
        )

        if not docs:
            print(f"  [{i}/5] ⊘ {city_id}: no cached data")
            failed += 1
            continue

        # Aggregate daily temps
        temps_by_day = {}
        for doc in docs:
            date = doc["created_at"].date()
            if date not in temps_by_day:
                temps_by_day[date] = []

            mean_c = (
                doc.get("result", {})
                .get("result", {})
                .get("stats_data", {})
                .get("temperature_stats", {})
                .get("mean")
            )
            if mean_c is not None:
                temps_by_day[date].append(celsius_to_fahrenheit(mean_c))

        # Compute daily stats
        daily_stats = {
            date.isoformat(): {
                "min": round(min(temps), 1),
                "max": round(max(temps), 1),
                "mean": round(sum(temps) / len(temps), 1),
            }
            for date, temps in temps_by_day.items()
        }

        if not daily_stats:
            print(f"  [{i}/5] ⊘ {city_id}: no temperature data")
            failed += 1
            continue

        # Build prompt from template (not stored in DB)
        temp_json = json.dumps(daily_stats, indent=2)
        prompt = get_trend_analysis_prompt(city_name, len(daily_stats), temp_json)

        try:
            # Call Groq LLM
            response_text = await reasoner_service.analyze_trend(prompt)

            # Extract confidence score
            confidence_score = 75.0
            if "CONFIDENCE:" in response_text:
                try:
                    conf_line = [l for l in response_text.split("\n") if "CONFIDENCE:" in l][0]
                    conf_str = conf_line.split("CONFIDENCE:")[-1].strip().rstrip("%")
                    confidence_score = float(conf_str.split()[0])
                except (ValueError, IndexError):
                    pass

            # Store in llm_analysis (NO PROMPT STORED)
            analysis_doc = {
                "_id": f"ANL-{city_id}-trend-{uuid.uuid4().hex[:8]}",
                "city_id": city_id,
                "anomaly_id": None,
                "analysis_type": "trend_analysis",
                "llm_model": "openai/gpt-oss-120b",
                "temperature_f": None,
                "date_analyzed": datetime.now(UTC),
                "response": response_text,
                "reasoning_steps": [],
                "confidence_score": confidence_score,
                "tags": ["trend_analysis", "heat_wave_forecast"],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }

            llm_coll.insert_one(analysis_doc)
            print(f"  [{i}/5] ✓ {city_id} — Groq generated forecast (confidence: {confidence_score:.0f}%)")
            successful += 1

        except Exception as exc:
            print(f"  [{i}/5] ✗ {city_id}: {str(exc)[:50]}")
            failed += 1

    print(f"\n✓ Generated {successful} real LLM analyses via Groq")
    print(f"✗ Failed: {failed}")
    print(f"\n✓ Analyses stored in llm_analysis collection (prompts in llm_prompts.py)")
    print(f"✓ System ready for video demo!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_sample_llm_analyses())

"""LLM-powered reasoning (RESPOND stage) via Groq's hosted openai/gpt-oss-120b.

Groq's API is OpenAI-compatible, so this reuses the AsyncOpenAI SDK pointed at Groq's
base_url — same pattern as groq_client.py, kept separate here because RESPOND needs its
own system prompt, JSON-object response format, and deterministic fallback.
"""

import json

from openai import AsyncOpenAI

from argus_agent.prompts.respond_prompt import RESPOND_SYSTEM_PROMPT, build_respond_user_prompt
from argus_agent.src.config import settings
from argus_agent.src.constants import GROQ_BASE_URL, GROQ_MODEL
from argus_agent.src.logging.app_logger import app_logger


class ReasonerService:
    def __init__(self) -> None:
        self._client = (
            AsyncOpenAI(api_key=settings.groq_api_key, base_url=GROQ_BASE_URL)
            if settings.groq_api_key
            else None
        )

    async def generate_recommendations(self, anomaly: dict, investigation: dict, impact: dict) -> list[dict]:
        if not self._client:
            return self._fallback_recommendations(impact)

        try:
            response = await self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": RESPOND_SYSTEM_PROMPT},
                    {"role": "user", "content": build_respond_user_prompt(anomaly, investigation, impact)},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "[]"
            parsed = json.loads(content)
            actions = parsed if isinstance(parsed, list) else parsed.get("actions", [])
            return actions or self._fallback_recommendations(impact)
        except Exception as exc:  # noqa: BLE001 — LLM calls fail in many nonfatal ways
            app_logger.warning("Groq recommendation generation failed: %s", exc)
            return self._fallback_recommendations(impact)

    async def analyze_trend(self, prompt: str) -> str:
        """Analyze temperature trend and generate heat wave forecast."""
        if not self._client:
            return self._fallback_trend_analysis()

        try:
            response = await self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a heat meteorologist analyzing temperature trends for emergency response. Provide concise, actionable analysis."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content or self._fallback_trend_analysis()
        except Exception as exc:
            app_logger.warning("Groq trend analysis failed: %s", exc)
            return self._fallback_trend_analysis()

    @staticmethod
    def _fallback_trend_analysis() -> str:
        """Fallback trend analysis when Groq is unavailable."""
        return """**HEAT WAVE STATUS**: Monitoring active
**TREND**: Data insufficient for forecast
**PEAK FORECAST**: Check 7-day history
**RISK LEVEL**: MODERATE (pending full analysis)
**KEY INSIGHTS**:
- Continue scanning to build trend data
- Use Groq API key for automated forecasting
**CONFIDENCE**: 30%"""

    @staticmethod
    def _fallback_recommendations(impact: dict) -> list[dict]:
        """Deterministic recommendations when no Groq key is configured or the call fails."""
        top_risks = impact.get("risk_ranking", [])[:3]
        actions = [
            {
                "action": f"Issue heat advisory to {r['name']} ({r['type'].replace('_', ' ')})",
                "target": "Facility management / emergency services",
                "urgency": "IMMEDIATE" if r["risk"] in ("CRITICAL", "HIGH") else "WITHIN_4_HOURS",
                "expected_impact": f"Reduces exposure risk at a {r['risk']}-rated site {r['distance_m']:.0f}m away",
            }
            for r in top_risks
        ]
        actions.append(
            {
                "action": "Continue monitoring the zone every scan cycle",
                "target": "ARGUS agent",
                "urgency": "WITHIN_4_HOURS",
                "expected_impact": "Detects escalation or resolution automatically",
            }
        )
        return actions


reasoner_service = ReasonerService()

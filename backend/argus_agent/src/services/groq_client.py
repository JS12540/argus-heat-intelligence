"""Generic Groq chat helper — for sub-agents and quick classification. The RESPOND stage
has its OWN Groq-backed client in reasoner_service.py (same base_url/model, but with a
fixed system prompt, JSON-object response format, and a deterministic fallback) — this one
is for anything else that just needs a quick, unstructured completion.

Groq's API is OpenAI-compatible, so this reuses the same SDK pointed at a different
base_url. Not yet called from any agent stage — ready for whenever sub-agents land.
"""

from openai import AsyncOpenAI

from argus_agent.src.config import settings
from argus_agent.src.constants import GROQ_BASE_URL, GROQ_MODEL


class GroqClient:
    def __init__(self) -> None:
        self._client = (
            AsyncOpenAI(api_key=settings.groq_api_key, base_url=GROQ_BASE_URL)
            if settings.groq_api_key
            else None
        )

    async def chat(self, system_prompt: str, user_prompt: str, model: str = GROQ_MODEL) -> str | None:
        if not self._client:
            return None
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content


groq_client = GroqClient()

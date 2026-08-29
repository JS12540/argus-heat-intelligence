"""LLM prompt templates for ARGUS heat intelligence analysis.

These prompts guide Groq to analyze temperature trends and generate heat wave forecasts.
Each prompt includes example JSON output format for structured response parsing.
"""

HEAT_WAVE_TREND_ANALYSIS_PROMPT = """You are a heat meteorologist analyzing temperature trends for emergency response.

CITY: {city_name}
HISTORICAL DATA (last {days} days):
{temperature_data_json}

ANALYZE AND PROVIDE:

1. **HEAT WAVE STATUS**: Is this a heat wave? Evidence from data?
2. **TREND**: Worsening / Stable / Improving?
3. **PEAK FORECAST**: Highest temp expected in next 3 days?
4. **RISK LEVEL**: LOW / MODERATE / HIGH / CRITICAL
5. **KEY INSIGHTS**: Bullet points for emergency planners
6. **CONFIDENCE**: 0-100% confidence in this forecast

Keep response concise and actionable.

EXAMPLE JSON OUTPUT FORMAT:
{{
  "heat_wave_status": "YES - Three consecutive days above 110°F",
  "trend": "WORSENING - +3.2°F per day",
  "peak_forecast": "118°F (expected Day 5)",
  "risk_level": "CRITICAL",
  "key_insights": [
    "Infrastructure strain likely at 115°F+",
    "Vulnerable populations at extreme risk",
    "Recommend opening cooling centers NOW",
    "Power grid strain expected mid-afternoon"
  ],
  "confidence": 92
}}"""


TREND_ANALYSIS_STRUCTURED_PROMPT = """You are a heat meteorologist analyzing 7-day temperature trends for emergency response in {city_name}.

HISTORICAL TEMPERATURE DATA:
{temperature_data_json}

Analyze the data and respond in the following JSON structure:

{{
  "heat_wave_status": "YES/NO - explanation with evidence",
  "trend_direction": "WORSENING|STABLE|IMPROVING",
  "trend_rate": "rate of change (°F/day or summary)",
  "peak_temperature": {{
    "value": 95.5,
    "unit": "°F",
    "date": "2026-08-31",
    "reason": "Explanation of why this peak is expected"
  }},
  "forecast_next_3_days": {{
    "day_1": 98.2,
    "day_2": 102.5,
    "day_3": 105.8,
    "trend": "WORSENING"
  }},
  "risk_level": "LOW|MODERATE|HIGH|CRITICAL",
  "infrastructure_impact": {{
    "power_grid": "Description of expected strain",
    "cooling_capacity": "Assessment of cooling center needs",
    "vulnerable_populations": "Groups most at risk"
  }},
  "recommended_actions": [
    "Action 1 for emergency planners",
    "Action 2",
    "Action 3"
  ],
  "confidence_score": 85,
  "data_quality_notes": "Any limitations in the data analysis"
}}

Provide ONLY the JSON response, no additional text."""


def get_trend_analysis_prompt(city_name: str, days: int, temperature_json: str) -> str:
    """Build trend analysis prompt with historical data."""
    return HEAT_WAVE_TREND_ANALYSIS_PROMPT.format(
        city_name=city_name,
        days=days,
        temperature_data_json=temperature_json,
    )


def get_structured_trend_analysis_prompt(city_name: str, temperature_json: str) -> str:
    """Build structured trend analysis prompt for JSON response."""
    return TREND_ANALYSIS_STRUCTURED_PROMPT.format(
        city_name=city_name,
        temperature_data_json=temperature_json,
    )

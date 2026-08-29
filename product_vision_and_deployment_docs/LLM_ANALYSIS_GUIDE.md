# ARGUS LLM Analysis Integration Guide

## Overview

The ARGUS system now has a dedicated **LLM Analysis Collection** in MongoDB to store AI-generated insights separately from raw anomaly data. This enables:

- **Reproducibility**: Store the exact prompt + response for every LLM call
- **Versioning**: Update analysis without modifying original anomalies
- **Auditing**: Trace which LLM model generated which insight
- **Training**: Use stored analyses to fine-tune future models
- **Cost tracking**: Monitor which analyses cost what

---

## Database Schema

### `llm_analysis` Collection

```javascript
{
  "_id": "ANL-phoenix-az-a1b2c3d4",
  "city_id": "phoenix-az",
  "anomaly_id": "ANO-phoenix-az-a1b2c3d4",  // null for city-wide analysis
  "analysis_type": "response_plan",         // "response_plan", "risk_assessment", "trend_analysis"
  "llm_model": "openai/gpt-oss-120b",       // which model generated this
  "temperature_f": 106.8,
  "date_analyzed": "2026-08-29T15:32:00Z",
  "prompt": "You are a heat response specialist. An extreme heat anomaly...",
  "response": "IMMEDIATE ACTIONS:\n1. Open cooling centers...",
  "reasoning_steps": [
    "Identified vulnerable populations: elderly (3 facilities), unhoused (2 camps)",
    "Assessed infrastructure risk: power grid overload risk > 70%",
    "Recommended resource allocation: 15 units"
  ],
  "confidence_score": 87.5,                  // 0-100, LLM's self-assessed confidence
  "tags": ["infrastructure_risk", "vulnerable_population", "urgent", "immediate_action"],
  "created_at": "2026-08-29T15:32:00Z",
  "updated_at": "2026-08-29T15:32:00Z"
}
```

---

## How to Add LLM Analysis to Your Pipeline

### Option 1: Simple Integration (Already in RESPOND Stage)

The RESPOND stage already calls Groq/OpenAI. Just store the result:

```python
# In services/reasoner_service.py (already does this):
async def generate_response_plan(anomaly: AnomalyDocument) -> ResponsePlan:
    """Generate response plan using Groq LLM."""
    
    prompt = f"""
    You are a heat response specialist. An extreme heat anomaly has been detected:
    - Location: {anomaly.city_name}, {anomaly.zone_name}
    - Temperature: {anomaly.temperature_f}°F
    - Severity: {anomaly.severity}
    - Hours above threshold: {anomaly.investigation.hours_above_threshold}
    
    Provide immediate recommended actions.
    """
    
    # Call Groq
    response = await groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,
    )
    
    response_text = response.choices[0].message.content
    
    # Store in LLM analysis collection
    analysis_doc = LLMAnalysisDocument(
        id=f"ANL-{anomaly.city_id}-{uuid4().hex[:8]}",
        city_id=anomaly.city_id,
        anomaly_id=anomaly.id,
        analysis_type="response_plan",
        llm_model="openai/gpt-oss-120b",
        temperature_f=anomaly.temperature_f,
        date_analyzed=datetime.now(UTC),
        prompt=prompt,
        response=response_text,
        reasoning_steps=[],  # Could parse these from response if structured
        confidence_score=88.0,  # Could ask LLM for self-assessment
        tags=["response_plan", anomaly.severity.lower()],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    
    get_llm_analysis_collection().insert_one(analysis_doc.to_mongo())
    
    # Parse response into ActionPlan
    return parse_response_plan(response_text)
```

### Option 2: Custom Analysis (New Insights)

Add new analysis types beyond response planning:

```python
async def generate_risk_assessment(
    city_id: str, 
    anomalies: list[AnomalyDocument],
    infrastructure_nearby: list[Infrastructure]
) -> None:
    """Analyze infrastructure risk given heat anomalies."""
    
    prompt = f"""
    Given the following heat anomalies and nearby infrastructure, assess risk:
    
    Anomalies:
    {json.dumps([a.model_dump() for a in anomalies], indent=2)}
    
    Infrastructure at risk:
    {json.dumps(infrastructure_nearby, indent=2)}
    
    Provide a risk assessment with:
    1. Which infrastructure is most at risk
    2. Recommended immediate mitigations
    3. 24-hour forecast impact
    """
    
    # Call LLM
    response = await groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2000,
    )
    
    # Store analysis
    analysis_doc = LLMAnalysisDocument(
        id=f"ANL-{city_id}-risk-{uuid4().hex[:8]}",
        city_id=city_id,
        anomaly_id=None,  # City-wide, not tied to single anomaly
        analysis_type="risk_assessment",
        llm_model="openai/gpt-oss-120b",
        temperature_f=None,  # N/A for city-wide
        date_analyzed=datetime.now(UTC),
        prompt=prompt,
        response=response.choices[0].message.content,
        tags=["city_wide", "infrastructure", "risk_assessment"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    
    get_llm_analysis_collection().insert_one(analysis_doc.to_mongo())
```

### Option 3: Trend Analysis

Analyze multi-day temperature patterns:

```python
async def generate_trend_analysis(city_id: str, days: int = 7) -> None:
    """Analyze temperature trend over past N days."""
    
    # Fetch historical temps from cache
    cache = get_fortyguard_cache_collection()
    historical = list(cache.find({
        "city_id": city_id,
        "label": {"$regex": "tcm"},  # Temperature data only
    }).sort("created_at", -1).limit(days))
    
    temps_by_day = {}
    for doc in historical:
        date = doc["created_at"].date()
        if date not in temps_by_day:
            temps_by_day[date] = []
        temps_by_day[date].append(
            doc["result"]["result"]["stats_data"]["temperature_stats"]["mean"]
        )
    
    # Compute daily stats
    daily_stats = {
        date: {
            "min": min(temps),
            "max": max(temps),
            "mean": sum(temps) / len(temps),
        }
        for date, temps in temps_by_day.items()
    }
    
    prompt = f"""
    Analyze the following temperature trend for {city_id}:
    
    {json.dumps(daily_stats, indent=2)}
    
    Provide:
    1. Is this a heat wave? Evidence?
    2. Trend direction (worsening, stable, improving)
    3. Forecast for next 3 days
    4. Risk level assessment
    """
    
    response = await groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1000,
    )
    
    analysis_doc = LLMAnalysisDocument(
        id=f"ANL-{city_id}-trend-{uuid4().hex[:8]}",
        city_id=city_id,
        analysis_type="trend_analysis",
        llm_model="openai/gpt-oss-120b",
        date_analyzed=datetime.now(UTC),
        prompt=prompt,
        response=response.choices[0].message.content,
        tags=["trend", "forecast", "heat_wave"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    
    get_llm_analysis_collection().insert_one(analysis_doc.to_mongo())
```

---

## API Endpoints (to be added)

### Get LLM Analysis for Anomaly

```
GET /api/anomalies/{anomaly_id}/llm-analysis

Returns all analyses generated for that anomaly:
[
  {
    "id": "ANL-phoenix-az-a1b2c3d4",
    "analysis_type": "response_plan",
    "llm_model": "openai/gpt-oss-120b",
    "response": "IMMEDIATE ACTIONS: ...",
    "confidence_score": 87.5,
    "created_at": "2026-08-29T15:32:00Z"
  }
]
```

### Get City Trend Analysis

```
GET /api/cities/{city_id}/llm-analysis?type=trend_analysis&days=7

Returns trend analysis for the city over last N days
```

### List All LLM Analyses

```
GET /api/llm-analysis?city_id=...&type=...&model=...

Query analyses by city, type, or model
```

---

## Cost & Performance

| Model | Speed | Cost per Call | Use Case |
|-------|-------|---------------|----------|
| Groq (gpt-oss-120b) | ~2 sec | ~$0.0001 | Fast response plans |
| OpenAI (gpt-5-mini) | ~10 sec | ~$0.001 | Slower, deeper analysis |
| Claude (via API) | ~15 sec | ~$0.0005 | Long-form reasoning |

**Recommendation**: Use Groq for fast response plans (RESPOND stage), reserve OpenAI/Claude for batch analyses (trend_analysis, risk_assessment) run at night.

---

## Structuring LLM Prompts for Heat Emergencies

### Response Plan Prompt Template

```
You are a heat emergency response specialist with expertise in:
- Public health and vulnerable populations
- Infrastructure resilience  
- Emergency management

DETECTED ANOMALY:
- Location: [city, zone]
- Temperature: [temp]°F
- Severity: [severity]
- Duration: [hours] hours above threshold
- Nearby infrastructure: [list]
- Population at risk: [demographic groups]

PROVIDE:

1. IMMEDIATE ACTIONS (next 2 hours):
   - Action: [what to do]
   - Target: [who/what]
   - Resources needed: [how many/much]

2. SHORT-TERM (next 24 hours):
   - [actions]

3. VULNERABLE POPULATIONS:
   - Identify groups most at risk
   - Recommend specific interventions

4. INFRASTRUCTURE CONCERNS:
   - What might fail under this heat
   - Mitigation measures

5. CONFIDENCE: [0-100] - how confident in these recommendations?

Keep response concise but actionable.
```

### Risk Assessment Prompt Template

```
You are an infrastructure resilience expert evaluating heat risk.

CITY: [city]
CURRENT HEAT ANOMALIES: [list with locations and temps]

INFRASTRUCTURE NEARBY:
[hospitals, power stations, transit hubs, etc. with coordinates and cooling capacity]

ASSESS:

1. CRITICAL FAILURES (>80% risk):
   - What specific infrastructure likely fails
   - Cascade effects
   - Time to failure

2. MODERATE RISK (30-80%):
   - Degraded performance
   - Recommended preparations

3. RESILIENCE STRATEGIES:
   - What we can do RIGHT NOW
   - Medium-term hardening
   - Long-term climate adaptation

STRUCTURE: JSON-formatted for programmatic parsing.
```

---

## Storing & Retrieving Analysis

### Store After Generation

```python
from argus_agent.src.db.mongo import get_llm_analysis_collection
from argus_agent.src.db.models import LLMAnalysisDocument

analysis = LLMAnalysisDocument(
    id=f"ANL-{city_id}-{uuid4().hex[:8]}",
    city_id=city_id,
    anomaly_id=anomaly_id,
    analysis_type="response_plan",
    llm_model="openai/gpt-oss-120b",
    temperature_f=anomaly.temperature_f,
    date_analyzed=datetime.now(UTC),
    prompt=prompt,
    response=llm_response,
    confidence_score=88.0,
    tags=["urgent", "response_plan"],
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)

get_llm_analysis_collection().insert_one(analysis.to_mongo())
```

### Retrieve by City

```python
from argus_agent.src.db.mongo import get_llm_analysis_collection

analyses = list(get_llm_analysis_collection().find({
    "city_id": "phoenix-az",
    "analysis_type": "response_plan",
}).sort("date_analyzed", -1).limit(10))
```

### Retrieve by Anomaly

```python
analyses = list(get_llm_analysis_collection().find({
    "anomaly_id": "ANO-phoenix-az-a1b2c3d4",
}).sort("created_at", -1))
```

---

## Dashboard Integration

### Show Analysis in Anomaly Detail

```typescript
// frontend/src/pages/Incident.tsx

export function Incident() {
  const { id } = useParams();
  const [anomaly, setAnomaly] = useState<Anomaly | null>(null);
  const [analysis, setAnalysis] = useState<LLMAnalysis[]>([]);
  
  useEffect(() => {
    // Fetch anomaly
    api.anomaly(id).then(setAnomaly);
    
    // Fetch LLM analysis for this anomaly
    fetch(`/api/anomalies/${id}/llm-analysis`)
      .then(r => r.json())
      .then(setAnalysis);
  }, [id]);
  
  return (
    <div>
      <AnomalyHeader anomaly={anomaly} />
      
      {/* LLM Response Plan */}
      {analysis.find(a => a.analysis_type === "response_plan") && (
        <div className="card">
          <h3>AI Response Plan</h3>
          <p>{analysis.find(a => a.analysis_type === "response_plan").response}</p>
          <span className="badge">Confidence: {analysis[0].confidence_score}%</span>
        </div>
      )}
    </div>
  );
}
```

---

## Next Steps

1. ✅ Add `LLMAnalysisDocument` model
2. ✅ Create `llm_analysis` collection
3. ⏳ Integrate into RESPOND stage (store all LLM outputs)
4. ⏳ Add API endpoints to retrieve analyses
5. ⏳ Show analyses in frontend Incident detail page
6. ⏳ Create batch job for nightly trend analysis
7. ⏳ Dashboard widget: "City-wide heat forecast" powered by trend analysis

---

## Example Workflow

```
1. DISCOVER: Temperature reading of 106°F at location
   ↓
2. INVESTIGATE: Get persistence (11h above 100°F), infrastructure nearby (3 hospitals)
   ↓
3. UNDERSTAND: Composite score = 78 → SEVERITY: HIGH
   ↓
4. RESPOND: Call Groq
   Prompt: "Heat emergency at [location], [temp], [infrastructure at risk]"
   Response: "OPEN COOLING CENTERS. ISSUE PUBLIC HEALTH ALERT. ..."
   ↓
5. STORE: Save LLM response in `llm_analysis` collection
   {
     "anomaly_id": "ANO-...",
     "response": "OPEN COOLING CENTERS...",
     "confidence_score": 89,
     "tags": ["urgent", "infrastructure_risk"]
   }
   ↓
6. DISPLAY: Show in dashboard
   Anomaly card → "AI-Generated Response" → [full plan with confidence]

```

---

**LLM analysis is the bridge between raw heat data and human action.**

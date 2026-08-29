import { useEffect, useState } from "react";

interface LLMAnalysis {
  city_id: string;
  response: string;
  confidence_score: number;
  analysis_type: string;
  date_analyzed: string;
}

interface Props {
  cityId: string;
  cityName: string;
}

export function LLMForecastCard({ cityId, cityName }: Props) {
  const [analysis, setAnalysis] = useState<LLMAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/cities/${cityId}/llm-trend-analysis?days=7`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        if (data.response && data.confidence_score !== undefined) {
          setAnalysis({
            city_id: cityId,
            response: data.response || "",
            confidence_score: data.confidence_score || 0,
            analysis_type: "trend_analysis",
            date_analyzed: new Date().toISOString(),
          });
        }
      } else {
        setError("Failed to generate AI forecast");
      }
    } catch (error) {
      console.error("Failed to fetch LLM analysis:", error);
      setError("AI analysis unavailable");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (cityId) {
      fetchAnalysis();
    }
  }, [cityId]);

  if (loading && !analysis) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-300 font-semibold">AI Heat Forecast</div>
          <div className="animate-spin text-slate-400">⟳</div>
        </div>
        <div className="mt-2 text-xs text-slate-500">Analyzing temperature patterns…</div>
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-slate-300 font-semibold">AI Heat Forecast</div>
            <div className="text-xs text-slate-500 mt-1">{error}</div>
          </div>
          <button
            onClick={fetchAnalysis}
            className="text-xs px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const cleanText = (text: string) => text.replace(/\*\*|\*|~~|__/g, "").trim();

  // Extract each numbered section, stopping right before the next known section label —
  // the LLM's response is often one flowing paragraph with no real line breaks, so a naive
  // "match to end of line" grabs into the next section's text instead.
  const extractSection = (label: string, nextLabel: string) => {
    const re = new RegExp(`${label}[:\\s]*\\*{0,2}([\\s\\S]*?)(?=\\d\\.\\s*\\*{0,2}\\s*${nextLabel}|$)`, "i");
    const m = analysis.response.match(re);
    return m ? cleanText(m[1]).slice(0, 140) : "";
  };

  const riskMatch = analysis.response.match(/\b(CRITICAL|HIGH|MODERATE|LOW)\b/i);
  const riskLevel = riskMatch ? riskMatch[1].toUpperCase() : "MODERATE";

  const heatWaveText = extractSection("HEAT[\\s-]*WAVE(?:\\s*STATUS)?", "TREND") || "Analyzing…";
  const trendText = extractSection("TREND", "PEAK") || "Stable";

  const riskColor: Record<string, string> = {
    CRITICAL: "text-red-400",
    HIGH: "text-orange-400",
    MODERATE: "text-yellow-400",
    LOW: "text-slate-400",
  };

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-white text-base">AI Heat Forecast</h3>
            <p className="text-sm text-slate-500 mt-0.5">{cityName}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-semibold text-white">{Math.round(analysis.confidence_score)}%</div>
            <p className="text-xs text-slate-500">Confidence</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded border border-slate-700 bg-slate-800 p-3">
            <p className="text-xs text-slate-500 uppercase">Status</p>
            <p className="text-sm text-slate-200 mt-1">{heatWaveText}</p>
          </div>
          <div className="rounded border border-slate-700 bg-slate-800 p-3">
            <p className="text-xs text-slate-500 uppercase">Trend</p>
            <p className="text-sm text-slate-200 mt-1">{trendText}</p>
          </div>
          <div className="rounded border border-slate-700 bg-slate-800 p-3">
            <p className="text-xs text-slate-500 uppercase">Risk</p>
            <p className={`text-sm font-semibold mt-1 ${riskColor[riskLevel] ?? "text-slate-300"}`}>{riskLevel}</p>
          </div>
        </div>

        <button
          onClick={fetchAnalysis}
          disabled={loading}
          className="w-full text-sm px-4 py-2 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 transition border border-slate-700"
        >
          {loading ? "Analyzing…" : "Refresh Analysis"}
        </button>
      </div>
    </div>
  );
}

import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { AgentFeed } from "../components/dashboard/AgentFeed";
import { AnalysisPanel } from "../components/dashboard/AnalysisPanel";
import { TemperatureTrendChart } from "../components/dashboard/TemperatureTrendChart";
import { LLMForecastCard } from "../components/dashboard/LLMForecastCard";
import { CityStatsHeader } from "../components/dashboard/CityStatsHeader";
import { MetricsPanel } from "../components/dashboard/MetricsPanel";
import { QueryPanel } from "../components/dashboard/QueryPanel";
import { AnomalyExplainer } from "../components/dashboard/AnomalyExplainer";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useAnomalies } from "../hooks/useAnomalies";
import { usePolling } from "../hooks/usePolling";

export function Dashboard() {
  const { cityId = "" } = useParams<{ cityId: string }>();
  const { data: anomalies, loading, refresh } = useAnomalies(cityId);
  const { data: cities } = usePolling(api.cities, 30_000);
  const { data: agentStatus } = usePolling(() => api.agentStatus(cityId), 3_000);
  const [scanning, setScanning] = useState(false);
  const [llmResponse, setLlmResponse] = useState<string | null>(null);

  const city = cities?.find((c) => c.id === cityId);

  useEffect(() => {
    // Fetch LLM analysis on mount/city change
    if (cityId) {
      fetch(`/api/cities/${cityId}/llm-trend-analysis`, { method: "POST" })
        .then((r) => r.json())
        .then((data) => setLlmResponse(data.response))
        .catch(() => {});
    }
  }, [cityId]);

  async function handleScan() {
    setScanning(true);
    try {
      await api.triggerScan(cityId);
      await refresh();
    } finally {
      setScanning(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Connecting to ARGUS…" />
      </div>
    );
  }

  const list = anomalies ?? [];
  const cityLabel = city ? `${city.name}, ${city.state}` : cityId;
  const meta = agentStatus?.last_scan_meta;
  const noRealData = !scanning && meta && !meta.demo_mode && meta.cells_with_data === 0;

  return (
    <div className="fade-in space-y-6 p-8">
      <CityStatsHeader
        cityId={cityId}
        cityName={cityLabel}
        anomalyCount={list.length}
        maxSeverity={city?.max_severity ?? undefined}
        lastScanMeta={meta ?? undefined}
      />

      {/* Explore FortyGuard directly first — decide what params actually return data for this
          city before spending ~5+ minutes on a full scan. */}
      <QueryPanel cityId={cityId} />

      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="relative overflow-hidden rounded-xl bg-gradient-to-br from-ember-500 to-crimson-600 px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:brightness-110 disabled:opacity-70"
          >
            {scanning && <span className="shimmer absolute inset-0" />}
            <span className="relative">{scanning ? "Scanning city…" : "Run Scan Now"}</span>
          </button>
          {scanning && (
            <div className="mt-2 text-xs text-slate-500">
              {agentStatus?.progress ?? "starting…"} · a real scan takes several minutes
            </div>
          )}
        </div>
        {meta && !scanning && (
          <div className="text-right text-xs text-slate-500">
            Last scan: {meta.cells_with_data}/{meta.cells_scanned} cells had real data
            {meta.city_exceedance_zone_count != null && ` · ${meta.city_exceedance_zone_count} zones exceeding threshold`}
          </div>
        )}
      </div>

      {noRealData && (
        <div className="rounded-xl border border-amber-500/25 bg-amber-500/10 p-4 text-sm text-amber-200">
          <span className="font-semibold">FortyGuard returned no data for this scan</span> — 0 of{" "}
          {meta.cells_scanned} grid cells had real temperature data for the requested day. This is
          not a bug: it means no anomalies could be detected because there was nothing to measure,
          not that conditions are calm. Use the Custom Query panel above to check whether a
          different date has coverage for {cityLabel}.
        </div>
      )}

      <div className="flex justify-end">
        <AnomalyExplainer />
      </div>
      <MetricsPanel anomalies={list} />

      <TemperatureTrendChart cityId={cityId} cityName={cityLabel} />

      <LLMForecastCard cityId={cityId} cityName={cityLabel} />

      <AnalysisPanel cityId={cityId} cityName={cityLabel} cells={meta?.cells} polygon={city?.polygon} anomalies={list} llmResponse={llmResponse ?? undefined} />

      <div style={{ height: 420 }}>
        <AgentFeed anomalies={list} />
      </div>
    </div>
  );
}

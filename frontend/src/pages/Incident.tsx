import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { SeverityBadge } from "../components/common/SeverityBadge";
import { InfrastructureList } from "../components/incident/InfrastructureList";
import { PipelineTrace } from "../components/incident/PipelineTrace";
import { RecommendationList } from "../components/incident/RecommendationList";
import { StageProgress } from "../components/incident/StageProgress";
import { usePolling } from "../hooks/usePolling";

export function Incident() {
  const { id } = useParams<{ id: string }>();
  const { data: anomaly, loading } = usePolling(() => api.anomaly(id!), 10_000);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Loading incident…" />
      </div>
    );
  }

  if (!anomaly) {
    return <div className="p-8 text-slate-400">Incident not found.</div>;
  }

  const inv = anomaly.investigation;

  return (
    <div className="fade-in space-y-6 p-8">
      <Link
        to={`/cities/${anomaly.city_id}`}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 transition hover:text-slate-200"
      >
        ← Back to {anomaly.city_name} Command Center
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-white">{anomaly.zone_name}</h1>
          <p className="mt-1 font-mono text-xs text-slate-500">{anomaly.id}</p>
        </div>
        <SeverityBadge severity={anomaly.severity} />
      </div>

      <div className="card p-5">
        <StageProgress stage={anomaly.stage} />
      </div>

      <PipelineTrace anomaly={anomaly} />

      <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-6">
        {[
          ["Temperature", `${anomaly.temperature_f.toFixed(1)}°F`],
          ["Composite Score", anomaly.composite_score.toFixed(0)],
          ["Persistence", inv ? `${inv.hours_above_threshold.toFixed(1)}h` : "—", "longest unbroken streak"],
          [
            "Exceedance",
            inv?.exceedance_hours_total != null ? `${inv.exceedance_hours_total.toFixed(1)}h` : "—",
            "total hours over threshold today",
          ],
          [
            "Peak Hour",
            inv?.peak_hour_utc != null ? `${String(inv.peak_hour_utc).padStart(2, "0")}:00 UTC` : "—",
            "when today's peak temp occurred",
          ],
          ["Trend", inv?.trend ?? "—"],
        ].map(([label, value, sublabel]) => (
          <div key={label} className="card card-interactive p-5">
            <div className="label">{label}</div>
            <div className="mt-1 font-display text-lg font-semibold text-white">{value}</div>
            {sublabel && <div className="mt-0.5 text-[11px] text-slate-500">{sublabel}</div>}
          </div>
        ))}
      </div>

      {inv && (
        <div className="card p-5">
          <h3 className="font-display text-sm font-semibold text-white">Investigation Summary</h3>
          <div className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <div className="label">Heat Index</div>
              <div className="text-slate-300">
                {inv.heat_index_f != null ? `${inv.heat_index_f.toFixed(0)}°F` : "—"}
              </div>
            </div>
            <div>
              <div className="label">Humidity</div>
              <div className="text-slate-300">
                {inv.humidity_percent != null ? `${inv.humidity_percent.toFixed(0)}%` : "—"}
              </div>
            </div>
            <div>
              <div className="label">Air Quality Index</div>
              <div className="text-slate-300">
                {inv.air_quality_index != null ? inv.air_quality_index.toFixed(0) : "—"}
              </div>
            </div>
            <div>
              <div className="label">Wet Bulb Temp</div>
              <div className="text-slate-300">
                {inv.wet_bulb_temperature_f != null ? `${inv.wet_bulb_temperature_f.toFixed(0)}°F` : "—"}
              </div>
            </div>
          </div>
          {inv.surface_composition && (
            <div className="mt-4 border-t border-white/[0.06] pt-4">
              <div className="label mb-2">Surface composition (satellite segmentation)</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(inv.surface_composition)
                  .sort(([, a], [, b]) => b - a)
                  .map(([name, pct]) => (
                    <span
                      key={name}
                      className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-300"
                    >
                      {name} {pct.toFixed(0)}%
                    </span>
                  ))}
              </div>
            </div>
          )}
          {inv.contextual_factors.length > 0 && (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-400">
              {inv.contextual_factors.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <InfrastructureList impact={anomaly.impact_assessment} />
        <RecommendationList plan={anomaly.response_plan} />
      </div>
    </div>
  );
}

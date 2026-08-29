import type { Anomaly } from "../../types";

interface StageInfo {
  key: string;
  title: string;
  system: string;
  detail: string;
  done: boolean;
}

/** Makes the actual agent architecture visible per-anomaly — which external system
 * backed each stage, and what it returned. Not a mockup: every value here is real. */
export function PipelineTrace({ anomaly }: { anomaly: Anomaly }) {
  const inv = anomaly.investigation;
  const impact = anomaly.impact_assessment;
  const plan = anomaly.response_plan;

  const investigateDetails: string[] = [];
  if (inv) {
    investigateDetails.push(`${inv.hours_above_threshold.toFixed(1)}h streak`);
    if (inv.exceedance_hours_total != null) investigateDetails.push(`${inv.exceedance_hours_total.toFixed(1)}h total`);
    if (inv.peak_hour_utc != null) investigateDetails.push(`peaks ${String(inv.peak_hour_utc).padStart(2, "0")}:00 UTC`);
    if (inv.heat_index_f != null) investigateDetails.push(`heat index ${inv.heat_index_f.toFixed(0)}°F`);
    if (inv.surface_composition) investigateDetails.push("surface segmentation confirmed");
  }

  const stages: StageInfo[] = [
    {
      key: "DISCOVER",
      title: "Discover",
      system: "FortyGuard · heatmap (tcm)",
      detail: `${anomaly.temperature_f.toFixed(1)}°F · composite score ${anomaly.composite_score.toFixed(0)}`,
      done: true,
    },
    {
      key: "INVESTIGATE",
      title: "Investigate",
      system: "FortyGuard · persistence + exceedance + time_of_measure + env_params + satellite",
      detail: investigateDetails.length ? investigateDetails.join(" · ") : "pending",
      done: !!inv,
    },
    {
      key: "UNDERSTAND",
      title: "Understand",
      system: "OpenStreetMap · Overpass API",
      detail: impact ? `${impact.total_infrastructure_at_risk} site(s) at risk within 1km` : "pending",
      done: !!impact,
    },
    {
      key: "RESPOND",
      title: "Respond",
      system: "Groq · openai/gpt-oss-120b",
      detail: plan ? `${plan.actions.length} action(s) generated` : "pending",
      done: !!plan,
    },
  ];

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-white">Agent Pipeline</h3>
        <span className="label">real data, not a mock</span>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {stages.map((s, i) => (
          <div key={s.key} className="relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            {i < stages.length - 1 && (
              <span className="absolute right-[-1px] top-1/2 hidden h-px w-3 -translate-y-1/2 bg-white/10 lg:block" />
            )}
            <div className="flex items-center justify-between">
              <span className="label">
                {i + 1}. {s.title}
              </span>
              <span
                className={`h-1.5 w-1.5 rounded-full ${s.done ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" : "bg-slate-600"}`}
              />
            </div>
            <div className="mt-2 truncate text-xs font-mono text-ember-400">{s.system}</div>
            <div className="mt-1.5 text-sm text-slate-300">{s.detail}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

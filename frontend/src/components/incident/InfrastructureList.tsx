import type { ImpactAssessment } from "../../types";
import { SeverityBadge } from "../common/SeverityBadge";

export function InfrastructureList({ impact }: { impact: ImpactAssessment | null }) {
  if (!impact) return null;

  return (
    <div className="card p-5">
      <h3 className="font-display text-sm font-semibold text-white">Infrastructure at Risk</h3>
      <div className="mt-4 space-y-3">
        {impact.risk_ranking.length === 0 && (
          <p className="text-sm text-slate-500">No vulnerable infrastructure found nearby.</p>
        )}
        {impact.risk_ranking.map((r, i) => (
          <div key={i} className="flex items-start justify-between gap-3 rounded-xl bg-white/[0.02] p-3">
            <div>
              <div className="text-sm font-medium text-slate-200">{r.name}</div>
              <div className="mt-0.5 text-xs text-slate-500">
                {r.distance_m.toFixed(0)}m away — {r.reason}
              </div>
            </div>
            <SeverityBadge severity={r.risk} />
          </div>
        ))}
      </div>

      {impact.cooling_assets_nearby.length > 0 && (
        <div className="mt-5 border-t border-white/[0.06] pt-4">
          <div className="label mb-2">Cooling assets nearby</div>
          <div className="flex flex-wrap gap-2">
            {impact.cooling_assets_nearby.map((c, i) => (
              <span
                key={i}
                className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300"
              >
                {c.name} · {c.distance_m.toFixed(0)}m
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

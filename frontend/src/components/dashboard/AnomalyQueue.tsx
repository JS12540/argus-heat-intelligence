import { Link } from "react-router-dom";
import type { Anomaly } from "../../types";
import { SeverityBadge } from "../common/SeverityBadge";

const ORDER: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 };

export function AnomalyQueue({ anomalies }: { anomalies: Anomaly[] }) {
  const sorted = [...anomalies].sort((a, b) => ORDER[a.severity] - ORDER[b.severity]);

  return (
    <div className="card flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
        <h2 className="font-display text-sm font-semibold text-white">Anomaly Queue</h2>
        <span className="label">{anomalies.length} active</span>
      </div>
      <div className="flex-1 divide-y divide-white/[0.05] overflow-y-auto">
        {sorted.length === 0 && (
          <div className="p-6 text-sm text-slate-500">No anomalies detected in the last scan.</div>
        )}
        {sorted.map((a) => (
          <Link
            key={a.id}
            to={`/incidents/${a.id}`}
            className="block px-5 py-4 transition hover:bg-white/[0.03]"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-200">{a.zone_name}</span>
              <SeverityBadge severity={a.severity} />
            </div>
            <div className="mt-1.5 flex items-center gap-4 text-xs text-slate-500">
              <span className="font-mono text-slate-400">{a.temperature_f.toFixed(1)}°F</span>
              <span>score {a.composite_score.toFixed(0)}</span>
              {a.investigation && <span>{a.investigation.hours_above_threshold.toFixed(1)}h persistent</span>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

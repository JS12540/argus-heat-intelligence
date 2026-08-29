import type { Anomaly } from "../../types";

function Metric({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className={`mt-1 font-display text-2xl font-semibold ${accent ?? "text-white"}`}>{value}</div>
    </div>
  );
}

export function MetricsPanel({ anomalies }: { anomalies: Anomaly[] }) {
  const critical = anomalies.filter((a) => a.severity === "CRITICAL").length;
  const infra = anomalies.reduce(
    (sum, a) => sum + (a.impact_assessment?.total_infrastructure_at_risk ?? 0),
    0,
  );
  const actions = anomalies.reduce((sum, a) => sum + (a.response_plan?.actions.length ?? 0), 0);

  return (
    <div className="card grid grid-cols-2 gap-6 p-6 sm:grid-cols-4">
      <Metric label="Active Anomalies" value={anomalies.length} />
      <Metric label="Critical" value={critical} accent={critical > 0 ? "text-crimson-400" : undefined} />
      <Metric label="Infrastructure at Risk" value={infra} />
      <Metric label="Actions Recommended" value={actions} accent="text-ember-400" />
    </div>
  );
}

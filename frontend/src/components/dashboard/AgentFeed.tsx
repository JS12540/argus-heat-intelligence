import type { Anomaly } from "../../types";

function timeOf(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

const SEVERITY_STYLE: Record<string, { border: string; text: string }> = {
  CRITICAL: { border: "border-l-red-500", text: "text-red-400" },
  HIGH: { border: "border-l-orange-500", text: "text-orange-400" },
  MEDIUM: { border: "border-l-yellow-500", text: "text-yellow-400" },
  LOW: { border: "border-l-slate-500", text: "text-slate-400" },
};

export function AgentFeed({ anomalies }: { anomalies: Anomaly[] }) {
  // Show CRITICAL, HIGH, MEDIUM, LOW only — exclude INFO
  const sorted = anomalies.filter((a) => a.severity !== "INFO");

  const events = [...sorted]
    .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1))
    .map((a) => {
      const inv = a.investigation;
      const heatIndexF = inv?.heat_index_f ? inv.heat_index_f : a.temperature_f;
      const heatIndexC = ((heatIndexF - 32) * 5) / 9;
      const trend = inv?.trend || "UNKNOWN";
      const humid = inv?.humidity_percent || 0;
      const loc = a.latitude != null && a.longitude != null ? `${a.latitude.toFixed(3)}, ${a.longitude.toFixed(3)}` : a.zone_name;
      return {
        at: a.detected_at,
        severity: a.severity,
        text: `${loc} — heat index ${heatIndexC.toFixed(0)}°C, ${humid}% humid, ${trend}`,
      };
    });

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 flex h-full flex-col overflow-hidden">
      <div className="border-b border-slate-700 px-5 py-4">
        <h2 className="font-semibold text-white text-base">Heat Zone Alerts</h2>
        <p className="text-xs text-slate-500 mt-0.5">Anomalies detected this scan</p>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto px-5 py-4">
        {events.length === 0 && (
          <div className="text-sm text-slate-500 italic">No zones detected — conditions stable.</div>
        )}
        {events.map((e, i) => {
          const style = SEVERITY_STYLE[e.severity] ?? SEVERITY_STYLE.LOW;
          return (
            <div key={i} className={`fade-in rounded border-l-2 ${style.border} bg-slate-800 p-3 text-sm`}>
              <div className="flex items-start justify-between gap-2 mb-1">
                <span className="font-mono text-xs text-slate-500">{timeOf(e.at)}</span>
                <span className={`font-semibold text-xs ${style.text}`}>{e.severity}</span>
              </div>
              <p className="text-slate-200 leading-snug">{e.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

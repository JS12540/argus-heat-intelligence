import type { ResponsePlan } from "../../types";

const URGENCY_STYLE: Record<string, string> = {
  IMMEDIATE: "text-crimson-400 border-crimson-500/30 bg-crimson-500/10",
  WITHIN_1_HOUR: "text-ember-400 border-ember-500/30 bg-ember-500/10",
  WITHIN_4_HOURS: "text-amber-300 border-amber-500/30 bg-amber-500/10",
  NEXT_DAY: "text-slate-400 border-white/15 bg-white/5",
};

export function RecommendationList({ plan }: { plan: ResponsePlan | null }) {
  if (!plan) return null;

  return (
    <div className="card p-5">
      <h3 className="font-display text-sm font-semibold text-white">Recommended Actions</h3>
      <ol className="mt-4 space-y-3">
        {plan.actions.map((a) => (
          <li key={a.rank} className="flex gap-3 rounded-xl bg-white/[0.02] p-3">
            <span className="font-display text-sm font-semibold text-slate-500">{a.rank}</span>
            <div className="flex-1">
              <div className="text-sm text-slate-200">{a.action}</div>
              <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                <span>{a.target}</span>
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${URGENCY_STYLE[a.urgency] ?? URGENCY_STYLE.NEXT_DAY}`}
                >
                  {a.urgency.replace(/_/g, " ")}
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-500">{a.expected_impact}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

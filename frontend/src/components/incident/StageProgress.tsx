const STAGES = ["DISCOVER", "INVESTIGATE", "UNDERSTAND", "RESPOND"];

export function StageProgress({ stage }: { stage: string }) {
  const activeIndex = Math.max(STAGES.indexOf(stage), 0);
  return (
    <div className="flex items-center gap-2">
      {STAGES.map((s, i) => (
        <div key={s} className="flex items-center gap-2">
          <div
            className={`h-1.5 w-16 rounded-full ${
              i <= activeIndex ? "bg-gradient-to-r from-ember-500 to-crimson-500" : "bg-white/10"
            }`}
          />
          <span className={`text-[11px] font-medium ${i <= activeIndex ? "text-slate-300" : "text-slate-600"}`}>
            {s}
          </span>
        </div>
      ))}
    </div>
  );
}

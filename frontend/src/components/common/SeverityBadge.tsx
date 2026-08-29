import type { Severity } from "../../types";

const STYLES: Record<Severity, string> = {
  CRITICAL: "bg-crimson-500/15 text-crimson-400 border-crimson-500/30",
  HIGH: "bg-ember-500/15 text-ember-400 border-ember-500/30",
  MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  LOW: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  INFO: "bg-white/5 text-slate-400 border-white/10",
};

const DOT: Record<Severity, string> = {
  CRITICAL: "bg-crimson-500",
  HIGH: "bg-ember-500",
  MEDIUM: "bg-amber-400",
  LOW: "bg-sky-400",
  INFO: "bg-slate-400",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide ${STYLES[severity]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${DOT[severity]}`} />
      {severity}
    </span>
  );
}

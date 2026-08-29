export function LoadingSpinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-slate-500 text-sm">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/10 border-t-ember-500" />
      {label ?? "Loading…"}
    </div>
  );
}

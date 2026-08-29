import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { usePolling } from "../../hooks/usePolling";

export function Header() {
  const { cityId } = useParams<{ cityId?: string }>();
  const { data: cities } = usePolling(api.cities, 30_000);
  const { data: status } = usePolling(
    () => (cityId ? api.agentStatus(cityId) : Promise.resolve(null)),
    5_000,
  );

  const city = cityId ? cities?.find((c) => c.id === cityId) : undefined;

  return (
    <header className="flex items-center justify-between border-b border-white/[0.06] px-8 py-5">
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-ember-500 to-crimson-600 shadow-glow">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2C12 2 6 9.5 6 14.5C6 18.09 8.69 21 12 21C15.31 21 18 18.09 18 14.5C18 9.5 12 2 12 2Z"
                fill="white"
                fillOpacity="0.95"
              />
            </svg>
          </span>
          <div>
            <div className="font-display text-[17px] font-semibold leading-tight tracking-tight text-white">
              ARGUS
            </div>
            <div className="label -mt-0.5">Autonomous Urban Heat Intelligence</div>
          </div>
        </Link>
        {cityId && (
          <Link
            to="/"
            className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400 transition hover:text-slate-200"
          >
            ← All Cities
          </Link>
        )}
      </div>

      <div className="flex items-center gap-6">
        {city && (
          <div className="text-right">
            <div className="label">Monitoring</div>
            <div className="text-sm font-medium text-slate-300">
              {city.name}, {city.state}
            </div>
          </div>
        )}
        {cityId && (
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5">
            <span
              className={`h-2 w-2 flex-none rounded-full ${status?.running ? "bg-ember-400 animate-pulse" : "bg-emerald-400"}`}
            />
            <span className="text-xs font-medium text-slate-300">
              {status?.running ? status.progress || "Scanning…" : "Live"}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}

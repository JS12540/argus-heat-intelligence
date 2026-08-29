import { useState } from "react";
import { api } from "../../api/client";
import type { AnalyticType, FilterType, QueryFeature, QueryResult } from "../../types";

const HOURS = Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, "0")}:00`);

const FILTER_TYPES: { value: FilterType; label: string; hint: string }[] = [
  { value: 3, label: "Single Day (recommended)", hint: "full day, 00:00–23:59 — most reliable" },
  { value: 1, label: "Single Hour", hint: "one hour, on the hour — often returns no data" },
  { value: 2, label: "Range of Hours", hint: "same day, start–end hour" },
  { value: 4, label: "Range of Days", hint: "up to 1 month" },
];

const ANALYTIC_TYPES: { value: AnalyticType; label: string; hint: string }[] = [
  { value: "tcm", label: "Temperature", hint: "snapshot, °F per tile" },
  { value: "exceedance", label: "Exceedance", hint: "total hours above/below threshold" },
  { value: "persistence", label: "Persistence", hint: "longest unbroken streak, in hours" },
  { value: "time_of_measure", label: "Time of Measure", hint: "hour of day (UTC) peak temp occurred" },
];

function defaultDate(): string {
  // FortyGuard has a confirmed ~1-day publish lag — "today" reliably returns n_cells: 0.
  // Default to yesterday so a first-time Run Query is far more likely to show real data.
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="label mb-1.5">{label}</div>
      {children}
    </label>
  );
}

const selectClass =
  "w-full rounded-lg border border-white/10 bg-obsidian-900 px-3 py-2 text-sm text-slate-200 outline-none transition focus:border-ember-500/50";

export function QueryPanel({ cityId }: { cityId: string }) {
  const [open, setOpen] = useState(true);
  const [filterType, setFilterType] = useState<FilterType>(3); // Single Day — far more reliable than Single Hour
  const [analyticType, setAnalyticType] = useState<AnalyticType>("tcm");
  const [startDate, setStartDate] = useState(defaultDate());
  const [startTime, setStartTime] = useState("14:00");
  const [endTime, setEndTime] = useState("18:00");
  const [endDate, setEndDate] = useState(defaultDate());
  const [thresholdF, setThresholdF] = useState(104);
  const [direction, setDirection] = useState<"above" | "below">("above");
  const [granularity, setGranularity] = useState<60 | 80 | 100>(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);

  const needsThreshold = analyticType === "exceedance" || analyticType === "persistence";

  async function handleRun() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.runQuery({
        city_id: cityId,
        filter_type: filterType,
        start_date: startDate,
        start_time: filterType === 1 || filterType === 2 ? startTime : undefined,
        end_time: filterType === 2 ? endTime : undefined,
        end_date: filterType === 4 ? endDate : undefined,
        analytic_type: analyticType,
        threshold_f: needsThreshold ? thresholdF : undefined,
        direction: needsThreshold ? direction : undefined,
        granularity,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
      >
        <div>
          <h2 className="font-display text-sm font-semibold text-white">Custom Query</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Direct FortyGuard access — any filter/analytic combination for this city.
          </p>
          <p className="mt-0.5 text-[11px] text-slate-600">
            Quick check before running a full scan — confirms data exists here, doesn't detect anomalies.
          </p>
        </div>
        <span className={`text-slate-500 transition-transform ${open ? "rotate-180" : ""}`}>▾</span>
      </button>

      {open && (
        <div className="fade-in border-t border-white/[0.06] p-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="Filter Type">
              <select
                className={selectClass}
                value={filterType}
                onChange={(e) => setFilterType(Number(e.target.value) as FilterType)}
              >
                {FILTER_TYPES.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
              <div className="mt-1 text-[11px] text-slate-500">
                {FILTER_TYPES.find((f) => f.value === filterType)?.hint}
              </div>
            </Field>

            <Field label="Analytic Type">
              <select
                className={selectClass}
                value={analyticType}
                onChange={(e) => setAnalyticType(e.target.value as AnalyticType)}
              >
                {ANALYTIC_TYPES.map((a) => (
                  <option key={a.value} value={a.value}>
                    {a.label}
                  </option>
                ))}
              </select>
              <div className="mt-1 text-[11px] text-slate-500">
                {ANALYTIC_TYPES.find((a) => a.value === analyticType)?.hint}
              </div>
            </Field>

            <Field label="Start Date">
              <input
                type="date"
                className={selectClass}
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </Field>

            <Field label="Granularity">
              <select
                className={selectClass}
                value={granularity}
                onChange={(e) => setGranularity(Number(e.target.value) as 60 | 80 | 100)}
              >
                <option value={60}>60m</option>
                <option value={80}>80m</option>
                <option value={100}>100m</option>
              </select>
            </Field>

            {(filterType === 1 || filterType === 2) && (
              <Field label="Start Time (UTC, on the hour)">
                <select className={selectClass} value={startTime} onChange={(e) => setStartTime(e.target.value)}>
                  {HOURS.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </Field>
            )}

            {filterType === 2 && (
              <Field label="End Time (UTC, on the hour)">
                <select className={selectClass} value={endTime} onChange={(e) => setEndTime(e.target.value)}>
                  {HOURS.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </Field>
            )}

            {filterType === 4 && (
              <Field label="End Date">
                <input
                  type="date"
                  className={selectClass}
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </Field>
            )}

            {needsThreshold && (
              <>
                <Field label="Threshold (°F)">
                  <input
                    type="number"
                    className={selectClass}
                    value={thresholdF}
                    onChange={(e) => setThresholdF(Number(e.target.value))}
                  />
                </Field>
                <Field label="Direction">
                  <select
                    className={selectClass}
                    value={direction}
                    onChange={(e) => setDirection(e.target.value as "above" | "below")}
                  >
                    <option value="above">Above</option>
                    <option value="below">Below</option>
                  </select>
                </Field>
              </>
            )}
          </div>

          <button
            onClick={handleRun}
            disabled={loading}
            className="mt-5 rounded-lg bg-gradient-to-br from-ember-500 to-crimson-600 px-4 py-2 text-sm font-semibold text-white shadow-glow transition hover:brightness-110 disabled:opacity-60"
          >
            {loading ? "Querying FortyGuard…" : "Run Query"}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-crimson-500/30 bg-crimson-500/10 p-3 text-sm text-crimson-300">
              {error}
            </div>
          )}

          {result && <QueryResultView result={result} />}
        </div>
      )}
    </div>
  );
}

function QueryResultView({ result }: { result: QueryResult }) {
  const stats = result.result.stats_data as Record<string, unknown> | undefined;
  const features = result.result.map_data?.features ?? [];
  const isTemperature = result.analytic_type === "tcm";

  // tcm nests its numbers under stats_data.temperature_stats; exceedance/persistence/
  // time_of_measure put them flat on stats_data. Two different shapes — reading the wrong
  // one silently renders 32.0°F (0°C) for everything instead of the real values.
  const tempStats = stats?.temperature_stats as Record<string, number> | undefined;
  const nCells = (isTemperature ? undefined : (stats?.n_cells as number | undefined)) ?? features.length;

  if (!stats || nCells === 0 || (isTemperature && !tempStats)) {
    return (
      <div className="mt-4 rounded-lg border border-amber-500/25 bg-amber-500/10 p-3 text-sm text-amber-200">
        No data returned (n_cells: 0). Not an error — FortyGuard has no processed data for this
        exact query. Try a date at least 1 day in the past.
      </div>
    );
  }

  const toF = (c: number) => (c * 9) / 5 + 32;

  return (
    <div className="mt-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {isTemperature ? (
          <>
            <Stat label="Min" value={`${toF(tempStats!.minimum).toFixed(1)}°F`} />
            <Stat label="Max" value={`${toF(tempStats!.maximum).toFixed(1)}°F`} />
            <Stat label="Mean" value={`${toF(tempStats!.mean).toFixed(1)}°F`} />
            <Stat label="Tiles" value={String(nCells)} />
          </>
        ) : (
          <>
            <Stat label="Min" value={`${stats.min ?? "—"} ${stats.units ?? ""}`} />
            <Stat label="Max" value={`${stats.max ?? "—"} ${stats.units ?? ""}`} />
            <Stat label="Mean" value={`${Number(stats.mean ?? 0).toFixed(1)} ${stats.units ?? ""}`} />
            <Stat label="Tiles" value={String(nCells)} />
          </>
        )}
      </div>
      <TileHeatmap features={features} analyticType={result.analytic_type} />
    </div>
  );
}

const HEATMAP_W = 420;
const HEATMAP_H = 260;
const HEATMAP_PAD = 12;

function featureValue(f: QueryFeature, isTemperature: boolean): number {
  const p = f.properties;
  return isTemperature ? p.average_temperature : p.value;
}

function featureCentroid(f: QueryFeature): [number, number] {
  const ring = f.geometry.coordinates[0];
  const lon = ring.reduce((s, c) => s + c[0], 0) / ring.length;
  const lat = ring.reduce((s, c) => s + c[1], 0) / ring.length;
  return [lon, lat];
}

/** Renders the actual returned tiles as a colored grid — this is the real heatmap Custom
 * Query fetches but previously only summarized as four numbers. */
function TileHeatmap({ features, analyticType }: { features: QueryFeature[]; analyticType: AnalyticType }) {
  if (features.length === 0) return null;
  const isTemperature = analyticType === "tcm";

  const points = features.map((f) => {
    const [lon, lat] = featureCentroid(f);
    return { lon, lat, value: featureValue(f, isTemperature) };
  });
  const lons = points.map((p) => p.lon);
  const lats = points.map((p) => p.lat);
  const values = points.map((p) => p.value);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minV = Math.min(...values), maxV = Math.max(...values);

  const project = (lon: number, lat: number): [number, number] => [
    HEATMAP_PAD + ((lon - minLon) / (maxLon - minLon || 1)) * (HEATMAP_W - 2 * HEATMAP_PAD),
    HEATMAP_H - HEATMAP_PAD - ((lat - minLat) / (maxLat - minLat || 1)) * (HEATMAP_H - 2 * HEATMAP_PAD),
  ];

  // Cool -> hot: blue through yellow to red (HSL hue 220 -> 0).
  const colorFor = (v: number) => `hsl(${220 - ((v - minV) / (maxV - minV || 1)) * 220}, 85%, 55%)`;
  const cellSize = Math.max(4, (Math.min(HEATMAP_W, HEATMAP_H) / Math.sqrt(points.length)) * 0.95);
  const toF = (c: number) => (c * 9) / 5 + 32;
  const formatValue = (v: number) => (isTemperature ? `${toF(v).toFixed(0)}°F` : v.toFixed(1));

  return (
    <div className="mt-4">
      <div className="label mb-2">Tile heatmap — {points.length} tiles returned</div>
      <svg
        viewBox={`0 0 ${HEATMAP_W} ${HEATMAP_H}`}
        className="w-full rounded-lg border border-white/[0.06] bg-obsidian-900"
      >
        {points.map((p, i) => {
          const [x, y] = project(p.lon, p.lat);
          return (
            <rect
              key={i}
              x={x - cellSize / 2}
              y={y - cellSize / 2}
              width={cellSize}
              height={cellSize}
              fill={colorFor(p.value)}
            >
              <title>{formatValue(p.value)}</title>
            </rect>
          );
        })}
      </svg>
      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
        <span>{formatValue(minV)} (coolest)</span>
        <span>{formatValue(maxV)} (hottest)</span>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
      <div className="label">{label}</div>
      <div className="mt-1 font-display text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";

interface DailyTemp {
  date: string;
  min_temp_f: number;
  max_temp_f: number;
  mean_temp_f: number;
  samples: number;
}

/**
 * 7-day temperature trend chart showing min/max/mean daily temperatures.
 * Visualizes heat waves and temperature patterns across time.
 */
export function TemperatureTrendChart({ cityId, cityName }: { cityId: string; cityName?: string }) {
  const [data, setData] = useState<DailyTemp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/cities/${cityId}/daily-temperatures?days=7`)
      .then((r) => r.json())
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cityId]);

  if (loading)
    return <div className="card flex h-80 items-center justify-center text-slate-400">Loading temperature data…</div>;

  if (error || data.length === 0)
    return <div className="card flex h-80 items-center justify-center text-slate-500">No 7-day data available</div>;

  // Convert F to C: (F - 32) × 5/9
  const fToC = (f: number) => Math.round(((f - 32) * 5) / 9 * 10) / 10;

  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    min_temp_c: fToC(d.min_temp_f),
    max_temp_c: fToC(d.max_temp_f),
    mean_temp_c: fToC(d.mean_temp_f),
    samples: d.samples,
  }));

  const minTemp = Math.min(...chartData.map((d) => d.min_temp_c));
  const maxTemp = Math.max(...chartData.map((d) => d.max_temp_c));

  // Heat thresholds (in Celsius)
  const SAFE_THRESHOLD = 28; // 82°F - comfortable
  const EXCESSIVE_THRESHOLD = 32; // 90°F - excessive heat warning
  const EXTREME_THRESHOLD = 35; // 95°F - extreme heat warning

  return (
    <div className="card space-y-4">
      <div>
        <h2 className="font-display text-lg font-semibold text-white">7-Day Temperature Trend</h2>
        <p className="mt-1 text-xs text-slate-500">{cityName} — min/max range and daily mean</p>
      </div>

      {/* Range + Mean Chart with Thresholds */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="gradMin" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradMax" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis dataKey="date" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" domain={[Math.floor(minTemp) - 2, Math.ceil(maxTemp) + 2]} label={{ value: "°C", angle: -90, position: "insideLeft" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid rgba(255,255,255,0.2)",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "#94a3b8" }}
            formatter={(value) => `${(value as number).toFixed(1)}°C`}
          />

          {/* Threshold reference lines */}
          <ReferenceLine y={SAFE_THRESHOLD} stroke="#10b981" strokeDasharray="5 5" opacity={0.5} label={{ value: "28°C Safe", position: "right", fill: "#10b981", fontSize: 11 }} />
          <ReferenceLine y={EXCESSIVE_THRESHOLD} stroke="#f59e0b" strokeDasharray="5 5" opacity={0.5} label={{ value: "32°C Excessive", position: "right", fill: "#f59e0b", fontSize: 11 }} />
          <ReferenceLine y={EXTREME_THRESHOLD} stroke="#ef4444" strokeDasharray="5 5" opacity={0.5} label={{ value: "35°C Extreme", position: "right", fill: "#ef4444", fontSize: 11 }} />

          <Legend />

          {/* Show range as area between min/max */}
          <Area
            type="monotone"
            dataKey="max_temp_c"
            name="Max Temperature"
            stroke="#ef4444"
            fill="url(#gradMax)"
            strokeWidth={2}
            dot={{ fill: "#ef4444", r: 4 }}
          />
          <Area
            type="monotone"
            dataKey="min_temp_c"
            name="Min Temperature"
            stroke="#3b82f6"
            fill="url(#gradMin)"
            strokeWidth={2}
            dot={{ fill: "#3b82f6", r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="mean_temp_c"
            name="Daily Mean"
            stroke="#fbbf24"
            strokeWidth={3}
            dot={{ fill: "#fbbf24", r: 5 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-2 border-t border-white/10 pt-4 text-center">
        <div>
          <div className="text-xs text-slate-500">7-Day Min</div>
          <div className="font-display text-sm font-semibold text-blue-400">{minTemp.toFixed(1)}°C</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">7-Day Max</div>
          <div className="font-display text-sm font-semibold text-red-400">{maxTemp.toFixed(1)}°C</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Avg Range</div>
          <div className="font-display text-sm font-semibold text-yellow-400">
            {((maxTemp - minTemp) / chartData.length).toFixed(1)}°C
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Samples</div>
          <div className="font-display text-sm font-semibold text-slate-300">{chartData.reduce((sum, d) => sum + d.samples, 0)}</div>
        </div>
      </div>

      {/* Threshold Context Only */}
      {chartData.length >= 2 && (
        <div className="border-t border-white/10 pt-4">
          {(() => {
            const lastMean = chartData[chartData.length - 1].mean_temp_c;

            // Threshold context
            let thresholdMsg = "";
            if (lastMean > EXTREME_THRESHOLD) {
              const above = (lastMean - EXTREME_THRESHOLD).toFixed(1);
              thresholdMsg = `🔴 EXTREME: ${above}°C above safe threshold`;
            } else if (lastMean > EXCESSIVE_THRESHOLD) {
              const above = (lastMean - EXCESSIVE_THRESHOLD).toFixed(1);
              thresholdMsg = `🟠 EXCESSIVE: ${above}°C above safe threshold`;
            } else if (lastMean > SAFE_THRESHOLD) {
              const above = (lastMean - SAFE_THRESHOLD).toFixed(1);
              thresholdMsg = `🟡 ELEVATED: ${above}°C above safe threshold`;
            } else {
              thresholdMsg = `🟢 SAFE: Within comfortable range`;
            }

            return (
              <div className="text-center text-sm font-semibold text-slate-200 bg-slate-800/50 rounded p-2">
                {thresholdMsg}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}

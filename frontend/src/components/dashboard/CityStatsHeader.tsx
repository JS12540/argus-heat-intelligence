import { useEffect, useState } from "react";

interface DailyTemp {
  date: string;
  min_temp_f: number;
  max_temp_f: number;
  mean_temp_f: number;
  samples: number;
}

interface Props {
  cityId: string;
  cityName: string;
  anomalyCount: number;
  maxSeverity?: string;
  lastScanMeta?: {
    cells_with_data: number;
    cells_scanned: number;
    city_exceedance_zone_count?: number;
  };
}

export function CityStatsHeader({ cityId, cityName, anomalyCount, maxSeverity, lastScanMeta }: Props) {
  const [avgTemp, setAvgTemp] = useState<number | null>(null);

  useEffect(() => {
    async function fetchTempData() {
      try {
        const res = await fetch(`/api/cities/${cityId}/daily-temperatures?days=7`);
        if (res.ok) {
          const data: DailyTemp[] = await res.json();
          if (data && data.length > 0) {
            // Get latest day temperature
            const latest = data[data.length - 1];
            const temp = Math.round(latest.mean_temp_f);
            setAvgTemp(isNaN(temp) ? null : temp);
          }
        }
      } catch (error) {
        console.error("Failed to fetch temperature data:", error);
      }
    }

    if (cityId) {
      fetchTempData();
    }
  }, [cityId]);

  const getSeverityColor = (severity?: string) => {
    if (!severity) return "from-blue-600 to-blue-700";
    if (severity === "CRITICAL") return "from-red-600 to-red-700";
    if (severity === "HIGH") return "from-orange-600 to-orange-700";
    if (severity === "MEDIUM") return "from-yellow-600 to-yellow-700";
    return "from-green-600 to-green-700";
  };


  const getHeatAlert = () => {
    if (!avgTemp) return null;
    if (avgTemp >= 95) return { label: "EXTREME HEAT", color: "text-red-400" };
    if (avgTemp >= 90) return { label: "EXCESSIVE HEAT", color: "text-orange-400" };
    if (avgTemp >= 85) return { label: "ELEVATED HEAT", color: "text-yellow-400" };
    return null;
  };

  return (
    <div className={`rounded-xl border border-white/10 bg-gradient-to-br ${getSeverityColor(maxSeverity)} bg-opacity-5 p-6 backdrop-blur-sm shadow-lg`}>
      <div className="space-y-4">
        {/* Title and Status */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">{cityName}</h1>
            <p className="text-sm text-slate-400 mt-1">🎯 Thermal Risk Command Center</p>
          </div>
          {maxSeverity && (
            <div className={`px-4 py-2 rounded-xl border text-sm font-bold shadow-lg
              ${maxSeverity === "CRITICAL" ? "bg-red-500/30 border-red-400 text-red-200" : ""}
              ${maxSeverity === "HIGH" ? "bg-orange-500/30 border-orange-400 text-orange-200" : ""}
              ${maxSeverity === "MEDIUM" ? "bg-yellow-500/30 border-yellow-400 text-yellow-200" : ""}
              ${!["CRITICAL", "HIGH", "MEDIUM"].includes(maxSeverity || "") ? "bg-green-500/30 border-green-400 text-green-200" : ""}
            `}>
              ⚠️ {maxSeverity}
            </div>
          )}
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Temperature */}
          <div className="rounded-lg bg-white/5 border border-white/10 p-3 hover:border-white/20 hover:shadow-md transition">
            <p className="text-xs text-slate-400 font-semibold">🌡️ Current Temp</p>
            <div className="mt-2">
              {avgTemp !== null ? (
                <span className="text-3xl font-bold text-white">{avgTemp}°F</span>
              ) : (
                <span className="text-sm text-slate-400">Loading…</span>
              )}
            </div>
            {getHeatAlert() && (
              <div className={`text-xs mt-2 font-semibold ${getHeatAlert()!.color}`}>
                ⚠️ {getHeatAlert()!.label}
              </div>
            )}
          </div>

          {/* Anomalies */}
          <div className="rounded-lg bg-white/5 border border-white/10 p-3 hover:border-white/20 hover:shadow-md transition">
            <p className="text-xs text-slate-400 font-semibold">🚨 Active Anomalies</p>
            <p className={`text-3xl font-bold mt-2 ${anomalyCount > 0 ? "text-red-400" : "text-green-400"}`}>
              {anomalyCount}
            </p>
          </div>

          {/* Data Coverage */}
          {lastScanMeta && (
            <div className="rounded-lg bg-white/5 border border-white/10 p-3 hover:border-white/20 hover:shadow-md transition">
              <p className="text-xs text-slate-400 font-semibold">📡 Data Coverage</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">
                {lastScanMeta.cells_with_data}/{lastScanMeta.cells_scanned}
              </p>
            </div>
          )}

          {/* Risk Zones */}
          {lastScanMeta?.city_exceedance_zone_count !== undefined && (
            <div className="rounded-lg bg-white/5 border border-white/10 p-3 hover:border-white/20 hover:shadow-md transition">
              <p className="text-xs text-slate-400 font-semibold">⚡ Risk Zones</p>
              <p className={`text-3xl font-bold mt-2 ${(lastScanMeta.city_exceedance_zone_count || 0) > 0 ? "text-orange-400" : "text-green-400"}`}>
                {lastScanMeta.city_exceedance_zone_count || 0}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

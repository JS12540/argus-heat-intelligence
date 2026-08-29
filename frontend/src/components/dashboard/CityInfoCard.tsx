import { useEffect, useState } from "react";

interface City {
  id: string;
  name: string;
  state: string;
  anomaly_count?: number;
  max_severity?: string;
  last_scan_at?: string;
}

interface CityStats {
  anomaly_count: number;
  max_severity: string | null;
  last_scan_at: string | null;
  avg_temp?: number;
  cells_with_data?: number;
}

interface Props {
  city: City;
  compact?: boolean;
}

export function CityInfoCard({ city, compact = false }: Props) {
  const [stats, setStats] = useState<CityStats>({
    anomaly_count: city.anomaly_count || 0,
    max_severity: city.max_severity || null,
    last_scan_at: city.last_scan_at || null,
  });

  const getSeverityColor = (severity: string | null) => {
    if (!severity) return "text-slate-400";
    if (severity === "CRITICAL") return "text-red-400";
    if (severity === "HIGH") return "text-orange-400";
    if (severity === "MEDIUM") return "text-yellow-400";
    return "text-green-400";
  };

  const getSeverityBg = (severity: string | null) => {
    if (!severity) return "bg-slate-500/20";
    if (severity === "CRITICAL") return "bg-red-500/20 border-red-500/30";
    if (severity === "HIGH") return "bg-orange-500/20 border-orange-500/30";
    if (severity === "MEDIUM") return "bg-yellow-500/20 border-yellow-500/30";
    return "bg-green-500/20 border-green-500/30";
  };

  const formatLastScan = (date: string | null) => {
    if (!date) return "Never scanned";
    const d = new Date(date);
    const now = new Date();
    const hours = Math.round((now.getTime() - d.getTime()) / (1000 * 60 * 60));
    if (hours < 1) return "Scanning now…";
    if (hours === 1) return "1 hour ago";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.round(hours / 24);
    if (days === 1) return "Yesterday";
    return `${days}d ago`;
  };

  if (compact) {
    return (
      <div className="rounded-lg bg-slate-900/50 border border-slate-700/50 p-3 hover:border-slate-600 transition">
        <div className="text-sm font-semibold text-white">{city.name}</div>
        <div className="text-xs text-slate-400 mt-1">{city.state}</div>
        {stats.anomaly_count > 0 && (
          <div className={`mt-2 text-xs font-semibold ${getSeverityColor(stats.max_severity)}`}>
            {stats.anomaly_count} anomal{stats.anomaly_count === 1 ? "y" : "ies"}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`rounded-xl border p-4 space-y-3 ${getSeverityBg(stats.max_severity)} transition`}>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">{city.name}</h3>
          <p className="text-sm text-slate-400">{city.state}</p>
        </div>
        {stats.max_severity && (
          <div className={`px-3 py-1 rounded-full text-xs font-bold border ${getSeverityColor(stats.max_severity)} border-current`}>
            {stats.max_severity}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/10">
        <div>
          <p className="text-xs text-slate-400">Active Anomalies</p>
          <p className="text-2xl font-bold text-white mt-1">{stats.anomaly_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Last Scan</p>
          <p className="text-sm font-medium text-slate-300 mt-1">{formatLastScan(stats.last_scan_at)}</p>
        </div>
      </div>

      <div className="text-xs text-slate-400 pt-2 border-t border-white/10">
        Hover over cities on the map for real-time updates
      </div>
    </div>
  );
}

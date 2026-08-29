import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { SEVERITY_COLOR } from "../constants/severityColors";
import { CONUS_BOUNDS, CONUS_OUTLINE } from "../data/usOutline";
import { api } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { usePolling } from "../hooks/usePolling";
import type { City } from "../types";

const WIDTH = 960;
const HEIGHT = 460;
const MAP_HEIGHT = 380; // leaves room at the bottom for the AK/HI insets

// Alaska and Hawaii sit nowhere near the CONUS bounding box on a real map, so — same
// convention every US map uses — they get small labeled inset boxes instead of being
// projected onto the main outline.
const INSET_CITY_IDS = new Set(["anchorage-ak", "honolulu-hi"]);

function project(lon: number, lat: number): [number, number] {
  const x = ((lon - CONUS_BOUNDS.minLon) / (CONUS_BOUNDS.maxLon - CONUS_BOUNDS.minLon)) * WIDTH;
  const y = MAP_HEIGHT - ((lat - CONUS_BOUNDS.minLat) / (CONUS_BOUNDS.maxLat - CONUS_BOUNDS.minLat)) * MAP_HEIGHT;
  return [x, y];
}

function markerColor(city: City): string {
  if (!city.max_severity) return "#3f4759"; // never scanned — neutral
  return SEVERITY_COLOR[city.max_severity];
}

function CityMarker({ city, x, y, onClick }: { city: City; x: number; y: number; onClick: () => void }) {
  const [hovering, setHovering] = useState(false);
  const scanned = city.last_scan_at != null;
  const r = scanned ? 5 + Math.min(city.anomaly_count, 6) : 4;
  const urgent = city.max_severity === "CRITICAL" || city.max_severity === "HIGH";

  const formatLastScan = (date: string | null) => {
    if (!date) return "Never scanned";
    const d = new Date(date);
    const now = new Date();
    const hours = Math.round((now.getTime() - d.getTime()) / (1000 * 60 * 60));
    if (hours < 1) return "Just now";
    if (hours === 1) return "1 hour ago";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.round(hours / 24);
    return `${days}d ago`;
  };

  return (
    <g
      className="cursor-pointer transition-transform hover:scale-125"
      onClick={onClick}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      style={{ transformOrigin: `${x}px ${y}px` }}
    >
      {scanned && city.max_severity && (
        <circle cx={x} cy={y} r={r + 10} fill={markerColor(city)} opacity={0.18} />
      )}
      {urgent && (
        <circle cx={x} cy={y} r={r} fill="none" stroke={markerColor(city)} strokeWidth="1.5" className="pulse-ring" />
      )}
      <circle
        cx={x}
        cy={y}
        r={r}
        fill={markerColor(city)}
        stroke="rgba(7,9,13,0.9)"
        strokeWidth="1.5"
        opacity={scanned ? 1 : 0.55}
      />
      <text x={x} y={y - r - 5} textAnchor="middle" fontSize="9" fill="#94a3b8" fontFamily="monospace">
        {city.state}
      </text>

      {/* Hover Tooltip */}
      {hovering && (
        <g>
          {/* Tooltip background box */}
          <rect
            x={x - 65}
            y={y - 90}
            width="130"
            height="80"
            rx="6"
            fill="rgba(15, 23, 42, 0.95)"
            stroke={markerColor(city)}
            strokeWidth="1.5"
          />
          {/* City name */}
          <text x={x} y={y - 70} textAnchor="middle" fontSize="11" fill="white" fontWeight="bold" fontFamily="sans-serif">
            {city.name}
          </text>
          {/* Severity and anomalies */}
          <text x={x} y={y - 55} textAnchor="middle" fontSize="9" fill="#cbd5e1" fontFamily="monospace">
            {city.max_severity ? `${city.max_severity} • ${city.anomaly_count} anomal` : "Not scanned"}
          </text>
          {/* Last scan */}
          <text x={x} y={y - 42} textAnchor="middle" fontSize="8" fill="#94a3b8" fontFamily="monospace">
            {formatLastScan(city.last_scan_at)}
          </text>
          {/* Click hint */}
          <text x={x} y={y - 28} textAnchor="middle" fontSize="7" fill="#64748b" fontStyle="italic" fontFamily="monospace">
            Click to open Command Center
          </text>
        </g>
      )}
    </g>
  );
}

export function NationalOverview() {
  const navigate = useNavigate();
  const { data: cities, loading } = usePolling(api.cities, 30_000);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Loading monitored cities…" />
      </div>
    );
  }

  const list = cities ?? [];
  const conusCities = list.filter((c) => !INSET_CITY_IDS.has(c.id));
  const insetCities = list.filter((c) => INSET_CITY_IDS.has(c.id));

  const scannedCount = list.filter((c) => c.last_scan_at).length;
  const totalAnomalies = list.reduce((sum, c) => sum + c.anomaly_count, 0);
  const criticalCount = list.filter((c) => c.max_severity === "CRITICAL").length;

  const outlinePoints = CONUS_OUTLINE.map(([lon, lat]) => project(lon, lat).join(",")).join(" ");

  return (
    <div className="fade-in space-y-6 p-8">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-white">National Overview</h1>
        <p className="mt-1 text-sm text-slate-500">
          Discovering thermal risk across the US before anyone knows where to look. Click any city to open
          its Command Center and run a scan.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          ["Monitored Cities", list.length, undefined],
          ["Scanned", scannedCount, undefined],
          ["Active Anomalies", totalAnomalies, totalAnomalies > 0 ? "text-ember-400" : undefined],
          ["Critical", criticalCount, criticalCount > 0 ? "text-crimson-400" : undefined],
        ].map(([label, value, accent]) => (
          <div key={label as string} className="card card-interactive p-5">
            <div className="label">{label}</div>
            <div className={`mt-1 font-display text-2xl font-semibold ${accent ?? "text-white"}`}>{value}</div>
          </div>
        ))}
      </div>

      <div className="card relative overflow-hidden p-4">
        <div className="absolute right-5 top-5 z-10 flex items-center gap-3 rounded-full border border-white/10 bg-obsidian-900/80 px-3 py-1.5 backdrop-blur">
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
            <span key={sev} className="flex items-center gap-1.5 text-[10px] font-medium text-slate-400">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: SEVERITY_COLOR[sev] }} />
              {sev}
            </span>
          ))}
        </div>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full">
          <defs>
            <pattern id="national-grid" width="24" height="24" patternUnits="userSpaceOnUse">
              <path d="M 24 0 L 0 0 0 24" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
            </pattern>
            <radialGradient id="map-glow" cx="50%" cy="35%" r="65%">
              <stop offset="0%" stopColor="rgba(245,148,58,0.06)" />
              <stop offset="100%" stopColor="transparent" />
            </radialGradient>
          </defs>
          <rect width={WIDTH} height={HEIGHT} fill="url(#national-grid)" />
          <rect width={WIDTH} height={HEIGHT} fill="url(#map-glow)" />

          <polygon
            points={outlinePoints}
            fill="rgba(245,148,58,0.05)"
            stroke="rgba(255,255,255,0.16)"
            strokeWidth="1.5"
          />

          {conusCities.map((city) => {
            const [lon, lat] = [city.polygon[0][0], city.polygon[0][1]];
            const [x, y] = project(lon, lat);
            return (
              <CityMarker key={city.id} city={city} x={x} y={y} onClick={() => navigate(`/cities/${city.id}`)} />
            );
          })}

          {/* Alaska / Hawaii insets, bottom-left — standard map convention */}
          <rect x={8} y={MAP_HEIGHT + 12} width={110} height={64} rx={8} fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" />
          <rect x={130} y={MAP_HEIGHT + 12} width={110} height={64} rx={8} fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" />
          {insetCities.map((city, i) => (
            <CityMarker
              key={city.id}
              city={city}
              x={8 + 55 + i * 122}
              y={MAP_HEIGHT + 44}
              onClick={() => navigate(`/cities/${city.id}`)}
            />
          ))}
        </svg>
      </div>
    </div>
  );
}

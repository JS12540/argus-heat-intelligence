import { useNavigate } from "react-router-dom";
import { SEVERITY_COLOR } from "../../constants/severityColors";
import type { Anomaly, ScanCell } from "../../types";

/** Cool -> hot: blue through yellow to red, scaled within this grid's own min/max. */
function heatColor(temp: number, min: number, max: number): string {
  const t = (temp - min) / (max - min || 1);
  return `hsl(${220 - t * 220}, 85%, 50%)`;
}

/** Lightweight SVG heat-grid — no external map SDK / API key required. Shows the raw
 * per-cell temperature reading from the last scan (even when 0 anomalies were found —
 * "calm" and "nothing scanned yet" are different states and should look different),
 * plus anomaly markers on top where the composite score crossed the threshold. */
export function CityGrid({
  anomalies,
  cells = [],
  cityName,
}: {
  anomalies: Anomaly[];
  cells?: ScanCell[];
  cityName?: string;
}) {
  const navigate = useNavigate();

  // Fallback bounds (0/1) apply ONLY when there's no real data at all — Math.min/max would
  // otherwise always include them as extra candidates, corrupting a real (small) range: e.g.
  // Burlington's real longitude ~-73.2 got Math.max(...lons, 1) => 1, turning a ~0.02° spread
  // into a fake ~74° one and collapsing all 9 cells onto the same pixel.
  const lats = [...anomalies.map((a) => a.latitude), ...cells.map((c) => c.lat)];
  const lons = [...anomalies.map((a) => a.longitude), ...cells.map((c) => c.lon)];
  const minLat = lats.length ? Math.min(...lats) : 0;
  const maxLat = lats.length ? Math.max(...lats) : 1;
  const minLon = lons.length ? Math.min(...lons) : 0;
  const maxLon = lons.length ? Math.max(...lons) : 1;
  const cellTemps = cells.map((c) => c.temperature_f);
  const minTemp = cellTemps.length ? Math.min(...cellTemps) : 0;
  const maxTemp = cellTemps.length ? Math.max(...cellTemps) : 1;

  // Top 90px reserved for the "Live Thermal Grid" header — the north-most cell (highest lat)
  // still lands top-left where the header sits, so this needs real clearance, not just a
  // small offset, regardless of which corner of the city's bounding box it falls in.
  const toXY = (lat: number, lon: number) => {
    const x = 40 + ((lon - minLon) / (maxLon - minLon || 1)) * 520;
    const y = 330 - ((lat - minLat) / (maxLat - minLat || 1)) * 240;
    return [x, y];
  };

  return (
    <div className="card relative h-full overflow-hidden">
      <div className="absolute left-5 top-4 z-10">
        <div className="label">Live Thermal Grid</div>
        <div className="font-display text-sm font-semibold text-white">{cityName ?? "—"}</div>
      </div>
      <svg viewBox="0 0 600 360" className="h-full w-full">
        <defs>
          <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.035)" strokeWidth="1" />
          </pattern>
          {Object.entries(SEVERITY_COLOR).map(([sev, color]) => (
            <radialGradient key={sev} id={`glow-${sev}`}>
              <stop offset="0%" stopColor={color} stopOpacity="0.55" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </radialGradient>
          ))}
        </defs>
        <rect width="600" height="360" fill="url(#grid)" />

        {cells.map((c, i) => {
          const [x, y] = toXY(c.lat, c.lon);
          return (
            <g key={i}>
              <rect
                x={x - 28}
                y={y - 28}
                width={56}
                height={56}
                fill={heatColor(c.temperature_f, minTemp, maxTemp)}
                opacity={0.5}
                rx={6}
              />
              <text x={x} y={y + 3} textAnchor="middle" fontSize="9" fill="#e2e8f0" fontFamily="monospace">
                {c.temperature_f.toFixed(0)}°F
              </text>
            </g>
          );
        })}

        {anomalies.map((a) => {
          const [x, y] = toXY(a.latitude, a.longitude);
          const r = 18 + a.composite_score / 3;
          return (
            <g
              key={a.id}
              className="cursor-pointer"
              onClick={() => navigate(`/incidents/${a.id}`)}
            >
              <circle cx={x} cy={y} r={r} fill={`url(#glow-${a.severity})`} />
              <circle
                cx={x}
                cy={y}
                r={5}
                fill={SEVERITY_COLOR[a.severity]}
                stroke="rgba(7,9,13,0.9)"
                strokeWidth="2"
              />
              <text x={x} y={y - r - 6} textAnchor="middle" fontSize="10" fill="#cbd5e1" fontFamily="monospace">
                {a.temperature_f.toFixed(0)}°F
              </text>
            </g>
          );
        })}

        {anomalies.length === 0 && cells.length === 0 && (
          <text x="300" y="180" textAnchor="middle" fontSize="13" fill="#64748b">
            No scan yet — run a scan to populate the grid
          </text>
        )}
      </svg>
    </div>
  );
}

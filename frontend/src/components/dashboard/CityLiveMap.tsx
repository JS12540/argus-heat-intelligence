import { useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, Rectangle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { ScanCell } from "../../types";

/**
 * Real street map (OpenStreetMap tiles, no API key) with the live scan grid overlaid.
 * Each cell is labeled with its compass zone (North/Southeast/etc.) relative to the city
 * center, and colored against fixed danger thresholds — not relative to this scan's own
 * min/max, so red always means genuinely dangerous.
 */
export function CityLiveMap({
  cells,
  polygon,
  cityName,
}: {
  cells: ScanCell[];
  polygon: [number, number][];
  cityName?: string;
}) {
  // Smooth blue (cold) -> red (hot) gradient over a fixed absolute range, so color reflects
  // real danger — not just "hottest of whatever narrow range this scan happened to return."
  const COLD_F = 65;
  const HOT_F = 105;
  const BLUE: [number, number, number] = [59, 130, 246];
  const RED: [number, number, number] = [239, 68, 68];
  const cellColor = (tempF: number): string => {
    const t = Math.max(0, Math.min(1, (tempF - COLD_F) / (HOT_F - COLD_F)));
    const r = Math.round(BLUE[0] + (RED[0] - BLUE[0]) * t);
    const g = Math.round(BLUE[1] + (RED[1] - BLUE[1]) * t);
    const b = Math.round(BLUE[2] + (RED[2] - BLUE[2]) * t);
    return `rgb(${r}, ${g}, ${b})`;
  };

  const { centerLat, centerLon, labeled, hottest, coolest } = useMemo(() => {
    if (!cells || cells.length === 0) {
      return { centerLat: 0, centerLon: 0, labeled: [], hottest: null, coolest: null };
    }
    const centerLat = cells.reduce((s, c) => s + c.lat, 0) / cells.length;
    const centerLon = cells.reduce((s, c) => s + c.lon, 0) / cells.length;

    const zoneName = (lat: number, lon: number): string => {
      const dLat = lat - centerLat;
      const dLon = lon - centerLon;
      const ns = Math.abs(dLat) < 0.002 ? "" : dLat > 0 ? "North" : "South";
      const ew = Math.abs(dLon) < 0.002 ? "" : dLon > 0 ? "East" : "West";
      return ns + ew || "Center";
    };

    const labeled = cells.map((c) => ({ ...c, zone: zoneName(c.lat, c.lon) }));
    const hottest = labeled.reduce((a, b) => (b.temperature_f > a.temperature_f ? b : a));
    const coolest = labeled.reduce((a, b) => (b.temperature_f < a.temperature_f ? b : a));

    return { centerLat, centerLon, labeled, hottest, coolest };
  }, [cells]);

  if (!cells || cells.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-sm text-slate-400">
        No grid data yet — run a scan to see the live map
      </div>
    );
  }

  const aoiBounds: [number, number][] = polygon?.map(([lon, lat]) => [lat, lon]) ?? [];

  return (
    <div className="space-y-3">
      {hottest && coolest && (
        <div className="rounded border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300">
          Hottest zone: <span className="font-semibold text-white">{hottest.zone}</span> at{" "}
          <span className="font-semibold" style={{ color: cellColor(hottest.temperature_f) }}>{hottest.temperature_f.toFixed(0)}°F</span>
          {"  ·  "}Coolest: <span className="font-semibold text-white">{coolest.zone}</span> at{" "}
          <span className="font-semibold" style={{ color: cellColor(coolest.temperature_f) }}>{coolest.temperature_f.toFixed(0)}°F</span>
        </div>
      )}

      <div className="rounded-lg overflow-hidden border border-slate-700" style={{ height: 440 }}>
        <MapContainer center={[centerLat, centerLon]} zoom={13} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {aoiBounds.length > 0 && (
            <Rectangle bounds={aoiBounds} pathOptions={{ color: "#64748b", weight: 1, fillOpacity: 0 }} />
          )}
          {labeled.map((cell, i) => (
            <CircleMarker
              key={i}
              center={[cell.lat, cell.lon]}
              radius={18}
              pathOptions={{
                color: cellColor(cell.temperature_f),
                fillColor: cellColor(cell.temperature_f),
                fillOpacity: 0.55,
                weight: 2,
              }}
            >
              <Tooltip permanent direction="center" className="!bg-transparent !border-0 !shadow-none !text-white !font-semibold">
                {cell.temperature_f.toFixed(0)}°
              </Tooltip>
              <Tooltip direction="top" offset={[0, -18]}>
                {cell.zone} — {cell.temperature_f.toFixed(1)}°F
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 gap-4">
        <span className="whitespace-nowrap">{cityName}</span>
        <div className="flex items-center gap-2 flex-1 max-w-xs">
          <span className="text-blue-400 font-medium">Cold ({COLD_F}°F)</span>
          <div
            className="flex-1 h-2 rounded-full"
            style={{ background: `linear-gradient(to right, rgb(${BLUE.join(",")}), rgb(${RED.join(",")}))` }}
          />
          <span className="text-red-400 font-medium">Hot ({HOT_F}°F)</span>
        </div>
      </div>
    </div>
  );
}

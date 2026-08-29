import { useState } from "react";
import { CityLiveMap } from "./CityLiveMap";
import type { Anomaly } from "../../types";

interface Props {
  cityId: string;
  cityName: string;
  cells?: any[];
  polygon?: [number, number][];
  anomalies: Anomaly[];
  llmResponse?: string;
}

export function AnalysisPanel({ cityId, cityName, cells, polygon, anomalies, llmResponse }: Props) {
  const [activeTab, setActiveTab] = useState<"grid" | "insights">("grid");

  const cleanText = (text: string) => text?.replace(/\*\*|__|\*|~~|`/g, "").trim() || "";

  const parseInsights = () => {
    if (!llmResponse) return [];
    const lines = llmResponse.split("\n").filter((l) => l.trim());
    return lines.filter((l) => l.startsWith("-") || l.startsWith("•")).map(cleanText);
  };

  return (
    <div className="rounded-xl border border-slate-700 overflow-hidden bg-slate-900">
      {/* Tab Headers */}
      <div className="flex border-b border-slate-700">
        <button
          onClick={() => setActiveTab("grid")}
          className={`flex-1 px-5 py-3 text-sm font-medium transition ${
            activeTab === "grid"
              ? "border-b-2 border-slate-300 text-white"
              : "text-slate-500 hover:text-slate-300"
          }`}
        >
          Live Thermal Grid
        </button>
        <button
          onClick={() => setActiveTab("insights")}
          className={`flex-1 px-5 py-3 text-sm font-medium transition ${
            activeTab === "insights"
              ? "border-b-2 border-slate-300 text-white"
              : "text-slate-500 hover:text-slate-300"
          }`}
        >
          AI Deep Dive
        </button>
      </div>

      {/* Content */}
      <div className="p-5 min-h-[420px]">
        {activeTab === "grid" ? (
          cells && cells.length > 0 ? (
            <CityLiveMap cells={cells} polygon={polygon ?? []} cityName={cityName} />
          ) : (
            <div className="flex flex-col items-center justify-center h-80 text-slate-400 space-y-2">
              <p className="text-sm font-medium text-slate-300">No grid data yet</p>
              <p className="text-xs text-slate-500">Run a full scan to visualize grid cell temperatures</p>
            </div>
          )
        ) : (
          <div className="space-y-4">
            {llmResponse ? (
              <>
                <div className="prose prose-invert max-w-none text-sm">
                  <p className="text-slate-300 leading-relaxed">{cleanText(llmResponse.substring(0, 300))}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase">Key Recommendations</h4>
                  <ul className="space-y-2">
                    {parseInsights()
                      .slice(0, 5)
                      .map((insight, i) => (
                        <li key={i} className="text-xs text-slate-300 flex gap-2">
                          <span className="text-slate-500 min-w-fit">•</span>
                          <span>{insight.substring(0, 100)}</span>
                        </li>
                      ))}
                  </ul>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-80 text-slate-400">
                <p>Generate AI analysis to see emergency planning insights</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

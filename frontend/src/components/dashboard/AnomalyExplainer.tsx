import { useState } from "react";

export function AnomalyExplainer() {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="text-xs px-3 py-1.5 rounded-full border border-blue-500/40 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 transition"
      >
        ❓ What is an Anomaly?
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border-2 border-blue-500 rounded-xl max-w-md p-6 space-y-4">
            <div className="flex items-start justify-between">
              <h3 className="text-lg font-bold text-white">🔥 What is an Anomaly?</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white text-2xl">
                ×
              </button>
            </div>

            <div className="space-y-3 text-sm text-slate-300">
              <p>
                An <strong className="text-blue-300">anomaly</strong> is a grid cell where temperature is{" "}
                <strong className="text-red-300">dangerously hot AND abnormal</strong>.
              </p>

              <div className="bg-slate-800 border-l-4 border-blue-500 p-3 rounded space-y-2">
                <p className="font-semibold text-blue-300">3 Triggers:</p>
                <ul className="space-y-1 ml-3">
                  <li>🌡️ <strong>Too Hot</strong> — exceeds safe threshold (32°C+)</li>
                  <li>📊 <strong>Abnormal</strong> — deviates from baseline (z-score {"> 2"})</li>
                  <li>⚠️ <strong>Dangerous</strong> — wet-bulb {">27°C"} OR heat index {">40°C"}</li>
                </ul>
              </div>

              <div className="bg-green-950/40 border-l-4 border-green-500 p-3 rounded">
                <p className="font-semibold text-green-300 mb-1">✅ NOT an anomaly:</p>
                <p className="text-xs">Phoenix 38°C in July = expected</p>
              </div>

              <div className="bg-red-950/40 border-l-4 border-red-500 p-3 rounded">
                <p className="font-semibold text-red-300 mb-1">🚨 IS an anomaly:</p>
                <p className="text-xs">Phoenix 40°C on cool day = unexpected + dangerous</p>
              </div>

              <p className="text-xs text-slate-400 italic">
                Severity: CRITICAL (most dangerous) → HIGH → MEDIUM → LOW
              </p>
            </div>

            <button
              onClick={() => setOpen(false)}
              className="w-full px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

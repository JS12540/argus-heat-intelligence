import type { AgentStatus, Anomaly, City, QueryRequestPayload, QueryResult, ScanMeta } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init);
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  cities: () => request<City[]>("/cities"),
  triggerScan: (cityId: string) =>
    request<{ anomalies_found: number; anomalies: Anomaly[]; scan_meta: ScanMeta }>("/agent/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city_id: cityId }),
    }),
  agentStatus: (cityId: string) => request<AgentStatus>(`/agent/status?city_id=${cityId}`),
  anomalies: (cityId?: string) =>
    request<Anomaly[]>(cityId ? `/anomalies?city_id=${cityId}` : "/anomalies"),
  anomaly: (id: string) => request<Anomaly>(`/anomalies/${id}`),
  runQuery: (payload: QueryRequestPayload) =>
    request<QueryResult>("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};

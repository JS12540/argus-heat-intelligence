import { api } from "../api/client";
import { usePolling } from "./usePolling";

export function useAnomalies(cityId: string, intervalMs = 10_000) {
  return usePolling(() => api.anomalies(cityId), intervalMs);
}

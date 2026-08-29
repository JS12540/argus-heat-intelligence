export type Severity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface AnomalySignals {
  who_band: string;
  z_score: number;
  rate_of_change_f_per_hr: number;
  spatial_anomaly_f: number;
  exceeds_danger_threshold?: boolean;
  city_exceedance_zone_count?: number | null;
}

export interface Investigation {
  hours_above_threshold: number; // persistence: longest unbroken streak
  exceedance_hours_total: number | null; // exceedance: total hours over threshold
  peak_hour_utc: number | null; // time_of_measure: hour of day (0-23 UTC) peak temp occurred
  trend: "WORSENING" | "STABLE" | string;
  heat_index_f: number | null;
  apparent_temperature_f: number | null;
  wet_bulb_temperature_f: number | null;
  humidity_percent: number | null;
  air_quality_index: number | null;
  surface_composition: Record<string, number> | null;
  contextual_factors: string[];
}

export interface RiskedInfrastructure {
  type: string;
  name: string;
  distance_m: number;
  impact_score: number;
  risk: Severity;
  reason: string;
}

export interface ImpactAssessment {
  total_infrastructure_at_risk: number;
  risk_ranking: RiskedInfrastructure[];
  cooling_assets_nearby: RiskedInfrastructure[];
}

export interface RecommendedAction {
  rank: number;
  action: string;
  target: string;
  urgency: "IMMEDIATE" | "WITHIN_1_HOUR" | "WITHIN_4_HOURS" | "NEXT_DAY" | string;
  expected_impact: string;
}

export interface ResponsePlan {
  actions: RecommendedAction[];
  generated_at: string;
}

export interface Anomaly {
  id: string;
  city_id: string;
  city_name: string;
  zone_name: string;
  latitude: number;
  longitude: number;
  temperature_f: number;
  severity: Severity;
  composite_score: number;
  signals: AnomalySignals;
  stage: string;
  detected_at: string;
  investigation: Investigation | null;
  impact_assessment: ImpactAssessment | null;
  response_plan: ResponsePlan | null;
  updated_at: string;
}

export interface ScanCell {
  lat: number;
  lon: number;
  temperature_f: number;
}

export interface ScanMeta {
  cells_scanned: number;
  cells_with_data: number; // < cells_scanned means FortyGuard returned no data for some cells
  city_exceedance_zone_count: number | null;
  city_persistence_hours: number | null;
  demo_mode: boolean; // true when no FORTYGUARD_API_KEY is set — cells_with_data is expected to be 0
  cells: ScanCell[]; // every grid cell's real reading, regardless of anomaly status
}

export interface AgentStatus {
  running: boolean;
  last_scan_at: string | null;
  progress?: string; // human-readable step, e.g. "DISCOVER: scanning cell 3/9" — a real scan takes minutes
  last_scan_meta?: ScanMeta | null;
}

export type FilterType = 1 | 2 | 3 | 4;
export type AnalyticType = "tcm" | "exceedance" | "persistence" | "time_of_measure";

export interface QueryRequestPayload {
  city_id: string;
  filter_type: FilterType;
  start_date: string;
  start_time?: string;
  end_time?: string;
  end_date?: string;
  analytic_type: AnalyticType;
  threshold_f?: number;
  direction?: "above" | "below";
  granularity?: 60 | 80 | 100;
}

export interface QueryFeature {
  properties: Record<string, number>;
  geometry: { type: "Polygon"; coordinates: [number, number][][] };
}

export interface QueryResult {
  city_id: string;
  analytic_type: AnalyticType;
  result: {
    map_data?: { features: QueryFeature[] };
    stats_data?: Record<string, unknown>;
  };
}

export interface City {
  id: string;
  name: string;
  state: string;
  polygon: [number, number][];
  anomaly_count: number;
  max_severity: Severity | null;
  last_scan_at: string | null;
}

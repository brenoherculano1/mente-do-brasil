import type { MetricId } from "@/types/api";

export type Anchor = Record<MetricId, number> & {
  year: number; need_window_start: number; need_window_end: number;
  capacity_competence: string; quality_flags: string[];
};
export type Timeline = { release_id: string; temporal_version: string; anchors: Anchor[] };
export const FAMILIES = {
  NEED_POSITION_UP: "Aumento da posição relativa de Need",
  CAPACITY_POSITION_DOWN: "Redução da posição relativa de Capacity",
  MISMATCH_POSITION_UP: "Aumento da posição relativa de Mismatch",
  NEED_COMPONENT_POSITION_UP: "Aumento em componente de Need",
  CAPACITY_COMPONENT_POSITION_DOWN: "Redução em componente de Capacity",
};
export type Change = Record<keyof typeof FAMILIES, boolean> & {
  health_region_code: string; health_region_name: string; uf: string;
  matched_change_families: number; delta_need_score: number;
  delta_capacity_score: number; delta_mismatch_score: number;
};
export type Changes = {
  records: Change[]; total_matching: number;
  geometry: GeoJSON.FeatureCollection | null;
};
export type Flow = {
  health_region_code: string; perspective: string;
  region: { health_region_name: string; uf: string; longitude: number; latitude: number };
  summary: { total_admissions: number | null; within_region_share: number | null;
    outflow_share: number | null; cross_state_outflow_share: number | null;
    nonsuppressed_destinations: number };
  connections: { health_region_code: string; health_region_name: string; uf: string;
    admissions: number | null; partial: boolean; longitude: number; latitude: number }[];
};

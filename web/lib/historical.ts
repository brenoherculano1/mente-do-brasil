import type { HealthRegionFeatureCollection, HealthRegionProfile, MetricId } from "@/types/api";

export const HISTORICAL_YEARS = [2022, 2023, 2024] as const;
export type HistoricalYear = typeof HISTORICAL_YEARS[number];

export function historicalYear(value?: string | string[]): HistoricalYear | null {
  if (value === undefined) return 2024;
  if (typeof value !== "string" || !HISTORICAL_YEARS.some((year) => String(year) === value)) return null;
  return Number(value) as HistoricalYear;
}

export type HistoricalRecord = Record<MetricId, number> & {
  year: HistoricalYear; health_region_code: string; health_region_name: string; uf: string;
  population: number; person_years: number; need_window_start: number; need_window_end: number;
  capacity_competence: string; geography_version: string; quality_flags: string[];
  suicide_deaths: number; psychiatric_admissions: number; caps_count: number;
  mental_health_beds_sus_count: number; psychiatrist_fte: number;
  suicide_percentile: number; psychiatric_admission_percentile: number;
  caps_percentile: number; beds_percentile: number; psychiatrist_fte_percentile: number;
};
export type HistoricalResponse = {
  reference_year: HistoricalYear; temporal_version: string; count: number;
  records: HistoricalRecord[]; geometry: HealthRegionFeatureCollection | null;
};

export function validateHistoricalResponse(data: HistoricalResponse, year: HistoricalYear) {
  if (data.reference_year !== year || data.count !== 439 || data.records.length !== 439 ||
      new Set(data.records.map((r) => r.health_region_code)).size !== 439 ||
      data.records.some((r) => r.year !== year)) {
    throw new Error("Os dados históricos não correspondem ao ano solicitado.");
  }
  return data;
}

// Presentation-only projection. No fabricated spatial, Radar or peer fields.
export function historicalSummary(r: HistoricalRecord): Pick<HealthRegionProfile, "need" | "capacity" | "mismatch"> {
  return {
    need: { score: r.need_score,
      suicide: { deaths: r.suicide_deaths, asmr: r.suicide_asmr, percentile: r.suicide_percentile },
      psychiatric_admissions: { count: r.psychiatric_admissions, rate: r.psychiatric_admission_rate, percentile: r.psychiatric_admission_percentile } },
    capacity: { score: r.capacity_score,
      caps: { count: r.caps_count, rate: r.caps_rate, percentile: r.caps_percentile },
      mental_health_beds_sus: { count: r.mental_health_beds_sus_count, rate: r.mental_health_beds_sus_rate, percentile: r.beds_percentile },
      psychiatrist_fte: { fte: r.psychiatrist_fte, rate: r.psychiatrist_fte_rate, percentile: r.psychiatrist_fte_percentile } },
    mismatch: { score: r.mismatch_score },
  };
}

export type MetricId =
  | "mismatch_score"
  | "need_score"
  | "capacity_score"
  | "suicide_asmr"
  | "psychiatric_admission_rate"
  | "caps_rate"
  | "mental_health_beds_sus_rate"
  | "psychiatrist_fte_rate";

export type GeometryProfile = "overview" | "detail" | "full";

export type ReleasePublic = {
  release_id: string;
  canonical_version: string;
  method_version: string;
  geography_version: string;
  release_status: string;
  quality_status: string;
  release_gate: string;
  public_release_status: string;
};

export type HealthRegionLookup = {
  health_region_code: string;
  health_region_name: string;
  uf: string;
  geography_version: string;
  release_id: string;
};

export type Pagination = {
  limit: number;
  offset: number;
  count: number;
  total: number;
};

export type PaginatedResponse<T> = {
  items: T[];
  pagination: Pagination;
};

export type IndicatorPublic = {
  indicator_id: string;
  indicator_name_pt: string;
  indicator_name_en: string;
  domain: string;
  description: string;
  unit: string;
  interpretation: string;
  what_it_does_not_measure: string[];
  source_system: string;
  observation_start: string | null;
  observation_end: string | null;
  method_version: string;
};

export type MapItem = {
  health_region_code: string;
  health_region_name: string;
  uf: string;
  population: number;
  metric: MetricId;
  value: number | null;
  data_quality_flags: string[];
  lisa_significant: boolean;
  lisa_cluster: LisaCluster | null;
};

export type HealthRegionFeature = {
  type: "Feature";
  id: string;
  geometry: GeoJSON.Geometry;
  properties: MapItem;
};

export type HealthRegionFeatureCollection = {
  type: "FeatureCollection";
  features: HealthRegionFeature[];
  crs: { type: "name"; properties: { name: string } };
  geometry_metadata: {
    profile: GeometryProfile;
    version: string;
    crs: string;
  };
};

export type HealthRegionProfile = {
  release: ReleasePublic;
  territory: {
    health_region_code: string;
    health_region_name: string;
    uf: string;
    uf_code: string;
    municipality_count: number;
    population: number;
    area_km2: number;
    population_density: number;
  };
  need: {
    suicide: { deaths: number; asmr: number; percentile: number };
    psychiatric_admissions: { count: number; rate: number; percentile: number };
    score: number;
  };
  capacity: {
    caps: { count: number; rate: number; percentile: number };
    mental_health_beds_sus: { count: number; rate: number; percentile: number };
    psychiatrist_fte: { fte: number; rate: number; percentile: number };
    score: number;
  };
  mismatch: { score: number };
  spatial: {
    lisa_local_i: number | null;
    lisa_p: number | null;
    lisa_q: number | null;
    lisa_significant: boolean;
    lisa_cluster: LisaCluster | null;
  };
  data_quality_flags: string[];
};

export type LisaCluster =
  | "HH"
  | "LL"
  | "HL"
  | "LH"
  | "high-high"
  | "low-low"
  | "high-low"
  | "low-high";

export type MunicipalityHealthRegion = {
  municipality_code_ibge: string;
  municipality_name: string;
  uf: string;
  health_region_code: string;
  health_region_name: string;
  geography_version: string;
};

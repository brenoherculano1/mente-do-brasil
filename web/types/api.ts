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

export type StateRegion = {
  health_region_code: string;
  health_region_name: string;
  uf: string;
  population: number;
  municipality_count: number;
  suicide_percentile: number | null;
  psychiatric_admission_percentile: number | null;
  need_score: number | null;
  caps_percentile: number | null;
  beds_percentile: number | null;
  psychiatrist_fte_percentile: number | null;
  capacity_score: number | null;
  mismatch_score: number | null;
  lisa_significant: boolean;
  lisa_cluster: LisaCluster | null;
  data_quality_flags: string[];
};

export type StateProfile = {
  release: ReleasePublic;
  state: {
    uf: string;
    state_name: string;
    health_region_count: number;
    population: number;
    municipality_count: number;
    lisa_significant_count: number;
    lisa_cluster_counts: Record<string, number>;
    quality_flag_counts: Record<string, number>;
  };
  regions: StateRegion[];
};

export type RadarSignalFamily =
  | "NEED_HIGH"
  | "CAPACITY_LOW"
  | "MISMATCH_MARKED_POSITIVE"
  | "CAPACITY_COMPONENT_LOW"
  | "SPATIAL_HH_MISMATCH";

export type RadarSignals = {
  need_high: boolean;
  capacity_low: boolean;
  mismatch_marked_positive: boolean;
  capacity_component_low: boolean;
  spatial_hh_mismatch: boolean;
  caps_low: boolean;
  beds_low: boolean;
  psychiatrist_fte_low: boolean;
  zero_registered_beds: boolean;
  matched_signal_families: number;
};

export type RadarRegion = {
  health_region_code: string;
  health_region_name: string;
  uf: string;
  population: number;
  municipality_count: number;
  need_score: number;
  capacity_score: number;
  mismatch_score: number;
  matched_signal_families: number;
  signals: RadarSignals;
  data_quality_flags: string[];
};

export type RadarFeature = {
  type: "Feature";
  id: string;
  geometry: GeoJSON.Geometry;
  properties: RadarRegion;
};

export type RadarResponse = {
  release: {
    release_id: string;
    intelligence_version: string;
    radar_ruleset_version: string;
    decomposition_version: string;
    peer_method_version: string;
  };
  filters: Record<string, unknown>;
  signal_definitions: Record<RadarSignalFamily, string>;
  total_matching: number;
  regions: RadarRegion[];
  geometry: {
    type: "FeatureCollection";
    features: RadarFeature[];
    crs: { type: "name"; properties: { name: string } };
    geometry_metadata: {
      profile: "overview";
      version: string;
      crs: string;
    };
  } | null;
};

export type DecompositionItem = {
  component: string;
  label: string;
  source_percentile: number;
  contribution: number;
  caution: string | null;
};

export type ExplanationResponse = {
  release: RadarResponse["release"];
  health_region_code: string;
  health_region_name: string;
  uf: string;
  matched_signal_families: number;
  triggers: string[];
  subsignals: string[];
  quality_cautions: string[];
  decomposition: DecompositionItem[];
  decomposition_sum: number;
  mismatch_score: number;
  interpretation: string;
};

export type PeerBenchmark = {
  metric_id: MetricId;
  target_value: number;
  peer_n_observed: number;
  peer_median: number | null;
  peer_q1: number | null;
  peer_q3: number | null;
  peer_min: number | null;
  peer_max: number | null;
  relative_to_peer_iqr:
    | "BELOW_PEER_IQR"
    | "WITHIN_PEER_IQR"
    | "ABOVE_PEER_IQR"
    | null;
  insufficient_reason: string | null;
};

export type PeerRegion = {
  health_region_code: string;
  health_region_name: string;
  uf: string;
  population: number;
  population_density: number;
  municipality_count: number;
  metric_value: number | null;
};

export type PeersResponse = {
  release: RadarResponse["release"];
  health_region_code: string;
  health_region_name: string;
  uf: string;
  method: {
    version: string;
    structural_variables: string[];
    transform: string;
    distance: string;
    selection: string;
    outcome_variables_used_for_selection: boolean;
    limitations: string[];
  };
  selected_metric: MetricId;
  peers: PeerRegion[];
  benchmarks: PeerBenchmark[];
};

export type InvestigationQuestion = {
  rule_id: string;
  version: string;
  category: "Base" | "Radar" | "Capacity" | "Spatial" | "Quality";
  question: string;
  rationale: string;
  priority: number;
  claim_limit: string;
};

export type ManagerMetricValue = {
  metric_id: MetricId;
  label: string;
  value: number | null;
  percentile: number | null;
  unit: string;
};

export type ManagerSpatialContext = {
  lisa_significant: boolean;
  lisa_cluster: LisaCluster | null;
  lisa_local_i: number | null;
  lisa_p: number | null;
  description: string;
};

export type ManagerVersions = RadarResponse["release"] & {
  manager_mode_version: string;
  report_version: string;
  investigation_guide_version: string;
  manager_brief_version: string;
};

export type ManagerRegionIdentity = {
  health_region_code: string;
  health_region_name: string;
  uf: string;
  population: number;
  municipality_count: number;
};

export type ManagerBrief = {
  release: ReleasePublic;
  versions: ManagerVersions;
  region: ManagerRegionIdentity;
  need_score: number;
  capacity_score: number;
  mismatch_score: number;
  radar_signals: RadarSignals;
  matched_signal_families: number;
  radar_triggers: string[];
  radar_subsignals: string[];
  deterministic_summary: string;
  decomposition: DecompositionItem[];
  peer_summary: {
    method_version: string;
    peer_count: number;
    default_metric: MetricId;
    selected_benchmarks: PeerBenchmark[];
  };
  spatial_context: ManagerSpatialContext;
  quality_cautions: string[];
  indicators: ManagerMetricValue[];
  investigation_questions: InvestigationQuestion[];
  method_references: string[];
  report_content_sha256: string;
};

export type ManagerCompareRegion = {
  identity: ManagerRegionIdentity;
  need_score: number;
  capacity_score: number;
  mismatch_score: number;
  indicators: ManagerMetricValue[];
  radar_signals: RadarSignals;
  matched_signal_families: number;
  quality_cautions: string[];
  lisa_context: ManagerSpatialContext;
};

export type ManagerCompareResponse = {
  release: ReleasePublic;
  versions: ManagerVersions;
  requested_codes: string[];
  metric_options: MetricId[];
  regions: ManagerCompareRegion[];
  ranking_introduced: boolean;
};

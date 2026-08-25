export const DATA_PAGE_SOURCES = {
  release: "metadata/releases/MDB_ANALYTICAL_2024_1.yaml",
  canonicalRelease: "metadata/releases/MDB_ANALYTICAL_2024_1_canonical.yaml",
  serving: "metadata/releases/MDB_ANALYTICAL_2024_1_serving.yaml",
  healthRegionsSchema: "metadata/canonical/health_regions_v1.yaml",
  crosswalkSchema: "metadata/canonical/municipality_health_region_crosswalk_v1.yaml",
  rawProvenance: "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv",
  webGeometry: "metadata/web_geometry/MDB_WEB_GEOMETRY_V1.yaml",
};

export const DATA_RELEASE = {
  releaseId: "MDB_ANALYTICAL_2024_1",
  methodVersion: "MDB_METHOD_1.0",
  canonicalVersion: "MDB_CANONICAL_1.0",
  geographyVersion: "BR_HEALTH_REGIONS_END2024_V1",
  webGeometryVersion: "MDB_WEB_GEOMETRY_V1",
  dataContract: "Não versionado neste release",
  releaseStatus: "VALIDATING",
  qualityStatus: "VALIDATED",
  releaseGate: "PASS",
  releaseReadiness: "READY",
  publicReleaseStatus: "NOT_RELEASED",
  publicAvailabilityText:
    "O release analítico atual foi validado, mas ainda não foi publicado publicamente.",
  publicAvailabilityLabel: "Ainda não publicado",
  accessDate: "2026-08-23",
  healthRegions: 439,
  municipalities: 5570,
  analyticalFields: 35,
  crosswalkFields: 9,
  canonicalHash: "a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515",
  crosswalkHash: "acd7ab896566d5ea730719eb46a079b0571d73fec617ef1d39db93099bd06b15",
};

export const DATASETS = [
  {
    title: "Health Regions analytical dataset",
    path: "data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet",
    purpose: "Dataset analítico principal, com uma linha por Região de Saúde.",
    unit: "Região de Saúde",
    rows: 439,
    columns: 35,
    format: "Parquet canonical",
    sha256: DATA_RELEASE.canonicalHash,
    release: DATA_RELEASE.releaseId,
    method: DATA_RELEASE.methodVersion,
    geography: DATA_RELEASE.geographyVersion,
    canonical: DATA_RELEASE.canonicalVersion,
  },
  {
    title: "Municipality to Health Region crosswalk",
    path: "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet",
    purpose:
      "Associa municípios à Região de Saúde utilizada no release; não representa uma análise municipal completa.",
    unit: "Município",
    rows: 5570,
    columns: 9,
    format: "Parquet canonical",
    sha256: DATA_RELEASE.crosswalkHash,
    release: DATA_RELEASE.releaseId,
    method: DATA_RELEASE.methodVersion,
    geography: DATA_RELEASE.geographyVersion,
    canonical: DATA_RELEASE.canonicalVersion,
  },
];

export const GEOMETRY_DATASETS = [
  {
    title: "Geometria científica",
    description:
      "Referência territorial locked usada para ciência e auditoria; não é substituída pela geometria simplificada da web.",
    version: DATA_RELEASE.geographyVersion,
    crs: "EPSG:4674",
  },
  {
    title: "Geometria web",
    description:
      "Camada derivada e simplificada usada apenas para renderização no navegador; não é fonte científica de área.",
    version: DATA_RELEASE.webGeometryVersion,
    crs: "EPSG:4326",
  },
];

export const PROVENANCE = {
  accessDate: "2026-08-23",
  total: 1137,
  breakdown: [
    ["POPSVS", 3],
    ["SIM", 81],
    ["SIH", 972],
    ["CNES_ST", 27],
    ["CNES_LT", 27],
    ["CNES_PF", 27],
  ] as const,
  cnesNote:
    "Para os arquivos históricos do CNES utilizados neste release, a URL histórica exata não foi preservada; a proveniência registra o uso do cache DATASUS validado no pipeline científico.",
};

export const PRIMARY_SOURCES = [
  ["SIM", "Mortalidade por suicídio", "2022-2024 pooled"],
  ["SIH/SUS", "Internações psiquiátricas", "2022-2024 pooled"],
  ["CNES", "CAPS, leitos e psiquiatras FTE", "dezembro de 2024"],
  ["DATASUS", "População e crosswalk de Regiões de Saúde conforme metodologia", "referência 2024"],
  ["IBGE", "Geometria municipal utilizada para composição territorial", "referência 2024"],
] as const;

export const DATA_DICTIONARY_CATEGORIES = [
  "Identificação e versão",
  "Território",
  "Need",
  "Capacity",
  "Mismatch",
  "Análise espacial",
  "Qualidade",
] as const;

export type DictionaryCategory = (typeof DATA_DICTIONARY_CATEGORIES)[number];

export type DataField = {
  name: string;
  label: string;
  category: DictionaryCategory;
  type: string;
  nullable: boolean;
  unit: string;
  sourceField: string;
  description: string;
  interpretation: string;
  limitations: string;
};

export const DATA_DICTIONARY: DataField[] = [
  field("release_id", "Release", "Identificação e versão", "string", false, "", "constant MDB_ANALYTICAL_2024_1", "Locked analytical release identifier.", "Release provenance field, not an analytical measure.", "Does not imply public release status."),
  field("method_version", "Método", "Identificação e versão", "string", false, "", "constant MDB_METHOD_1.0", "Locked method version used by the source scientific release.", "Method provenance field.", "Not a recalculation marker."),
  field("geography_version", "Geografia", "Identificação e versão", "string", false, "", "constant BR_HEALTH_REGIONS_END2024_V1", "Locked health-region geography version.", "Geography provenance field.", "Valid only for the locked end-2024 health-region definition."),
  field("health_region_code", "Código da Região de Saúde", "Território", "string", false, "", "health_region_code", "Five-character health-region code.", "Primary key for canonical health-region records.", "Must remain a string to preserve leading structure."),
  field("health_region_name", "Nome da Região de Saúde", "Território", "string", false, "", "health_region_name", "Health-region name in the locked analytical dataset.", "Human-readable health-region label.", "Names inherit source spelling and accent conventions."),
  field("uf_code", "Código da UF", "Território", "string", false, "", "health_region_code prefix", "Two-digit federative-unit prefix derived from health_region_code.", "Territorial key for joining state-level references.", "Derived only as a code-format validation, not as a new measure."),
  field("uf", "UF", "Território", "string", false, "", "UF", "Brazilian state abbreviation.", "State abbreviation associated with the health region.", "Validated against the health_region_code prefix."),
  field("municipality_count", "Municípios", "Território", "int64", false, "municipalities", "municipality_count", "Number of municipalities in the health region.", "Territorial composition count.", "Depends on the locked end-2024 crosswalk."),
  field("population", "População", "Território", "int64", false, "people", "population_2024", "Health-region population used by the scientific release.", "Population denominator for 2024 rate fields.", "Not updated beyond the locked source release."),
  field("area_km2", "Área", "Território", "float64", false, "square kilometers", "area_km2", "Health-region land area.", "Territorial area used for density.", "Inherits locked geography precision."),
  field("population_density", "Densidade populacional", "Território", "float64", false, "people per square kilometer", "population_density_2024", "Population density for the health region.", "Contextual density measure.", "Not part of the mismatch score."),
  field("suicide_deaths", "Óbitos por suicídio", "Need", "int64", false, "deaths", "deaths_pooled", "Pooled suicide deaths from the locked source period.", "Count underlying the suicide mortality indicator.", "Public interpretation should account for small-number flags."),
  field("suicide_asmr", "Mortalidade por suicídio padronizada", "Need", "float64", false, "deaths per 100000 population", "ASMR", "Age-standardized suicide mortality rate.", "Higher values indicate higher suicide mortality need.", "Locked scientific output; not recalculated here."),
  field("suicide_percentile", "Percentil de mortalidade por suicídio", "Need", "float64", false, "percentile scaled 0 to 1", "suicide_percentile", "Percentile rank for suicide mortality need.", "Higher values indicate higher relative need.", "Percentile is copied from locked output, not recalculated."),
  field("psychiatric_admissions", "Internações psiquiátricas", "Need", "int64", false, "admissions", "admission_n", "Psychiatric admissions count from SIH/SUS.", "Count underlying the admission-rate need indicator.", "Captures SIH/SUS admissions only."),
  field("psychiatric_admission_rate", "Taxa de internações psiquiátricas", "Need", "float64", false, "admissions per 100000 population", "admission_rate", "Psychiatric admission rate.", "Higher values contribute to higher measured need.", "Locked scientific output; not recalculated here."),
  field("psychiatric_admission_percentile", "Percentil de internações psiquiátricas", "Need", "float64", false, "percentile scaled 0 to 1", "admissions_percentile", "Percentile rank for psychiatric admission rate.", "Higher values indicate higher relative need.", "Percentile is copied from locked output, not recalculated."),
  field("caps_count", "CAPS", "Capacity", "int64", false, "services", "unique_CAPS_n", "Unique CAPS count.", "Service count underlying CAPS capacity rate.", "CNES-based locked count."),
  field("caps_rate", "Taxa de CAPS", "Capacity", "float64", false, "CAPS per 100000 population", "CAPS_rate_per_100k", "CAPS rate per population.", "Higher values indicate higher service capacity.", "Locked scientific output; not recalculated here."),
  field("caps_percentile", "Percentil de CAPS", "Capacity", "float64", false, "percentile scaled 0 to 1", "CAPS_percentile", "Percentile rank for CAPS rate.", "Higher values indicate higher relative capacity.", "Percentile is copied from locked output, not recalculated."),
  field("mental_health_beds_sus_count", "Leitos SUS de saúde mental", "Capacity", "int64", false, "beds", "SUS_mental_health_beds_n", "SUS mental-health beds count.", "Bed count underlying the SUS mental-health bed rate.", "CNES-based locked count."),
  field("mental_health_beds_sus_rate", "Taxa de leitos SUS de saúde mental", "Capacity", "float64", false, "beds per 100000 population", "bed_rate_per_100k", "SUS mental-health bed rate.", "Higher values indicate higher bed capacity.", "Locked scientific output; not recalculated here."),
  field("beds_percentile", "Percentil de leitos", "Capacity", "float64", false, "percentile scaled 0 to 1", "beds_percentile", "Percentile rank for SUS mental-health bed rate.", "Higher values indicate higher relative capacity.", "Percentile is copied from locked output, not recalculated."),
  field("psychiatrist_fte", "Psiquiatras FTE", "Capacity", "float64", false, "40-hour weekly FTE", "psychiatrist_FTE", "SUS psychiatrist full-time equivalent count.", "Workforce capacity expressed as FTE.", "Inherits CNES PF source limitations documented in the release."),
  field("psychiatrist_fte_rate", "Taxa de psiquiatras FTE", "Capacity", "float64", false, "FTE per 100000 population", "FTE_rate_per_100k", "SUS psychiatrist FTE rate.", "Higher values indicate higher workforce capacity.", "Locked scientific output; not recalculated here."),
  field("psychiatrist_fte_percentile", "Percentil de psiquiatras FTE", "Capacity", "float64", false, "percentile scaled 0 to 1", "FTE_percentile", "Percentile rank for SUS psychiatrist FTE rate.", "Higher values indicate higher relative capacity.", "Percentile is copied from locked output, not recalculated."),
  field("need_score", "Need Score", "Need", "float64", false, "score scaled 0 to 1", "Need_r", "Composite need score from the locked method.", "Higher values indicate higher measured mental-health need.", "Copied from locked output; component weights are not modified here."),
  field("capacity_score", "Capacity Score", "Capacity", "float64", false, "score scaled 0 to 1", "Capacity_r", "Composite capacity score from the locked method.", "Higher values indicate higher measured system capacity.", "Copied from locked output; component weights are not modified here."),
  field("mismatch_score", "Mismatch Score", "Mismatch", "float64", false, "score scaled -1 to 1", "Mismatch_r", "Locked need-capacity mismatch score.", "Higher values indicate greater need relative to capacity.", "Integrity-checked against need minus capacity but never overwritten."),
  field("lisa_local_i", "Local Moran I", "Análise espacial", "float64", false, "local Moran I", "local_I", "Local Moran statistic for mismatch.", "Local spatial association measure.", "Uses locked corrected spatial output only."),
  field("lisa_p", "Pseudo-p local", "Análise espacial", "float64", false, "probability", "raw_pseudo_p", "Raw pseudo-p value for local spatial association.", "Unadjusted local significance evidence.", "Do not use alone as the locked FDR decision."),
  field("lisa_q", "q ajustado LISA", "Análise espacial", "float64", false, "probability", "BH_adjusted_q", "Benjamini-Hochberg adjusted q value.", "FDR-adjusted local significance evidence.", "The boolean lisa_significant is the canonical locked decision."),
  field("lisa_significant", "LISA significativo", "Análise espacial", "bool", false, "", "significant_at_q_0.10", "Locked FDR significance indicator at q < 0.10.", "True means LISA is significant under the locked FDR rule.", "Not derived from cluster_label text."),
  field("lisa_cluster", "Cluster LISA", "Análise espacial", "string", false, "", "cluster_label", "LISA cluster label from the corrected locked output.", "Spatial mismatch cluster class or not_significant.", "Significance is represented by lisa_significant, not inferred from this label."),
  field("data_quality_flags", "Flags de qualidade", "Qualidade", "list<string>", false, "", "small_number_flag; SUS_mental_health_beds_n", "Directly supported quality flags for public product interpretation.", "Empty list means no canonical flag assigned.", "Only SMALL_SUICIDE_COUNT and ZERO_REGISTERED_BEDS are created in this version."),
];

function field(
  name: string,
  label: string,
  category: DictionaryCategory,
  type: string,
  nullable: boolean,
  unit: string,
  sourceField: string,
  description: string,
  interpretation: string,
  limitations: string,
): DataField {
  return {
    name,
    label,
    category,
    type,
    nullable,
    unit,
    sourceField,
    description,
    interpretation,
    limitations,
  };
}

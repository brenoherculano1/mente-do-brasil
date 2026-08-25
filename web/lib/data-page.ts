export const DATA_PAGE_SOURCES = {
  release: "metadata/releases/MDB_ANALYTICAL_2024_1.yaml",
  canonicalRelease: "metadata/releases/MDB_ANALYTICAL_2024_1_canonical.yaml",
  serving: "metadata/releases/MDB_ANALYTICAL_2024_1_serving.yaml",
  dataContract: "metadata/contracts/MDB_DATA_CONTRACT_V1.0.yaml",
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
  dataContract: "MDB_DATA_CONTRACT_V1.0",
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
    title: "Dataset analítico por Região de Saúde",
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
    title: "Crosswalk município → Região de Saúde",
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
      "Referência territorial fixada nesta versão para ciência e auditoria; não é substituída pela geometria simplificada da web.",
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
  field("release_id", "Release", "Identificação e versão", "string", false, "", "constant MDB_ANALYTICAL_2024_1", "Identificador do release analítico fixado nesta versão.", "Campo de proveniência do release, não uma medida analítica.", "Não indica publicação pública do release."),
  field("method_version", "Método", "Identificação e versão", "string", false, "", "constant MDB_METHOD_1.0", "Versão do método utilizada pelo release científico de origem.", "Campo de proveniência metodológica.", "Não é marcador de recálculo."),
  field("geography_version", "Geografia", "Identificação e versão", "string", false, "", "constant BR_HEALTH_REGIONS_END2024_V1", "Versão da malha de Regiões de Saúde fixada para o release.", "Campo de proveniência geográfica.", "Válido apenas para a definição de Regiões de Saúde do fim de 2024."),
  field("health_region_code", "Código da Região de Saúde", "Território", "string", false, "", "health_region_code", "Código de cinco caracteres da Região de Saúde.", "Chave primária dos registros canônicos por Região de Saúde.", "Deve permanecer como texto para preservar sua estrutura."),
  field("health_region_name", "Nome da Região de Saúde", "Território", "string", false, "", "health_region_name", "Nome da Região de Saúde no dataset analítico versionado.", "Rótulo legível da Região de Saúde.", "Os nomes herdam a grafia e as convenções de acentuação da fonte."),
  field("uf_code", "Código da UF", "Território", "string", false, "", "health_region_code prefix", "Prefixo de dois dígitos da UF derivado de health_region_code.", "Chave territorial para associação com referências estaduais.", "Derivado apenas como validação de formato do código, não como nova medida."),
  field("uf", "UF", "Território", "string", false, "", "UF", "Sigla da unidade federativa brasileira.", "Sigla estadual associada à Região de Saúde.", "Validada contra o prefixo de health_region_code."),
  field("municipality_count", "Municípios", "Território", "int64", false, "municípios", "municipality_count", "Número de municípios na Região de Saúde.", "Contagem da composição territorial.", "Depende do crosswalk fixado para o fim de 2024."),
  field("population", "População", "Território", "int64", false, "pessoas", "population_2024", "População da Região de Saúde usada no release científico.", "Denominador populacional dos campos de taxa de 2024.", "Não é atualizada além da fonte fixada neste release."),
  field("area_km2", "Área", "Território", "float64", false, "km²", "area_km2", "Área territorial da Região de Saúde.", "Área usada para cálculo de densidade.", "Herda a precisão da geografia fixada nesta versão."),
  field("population_density", "Densidade populacional", "Território", "float64", false, "pessoas por km²", "population_density_2024", "Densidade populacional da Região de Saúde.", "Medida contextual de densidade.", "Não integra o escore de mismatch."),
  field("suicide_deaths", "Óbitos por suicídio", "Need", "int64", false, "óbitos", "deaths_pooled", "Óbitos por suicídio agregados no período de origem fixado.", "Contagem subjacente ao indicador de mortalidade por suicídio.", "A interpretação pública deve considerar flags de números pequenos."),
  field("suicide_asmr", "Mortalidade por suicídio padronizada", "Need", "float64", false, "óbitos por 100.000 habitantes", "ASMR", "Taxa de mortalidade por suicídio padronizada por idade.", "Valores mais altos correspondem a maior posição relativa neste indicador de necessidade medida.", "Resultado científico validado e versionado; não é recalculado aqui."),
  field("suicide_percentile", "Percentil de mortalidade por suicídio", "Need", "float64", false, "percentil em escala de 0 a 1", "suicide_percentile", "Posição percentílica da mortalidade por suicídio no componente de necessidade.", "Valores mais altos correspondem a maior posição relativa no componente de necessidade medida utilizado neste release.", "Percentil proveniente do resultado científico versionado, sem recálculo nesta página."),
  field("psychiatric_admissions", "Internações psiquiátricas", "Need", "int64", false, "internações", "admission_n", "Contagem de internações psiquiátricas no SIH/SUS.", "Contagem subjacente ao indicador de taxa de internações.", "Capta apenas internações registradas no SIH/SUS."),
  field("psychiatric_admission_rate", "Taxa de internações psiquiátricas", "Need", "float64", false, "internações por 100.000 habitantes", "admission_rate", "Taxa de internações psiquiátricas.", "Valores mais altos correspondem a maior posição relativa neste indicador de necessidade medida.", "Resultado científico validado e versionado; não é recalculado aqui."),
  field("psychiatric_admission_percentile", "Percentil de internações psiquiátricas", "Need", "float64", false, "percentil em escala de 0 a 1", "admissions_percentile", "Posição percentílica da taxa de internações psiquiátricas.", "Valores mais altos correspondem a maior posição relativa no componente de necessidade medida utilizado neste release.", "Percentil proveniente do resultado científico versionado, sem recálculo nesta página."),
  field("caps_count", "CAPS", "Capacity", "int64", false, "serviços", "unique_CAPS_n", "Contagem de CAPS únicos.", "Contagem de serviços subjacente à taxa de capacidade por CAPS.", "Contagem baseada no CNES e fixada neste release."),
  field("caps_rate", "Taxa de CAPS", "Capacity", "float64", false, "CAPS por 100.000 habitantes", "CAPS_rate_per_100k", "Taxa de CAPS por população.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada medida por este indicador.", "Resultado científico validado e versionado; não é recalculado aqui."),
  field("caps_percentile", "Percentil de CAPS", "Capacity", "float64", false, "percentil em escala de 0 a 1", "CAPS_percentile", "Posição percentílica da taxa de CAPS.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada medida por este indicador.", "Percentil proveniente do resultado científico versionado, sem recálculo nesta página."),
  field("mental_health_beds_sus_count", "Leitos SUS de saúde mental", "Capacity", "int64", false, "leitos", "SUS_mental_health_beds_n", "Contagem de leitos SUS de saúde mental.", "Contagem de leitos subjacente à taxa de leitos SUS de saúde mental.", "Contagem baseada no CNES e fixada neste release."),
  field("mental_health_beds_sus_rate", "Taxa de leitos SUS de saúde mental", "Capacity", "float64", false, "leitos por 100.000 habitantes", "bed_rate_per_100k", "Taxa de leitos SUS de saúde mental.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada medida por este indicador.", "Resultado científico validado e versionado; não é recalculado aqui."),
  field("beds_percentile", "Percentil de leitos", "Capacity", "float64", false, "percentil em escala de 0 a 1", "beds_percentile", "Posição percentílica da taxa de leitos SUS de saúde mental.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada medida por este indicador.", "Percentil proveniente do resultado científico versionado, sem recálculo nesta página."),
  field("psychiatrist_fte", "Psiquiatras FTE", "Capacity", "float64", false, "FTE semanal de 40 horas", "psychiatrist_FTE", "Contagem de psiquiatras SUS em equivalente de tempo integral.", "Capacidade de força de trabalho expressa em FTE.", "Herda as limitações da fonte CNES PF documentadas no release."),
  field("psychiatrist_fte_rate", "Taxa de psiquiatras FTE", "Capacity", "float64", false, "FTE por 100.000 habitantes", "FTE_rate_per_100k", "Taxa de psiquiatras SUS em FTE.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada de força de trabalho medida por este indicador.", "Resultado científico validado e versionado; não é recalculado aqui."),
  field("psychiatrist_fte_percentile", "Percentil de psiquiatras FTE", "Capacity", "float64", false, "percentil em escala de 0 a 1", "FTE_percentile", "Posição percentílica da taxa de psiquiatras SUS em FTE.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada medida por este indicador.", "Percentil proveniente do resultado científico versionado, sem recálculo nesta página."),
  field("need_score", "Need Score", "Need", "float64", false, "escore em escala de 0 a 1", "Need_r", "Escore composto de necessidade definido pelo método versionado.", "Valores mais altos correspondem a maior posição relativa no componente de necessidade medida utilizado neste release.", "Proveniente do resultado científico versionado; os pesos dos componentes não são alterados aqui."),
  field("capacity_score", "Capacity Score", "Capacity", "float64", false, "escore em escala de 0 a 1", "Capacity_r", "Escore composto de capacidade definido pelo método versionado.", "Valores mais altos correspondem a maior posição relativa na capacidade registrada medida neste release.", "Proveniente do resultado científico versionado; os pesos dos componentes não são alterados aqui."),
  field("mismatch_score", "Mismatch Score", "Mismatch", "float64", false, "escore em escala de -1 a 1", "Mismatch_r", "Escore de mismatch necessidade-capacidade fixado no release.", "Valores mais altos correspondem a maior necessidade medida relativa à capacidade registrada.", "Validado contra necessidade menos capacidade, mas nunca sobrescrito nesta página."),
  field("lisa_local_i", "Local Moran I", "Análise espacial", "float64", false, "local Moran I", "local_I", "Estatística local de Moran para mismatch.", "Medida de associação espacial local.", "Usa apenas o resultado espacial corrigido e versionado."),
  field("lisa_p", "Pseudo-p local", "Análise espacial", "float64", false, "probabilidade", "raw_pseudo_p", "Valor pseudo-p bruto para associação espacial local.", "Evidência local de significância sem ajuste.", "Não deve ser usado isoladamente como decisão FDR versionada."),
  field("lisa_q", "q ajustado LISA", "Análise espacial", "float64", false, "probabilidade", "BH_adjusted_q", "Valor q ajustado por Benjamini-Hochberg.", "Evidência local de significância após ajuste por FDR.", "O campo booleano lisa_significant é a decisão canônica versionada."),
  field("lisa_significant", "LISA significativo", "Análise espacial", "bool", false, "", "significant_at_q_0.10", "Indicador de significância FDR fixado em q < 0,10.", "Verdadeiro significa LISA significativo sob a regra FDR versionada.", "Não é derivado do texto de cluster_label."),
  field("lisa_cluster", "Cluster LISA", "Análise espacial", "string", false, "", "cluster_label", "Rótulo de cluster LISA proveniente do resultado corrigido e versionado.", "Classe de cluster espacial de mismatch ou not_significant.", "A significância é representada por lisa_significant, não inferida deste rótulo."),
  field("data_quality_flags", "Flags de qualidade", "Qualidade", "list<string>", false, "", "small_number_flag; SUS_mental_health_beds_n", "Flags de qualidade diretamente sustentadas para interpretação pública do produto.", "Lista vazia significa ausência de flag canônica atribuída.", "Somente SMALL_SUICIDE_COUNT e ZERO_REGISTERED_BEDS são criadas nesta versão."),
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

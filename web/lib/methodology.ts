export const METHOD_IDENTIFIERS = {
  method: "MDB_METHOD_1.0",
  release: "MDB_ANALYTICAL_2024_1",
  canonical: "MDB_CANONICAL_1.0",
  geography: "BR_HEALTH_REGIONS_END2024_V1",
  webGeometry: "MDB_WEB_GEOMETRY_V1",
  intelligence: "MDB_TERRITORIAL_INTELLIGENCE_1.0",
  radarRuleset: "MDB_RADAR_RULESET_1.0",
  decomposition: "MDB_MISMATCH_DECOMPOSITION_1.0",
  peerMethod: "MDB_PEER_METHOD_1.0",
};

export const SCIENTIFIC_SOURCES = {
  release: "metadata/releases/MDB_ANALYTICAL_2024_1.yaml",
  canonical: "metadata/releases/MDB_ANALYTICAL_2024_1_canonical.yaml",
  serving: "metadata/releases/MDB_ANALYTICAL_2024_1_serving.yaml",
  suicide: "metadata/indicators/suicide_asmr.yaml",
  admissions: "metadata/indicators/psychiatric_admission_rate.yaml",
  caps: "metadata/indicators/caps_rate.yaml",
  beds: "metadata/indicators/mental_health_beds_sus_rate.yaml",
  psychiatrists: "metadata/indicators/psychiatrist_fte_rate.yaml",
  percentiles: "src/mente_do_brasil/quality.py",
  manuscriptStatus: "metadata/publication/manuscript_status.yaml",
  lockedConfig:
    "/Users/brenoherculano/Desktop/Brazil Mental Health Spatial Inequality Project/phase1_method_lock/analysis_config_LOCKED.yaml",
  methodLedger:
    "/Users/brenoherculano/Desktop/Brazil Mental Health Spatial Inequality Project/phase1_method_lock/method_decision_ledger.md",
};

export const METHODOLOGY_LOCKS = {
  healthRegions: 439,
  municipalities: 5570,
  rawProvenanceRecords: 1137,
  standardPopulation: "WHO_standard_population",
  standardPopulationLabel: "WHO standard population",
  suicidePeriod: "2022-2024 pooled",
  capacityCompetence: "Dez/2024",
  sourceAccessDate: "2026-08-23",
  canonicalRows: 439,
  crosswalkRows: 5570,
  lisaJoin: "439/439",
  moranI: "0.525494388844",
  moranPseudoP: "0.0001",
  moranPermutations: "9.999",
  moranSeed: "20260823",
  lisaSignificant: 135,
  lisaHH: 60,
  lisaLL: 66,
  lisaHL: 4,
  lisaLH: 5,
  smallSuicideCount: 7,
  zeroRegisteredBeds: 275,
  percentileAlgorithm:
    "Ordena valores observados, preserva ausentes sem imputar, calcula less + (equal - 1) / 2 e divide por max(n observados - 1, 1), gerando escala 0-1.",
  percentileTies: "Empates recebem a posição média dentro do grupo empatado.",
  percentileNullHandling:
    "Valores ausentes semânticos, null, not_available, not_applicable e suppressed são preservados; zeros válidos são mantidos.",
};

export const MANUSCRIPT_PUBLIC_STATUS = {
  title:
    "Spatial mismatch between mental-health need indicators and public-sector capacity across Brazilian Health Regions",
  publicClaim: "Status: manuscrito submetido ao Health & Place.",
  source: SCIENTIFIC_SOURCES.manuscriptStatus,
};

export const RATE_DENOMINATORS = [
  {
    indicator: "psychiatric_admission_rate",
    denominator: "População pessoa-anos 2022-2024",
    unit: "internações por 100.000 pessoa-anos",
    source: SCIENTIFIC_SOURCES.admissions,
  },
  {
    indicator: "caps_rate",
    denominator: "População residente de 2024",
    unit: "CAPS por 100.000 residentes",
    source: SCIENTIFIC_SOURCES.caps,
  },
  {
    indicator: "mental_health_beds_sus_rate",
    denominator: "População residente de 2024",
    unit: "leitos SUS por 100.000 residentes",
    source: SCIENTIFIC_SOURCES.beds,
  },
  {
    indicator: "psychiatrist_fte_rate",
    denominator: "População residente de 2024",
    unit: "FTE de psiquiatras por 100.000 residentes",
    source: SCIENTIFIC_SOURCES.psychiatrists,
  },
];

export const METHODOLOGY_NAV = [
  ["overview", "Visão geral"],
  ["geography", "Geografia"],
  ["sources", "Fontes e períodos"],
  ["need", "Need"],
  ["capacity", "Capacity"],
  ["percentiles", "Percentis"],
  ["mismatch", "Mismatch"],
  ["radar", "Radar Territorial"],
  ["decomposition", "Decomposição"],
  ["peers", "Peers estruturais"],
  ["spatial", "Análise espacial"],
  ["quality", "Qualidade dos dados"],
  ["limitations", "Limitações"],
  ["use", "Como usar"],
  ["versions", "Versionamento"],
  ["reproducibility", "Reprodutibilidade"],
  ["scientific-base", "Base científica"],
  ["citation", "Como citar"],
] as const;

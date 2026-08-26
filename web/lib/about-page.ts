import { DATA_RELEASE, PRIMARY_SOURCES } from "@/lib/data-page";
import { MANUSCRIPT_PUBLIC_STATUS, METHODOLOGY_LOCKS } from "@/lib/methodology";

export const ABOUT_PAGE = {
  subtitle: "Inteligência territorial em saúde mental no Brasil.",
  positioning:
    "O Mente do Brasil é uma infraestrutura independente de dados e inteligência territorial em saúde mental construída a partir de dados públicos brasileiros.",
  heroDescription:
    "Uma infraestrutura independente para organizar, comparar e tornar mais compreensíveis dados territoriais de saúde mental no Brasil.",
  independenceStatement:
    "O Mente do Brasil é uma iniciativa independente. Utiliza dados públicos produzidos por sistemas e instituições oficiais, mas não é um sistema oficial do Ministério da Saúde, DATASUS, IBGE ou de governos estaduais ou municipais.",
  governmentDisclaimer:
    "O uso desses dados não implica vínculo institucional, endosso ou participação dessas instituições no desenvolvimento do projeto.",
  patientDisclaimer:
    "O Mente do Brasil não é, nesta versão, um diretório de serviços de saúde mental para pacientes e não deve ser utilizado para situações de urgência ou orientação clínica individual.",
  publicReleaseCopy: DATA_RELEASE.publicAvailabilityText,
  releaseStatus: DATA_RELEASE.publicReleaseStatus,
  manuscriptStatus: MANUSCRIPT_PUBLIC_STATUS.publicClaim,
  manuscriptTitle: MANUSCRIPT_PUBLIC_STATUS.title,
  scope: {
    healthRegions: DATA_RELEASE.healthRegions,
    municipalities: DATA_RELEASE.municipalities,
    needPeriod: "2022–2024",
    capacityReference: "Dezembro de 2024",
  },
  versions: {
    releaseId: DATA_RELEASE.releaseId,
    method: DATA_RELEASE.methodVersion,
    geography: DATA_RELEASE.geographyVersion,
    dataContract: DATA_RELEASE.dataContract,
    publicationSource: MANUSCRIPT_PUBLIC_STATUS.source,
  },
  sourceSystems: PRIMARY_SOURCES.map(([source]) => source),
  sourceFiles: [
    "metadata/releases/MDB_ANALYTICAL_2024_1.yaml",
    "metadata/canonical/health_regions_v1.yaml",
    "metadata/canonical/municipality_health_region_crosswalk_v1.yaml",
    "metadata/contracts/MDB_DATA_CONTRACT_V1.0.yaml",
    "metadata/publication/manuscript_status.yaml",
  ],
  provenanceRecords: METHODOLOGY_LOCKS.rawProvenanceRecords,
};

export const ABOUT_FLOW = [
  "Dados públicos",
  "Padronização",
  "Territorialização",
  "Validação",
  "Comparação",
  "Investigação",
] as const;

export const ABOUT_ACTIONS = [
  ["Organizar", "dados de diferentes sistemas e períodos."],
  ["Territorializar", "informações na geografia analítica do projeto."],
  ["Comparar", "indicadores em escalas metodologicamente compatíveis."],
  ["Documentar", "fontes, decisões, limitações e versões."],
  ["Investigar", "padrões e diferenças territoriais."],
  ["Preparar", "dados para reutilização auditável em releases públicos."],
] as const;

export const ABOUT_AUDIENCES = [
  "gestores e equipes técnicas em diferentes níveis do SUS",
  "equipes da RAPS",
  "formuladores de políticas públicas",
  "conselhos de saúde",
  "pesquisadores e universidades",
  "sociedades científicas",
  "organizações da sociedade civil",
  "jornalistas",
  "organizações nacionais e internacionais que trabalhem com saúde pública",
] as const;

export const ABOUT_PRINCIPLES = [
  [
    "Rigor científico",
    "Indicadores, filtros, fórmulas e decisões analíticas são definidos e versionados antes de serem apresentados como resultados.",
  ],
  [
    "Transparência",
    "Fontes, limitações, versões, hashes e decisões metodológicas devem ser documentáveis e auditáveis.",
  ],
  [
    "Interpretação responsável",
    "O projeto separa o que os dados medem do que eles podem apenas sugerir.",
  ],
  [
    "Território",
    "A geografia não é tratada apenas como elemento visual. Ela faz parte da pergunta analítica.",
  ],
  [
    "Reprodutibilidade",
    "Releases devem poder ser identificados, reconstruídos e comparados sem substituição silenciosa de resultados anteriores.",
  ],
  [
    "Utilidade pública",
    "O produto é desenhado para reduzir o trabalho necessário para transformar dados fragmentados em perguntas territoriais investigáveis.",
  ],
] as const;

export const ABOUT_NOT_LIST = [
  "não é um sistema oficial do governo;",
  "não é uma ferramenta de diagnóstico individual;",
  "não mede diretamente prevalência de transtornos mentais;",
  "não mede sozinho qualidade ou acesso assistencial;",
  "não produz rankings de territórios;",
  "não recomenda automaticamente onde recursos devem ser alocados;",
  "não é um diretório de atendimento para pacientes.",
] as const;

import type { MetricId } from "@/types/api";

export type MetricConfig = {
  id: MetricId;
  label: string;
  shortLabel: string;
  description: string;
  secondary: string;
  unit: string;
  scale: "diverging" | "score" | "rate";
};

export const METRICS: MetricConfig[] = [
  {
    id: "mismatch_score",
    label: "Diferença entre necessidade e capacidade",
    shortLabel: "Diferença necessidade-capacidade",
    description: "Compara a necessidade medida com a estrutura assistencial registrada em cada região.",
    secondary:
      "Valores positivos indicam necessidade relativamente maior que capacidade na comparação nacional. Índice técnico: Mismatch.",
    unit: "score relativo",
    scale: "diverging",
  },
  {
    id: "need_score",
    label: "Necessidade em saúde mental",
    shortLabel: "Necessidade",
    description: "Posição relativa da região nos indicadores de mortalidade por suicídio e internações psiquiátricas.",
    secondary: "Não é prevalência de transtorno mental.",
    unit: "score 0-1",
    scale: "score",
  },
  {
    id: "capacity_score",
    label: "Estrutura de atendimento",
    shortLabel: "Estrutura",
    description: "Posição relativa da região em CAPS, leitos de saúde mental e carga horária de psiquiatras no SUS.",
    secondary: "Não equivale automaticamente a acesso efetivo ou qualidade assistencial.",
    unit: "score 0-1",
    scale: "score",
  },
  {
    id: "suicide_asmr",
    label: "Mortalidade por suicídio",
    shortLabel: "Mortalidade por suicídio",
    description: "Taxa padronizada de mortalidade por suicídio usada na dimensão de necessidade medida.",
    secondary: "A interpretação deve considerar as observações de qualidade quando presentes.",
    unit: "ASMR",
    scale: "rate",
  },
  {
    id: "psychiatric_admission_rate",
    label: "Internações psiquiátricas no SUS",
    shortLabel: "Internações",
    description: "Taxa de internações psiquiátricas registradas no SUS.",
    secondary: "Não é medida de prevalência.",
    unit: "taxa",
    scale: "rate",
  },
  {
    id: "caps_rate",
    label: "Centros de Atenção Psicossocial (CAPS)",
    shortLabel: "CAPS",
    description: "Taxa de CAPS registrada na dimensão de capacidade.",
    secondary: "Capacidade registrada não equivale automaticamente a acesso efetivo.",
    unit: "taxa",
    scale: "rate",
  },
  {
    id: "mental_health_beds_sus_rate",
    label: "Leitos de saúde mental no SUS",
    shortLabel: "Leitos SUS",
    description: "Taxa de leitos de saúde mental no SUS registrada na dimensão de capacidade.",
    secondary: "Não implica disponibilidade imediata para todos os territórios.",
    unit: "taxa",
    scale: "rate",
  },
  {
    id: "psychiatrist_fte_rate",
    label: "Psiquiatras no SUS",
    shortLabel: "Psiquiatras",
    description: "Carga horária registrada de psiquiatras no SUS, convertida em equivalentes de jornada integral.",
    secondary: "Medida de capacidade registrada, não de acesso efetivo individual.",
    unit: "FTE por população",
    scale: "rate",
  },
];

export const DEFAULT_METRIC: MetricId = "mismatch_score";

export const METRIC_IDS = METRICS.map((metric) => metric.id);

export function getMetricConfig(metricId: MetricId) {
  return METRICS.find((metric) => metric.id === metricId) ?? METRICS[0];
}

export function parseMetric(value: string | string[] | undefined): MetricId {
  const candidate = Array.isArray(value) ? value[0] : value;
  return METRIC_IDS.includes(candidate as MetricId) ? (candidate as MetricId) : DEFAULT_METRIC;
}

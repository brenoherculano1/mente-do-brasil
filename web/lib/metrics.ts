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
    label: "Mismatch",
    shortLabel: "Mismatch",
    description: "Sinal de desalinhamento territorial relativo entre necessidade medida e capacidade registrada.",
    secondary:
      "Valores positivos indicam necessidade medida relativamente maior que capacidade registrada na distribuição nacional.",
    unit: "score relativo",
    scale: "diverging",
  },
  {
    id: "need_score",
    label: "Need",
    shortLabel: "Need",
    description: "Composição de indicadores de necessidade medida retornada pela API.",
    secondary: "Não é prevalência de transtorno mental.",
    unit: "score 0-1",
    scale: "score",
  },
  {
    id: "capacity_score",
    label: "Capacity",
    shortLabel: "Capacity",
    description: "Composição de capacidade registrada retornada pela API.",
    secondary: "Não equivale automaticamente a acesso efetivo ou qualidade assistencial.",
    unit: "score 0-1",
    scale: "score",
  },
  {
    id: "suicide_asmr",
    label: "Suicídio",
    shortLabel: "Suicídio",
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
    label: "CAPS",
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
    label: "Psiquiatras FTE no SUS",
    shortLabel: "Psiquiatras FTE",
    description: "Taxa de psiquiatras FTE no SUS registrada na dimensão de capacidade.",
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

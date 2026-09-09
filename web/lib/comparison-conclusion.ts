import { formatMetricValue } from "@/lib/format";
import { getMetricConfig } from "@/lib/metrics";
import type { ManagerCompareRegion, MetricId } from "@/types/api";

type ComparedValue = { name: string; value: number };

export function buildComparisonConclusion(regions: ManagerCompareRegion[], metric: MetricId) {
  const config = getMetricConfig(metric);
  const values = regions
    .map((region): ComparedValue | null => {
      const item = region.indicators.find((indicator) => indicator.metric_id === metric);
      return item?.value == null
        ? null
        : { name: region.identity.health_region_name, value: item.value };
    })
    .filter((item): item is ComparedValue => item !== null)
    .sort((a, b) => b.value - a.value);

  if (values.length < 2) {
    return "Não há dados suficientes para produzir uma síntese desta comparação.";
  }

  const highest = values[0];
  const lowest = values[values.length - 1];
  const highValue = formatMetricValue(highest.value, config.scale);
  const lowValue = formatMetricValue(lowest.value, config.scale);

  if (metric === "mismatch_score") {
    if (highest.value <= 0) {
      return `Nas regiões comparadas, a estrutura registrada ocupa posição relativa igual ou superior à necessidade medida. ${lowest.name} apresenta a diferença mais favorável (${lowValue}) e ${highest.name}, a menos pronunciada (${highValue}).`;
    }
    if (lowest.value >= 0) {
      return `Nas regiões comparadas, a necessidade medida ocupa posição relativa superior à estrutura registrada. O sinal é mais acentuado em ${highest.name} (${highValue}) e menos acentuado em ${lowest.name} (${lowValue}).`;
    }
    return `${highest.name} apresenta necessidade relativamente mais acima da estrutura registrada (${highValue}), enquanto ${lowest.name} apresenta estrutura relativamente acima da necessidade medida (${lowValue}).`;
  }

  if (metric === "need_score" || metric === "suicide_asmr" || metric === "psychiatric_admission_rate") {
    return `${highest.name} apresenta o maior valor do indicador de necessidade selecionado (${highValue}); ${lowest.name}, o menor (${lowValue}). Essa diferença é descritiva e não mede prevalência nem qualidade do cuidado.`;
  }

  return `${highest.name} apresenta a maior capacidade registrada no indicador selecionado (${highValue}); ${lowest.name}, a menor (${lowValue}). Isso não comprova acesso efetivo, disponibilidade imediata ou qualidade assistencial.`;
}

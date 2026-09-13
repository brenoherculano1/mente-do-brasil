import type { IndicatorDirection } from "@/lib/public-language";
import type { MetricId } from "@/types/api";

export type RelativeTone = "favorable" | "attention" | "neutral";

export function toneForDirection(value: number, direction: IndicatorDirection): RelativeTone {
  if (value >= 0.75) return direction === "capacity" ? "favorable" : "attention";
  if (value <= 0.25) return direction === "capacity" ? "attention" : "favorable";
  return "neutral";
}

export function toneForMismatch(_value: number): RelativeTone {
  void _value;
  // The sign of a relative difference does not establish quality or adequacy.
  return "neutral";
}

export function toneForMetric(
  metric: MetricId,
  value: number | null,
  percentile: number | null,
): RelativeTone {
  if (metric === "mismatch_score") return value === null ? "neutral" : toneForMismatch(value);
  if (percentile === null) return "neutral";
  const direction = metric === "need_score" || metric === "suicide_asmr" || metric === "psychiatric_admission_rate"
    ? "need"
    : "capacity";
  return toneForDirection(percentile, direction);
}

export function relativeBandLabel(value: number) {
  if (value <= 0.25) return "Faixa relativa baixa";
  if (value >= 0.75) return "Faixa relativa alta";
  return "Faixa relativa intermediária";
}

export function toneLabel(tone: RelativeTone) {
  if (tone === "favorable") return "Posição relativa, não avaliação de qualidade";
  if (tone === "attention") return "Sinal de atenção";
  return "Comparação relativa, não nota de qualidade";
}

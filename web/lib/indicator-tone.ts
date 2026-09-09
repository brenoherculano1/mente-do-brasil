import type { IndicatorDirection } from "@/lib/public-language";
import type { MetricId } from "@/types/api";

export type RelativeTone = "favorable" | "attention" | "neutral";

export function toneForDirection(value: number, direction: IndicatorDirection): RelativeTone {
  if (value >= 0.75) return direction === "capacity" ? "favorable" : "attention";
  if (value <= 0.25) return direction === "capacity" ? "attention" : "favorable";
  return "neutral";
}

export function toneForMismatch(value: number): RelativeTone {
  if (value <= -0.1) return "favorable";
  if (value >= 0.1) return "attention";
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

export function toneLabel(tone: RelativeTone) {
  if (tone === "favorable") return "Leitura relativamente favorável";
  if (tone === "attention") return "Sinal de atenção";
  return "Faixa intermediária";
}

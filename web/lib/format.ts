const integerFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const oneDecimalFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const twoDecimalFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatInteger(value: number | null | undefined) {
  return value == null ? "Sem dado" : integerFormatter.format(value);
}

export function formatRate(value: number | null | undefined) {
  return value == null ? "Sem dado" : oneDecimalFormatter.format(value);
}

export function formatScore(value: number | null | undefined, signed = false) {
  if (value == null) return "Sem dado";
  const formatted = twoDecimalFormatter.format(value);
  return signed && value > 0 ? `+${formatted}` : formatted;
}

export function formatPercentile(value: number | null | undefined) {
  if (value == null) return "Sem dado";
  return `${Math.round(value * 100)}º percentil`;
}

export function formatFte(value: number | null | undefined) {
  return value == null ? "Sem dado" : oneDecimalFormatter.format(value);
}

export function formatMetricValue(value: number | null | undefined, metricScale: string) {
  if (metricScale === "diverging") return formatScore(value, true);
  if (metricScale === "score") return formatScore(value);
  return formatRate(value);
}

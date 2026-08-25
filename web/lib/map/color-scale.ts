import type { MetricConfig } from "@/lib/metrics";

export const MAP_COLORS = {
  negative: "#315c8c",
  neutral: "#ece8dc",
  positive: "#9a5a2d",
  scoreLow: "#e8eee8",
  scoreHigh: "#0f766e",
  rateLow: "#edf1ea",
  rateHigh: "#7c4d79",
  missing: "#9da59f",
};

export type ScaleDomain = {
  min: number;
  max: number;
  maxAbs: number;
};

export function getScaleDomain(values: Array<number | null | undefined>): ScaleDomain {
  const valid = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (valid.length === 0) return { min: 0, max: 0, maxAbs: 0 };
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  return { min, max, maxAbs: Math.max(Math.abs(min), Math.abs(max)) };
}

export function colorForValue(
  value: number | null | undefined,
  metric: Pick<MetricConfig, "scale">,
  domain: ScaleDomain,
) {
  if (value == null || !Number.isFinite(value)) return MAP_COLORS.missing;
  if (metric.scale === "diverging") {
    if (value === 0 || domain.maxAbs === 0) return MAP_COLORS.neutral;
    return value < 0 ? MAP_COLORS.negative : MAP_COLORS.positive;
  }
  if (metric.scale === "score") {
    return value <= 0 ? MAP_COLORS.scoreLow : MAP_COLORS.scoreHigh;
  }
  if (domain.max <= domain.min) return MAP_COLORS.rateHigh;
  return value <= domain.min ? MAP_COLORS.rateLow : MAP_COLORS.rateHigh;
}

export function mapLibreFillExpression(metric: Pick<MetricConfig, "scale">, domain: ScaleDomain) {
  if (metric.scale === "diverging") {
    const maxAbs = domain.maxAbs || 1;
    return [
      "case",
      ["!", ["has", "value"]],
      MAP_COLORS.missing,
      ["==", ["get", "value"], null],
      MAP_COLORS.missing,
      [
        "interpolate",
        ["linear"],
        ["get", "value"],
        -maxAbs,
        MAP_COLORS.negative,
        0,
        MAP_COLORS.neutral,
        maxAbs,
        MAP_COLORS.positive,
      ],
    ];
  }
  if (metric.scale === "score") {
    return [
      "case",
      ["==", ["get", "value"], null],
      MAP_COLORS.missing,
      [
        "interpolate",
        ["linear"],
        ["get", "value"],
        0,
        MAP_COLORS.scoreLow,
        1,
        MAP_COLORS.scoreHigh,
      ],
    ];
  }
  return [
    "case",
    ["==", ["get", "value"], null],
    MAP_COLORS.missing,
    [
      "interpolate",
      ["linear"],
      ["get", "value"],
      domain.min,
      MAP_COLORS.rateLow,
      domain.max || 1,
      MAP_COLORS.rateHigh,
    ],
  ];
}

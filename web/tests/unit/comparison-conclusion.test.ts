import { describe, expect, it } from "vitest";
import { buildComparisonConclusion } from "@/lib/comparison-conclusion";
import type { ManagerCompareRegion, MetricId } from "@/types/api";

function region(name: string, metric: MetricId, value: number): ManagerCompareRegion {
  return {
    identity: {
      health_region_code: name === "Garanhuns" ? "26004" : "26003",
      health_region_name: name,
      uf: "PE",
      population: 1,
      municipality_count: 1,
    },
    need_score: 0,
    capacity_score: 0,
    mismatch_score: 0,
    indicators: [{ metric_id: metric, label: metric, value, percentile: 0.5, unit: "" }],
    radar_signals: {
      need_high: false,
      capacity_low: false,
      mismatch_marked_positive: false,
      capacity_component_low: false,
      spatial_hh_mismatch: false,
      caps_low: false,
      beds_low: false,
      psychiatrist_fte_low: false,
      zero_registered_beds: false,
      matched_signal_families: 0,
    },
    matched_signal_families: 0,
    quality_cautions: [],
    lisa_context: {
      lisa_significant: false,
      lisa_cluster: null,
      lisa_local_i: null,
      lisa_p: null,
      description: "",
    },
  };
}

describe("buildComparisonConclusion", () => {
  it("describes ties without selecting an extreme region", () => {
    const text = buildComparisonConclusion([region("A", "mismatch_score", 0), region("B", "mismatch_score", 0)], "mismatch_score");
    expect(text).toContain("mesmo valor");
    expect(text).not.toMatch(/mais pronunciada|favorável/);
  });

  it("excludes non-finite values", () => {
    expect(buildComparisonConclusion([region("A", "mismatch_score", NaN), region("B", "mismatch_score", 0)], "mismatch_score")).toContain("Não há dados suficientes");
  });

  it("describes negative mismatch without a normative ranking", () => {
    const conclusion = buildComparisonConclusion(
      [region("Garanhuns", "mismatch_score", -0.54), region("Caruaru", "mismatch_score", -0.37)],
      "mismatch_score",
    );

    expect(conclusion).toContain("estrutura registrada ocupa posição relativa igual ou superior");
    expect(conclusion).toContain("mais pronunciada em Garanhuns");
    expect(conclusion).not.toMatch(/favorável|melhor|pior/);
  });

  it("states the access limitation for capacity comparisons", () => {
    const conclusion = buildComparisonConclusion(
      [region("Garanhuns", "caps_rate", 3.4), region("Caruaru", "caps_rate", 1.8)],
      "caps_rate",
    );

    expect(conclusion).toContain("não comprova acesso efetivo");
  });
});

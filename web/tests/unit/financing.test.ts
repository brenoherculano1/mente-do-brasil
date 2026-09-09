import { describe, expect, it } from "vitest";
import { summarizeFinancing } from "@/lib/financing";
import type { FinancingRecord } from "@/types/api";

const record = (uf: string, value: number | null): FinancingRecord => ({
  financing_version: "test",
  siops_snapshot_id: "test",
  year: 2024,
  health_region_code: `${uf}001`,
  health_region_name: "Teste",
  uf,
  municipalities_expected: 1,
  municipalities_observed: value === null ? 0 : 1,
  population_expected: 100,
  population_covered: value === null ? null : 100,
  coverage_share: value === null ? 0 : 1,
  coverage_population_share: value === null ? null : 1,
  total_health_expenditure_brl: value,
  health_expenditure_per_capita_brl: value,
  headline_available: value !== null,
  quality_flags: [],
  source_period: "2024",
  source_indicator: "test",
  scope: "GENERAL_HEALTH_FINANCING_CONTEXT",
});

describe("summarizeFinancing", () => {
  it("sums available regions and reports coverage", () => {
    expect(summarizeFinancing([record("PB", 100), record("PB", null), record("PE", 50)], "PB"))
      .toEqual({ total: 100, observed: 1, expected: 2 });
  });

  it("does not present zero when no value is available", () => {
    expect(summarizeFinancing([record("PB", null)], "PB").total).toBeNull();
  });
});

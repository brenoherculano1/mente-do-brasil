import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FinancingPage } from "@/features/financing/FinancingPage";
import { METRICS } from "@/lib/metrics";
import { attentionLabel } from "@/features/intelligence/RadarPage";

vi.mock("@/features/advanced/useResource", () => ({ useResource: () => ({ data: null, loading: false, error: null }) }));
vi.mock("@/features/advanced/OverviewMap", () => ({ OverviewMap: () => null }));
vi.mock("@/features/share/ShareButton", () => ({ ShareButton: () => null }));
vi.mock("@/features/intelligence/RadarMap", () => ({ RadarMap: () => null }));

describe("founder review copy safeguards", () => {
  it("uses both selected financing years in the heading", () => {
    render(<FinancingPage />);
    expect(screen.getByRole("heading", { name: "Despesa geral em saúde: 2022 e 2024" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Ano final"), { target: { value: "2023" } });
    expect(screen.getByRole("heading", { name: "Despesa geral em saúde: 2022 e 2023" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Ano inicial"), { target: { value: "2024" } });
    expect(screen.getByRole("heading", { name: "Despesa geral em saúde: 2024 e 2023" })).toBeTruthy();
  });

  it.each([0, 1, 2, 3, 4, 5])("describes %i signals without priority inference", count => {
    expect(attentionLabel(count)).toBe(`${count} ${count === 1 ? "sinal" : "sinais"}`);
  });

  it("labels every comparison rate with its documented population denominator", () => {
    const rates = METRICS.filter(metric => metric.scale === "rate");
    expect(rates).toHaveLength(5);
    for (const metric of rates) expect(metric.comparisonLabel).toContain("por 100 mil hab.");
    expect(rates.find(metric => metric.id === "suicide_asmr")?.comparisonLabel).toContain("padronizada por idade");
    expect(rates.find(metric => metric.id === "psychiatrist_fte_rate")?.comparisonLabel).toContain("Jornadas equivalentes");
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MethodologyPage } from "@/features/methodology/MethodologyPage";
import {
  MANUSCRIPT_PUBLIC_STATUS,
  METHOD_IDENTIFIERS,
  METHODOLOGY_LOCKS,
  RATE_DENOMINATORS,
} from "@/lib/methodology";

describe("methodology page", () => {
  it("uses the locked current scientific identity", () => {
    expect(METHOD_IDENTIFIERS).toMatchObject({release: "MDB_ANALYTICAL_2024_2", method: "MDB_METHOD_1.1", canonical: "MDB_CANONICAL_1.1", intelligence: "MDB_TERRITORIAL_INTELLIGENCE_1.1"});
    expect(METHODOLOGY_LOCKS).toMatchObject({moranI: "0.5256454566660947", moranPseudoP: "0.0001", lisaSignificant: 136, lisaHH: 60, lisaLL: 65, lisaHL: 5, lisaLH: 6, healthRegions: 439, municipalities: 5570});
  });
  function renderTechnicalMethodology() {
    render(<MethodologyPage />);
    fireEvent.click(screen.getByRole("tab", { name: "Metodologia completa" }));
  }

  it("opens in public language without technical identifiers", () => {
    render(<MethodologyPage />);
    expect(screen.getByRole("tab", { name: "Como funciona" })).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByText(METHOD_IDENTIFIERS.release)).not.toBeInTheDocument();
    expect(screen.getByText("O que esta leitura permite entender")).toBeInTheDocument();
  });

  it("keeps technical identifiers out while retaining methodological detail", () => {
    renderTechnicalMethodology();
    expect(screen.getByRole("heading", { level: 1, name: "Metodologia" })).toBeInTheDocument();
    expect(screen.queryByText(METHOD_IDENTIFIERS.method)).not.toBeInTheDocument();
    expect(screen.queryByText(METHOD_IDENTIFIERS.release)).not.toBeInTheDocument();
    expect(screen.queryByText(METHOD_IDENTIFIERS.geography)).not.toBeInTheDocument();
    expect(screen.getByText(METHODOLOGY_LOCKS.standardPopulationLabel)).toBeInTheDocument();
  });

  it("renders Need, Capacity, and Mismatch formulas", () => {
    renderTechnicalMethodology();
    expect(screen.getByText(/Need Score =/)).toBeInTheDocument();
    expect(screen.getByText(/Capacity Score =/)).toBeInTheDocument();
    expect(screen.getByText("Mismatch = Need Score - Capacity Score")).toBeInTheDocument();
  });

  it("documents denominators from the locked method constants", () => {
    expect(RATE_DENOMINATORS).toEqual([
      expect.objectContaining({
        indicator: "psychiatric_admission_rate",
        unit: "internações por 100.000 pessoa-anos",
      }),
      expect.objectContaining({ indicator: "caps_rate", unit: "CAPS por 100.000 residentes" }),
      expect.objectContaining({
        indicator: "mental_health_beds_sus_rate",
        unit: "leitos SUS por 100.000 residentes",
      }),
      expect.objectContaining({
        indicator: "psychiatrist_fte_rate",
        unit: "FTE de psiquiatras por 100.000 residentes",
      }),
    ]);
  });

  it("preserves claim discipline and limitations", () => {
    renderTechnicalMethodology();
    expect(
      screen.getByText(/não uma medida direta de acesso efetivo, qualidade assistencial/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Limitações" })).toBeInTheDocument();
    expect(screen.getByText("Mismatch não tem leitura etiológica")).toBeInTheDocument();
    expect(screen.getByText(/Need Score combina dois indicadores distintos/i)).toBeInTheDocument();
  });

  it("documents territorial intelligence product methods without recalculating science", () => {
    renderTechnicalMethodology();
    expect(screen.queryByText(METHOD_IDENTIFIERS.intelligence)).not.toBeInTheDocument();
    expect(screen.queryByText(METHOD_IDENTIFIERS.radarRuleset)).not.toBeInTheDocument();
    expect(screen.queryByText(METHOD_IDENTIFIERS.decomposition)).not.toBeInTheDocument();
    expect(screen.queryByText(METHOD_IDENTIFIERS.peerMethod)).not.toBeInTheDocument();
    expect(screen.getByText(/Variáveis de outcome não entram na seleção dos peers/i))
      .toBeInTheDocument();
  });

  it("renders LISA counts and warning without disease concentration claim", () => {
    renderTechnicalMethodology();
    expect(screen.getByText(String(METHODOLOGY_LOCKS.lisaSignificant))).toBeInTheDocument();
    expect(screen.getByText("60 / 65 / 5 / 6")).toBeInTheDocument();
    expect(
      screen.getByText(/Um cluster HH não deve ser interpretado como concentração de doença mental/i),
    ).toBeInTheDocument();
  });

  it("renders the conservative manuscript submission status", () => {
    renderTechnicalMethodology();
    expect(screen.getByText(new RegExp(MANUSCRIPT_PUBLIC_STATUS.title))).toBeInTheDocument();
    expect(screen.getByText(/Status: manuscrito submetido ao Health & Place\./)).toBeInTheDocument();
  });
});

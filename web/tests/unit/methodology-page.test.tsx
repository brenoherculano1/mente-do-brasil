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

  it("renders locked metadata identifiers and standard population", () => {
    renderTechnicalMethodology();
    expect(screen.getByRole("heading", { level: 1, name: "Metodologia" })).toBeInTheDocument();
    expect(screen.getAllByText(METHOD_IDENTIFIERS.method).length).toBeGreaterThan(0);
    expect(screen.getAllByText(METHOD_IDENTIFIERS.release).length).toBeGreaterThan(0);
    expect(screen.getAllByText(METHOD_IDENTIFIERS.geography).length).toBeGreaterThan(0);
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
    expect(screen.getByText(METHOD_IDENTIFIERS.intelligence)).toBeInTheDocument();
    expect(screen.getByText(METHOD_IDENTIFIERS.radarRuleset)).toBeInTheDocument();
    expect(screen.getByText(METHOD_IDENTIFIERS.decomposition)).toBeInTheDocument();
    expect(screen.getByText(METHOD_IDENTIFIERS.peerMethod)).toBeInTheDocument();
    expect(screen.getByText(/Variáveis de outcome não entram na seleção dos peers/i))
      .toBeInTheDocument();
  });

  it("renders LISA counts and warning without disease concentration claim", () => {
    renderTechnicalMethodology();
    expect(screen.getByText(String(METHODOLOGY_LOCKS.lisaSignificant))).toBeInTheDocument();
    expect(screen.getByText("60 / 66 / 4 / 5")).toBeInTheDocument();
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

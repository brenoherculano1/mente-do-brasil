import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MethodologyPage } from "@/features/methodology/MethodologyPage";
import { METHOD_IDENTIFIERS, METHODOLOGY_LOCKS, RATE_DENOMINATORS } from "@/lib/methodology";

describe("methodology page", () => {
  it("renders locked metadata identifiers and standard population", () => {
    render(<MethodologyPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Metodologia" })).toBeInTheDocument();
    expect(screen.getAllByText(METHOD_IDENTIFIERS.method).length).toBeGreaterThan(0);
    expect(screen.getAllByText(METHOD_IDENTIFIERS.release).length).toBeGreaterThan(0);
    expect(screen.getAllByText(METHOD_IDENTIFIERS.geography).length).toBeGreaterThan(0);
    expect(screen.getByText(METHODOLOGY_LOCKS.standardPopulationLabel)).toBeInTheDocument();
  });

  it("renders Need, Capacity, and Mismatch formulas", () => {
    render(<MethodologyPage />);
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
    render(<MethodologyPage />);
    expect(
      screen.getByText(/não uma medida direta de déficit, acesso, qualidade ou necessidade não atendida/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Limitações" })).toBeInTheDocument();
    expect(screen.getByText("Mismatch não é causal")).toBeInTheDocument();
    expect(screen.getByText(/Need Score combina dois indicadores distintos/i)).toBeInTheDocument();
  });

  it("renders LISA counts and warning without disease-hotspot claim", () => {
    render(<MethodologyPage />);
    expect(screen.getByText(String(METHODOLOGY_LOCKS.lisaSignificant))).toBeInTheDocument();
    expect(screen.getByText("60 / 66 / 4 / 5")).toBeInTheDocument();
    expect(
      screen.getByText(/Um cluster HH não deve ser interpretado como um hotspot de doença mental/i),
    ).toBeInTheDocument();
  });
});

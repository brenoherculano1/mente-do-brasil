import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DataPage } from "@/features/data/DataPage";

describe("data page", () => {
  it("explains coverage without exposing internal identifiers", () => {
    const { container } = render(<DataPage />);
    expect(screen.getByRole("heading", { level: 1, name: "De onde vêm os dados" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dados validados até 2024" })).toBeInTheDocument();
    expect(screen.getByText(/A disponibilidade varia por indicador/)).toBeInTheDocument();
    expect(screen.getByText(/A estrutura pode ser atualizada independentemente/)).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/MDB_|SHA-?256|\.parquet|metadata\//i);
  });

  it("shows counts, rates, periods, and territorial coverage", () => {
    render(<DataPage />);
    expect(screen.getAllByText("Quantidade e taxa por 100 mil habitantes")).toHaveLength(2);
    expect(screen.getByText("Jornadas equivalentes e taxa por 100 mil habitantes")).toBeInTheDocument();
    expect(screen.getAllByText("Dezembro de 2024").length).toBeGreaterThan(0);
    expect(screen.getByText(/Cada um dos 5.570 municípios/)).toBeInTheDocument();
  });

  it("keeps the methodology link available", () => {
    render(<DataPage />);
    expect(screen.getByRole("link", { name: /Ver metodologia completa/i })).toHaveAttribute(
      "href",
      "/metodologia",
    );
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DataPage } from "@/features/data/DataPage";
import { DATA_DICTIONARY, DATA_RELEASE } from "@/lib/data-page";

describe("data page", () => {
  it("renders release identifiers, counts, and locked hashes", () => {
    render(<DataPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Dados e versões" })).toBeInTheDocument();
    expect(screen.getAllByText(DATA_RELEASE.releaseId).length).toBeGreaterThan(0);
    expect(screen.getAllByText(DATA_RELEASE.methodVersion).length).toBeGreaterThan(0);
    expect(screen.getAllByText(DATA_RELEASE.geographyVersion).length).toBeGreaterThan(0);
    expect(screen.getAllByText("439").length).toBeGreaterThan(0);
    expect(screen.getByText("5.570")).toBeInTheDocument();
    expect(screen.getAllByText("35").length).toBeGreaterThan(0);
    expect(screen.getByText(DATA_RELEASE.canonicalHash)).toBeInTheDocument();
    expect(screen.getByText(DATA_RELEASE.crosswalkHash)).toBeInTheDocument();
  });

  it("translates NOT_RELEASED without exposing downloads or localhost", () => {
    const { container } = render(<DataPage />);
    expect(screen.getByText(DATA_RELEASE.publicAvailabilityText)).toBeInTheDocument();
    expect(screen.getAllByText("Ainda não publicado").length).toBeGreaterThan(0);
    expect(screen.getByText("NOT_RELEASED")).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/http:\/\/127\.0\.0\.1|localhost/i);
    expect(container.textContent).not.toMatch(/Download agora|API pública ativa|Publicado/);
    expect(screen.queryByRole("link", { name: /download/i })).not.toBeInTheDocument();
  });

  it("renders the complete 35-field dictionary and filters locally", () => {
    render(<DataPage />);
    expect(DATA_DICTIONARY).toHaveLength(35);
    expect(screen.getByText("35 de 35 campos.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Buscar campo"), { target: { value: "psychiatrist" } });
    expect(screen.getByText("psychiatrist_fte_rate")).toBeInTheDocument();
    expect(screen.queryByText("suicide_asmr")).not.toBeInTheDocument();
  });

  it("documents null semantics, license uncertainty, and citation state", () => {
    const { container } = render(<DataPage />);
    expect(screen.getByText(/Null não equivale a zero/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        "A licença de reutilização do primeiro release público ainda será definida antes da publicação.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "A forma definitiva de citação será disponibilizada junto ao primeiro release público.",
      ),
    ).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/doi:|10\.\d{4,9}\//i);
    expect(container.textContent).not.toMatch(/CC BY|CC0|ODbL|MIT License/i);
  });

  it("keeps the methodology link available", () => {
    render(<DataPage />);
    expect(screen.getByRole("link", { name: /Entender como os indicadores são calculados/i })).toHaveAttribute(
      "href",
      "/metodologia",
    );
  });
});

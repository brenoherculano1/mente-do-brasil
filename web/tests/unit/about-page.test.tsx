import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AboutPage } from "@/features/about/AboutPage";
import { ABOUT_PAGE, ABOUT_PRINCIPLES } from "@/lib/about-page";

describe("about page", () => {
  it("renders the institutional positioning and current scope", () => {
    render(<AboutPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Sobre o Mente do Brasil" }),
    ).toBeInTheDocument();
    expect(screen.getByText(ABOUT_PAGE.positioning)).toBeInTheDocument();
    expect(screen.getByText("439")).toBeInTheDocument();
    expect(screen.getByText("5.570")).toBeInTheDocument();
    expect(screen.getByText("2022–2024")).toBeInTheDocument();
    expect(screen.getByText("Dezembro de 2024")).toBeInTheDocument();
  });

  it("states independence, public-data use, and government disclaimer", () => {
    render(<AboutPage />);
    expect(screen.getByText(ABOUT_PAGE.independenceStatement)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(ABOUT_PAGE.governmentDisclaimer))).toBeInTheDocument();
    expect(screen.getAllByText(/dados públicos/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/não é um sistema oficial/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/não implica vínculo institucional, endosso ou participação/i)).toBeInTheDocument();
  });

  it("keeps release and manuscript status conservative", () => {
    render(<AboutPage />);
    expect(screen.getByText("NOT_RELEASED")).toBeInTheDocument();
    expect(screen.getByText(ABOUT_PAGE.publicReleaseCopy)).toBeInTheDocument();
    expect(screen.getByText(/ainda não foi publicado publicamente/i)).toBeInTheDocument();
    expect(screen.getByText(ABOUT_PAGE.manuscriptStatus)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(ABOUT_PAGE.manuscriptTitle))).toBeInTheDocument();
  });

  it("renders required links and what-it-is-not section", () => {
    render(<AboutPage />);
    expect(screen.getByRole("link", { name: "Explorar o Brasil" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Entender a metodologia" })).toHaveAttribute(
      "href",
      "/metodologia",
    );
    expect(screen.getByRole("link", { name: "Ver dados e versões" })).toHaveAttribute("href", "/dados");
    expect(
      screen.getByRole("heading", { level: 2, name: "O que o Mente do Brasil não é" }),
    ).toBeInTheDocument();
  });

  it("renders six principles without commercial or invented-governance claims", () => {
    const { container } = render(<AboutPage />);
    expect(ABOUT_PRINCIPLES).toHaveLength(6);
    for (const [title] of ABOUT_PRINCIPLES) {
      expect(screen.getByRole("heading", { level: 3, name: title })).toBeInTheDocument();
    }
    expect(container.textContent).not.toMatch(/MedLegacy|fundador|conselho científico|parceiros|patrocinadores/i);
    expect(container.textContent).not.toMatch(/revolucionando|transformando vidas|dados que salvam vidas/i);
  });

  it("avoids problematic scientific and publication claims outside explicit limitations", () => {
    const { container } = render(<AboutPage />);
    const text = container.textContent || "";
    expect(text).not.toMatch(/déficit assistencial|necessidade não atendida|hotspot de doença mental/i);
    expect(text).not.toMatch(/melhores regiões|piores regiões|recomendamos/i);
    expect(text).not.toMatch(/published|publicado no Health & Place|accepted|aceito|in press|peer-reviewed/i);
    expect(text).not.toMatch(/parceria com Ministério|parceria com DATASUS|parceria com IBGE/i);
    expect(text).not.toMatch(/plataforma oficial|produto do SUS/i);
  });
});

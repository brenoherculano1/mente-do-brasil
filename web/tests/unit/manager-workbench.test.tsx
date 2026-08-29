import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ManagerWorkbench } from "@/features/manager/ManagerWorkbench";

vi.mock("@/lib/api/client", () => ({
  getManagerBrief: vi.fn(),
  getManagerCompare: vi.fn(() => new Promise(() => {})),
  lookupMunicipality: vi.fn(),
  searchHealthRegions: vi.fn(() => Promise.resolve({ items: [] })),
}));

describe("ManagerWorkbench", () => {
  it("renders empty state without selecting a random region", () => {
    render(<ManagerWorkbench />);
    expect(screen.getAllByText("Modo Gestor")[0]).toBeInTheDocument();
    expect(screen.getByText("Escolha uma Região de Saúde para começar.")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Visão territorial" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("starts in compare mode when URL compare state exists", () => {
    render(<ManagerWorkbench initialCompare="12001,31001" />);
    expect(screen.getByRole("tab", { name: "Comparar territórios" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("2 a 4 Regiões de Saúde")).toBeInTheDocument();
  });
});

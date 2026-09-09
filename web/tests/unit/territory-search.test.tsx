import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TerritorySearch } from "@/features/explorer/TerritorySearch";

vi.mock("@/lib/api/client", () => ({
  lookupMunicipality: vi.fn(),
  searchHealthRegions: vi.fn(() => Promise.resolve({ items: [{
    health_region_code: "26005",
    health_region_name: "Garanhuns",
    uf: "PE",
    geography_version: "test",
    release_id: "test",
  }] })),
  searchMunicipalities: vi.fn(() => Promise.resolve([{
    municipality_code_ibge: "2606002",
    municipality_name: "Garanhuns",
    uf: "PE",
    health_region_code: "26005",
    health_region_name: "Garanhuns",
    geography_version: "test",
  }])),
}));

describe("TerritorySearch", () => {
  it("confirms a municipality selection and closes the results", async () => {
    const onSelectRegion = vi.fn();
    render(<TerritorySearch onSelectRegion={onSelectRegion} />);

    fireEvent.change(screen.getByLabelText("Encontre sua região"), { target: { value: "garanhuns" } });
    const results = await screen.findByRole("list", { name: "Resultados da busca territorial" });
    expect(results.querySelectorAll("button")).toHaveLength(1);
    fireEvent.click(results.querySelector("button")!);

    expect(onSelectRegion).toHaveBeenCalledWith("26005");
    expect(screen.getByRole("status")).toHaveTextContent(
      "Garanhuns pertence à Região de Saúde Garanhuns (PE)",
    );
    await waitFor(() => expect(screen.queryByRole("list", { name: "Resultados da busca territorial" })).not.toBeInTheDocument());
  });
});

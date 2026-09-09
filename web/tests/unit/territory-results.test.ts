import { describe, expect, it } from "vitest";
import { mergeTerritoryResults, type TerritorySearchResult } from "@/lib/territory-results";

function result(overrides: Partial<TerritorySearchResult>): TerritorySearchResult {
  return {
    health_region_code: "26003",
    health_region_name: "Caruaru",
    uf: "PE",
    geography_version: "test",
    release_id: "test",
    ...overrides,
  };
}

describe("mergeTerritoryResults", () => {
  it("shows a same-name municipality and health region only once", () => {
    const merged = mergeTerritoryResults(
      [result({ municipality_name: "Caruaru" })],
      [result({})],
    );

    expect(merged).toHaveLength(1);
    expect(merged[0].municipality_name).toBe("Caruaru");
  });

  it("preserves different municipalities from the same health region", () => {
    const merged = mergeTerritoryResults(
      [
        result({ municipality_name: "Caruaru" }),
        result({ municipality_name: "Bezerros" }),
      ],
      [result({})],
    );

    expect(merged.map((item) => item.municipality_name)).toEqual(["Caruaru", "Bezerros"]);
  });

  it("normalizes accents and letter case before removing the duplicate region", () => {
    const merged = mergeTerritoryResults(
      [result({ municipality_name: "São João Del Rei", health_region_name: "Sao Joao del Rei" })],
      [result({ health_region_name: "Sao Joao del Rei" })],
    );

    expect(merged).toHaveLength(1);
  });
});

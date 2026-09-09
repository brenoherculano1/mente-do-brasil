import type { HealthRegionLookup } from "@/types/api";

export type TerritorySearchResult = HealthRegionLookup & { municipality_name?: string };

function normalizeName(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLocaleLowerCase("pt-BR");
}

export function mergeTerritoryResults(
  municipalities: TerritorySearchResult[],
  regions: TerritorySearchResult[],
) {
  const municipalityRegionNames = new Set(
    municipalities
      .filter(
        (item) =>
          item.municipality_name &&
          normalizeName(item.municipality_name) === normalizeName(item.health_region_name),
      )
      .map((item) => item.health_region_code),
  );

  return [...municipalities, ...regions]
    .filter(
      (item) => item.municipality_name || !municipalityRegionNames.has(item.health_region_code),
    )
    .filter(
      (item, index, items) =>
        items.findIndex(
          (candidate) =>
            candidate.health_region_code === item.health_region_code &&
            candidate.municipality_name === item.municipality_name,
        ) === index,
    );
}

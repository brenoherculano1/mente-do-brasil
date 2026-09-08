"use client";

import { useEffect, useState } from "react";
import { lookupMunicipality, searchHealthRegions, searchMunicipalities } from "@/lib/api/client";
import type { HealthRegionLookup, MunicipalityHealthRegion } from "@/types/api";

type SearchResult = HealthRegionLookup & { municipality_name?: string };

export function TerritorySearch({ onSelectRegion }: { onSelectRegion: (code: string) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "empty" | "error">("idle");

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      setStatus("idle");
      return;
    }
    const timeout = window.setTimeout(async () => {
      setStatus("loading");
      try {
        if (/^\d{7}$/.test(trimmed)) {
          const municipality = await lookupMunicipality(trimmed);
          setResults([
            {
              health_region_code: municipality.health_region_code,
              health_region_name: municipality.health_region_name,
              uf: municipality.uf,
              geography_version: municipality.geography_version,
              release_id: "",
              municipality_name: municipality.municipality_name,
            },
          ]);
          setStatus("idle");
          return;
        }
        const [regions, municipalities] = await Promise.all([
          searchHealthRegions(trimmed),
          searchMunicipalities(trimmed),
        ]);
        const municipalityResults: SearchResult[] = municipalities.map(
          (municipality: MunicipalityHealthRegion) => ({
            health_region_code: municipality.health_region_code,
            health_region_name: municipality.health_region_name,
            uf: municipality.uf,
            geography_version: municipality.geography_version,
            release_id: "",
            municipality_name: municipality.municipality_name,
          }),
        );
        const regionResults: SearchResult[] = regions.items;
        const combined = [...municipalityResults, ...regionResults].filter(
          (item, index, items) =>
            items.findIndex(
              (candidate) =>
                candidate.health_region_code === item.health_region_code &&
                candidate.municipality_name === item.municipality_name,
            ) === index,
        );
        setResults(combined.slice(0, 10));
        setStatus(combined.length === 0 ? "empty" : "idle");
      } catch {
        setResults([]);
        setStatus("error");
      }
    }, 260);
    return () => window.clearTimeout(timeout);
  }, [query]);

  return (
    <div className="control-group">
      <label className="field-label" htmlFor="territory-search">
        Encontre sua região
      </label>
      <input
        className="input"
        id="territory-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Digite uma cidade ou Região de Saúde"
        autoComplete="off"
      />
      <p className="small-text">
        Busque por qualquer município brasileiro ou pelo nome da Região de Saúde.
      </p>
      {status === "loading" && <div className="skeleton" aria-label="Carregando busca" />}
      {status === "error" && (
        <p className="small-text" role="alert">
          Não foi possível carregar os dados agora.
        </p>
      )}
      {status === "empty" && <p className="small-text">Nenhuma Região de Saúde encontrada.</p>}
      {results.length > 0 && (
        <ul className="result-list" aria-label="Resultados da busca territorial">
          {results.map((result) => (
            <li key={result.health_region_code}>
              <button
                className="result-button"
                onClick={() => onSelectRegion(result.health_region_code)}
              >
                <strong>{result.health_region_name}</strong>
                <span className="small-text">
                  {result.municipality_name
                    ? `${result.municipality_name} · ${result.uf}`
                    : result.uf}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

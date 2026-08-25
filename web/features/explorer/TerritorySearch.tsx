"use client";

import { useEffect, useState } from "react";
import { lookupMunicipality, searchHealthRegions } from "@/lib/api/client";
import type { HealthRegionLookup } from "@/types/api";

export function TerritorySearch({ onSelectRegion }: { onSelectRegion: (code: string) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<HealthRegionLookup[]>([]);
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
              release_id: "MDB_ANALYTICAL_2024_1",
            },
          ]);
          setStatus("idle");
          return;
        }
        const response = await searchHealthRegions(trimmed);
        setResults(response.items);
        setStatus(response.items.length === 0 ? "empty" : "idle");
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
        Busca territorial
      </label>
      <input
        className="input"
        id="territory-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Região de Saúde ou código IBGE do município"
        autoComplete="off"
      />
      <p className="small-text">
        Região de Saúde pode ser localizada por nome ou código. Município, nesta
        etapa, é resolvido pelo código IBGE de 7 dígitos.
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
                  {result.uf} · {result.health_region_code}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

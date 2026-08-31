"use client";

import Link from "next/link";
import { useState } from "react";
import { VALID_UFS } from "@/lib/states";
import type { FinancingResponse, HealthRegionFeatureCollection } from "@/types/api";
import { useResource } from "@/features/advanced/useResource";
import { OverviewMap } from "@/features/advanced/OverviewMap";

const currency = (value: number | null) => value === null ? "Indisponível" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
export function FinancingPage() {
  const [year, setYear] = useState(2024); const [uf, setUf] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const { data, loading, error } = useResource<FinancingResponse>(`/api/v1/financing/health-regions?year=${year}`);
  const map = useResource<HealthRegionFeatureCollection>("/api/v1/map/health-regions?include_geometry=true&geometry_profile=overview");
  const series = useResource<FinancingResponse>(selected ? `/api/v1/health-regions/${selected}/financing` : null);
  const records = data?.records.filter((row) => !uf || row.uf === uf) ?? [];
  const byCode = new Map(records.map((row) => [row.health_region_code, row]));
  const geometry: GeoJSON.FeatureCollection | null = map.data && data ? { type: "FeatureCollection", features: map.data.features.filter((feature) => byCode.has(feature.properties.health_region_code)).map((feature) => ({
    ...feature, properties: { health_region_code: feature.properties.health_region_code,
      health_expenditure_per_capita_brl: byCode.get(feature.properties.health_region_code)?.health_expenditure_per_capita_brl ?? null },
  })) } : null;
  return <main className="page-shell"><section className="intro"><h1>Contexto de financiamento da saúde</h1>
    <p>Esta camada descreve o contexto geral de financiamento da saúde e não mede gasto específico em saúde mental.</p></section>
    <div className="advanced-controls"><label>Exercício<select className="input" value={year} onChange={(e) => setYear(Number(e.target.value))}>{[2022, 2023, 2024].map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>UF<select className="input" value={uf} onChange={(e) => setUf(e.target.value)}><option value="">Brasil</option>{VALID_UFS.map((value) => <option key={value}>{value}</option>)}</select></label></div>
    <p className="small-text">Valores em reais correntes do respectivo exercício; comparações entre anos não representam variação real descontada da inflação.</p>
    {loading && <p role="status">Carregando financiamento...</p>}{error && <p role="alert">{error}</p>}
    <OverviewMap data={geometry} selected={selected} onSelect={setSelected} field="health_expenditure_per_capita_brl" money />
    <p className="small-text">R$/habitante: menos de 1.000 · 1.000–2.000 · 2.000–4.000 · 4.000–8.000 · 8.000 ou mais. Cinza: dados parciais/indisponível.</p>
    {selected && <section><h2>{byCode.get(selected)?.health_region_name ?? selected}</h2>
      <Link href={`/regiao/${selected}`}>Abrir perfil regional</Link>
      <div className="table-wrap"><table><caption>Série nominal</caption><thead><tr><th>Ano</th><th>Total em saúde</th><th>Por habitante</th><th>Cobertura municipal</th></tr></thead><tbody>
        {series.data?.records.map((row) => <tr key={row.year}><th scope="row">{row.year}</th><td>{currency(row.total_health_expenditure_brl)}</td><td>{currency(row.health_expenditure_per_capita_brl)}</td><td>{row.municipalities_observed}/{row.municipalities_expected}{!row.headline_available && " · Dados parciais"}</td></tr>)}
      </tbody></table></div></section>}
    <div className="table-wrap"><table><thead><tr><th>Região</th><th>UF</th><th>Total em saúde</th><th>R$/habitante</th><th>Cobertura</th></tr></thead><tbody>
      {records.map((row) => <tr key={row.health_region_code}><th scope="row"><button type="button" className="inline-link" onClick={() => setSelected(row.health_region_code)}>{row.health_region_name}</button></th><td>{row.uf}</td><td>{currency(row.total_health_expenditure_brl)}</td><td>{currency(row.health_expenditure_per_capita_brl)}</td><td>{row.municipalities_observed}/{row.municipalities_expected} · {row.headline_available ? "Completa" : "Dados parciais/indisponível"}</td></tr>)}
    </tbody></table></div>
  </main>;
}

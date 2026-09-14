"use client";

import Link from "next/link";
import { useState } from "react";
import { VALID_UFS } from "@/lib/states";
import type { FinancingResponse, HealthRegionFeatureCollection } from "@/types/api";
import { useResource } from "@/features/advanced/useResource";
import { OverviewMap } from "@/features/advanced/OverviewMap";
import { ShareButton } from "@/features/share/ShareButton";
import { summarizeFinancing } from "@/lib/financing";

const currency = (value: number | null) => value === null ? "Indisponível" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
const percent = (value: number | null) => value === null ? "Indisponível" : new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }).format(value);

export function FinancingPage() {
  const [year, setYear] = useState(2024); const [uf, setUf] = useState("");
  const [startYear, setStartYear] = useState(2022);
  const [endYear, setEndYear] = useState(2024);
  const [selected, setSelected] = useState<string | null>(null);
  const { data, loading, error } = useResource<FinancingResponse>(`/api/v1/financing/health-regions?year=${year}`);
  const startData = useResource<FinancingResponse>(`/api/v1/financing/health-regions?year=${startYear}`);
  const endData = useResource<FinancingResponse>(`/api/v1/financing/health-regions?year=${endYear}`);
  const map = useResource<HealthRegionFeatureCollection>("/api/v1/map/health-regions?include_geometry=true&geometry_profile=overview");
  const series = useResource<FinancingResponse>(selected ? `/api/v1/health-regions/${selected}/financing` : null);
  const records = data?.records.filter((row) => !uf || row.uf === uf) ?? [];
  const startSummary = summarizeFinancing(startData.data?.records ?? [], uf);
  const endSummary = summarizeFinancing(endData.data?.records ?? [], uf);
  const nominalDifference = startSummary.total === null || endSummary.total === null
    ? null
    : endSummary.total - startSummary.total;
  const nominalVariation = startSummary.total && nominalDifference !== null
    ? nominalDifference / startSummary.total
    : null;
  const scopeLabel = uf || "Brasil";
  const byCode = new Map(records.map((row) => [row.health_region_code, row]));
  const geometry: GeoJSON.FeatureCollection | null = map.data && data ? { type: "FeatureCollection", features: map.data.features.filter((feature) => byCode.has(feature.properties.health_region_code)).map((feature) => ({
    ...feature, properties: { health_region_code: feature.properties.health_region_code,
      health_expenditure_per_capita_brl: byCode.get(feature.properties.health_region_code)?.health_expenditure_per_capita_brl ?? null },
  })) } : null;
  return <main className="page-shell financing-page"><section className="intro"><p className="eyebrow">Contexto para interpretar a rede</p><h1>Recursos e estrutura de saúde</h1>
    <p>Veja quanto os municípios de cada Região de Saúde registraram em despesas gerais de saúde e use esse contexto ao investigar a organização da atenção em saúde mental.</p>
    <div className="notice financing-caution"><strong>Importante</strong><p>Os valores são de toda a saúde. Eles não medem gasto específico em saúde mental e, isoladamente, não indicam suficiência, eficiência ou qualidade.</p></div></section>
    <div className="advanced-controls"><label>Exercício<select className="input" value={year} onChange={(e) => setYear(Number(e.target.value))}>{[2022, 2023, 2024].map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>UF<select className="input" value={uf} onChange={(e) => setUf(e.target.value)}><option value="">Brasil</option>{VALID_UFS.map((value) => <option key={value}>{value}</option>)}</select></label></div>
    <p className="small-text">Valores em reais correntes do respectivo exercício; comparações entre anos não representam variação real descontada da inflação.</p>
    <section className="financing-comparison" aria-labelledby="financing-comparison-title">
      <div className="section-heading-inline">
        <div><p className="eyebrow">Comparar exercícios</p><h2 id="financing-comparison-title">Despesa geral em saúde: {startYear} e {endYear}</h2></div>
        <ShareButton title={`Despesa geral em saúde — ${scopeLabel} | Mente do Brasil`} text={`Compare a despesa geral em saúde registrada em ${scopeLabel}. Os valores são nominais e não representam gasto específico em saúde mental.`} />
      </div>
      <div className="year-comparison-controls">
        <label>Ano inicial<select className="input" value={startYear} onChange={(event) => setStartYear(Number(event.target.value))}>{[2022, 2023, 2024].map((value) => <option key={value}>{value}</option>)}</select></label>
        <label>Ano final<select className="input" value={endYear} onChange={(event) => setEndYear(Number(event.target.value))}>{[2022, 2023, 2024].map((value) => <option key={value}>{value}</option>)}</select></label>
      </div>
      <div className="financing-summary-grid">
        <Summary label={`${startYear} · ${scopeLabel}`} value={currency(startSummary.total)} coverage={`${startSummary.observed}/${startSummary.expected} regiões com valor`} />
        <Summary label={`${endYear} · ${scopeLabel}`} value={currency(endSummary.total)} coverage={`${endSummary.observed}/${endSummary.expected} regiões com valor`} />
        <Summary label="Diferença nominal" value={currency(nominalDifference)} coverage={percent(nominalVariation)} />
      </div>
      <p className="metric-interpretation">A comparação soma apenas Regiões de Saúde com valor disponível em cada exercício. Diferença nominal inclui inflação e mudanças de cobertura; não mede aumento real de investimento.</p>
    </section>
    <div className="notice financing-counter-limit"><strong>Por que não há um contador em tempo real?</strong><p>A fonte atual registra despesas anuais de toda a saúde. Ela não separa, de forma comparável, o gasto específico em saúde mental e não é atualizada em tempo real. Exibir um contador desse tipo produziria uma precisão que os dados não sustentam.</p></div>
    <p className="coverage-2025-note"><strong>Por que 2025 não aparece?</strong> A cobertura pública permanece em 2022–2024 porque 2025 ainda não passou pelo mesmo ciclo de disponibilidade, compatibilização territorial, checagem de completude e validação aplicado aos anos publicados.</p>
    {loading && <p role="status">Carregando recursos...</p>}{error && <p role="alert">{error}</p>}
    <OverviewMap data={geometry} selected={selected} onSelect={setSelected} field="health_expenditure_per_capita_brl" money />
    <p className="small-text">R$/habitante: menos de 1.000 · 1.000–2.000 · 2.000–4.000 · 4.000–8.000 · 8.000 ou mais. Cinza: dados parciais/indisponível.</p>
    {selected && <section><h2>{byCode.get(selected)?.health_region_name ?? selected}</h2>
      <Link href={`/regiao/${selected}`}>Abrir perfil regional</Link>
      <p>Use a série para observar o contexto local ao longo do tempo. Valores correntes não permitem concluir crescimento real sem ajuste de inflação.</p>
      <div className="table-wrap"><table><caption>Recursos gerais de saúde registrados</caption><thead><tr><th>Ano</th><th>Total em saúde</th><th>Por habitante</th><th>Cobertura municipal</th></tr></thead><tbody>
        {series.data?.records.map((row) => <tr key={row.year}><th scope="row">{row.year}</th><td>{currency(row.total_health_expenditure_brl)}</td><td>{currency(row.health_expenditure_per_capita_brl)}</td><td>{row.municipalities_observed}/{row.municipalities_expected}{!row.headline_available && " · Dados parciais"}</td></tr>)}
      </tbody></table></div></section>}
    <div className="table-wrap"><table><thead><tr><th>Região</th><th>UF</th><th>Total em saúde</th><th>R$/habitante</th><th>Cobertura</th></tr></thead><tbody>
      {records.map((row) => <tr key={row.health_region_code}><th scope="row"><button type="button" className="inline-link" onClick={() => setSelected(row.health_region_code)}>{row.health_region_name}</button></th><td>{row.uf}</td><td>{currency(row.total_health_expenditure_brl)}</td><td>{currency(row.health_expenditure_per_capita_brl)}</td><td>{row.municipalities_observed}/{row.municipalities_expected} · {row.headline_available ? "Completa" : "Dados parciais/indisponível"}</td></tr>)}
    </tbody></table></div>
  </main>;
}

function Summary({ label, value, coverage }: { label: string; value: string; coverage: string }) {
  return <div className="financing-summary"><span>{label}</span><strong>{value}</strong><small>{coverage}</small></div>;
}

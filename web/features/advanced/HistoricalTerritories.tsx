"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { request } from "@/lib/api/client";
import { formatInteger, formatRate, formatScore } from "@/lib/format";
import { METRICS } from "@/lib/metrics";
import { describeMismatch } from "@/lib/public-language";
import { validateHistoricalResponse, type HistoricalRecord, type HistoricalResponse, type HistoricalYear } from "@/lib/historical";
import { TerritorySearch } from "@/features/explorer/TerritorySearch";
import { ScoreOverview } from "@/features/profile/ScoreOverview";

export function HistoricalTerritories({ year, code, compare = "12001,31001" }: {
  year: HistoricalYear; code?: string; compare?: string;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const [records, setRecords] = useState<HistoricalRecord[] | null>(null);
  const [error, setError] = useState(false);
  const [codes, setCodes] = useState(() => code ? [code] : [...new Set(compare.split(",").filter((v) => /^\d{5}$/.test(v)))].slice(0, 4));
  useEffect(() => {
    let active = true;
    request<HistoricalResponse>(`/api/v1/historical/health-regions?year=${year}`)
      .then((data) => { const valid = validateHistoricalResponse(data, year); if (active) setRecords(valid.records); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [year]);
  function select(next: string[]) {
    setCodes(next);
    const query = new URLSearchParams(params.toString());
    query.set("compare", next.join(","));
    router.replace(`/comparar?${query}`, { scroll: false });
  }
  const selected = codes.map((value) => records?.find((r) => r.health_region_code === value)).filter((r): r is HistoricalRecord => Boolean(r));
  return <div className="page-shell" data-testid="historical-territories" data-year={year}>
    <header className="intro">
      <p className="eyebrow">Dados históricos · {year}</p>
      <h1>{code ? selected[0]?.health_region_name ?? "Perfil regional" : "Compare regiões"}</h1>
      <p>Necessidade: janela {year - 2}–{year}. Estrutura: dezembro de {year}. As 439 Regiões de Saúde mantêm a composição territorial congelada de referência.</p>
    </header>
    {!code && <section aria-label="Seleção de regiões">
      <h2>Regiões selecionadas ({codes.length}/4)</h2>
      <TerritorySearch onSelectRegion={(value) => { if (!codes.includes(value) && codes.length < 4) select([...codes, value]); }} />
      <div className="nav-links">{codes.map((value) => <button className="text-button" key={value} onClick={() => select(codes.filter((c) => c !== value))}>
        {records?.find((r) => r.health_region_code === value)?.health_region_name ?? value} ×
      </button>)}</div>
      {codes.length < 2 && <p>Selecione pelo menos duas regiões para comparar.</p>}
    </section>}
    {error && <p role="alert">Não foi possível consultar {year}. Nenhum dado de outro ano foi usado. Recarregue a página para tentar novamente.</p>}
    {!records && !error && <p role="status">Carregando observações de {year}...</p>}
    {records && selected.length !== codes.length && <p role="alert">Uma região selecionada não possui observação neste produto histórico.</p>}
    {selected.map((r) => <section className="profile-section" key={r.health_region_code} data-region={r.health_region_code}>
      <h2><Link href={`/regiao/${r.health_region_code}?ano=${year}`}>{r.health_region_name}</Link> · {r.uf}</h2>
      <p>População de referência: {formatInteger(r.population)}</p>
      <ScoreOverview need={r.need_score} capacity={r.capacity_score} mismatch={r.mismatch_score} />
      <p>{describeMismatch(r.mismatch_score)}</p>
      <dl className="home-facts">
        <div><dt>{formatInteger(r.caps_count)}</dt><dd>CAPS</dd></div>
        <div><dt>{formatInteger(r.mental_health_beds_sus_count)}</dt><dd>Leitos SUS de saúde mental</dd></div>
        <div><dt>{formatRate(r.psychiatrist_fte)}</dt><dd>Jornadas equivalentes de psiquiatras, não pessoas únicas</dd></div>
        <div><dt>{formatInteger(r.psychiatric_admissions)}</dt><dd>Internações em {r.need_window_start}–{r.need_window_end}</dd></div>
      </dl>
    </section>)}
    {selected.length > 0 && <section className="profile-section">
      <h2>Indicadores de {year}</h2>
      <div className="table-wrap" tabIndex={0} role="region" aria-label="Indicadores históricos">
        <table><thead><tr><th>Indicador</th>{selected.map((r) => <th key={r.health_region_code}>{r.health_region_name}</th>)}</tr></thead>
          <tbody>{METRICS.map((m) => <tr key={m.id}><th scope="row">{m.label} ({m.unit})</th>{selected.map((r) => <td key={r.health_region_code} data-metric={m.id}>{m.scale === "rate" ? formatRate(r[m.id]) : formatScore(r[m.id])}</td>)}</tr>)}</tbody>
        </table>
      </div>
      {!code && selected.length >= 2 && <><h2>Leitura da comparação</h2><p>{selected.map((r) => `${r.health_region_name}: ${describeMismatch(r.mismatch_score)}`).join(" ")}</p></>}
      <p>Os índices descrevem posições relativas no mesmo ano, não qualidade do cuidado ou quantidade de recursos que faltam. O Radar, os agrupamentos espaciais e as comparações entre regiões semelhantes pertencem à edição analítica de 2024 e não são reproduzidos para {year}.</p>
    </section>}
  </div>;
}

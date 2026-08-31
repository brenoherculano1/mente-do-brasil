"use client";

import Link from "next/link";
import { useState } from "react";
import { VALID_UFS } from "@/lib/states";
import { FAMILIES, type Changes } from "./types";
import { useResource } from "./useResource";
import { OverviewMap } from "./OverviewMap";
import { TimelinePanel } from "./TimelinePanel";

export function ChangesPage() {
  const [period, setPeriod] = useState("2022,2024");
  const [uf, setUf] = useState(""); const [family, setFamily] = useState("");
  const [minimum, setMinimum] = useState("1"); const [q, setQ] = useState("");
  const [sort, setSort] = useState("families"); const [selected, setSelected] = useState<string | null>(null);
  const [start, end] = period.split(",");
  const params = new URLSearchParams({ from_year: start, to_year: end, min_change_families: minimum,
    include_geometry: "true", sort });
  if (uf) params.set("uf", uf); if (family) params.set("signal", family); if (q) params.set("q", q);
  const { data, error, loading } = useResource<Changes>(`/api/v1/changes/health-regions?${params}`);
  const region = data?.records.find((row) => row.health_region_code === selected);
  const fmt = (n: number) => new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3, signDisplay: "always" }).format(n);
  return <main className="page-shell"><section className="intro"><h1>Mudanças territoriais</h1>
    <p>Onde a posição territorial mudou de forma relevante entre os períodos comparáveis?</p></section>
    <div className="advanced-controls">
      <label>Período<select className="input" value={period} onChange={(e) => setPeriod(e.target.value)}>{["2022,2023", "2023,2024", "2022,2024"].map((value) => <option key={value} value={value}>{value.replace(",", " → ")}</option>)}</select></label>
      <label>UF<select className="input" value={uf} onChange={(e) => setUf(e.target.value)}><option value="">Brasil</option>{VALID_UFS.map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>Família<select className="input" value={family} onChange={(e) => setFamily(e.target.value)}><option value="">Todas</option>{Object.entries(FAMILIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Mínimo de famílias<select className="input" value={minimum} onChange={(e) => setMinimum(e.target.value)}>{[0, 1, 2, 3, 4, 5].map((n) => <option key={n}>{n}</option>)}</select></label>
      <label>Buscar região<input className="input" value={q} onChange={(e) => setQ(e.target.value)} /></label>
      <label>Ordenar<select className="input" value={sort} onChange={(e) => setSort(e.target.value)}><option value="families">Mais famílias atendidas</option><option value="mismatch">Maior mudança de Mismatch</option><option value="name">Alfabética</option></select></label>
    </div>
    {loading && <p role="status">Carregando mudanças...</p>}{error && <p role="alert">{error}</p>}
    {data && <><OverviewMap data={data.geometry} field="matched_change_families" selected={selected} onSelect={setSelected} />
      <p>Famílias de mudança relativa atendidas: 0–5. {data.total_matching} regiões no filtro.</p>
      {region && <section><h2>{region.health_region_name} · {region.uf}</h2>
        <p>Δ Need {fmt(region.delta_need_score)} · Δ Capacity {fmt(region.delta_capacity_score)} · Δ Mismatch {fmt(region.delta_mismatch_score)}</p>
        <ul>{Object.entries(FAMILIES).filter(([key]) => region[key as keyof typeof FAMILIES]).map(([key, label]) => <li key={key}>{label}</li>)}</ul>
        <p><Link href={`/regiao/${selected}#evolucao`}>Ver evolução da região</Link> · <Link href={`/gestor?regiao=${selected}`}>Abrir no Modo Gestor</Link></p>
        <TimelinePanel code={region.health_region_code} /></section>}
      <div className="table-wrap"><table><thead><tr><th>Região</th><th>UF</th><th>Famílias</th><th>Δ Mismatch</th></tr></thead><tbody>
        {data.records.map((row) => <tr key={row.health_region_code}><th scope="row"><button type="button" className="inline-link" onClick={() => setSelected(row.health_region_code)}>{row.health_region_name}</button></th><td>{row.uf}</td><td>{row.matched_change_families}</td><td>{fmt(row.delta_mismatch_score)}</td></tr>)}
      </tbody></table></div>{data.records.length === 0 && <p>Nenhuma região corresponde aos filtros.</p>}</>}
  </main>;
}

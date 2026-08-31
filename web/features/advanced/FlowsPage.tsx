"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import type { HealthRegionLookup, PaginatedResponse } from "@/types/api";
import type { Flow } from "./types";
import { useResource } from "./useResource";

function FlowMap({ flow }: { flow: Flow }) {
  const element = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!element.current) return;
    const origin: [number, number] = [flow.region.longitude, flow.region.latitude];
    const connections = flow.connections.filter((row) => row.admissions !== null && !row.partial && row.health_region_code !== flow.health_region_code);
    const data: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: connections.map((row) => ({
      type: "Feature", properties: { health_region_code: row.health_region_code },
      geometry: { type: "LineString", coordinates: [origin, [row.longitude, row.latitude]] },
    })) };
    const points: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [origin, ...connections.map((r) => [r.longitude, r.latitude])].map((coordinates) => ({
      type: "Feature", properties: {}, geometry: { type: "Point", coordinates },
    })) };
    const map = new maplibregl.Map({ container: element.current, center: origin, zoom: 6,
      style: { version: 8, sources: { flows: { type: "geojson", data }, points: { type: "geojson", data: points } }, layers: [
        { id: "background", type: "background", paint: { "background-color": "#edf1f4" } },
        { id: "flows", type: "line", source: "flows", paint: { "line-color": "#5c778b", "line-width": 2 } },
        { id: "points", type: "circle", source: "points", paint: { "circle-color": "#294b63", "circle-radius": 5 } },
      ] }, attributionControl: false });
    const bounds = new maplibregl.LngLatBounds(origin, origin);
    connections.forEach((row) => bounds.extend([row.longitude, row.latitude]));
    map.fitBounds(bounds, { padding: 55, maxZoom: 7, duration: 0 });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    return () => map.remove();
  }, [flow]);
  return <div ref={element} className="map-container" style={{ height: 400 }} aria-label="Conexões territoriais não suprimidas" />;
}

export function FlowSummary({ flow }: { flow: Flow }) {
  const percent = (value: number | null) => value === null ? "Indisponível" : new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1 }).format(value);
  return <><dl className="advanced-stats"><div><dt>AIHs de residentes</dt><dd>{flow.summary.total_admissions?.toLocaleString("pt-BR") ?? "Indisponível"}</dd></div>
    <div><dt>Na própria região</dt><dd>{percent(flow.summary.within_region_share)}</dd></div><div><dt>Fora da região</dt><dd>{percent(flow.summary.outflow_share)}</dd></div><div><dt>Fora da UF</dt><dd>{percent(flow.summary.cross_state_outflow_share)}</dd></div></dl>
    <div className="table-wrap"><table><thead><tr><th>{flow.perspective === "origin" ? "Destino" : "Origem"}</th><th>UF</th><th>Internações/AIHs</th></tr></thead><tbody>
      {flow.connections.map((row) => <tr key={row.health_region_code}><th scope="row"><Link href={`/regiao/${row.health_region_code}`}>{row.health_region_name}</Link></th><td>{row.uf}</td><td>{row.admissions === null ? "Indisponível (supressão)" : row.admissions.toLocaleString("pt-BR")}</td></tr>)}
    </tbody></table></div></>;
}

export function FlowsPage({ initialCode }: { initialCode?: string }) {
  const [q, setQ] = useState(""); const [code, setCode] = useState(initialCode ?? "");
  const [perspective, setPerspective] = useState("origin");
  const search = useResource<PaginatedResponse<HealthRegionLookup>>(q.length >= 2 ? `/api/v1/health-regions?q=${encodeURIComponent(q)}&limit=8` : null);
  const { data, loading, error } = useResource<Flow>(code ? `/api/v1/health-regions/${code}/flows?perspective=${perspective}&limit=8` : null);
  return <main className="page-shell"><section className="intro"><h1>Fluxos territoriais de internações psiquiátricas</h1>
    <p>Explore onde ocorrem as internações registradas de residentes das Regiões de Saúde.</p>
    <p>Os dados representam internações/AIHs, não pacientes únicos.</p></section>
    <div className="advanced-controls"><label>Região de Saúde<input className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nome ou código" /></label>
      <label>Perspectiva<select className="input" value={perspective} onChange={(e) => setPerspective(e.target.value)}><option value="origin">Saída de residentes</option><option value="destination">Internações realizadas na região</option></select></label></div>
    {search.data && <ul>{search.data.items.map((row) => <li key={row.health_region_code}><button type="button" className="inline-link" onClick={() => { setCode(row.health_region_code); setQ(""); }}>{row.health_region_name} · {row.uf}</button></li>)}</ul>}
    {!code && <p>Selecione uma Região de Saúde.</p>}{loading && <p role="status">Carregando fluxos...</p>}{error && <p role="alert">{error}</p>}
    {data && <><h2>{data.region.health_region_name} · {data.region.uf}</h2><FlowMap flow={data} /><p className="small-text">Até oito conexões. Pares com contribuições suprimidas não são desenhados. Referência: 2022–2024.</p><FlowSummary flow={data} /></>}
  </main>;
}

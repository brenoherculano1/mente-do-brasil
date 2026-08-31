"use client";

import { useState } from "react";
import { useResource } from "./useResource";
import type { Timeline } from "./types";
import type { MetricId } from "@/types/api";

const METRICS: [MetricId, string][] = [["need_score", "Need"], ["capacity_score", "Capacity"],
  ["mismatch_score", "Mismatch"], ["suicide_asmr", "Suicídio"], ["psychiatric_admission_rate", "Internações"],
  ["caps_rate", "CAPS"], ["mental_health_beds_sus_rate", "Leitos"], ["psychiatrist_fte_rate", "Psiquiatras FTE"]];
const number = (value: number) => new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(value);

export function TimelinePanel({ code }: { code: string }) {
  const { data, error, loading } = useResource<Timeline>(`/api/v1/health-regions/${code}/timeline`);
  const [metric, setMetric] = useState<MetricId>("need_score");
  return <section id="evolucao" aria-labelledby={`timeline-${code}`}>
    <h2 id={`timeline-${code}`}>Evolução territorial</h2>
    <label className="control-group"><span>Indicador</span><select className="input" value={metric} onChange={(event) => setMetric(event.target.value as MetricId)}>
      {METRICS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
    </select></label>
    {loading && <p role="status">Carregando evolução...</p>}{error && <p role="alert">{error}</p>}
    {data && <div className="table-wrap"><table><caption>Três âncoras comparáveis, sem suavização</caption>
      <thead><tr><th>Ano</th><th>{METRICS.find(([id]) => id === metric)?.[1]}</th><th>Janela de Need</th><th>Capacity</th></tr></thead>
      <tbody>{data.anchors.map((row) => <tr key={row.year}><th scope="row">{row.year}</th><td>{number(row[metric])}</td>
        <td>{row.need_window_start}–{row.need_window_end}</td><td>{row.capacity_competence}</td></tr>)}</tbody>
    </table></div>}
    <p className="small-text">Need utiliza janelas móveis de três anos. Capacity utiliza o registro de dezembro. As posições são relativas às regiões no respectivo período.</p>
  </section>;
}

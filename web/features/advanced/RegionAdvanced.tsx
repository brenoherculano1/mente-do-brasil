"use client";

import Link from "next/link";
import type { FinancingResponse } from "@/types/api";
import type { Flow } from "./types";
import { TimelinePanel } from "./TimelinePanel";
import { FlowSummary } from "./FlowsPage";
import { useResource } from "./useResource";

export function RegionAdvanced({ code }: { code: string }) {
  const finance = useResource<FinancingResponse>(`/api/v1/health-regions/${code}/financing`);
  const flows = useResource<Flow>(`/api/v1/health-regions/${code}/flows?limit=3`);
  const money = (value: number | null) => value === null ? "Indisponível (dados parciais)" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
  return <div className="advanced-region"><TimelinePanel code={code} />
    <section id="financiamento"><h2>Contexto de financiamento da saúde</h2>
      <p>Esta camada descreve o contexto geral de financiamento da saúde e não mede gasto específico em saúde mental.</p>
      {finance.error && <p role="alert">{finance.error}</p>}
      <div className="table-wrap"><table><thead><tr><th>Ano</th><th>Total em saúde</th><th>R$/habitante</th><th>Municípios</th></tr></thead><tbody>{finance.data?.records.map((r) => <tr key={r.year}><th>{r.year}</th><td>{money(r.total_health_expenditure_brl)}</td><td>{money(r.health_expenditure_per_capita_brl)}</td><td>{r.municipalities_observed}/{r.municipalities_expected}</td></tr>)}</tbody></table></div>
      <p className="small-text">Valores em reais correntes do respectivo exercício; comparações entre anos não representam variação real descontada da inflação.</p><Link href="/financiamento">Explorar financiamento</Link></section>
    <section id="fluxos"><h2>Fluxos de internações psiquiátricas</h2><p>Internações/AIHs, não pacientes únicos. Referência: 2022–2024.</p>
      {flows.error && <p role="alert">{flows.error}</p>}{flows.data && <FlowSummary flow={flows.data} />}<Link href={`/fluxos?regiao=${code}`}>Explorar fluxos</Link></section>
  </div>;
}

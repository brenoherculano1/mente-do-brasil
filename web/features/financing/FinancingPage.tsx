"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getFinancing } from "@/lib/api/client";
import { formatInteger } from "@/lib/format";
import type { FinancingResponse } from "@/types/api";

const YEARS = [2022, 2023, 2024];

export function FinancingPage() {
  const [year, setYear] = useState(2024);
  const [data, setData] = useState<FinancingResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    void getFinancing(year).then(setData).catch(() => setError("Não foi possível carregar os dados."));
  }, [year]);

  return (
    <main className="page-shell">
      <section className="intro" aria-labelledby="financing-title">
        <p className="eyebrow">Contexto financeiro</p>
        <h1 id="financing-title">Financiamento</h1>
        <p>Despesa pública total em saúde por habitante, por Região de Saúde.</p>
      </section>
      <section className="panel">
        <p className="small-text">
          Esta camada descreve o contexto geral de financiamento da saúde e não mede gasto específico em saúde mental.
        </p>
        <label className="control-group" htmlFor="financing-year">
          <span className="field-label">Exercício</span>
          <select id="financing-year" className="input" value={year} onChange={(event) => setYear(Number(event.target.value))}>
            {YEARS.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
      </section>
      {error && <p role="alert" className="small-text">{error}</p>}
      <section className="panel" aria-live="polite">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Região</th><th>Municípios</th><th>R$/habitante</th><th>Cobertura</th></tr></thead>
            <tbody>
              {(data?.records ?? []).map((record) => (
                <tr key={record.health_region_code}>
                  <th scope="row"><Link href={`/regiao/${record.health_region_code}`}>{record.health_region_code}</Link></th>
                  <td>{record.municipalities_observed}/{record.municipalities_expected}</td>
                  <td>{record.headline_available && record.health_expenditure_per_capita_brl !== null ? `R$ ${formatInteger(Math.round(record.health_expenditure_per_capita_brl))}` : "Indisponível"}</td>
                  <td>{record.headline_available ? "Completa" : "Parcial"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <p className="small-text">Valores em reais correntes do respectivo exercício; comparações entre anos não representam variação real descontada da inflação.</p>
    </main>
  );
}

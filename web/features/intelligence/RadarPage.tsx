"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getRadarHealthRegions } from "@/lib/api/client";
import { formatInteger, formatScore } from "@/lib/format";
import { VALID_UFS } from "@/lib/states";
import type { RadarRegion, RadarResponse, RadarSignalFamily } from "@/types/api";
import { RadarMap } from "./RadarMap";

const SIGNAL_OPTIONS: Array<{ value: RadarSignalFamily; label: string }> = [
  { value: "NEED_HIGH", label: "Need alto" },
  { value: "CAPACITY_LOW", label: "Capacity baixo" },
  { value: "MISMATCH_MARKED_POSITIVE", label: "Mismatch marcado" },
  { value: "CAPACITY_COMPONENT_LOW", label: "Componente baixo" },
  { value: "SPATIAL_HH_MISMATCH", label: "Contexto HH" },
];

const SIGNAL_LABELS: Array<[keyof RadarRegion["signals"], string]> = [
  ["need_high", "Need em faixa relativamente alta"],
  ["capacity_low", "Capacity em faixa relativamente baixa"],
  ["mismatch_marked_positive", "Mismatch >= +0,25"],
  ["capacity_component_low", "Componente de Capacity em faixa baixa"],
  ["spatial_hh_mismatch", "Contexto espacial HH significativo"],
];

export function RadarPage({ initialUf }: { initialUf?: string }) {
  const [uf, setUf] = useState(initialUf ?? "");
  const [minFamilies, setMinFamilies] = useState(2);
  const [signal, setSignal] = useState<RadarSignalFamily | "">("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<"signals" | "mismatch" | "name">("signals");
  const [data, setData] = useState<RadarResponse | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRadar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getRadarHealthRegions({
        uf: uf || undefined,
        signal: signal || undefined,
        minSignalFamilies: minFamilies,
        q: query.trim() || undefined,
        sort,
        includeGeometry: true,
      });
      setData(response);
      setSelectedCode((current) =>
        current && response.regions.some((region) => region.health_region_code === current)
          ? current
          : response.regions[0]?.health_region_code ?? null,
      );
    } catch {
      setError("Não foi possível carregar o Radar agora.");
    } finally {
      setLoading(false);
    }
  }, [minFamilies, query, signal, sort, uf]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      void loadRadar();
    }, 180);
    return () => window.clearTimeout(handle);
  }, [loadRadar]);

  const selected = useMemo(
    () => data?.regions.find((region) => region.health_region_code === selectedCode) ?? null,
    [data?.regions, selectedCode],
  );

  return (
    <div className="page-shell radar-shell">
      <section className="intro radar-intro" aria-labelledby="radar-title">
        <p className="eyebrow">Inteligência territorial</p>
        <h1 id="radar-title">Radar Territorial</h1>
        <p>
          Explore a confluência de sinais territoriais que podem ajudar a definir
          onde investigar com mais atenção.
        </p>
      </section>

      <section className="radar-grid" aria-label="Radar Territorial">
        <aside className="panel radar-controls" aria-label="Controles do Radar">
          <div className="radar-method-note">
            <strong>O Radar não é ranking.</strong>
            <p className="small-text">
              Ele combina critérios transparentes e não produz recomendação
              automática de recursos.
            </p>
            <Link href="/metodologia#radar" className="inline-link">
              Como o Radar funciona
            </Link>
          </div>

          <label className="control-group">
            <span className="field-label">Scope</span>
            <select className="input" value={uf} onChange={(event) => setUf(event.target.value)}>
              <option value="">Brasil</option>
              {VALID_UFS.map((option) => (
                <option value={option} key={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="control-group">
            <span className="field-label">Mínimo de famílias</span>
            <select
              className="input"
              value={minFamilies}
              onChange={(event) => setMinFamilies(Number(event.target.value))}
            >
              {[1, 2, 3, 4, 5].map((value) => (
                <option value={value} key={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>

          <label className="control-group">
            <span className="field-label">Família de sinal</span>
            <select
              className="input"
              value={signal}
              onChange={(event) => setSignal(event.target.value as RadarSignalFamily | "")}
            >
              <option value="">Todas</option>
              {SIGNAL_OPTIONS.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="control-group">
            <span className="field-label">Buscar Região de Saúde</span>
            <input
              className="input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Nome ou código"
              autoComplete="off"
            />
          </label>

          <label className="control-group">
            <span className="field-label">Ordenar por</span>
            <select
              className="input"
              value={sort}
              onChange={(event) => setSort(event.target.value as "signals" | "mismatch" | "name")}
            >
              <option value="signals">Mais critérios atendidos</option>
              <option value="mismatch">Maior Mismatch</option>
              <option value="name">Nome da região</option>
            </select>
          </label>
        </aside>

        <div className="radar-main">
          <div className="map-frame radar-map-frame">
            {loading && <div className="map-overlay"><div className="map-status">Carregando Radar...</div></div>}
            {error && (
              <div className="map-overlay">
                <div className="map-status" role="alert">{error}</div>
              </div>
            )}
            <RadarMap
              data={data?.geometry ?? null}
              selectedCode={selectedCode}
              onSelectRegion={setSelectedCode}
            />
          </div>
          <RadarLegend />
        </div>

        <aside className="panel radar-selected" aria-label="Região selecionada no Radar">
          <SelectedRadarRegion region={selected} />
        </aside>
      </section>

      <section className="state-section" aria-labelledby="radar-list-title">
        <p className="eyebrow">Lista acessível</p>
        <h2 id="radar-list-title">Regiões exibidas</h2>
        <p className="small-text" aria-live="polite">
          {data ? `${formatInteger(data.total_matching)} Regiões de Saúde atendem os filtros.` : "Carregando."}
        </p>
        <div className="radar-list">
          {data?.regions.map((region) => (
            <button
              type="button"
              className="radar-list-item"
              key={region.health_region_code}
              onClick={() => setSelectedCode(region.health_region_code)}
              aria-current={selectedCode === region.health_region_code}
            >
              <span>
                <strong>{region.health_region_name}</strong>
                <span className="small-text">
                  {region.uf} · {region.health_region_code}
                </span>
              </span>
              <span className="radar-count">{region.matched_signal_families} de 5</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function SelectedRadarRegion({ region }: { region: RadarRegion | null }) {
  if (!region) {
    return <p className="small-text">Selecione uma Região de Saúde no mapa ou na lista.</p>;
  }
  const activeSignals = SIGNAL_LABELS.filter(([key]) => region.signals[key]);
  return (
    <div className="radar-drawer-content">
      <p className="eyebrow">Região selecionada</p>
      <h2>{region.health_region_name}</h2>
      <p className="small-text">
        {region.uf} · {region.health_region_code} · população {formatInteger(region.population)}
      </p>
      <div className="metric-row">
        <Metric label="Need" value={formatScore(region.need_score)} />
        <Metric label="Capacity" value={formatScore(region.capacity_score)} />
        <Metric label="Mismatch" value={formatScore(region.mismatch_score, true)} />
      </div>
      <div className="radar-count large">{region.matched_signal_families} de 5 famílias</div>
      <h3>Por que apareceu?</h3>
      <ul className="signal-list">
        {activeSignals.map(([, label]) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
      {region.data_quality_flags.length > 0 && (
        <p className="small-text">Observações de qualidade: {region.data_quality_flags.join(", ")}</p>
      )}
      <div className="nav-links">
        <Link className="text-button" href={`/regiao/${region.health_region_code}#inteligencia`}>
          Ver análise completa
        </Link>
        <Link className="text-button" href={`/gestor?regiao=${region.health_region_code}`}>
          Modo Gestor
        </Link>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-chip">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RadarLegend() {
  return (
    <div className="radar-legend" aria-label="Famílias de sinais atendidas">
      <span>Famílias de sinais atendidas</span>
      {[0, 1, 2, 3, "4+"].map((label, index) => (
        <span className="radar-legend-item" key={label}>
          <span style={{ background: ["#eef1ed", "#d9ded4", "#bfc9bf", "#8da99f", "#446b68"][index] }} />
          {label}
        </span>
      ))}
    </div>
  );
}

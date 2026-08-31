"use client";

import Link from "next/link";
import { RegionAdvanced } from "@/features/advanced/RegionAdvanced";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getManagerBrief,
  getManagerCompare,
  lookupMunicipality,
  searchHealthRegions,
} from "@/lib/api/client";
import { formatInteger, formatMetricValue, formatPercentile, formatScore } from "@/lib/format";
import { getMetricConfig, METRICS } from "@/lib/metrics";
import type {
  HealthRegionLookup,
  ManagerBrief,
  ManagerCompareResponse,
  ManagerMetricValue,
  MetricId,
} from "@/types/api";

type Tab = "territorial" | "compare" | "meeting";

const TAB_LABELS: Array<{ id: Tab; label: string }> = [
  { id: "territorial", label: "Visão territorial" },
  { id: "compare", label: "Comparar territórios" },
  { id: "meeting", label: "Preparar reunião" },
];

const COMPARE_DEFAULTS = ["12001", "31001"];

export function ManagerWorkbench({
  initialRegionCode,
  initialCompare,
}: {
  initialRegionCode?: string;
  initialCompare?: string;
}) {
  const [activeTab, setActiveTab] = useState<Tab>(initialCompare ? "compare" : "territorial");
  const [query, setQuery] = useState(initialRegionCode ?? "");
  const [selectedCode, setSelectedCode] = useState(initialRegionCode);
  const [brief, setBrief] = useState<ManagerBrief | null>(null);
  const [suggestions, setSuggestions] = useState<HealthRegionLookup[]>([]);
  const [compareCodes, setCompareCodes] = useState(() => parseCompare(initialCompare));
  const [compareQuery, setCompareQuery] = useState("");
  const [compare, setCompare] = useState<ManagerCompareResponse | null>(null);
  const [metric, setMetric] = useState<MetricId>("mismatch_score");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const selectedMetric = useMemo(() => getMetricConfig(metric), [metric]);

  useEffect(() => {
    if (!selectedCode || !/^\d{5}$/.test(selectedCode)) {
      setBrief(null);
      return;
    }
    setLoading(true);
    void getManagerBrief(selectedCode)
      .then((data) => {
        setBrief(data);
        setQuery(`${data.region.health_region_name} (${data.region.health_region_code})`);
      })
      .catch(() => setMessage("Não foi possível carregar esta Região de Saúde."))
      .finally(() => setLoading(false));
  }, [selectedCode]);

  useEffect(() => {
    const term = query.trim();
    if (term.length < 2 || /^\d{5}$/.test(term)) {
      setSuggestions([]);
      return;
    }
    const handle = window.setTimeout(() => {
      void searchHealthRegions(term, 6)
        .then((result) => setSuggestions(result.items))
        .catch(() => setSuggestions([]));
    }, 180);
    return () => window.clearTimeout(handle);
  }, [query]);

  const loadCompare = useCallback(
    (codes: string[]) => {
      if (codes.length < 2) {
        setCompare(null);
        return;
      }
      void getManagerCompare(codes)
        .then(setCompare)
        .catch(() => setMessage("Não foi possível carregar a comparação."));
    },
    [setCompare],
  );

  useEffect(() => {
    loadCompare(compareCodes);
  }, [compareCodes, loadCompare]);

  function syncUrl(nextCode = selectedCode, nextCompare = compareCodes, tab = activeTab) {
    const url = new URL(window.location.href);
    url.search = "";
    if (tab === "compare" && nextCompare.length >= 2) {
      url.searchParams.set("compare", nextCompare.join(","));
    } else if (nextCode) {
      url.searchParams.set("regiao", nextCode);
    }
    window.history.pushState({}, "", url.toString());
  }

  async function selectFromQuery() {
    const term = query.trim();
    if (/^\d{5}$/.test(term)) {
      setSelectedCode(term);
      syncUrl(term, compareCodes, "territorial");
      return;
    }
    if (/^\d{7}$/.test(term)) {
      const municipality = await lookupMunicipality(term);
      setSelectedCode(municipality.health_region_code);
      syncUrl(municipality.health_region_code, compareCodes, "territorial");
      return;
    }
    if (suggestions[0]) {
      setSelectedCode(suggestions[0].health_region_code);
      syncUrl(suggestions[0].health_region_code, compareCodes, "territorial");
    }
  }

  async function addCompareCode() {
    const term = compareQuery.trim();
    let code = /^\d{5}$/.test(term) ? term : "";
    if (!code && /^\d{7}$/.test(term)) {
      const municipality = await lookupMunicipality(term);
      code = municipality.health_region_code;
    }
    if (!code) {
      const result = await searchHealthRegions(term, 1);
      code = result.items[0]?.health_region_code ?? "";
    }
    if (!code || compareCodes.includes(code) || compareCodes.length >= 4) return;
    const next = [...compareCodes, code];
    setCompareCodes(next);
    setCompareQuery("");
    syncUrl(selectedCode, next, "compare");
  }

  function switchTab(tab: Tab) {
    setActiveTab(tab);
    syncUrl(selectedCode, compareCodes, tab);
  }

  function copyLink() {
    void navigator.clipboard.writeText(window.location.href).then(() => {
      setMessage("Link copiado.");
    });
  }

  return (
    <div className="page-shell manager-shell">
      <section className="intro manager-intro" aria-labelledby="manager-title">
        <p className="eyebrow">Modo Gestor</p>
        <h1 id="manager-title">Modo Gestor</h1>
        <p>
          Uma leitura territorial organizada para investigação, comparação e
          preparação de reuniões.
        </p>
      </section>

      <section className="panel manager-selector" aria-label="Selecionar território">
        <label className="control-group manager-search">
          <span className="field-label">Região, código ou município IBGE</span>
          <input
            className="input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ex.: 12001, Alto Acre ou 1200401"
            autoComplete="off"
          />
        </label>
        <button className="primary-button" type="button" onClick={() => void selectFromQuery()}>
          Abrir leitura
        </button>
        {suggestions.length > 0 && (
          <div className="manager-suggestions" role="listbox" aria-label="Sugestões">
            {suggestions.map((item) => (
              <button
                key={item.health_region_code}
                type="button"
                onClick={() => {
                  setSelectedCode(item.health_region_code);
                  syncUrl(item.health_region_code, compareCodes, "territorial");
                  setSuggestions([]);
                }}
              >
                {item.health_region_name} · {item.uf} · {item.health_region_code}
              </button>
            ))}
          </div>
        )}
      </section>

      <div className="manager-tabs" role="tablist" aria-label="Modos do Gestor">
        {TAB_LABELS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={activeTab === tab.id ? "active" : ""}
            onClick={() => switchTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {message && <p className="small-text" role="status">{message}</p>}
      {loading && <p className="small-text">Carregando leitura territorial...</p>}

      {activeTab === "territorial" && (
        <TerritorialMode brief={brief} selectedMetric={selectedMetric.shortLabel} />
      )}
      {activeTab === "compare" && (
        <CompareMode
          compare={compare}
          compareCodes={compareCodes}
          compareQuery={compareQuery}
          metric={metric}
          onMetric={setMetric}
          onCompareQuery={setCompareQuery}
          onAdd={() => void addCompareCode()}
          onRemove={(code) => {
            const next = compareCodes.filter((item) => item !== code);
            setCompareCodes(next.length >= 2 ? next : COMPARE_DEFAULTS);
            syncUrl(selectedCode, next.length >= 2 ? next : COMPARE_DEFAULTS, "compare");
          }}
        />
      )}
      {activeTab === "meeting" && <MeetingMode brief={brief} onCopy={copyLink} />}
    </div>
  );
}

function TerritorialMode({
  brief,
  selectedMetric,
}: {
  brief: ManagerBrief | null;
  selectedMetric: string;
}) {
  if (!brief) {
    return (
      <section className="panel manager-empty">
        <h2>Escolha uma Região de Saúde para começar.</h2>
        <p>Use nome, código da Região de Saúde ou código IBGE de município.</p>
      </section>
    );
  }
  return (
    <>
      <QuickRead brief={brief} />
      <section className="manager-grid">
        <article className="panel manager-section">
          <p className="eyebrow">O que merece investigação?</p>
          <h2>Famílias acionadas</h2>
          {brief.radar_triggers.length > 0 ? (
            <ul className="signal-list">
              {brief.radar_triggers.map((trigger) => <li key={trigger}>{trigger}</li>)}
            </ul>
          ) : (
            <p>Nenhum dos cinco critérios predefinidos do Radar foi acionado neste release.</p>
          )}
          {brief.radar_subsignals.length > 0 && (
            <ul className="signal-list compact">
              {brief.radar_subsignals.map((item) => <li key={item}>{item}</li>)}
            </ul>
          )}
        </article>
        <article className="panel manager-section">
          <p className="eyebrow">Como o Mismatch é formado?</p>
          <h2>Contribuições algébricas</h2>
          <ContributionBars items={brief.decomposition} />
        </article>
      </section>
      <section className="manager-grid">
        <article className="panel manager-section">
          <p className="eyebrow">Peers estruturais</p>
          <h2>Comparação padrão: {selectedMetric}</h2>
          <p>
            A referência usa 10 peers estruturais por população, densidade
            populacional e número de municípios.
          </p>
          <Link className="text-button" href={`/regiao/${brief.region.health_region_code}#peers`}>
            Ver peers no perfil
          </Link>
        </article>
        <article className="panel manager-section">
          <p className="eyebrow">Contexto espacial</p>
          <h2>LISA</h2>
          <p>{brief.spatial_context.description}</p>
          {brief.quality_cautions.map((caution) => (
            <p className="quality-note" key={caution}>{caution}</p>
          ))}
        </article>
      </section>
      <Questions brief={brief} />
      {brief.release.release_id === "MDB_ANALYTICAL_2024_2" && (
        <RegionAdvanced code={brief.region.health_region_code} />
      )}
      <ReportActions brief={brief} />
    </>
  );
}

function QuickRead({ brief }: { brief: ManagerBrief }) {
  return (
    <section className="panel manager-quick" aria-labelledby="quick-title">
      <div>
        <p className="eyebrow">Leitura em 60 segundos</p>
        <h2 id="quick-title">{brief.region.health_region_name}</h2>
        <p>{brief.deterministic_summary}</p>
        <p className="small-text">
          {brief.region.uf} · {brief.region.health_region_code} · população{" "}
          {formatInteger(brief.region.population)} · {brief.region.municipality_count} municípios
        </p>
      </div>
      <div className="manager-metrics" aria-label="Indicadores sintéticos">
        <MetricChip label="Need" value={formatScore(brief.need_score)} />
        <MetricChip label="Capacity" value={formatScore(brief.capacity_score)} />
        <MetricChip label="Mismatch" value={formatScore(brief.mismatch_score, true)} />
        <MetricChip label="Radar" value={`${brief.matched_signal_families}/5`} />
      </div>
      <div className="nav-links">
        <Link className="text-button" href={`/regiao/${brief.region.health_region_code}`}>
          Ver perfil completo
        </Link>
      </div>
    </section>
  );
}

function ContributionBars({ items }: { items: ManagerBrief["decomposition"] }) {
  const maxAbs = Math.max(1, ...items.map((item) => Math.abs(item.contribution * 100)));
  return (
    <div className="decomposition-chart">
      {items.map((item) => {
        const value = item.contribution * 100;
        const width = `${Math.max(2, (Math.abs(value) / maxAbs) * 48)}%`;
        return (
          <div className="decomposition-row" key={item.component}>
            <div className="decomposition-label">
              <strong>{item.label}</strong>
              <span>{formatPercentile(item.source_percentile)} · {formatScore(item.contribution, true)}</span>
            </div>
            <div className="decomposition-bar" aria-hidden="true">
              <span className="zero-line" />
              <span
                className={value >= 0 ? "bar-positive" : "bar-negative"}
                style={value >= 0 ? { left: "50%", width } : { right: "50%", width }}
              />
            </div>
          </div>
        );
      })}
      <p className="small-text">Contribuições algébricas; sem leitura etiológica.</p>
    </div>
  );
}

function Questions({ brief }: { brief: ManagerBrief }) {
  return (
    <section className="panel manager-section" aria-labelledby="questions-title">
      <p className="eyebrow">Perguntas para investigação</p>
      <h2 id="questions-title">Agenda da reunião</h2>
      <div className="question-list">
        {brief.investigation_questions.map((item) => (
          <details key={item.rule_id} className="question-item">
            <summary>
              <span>{item.question}</span>
              <strong>{item.category}</strong>
            </summary>
            <p>{item.rationale}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

function ReportActions({ brief }: { brief: ManagerBrief }) {
  return (
    <section className="panel manager-report" aria-label="Exportar relatório">
      <div>
        <p className="eyebrow">Relatório territorial</p>
        <h2>Levar para reunião</h2>
        <p className="small-text">Conteúdo-base: {brief.report_content_sha256.slice(0, 16)}</p>
      </div>
      <a
        className="primary-button"
        href={`/api/v1/health-regions/${brief.region.health_region_code}/report.pdf`}
      >
        Baixar relatório territorial
      </a>
    </section>
  );
}

function MeetingMode({ brief, onCopy }: { brief: ManagerBrief | null; onCopy: () => void }) {
  if (!brief) return <TerritorialMode brief={brief} selectedMetric="Mismatch" />;
  return (
    <>
      <QuickRead brief={brief} />
      <section className="manager-grid">
        <article className="panel manager-section">
          <h2>Fatos para abrir a reunião</h2>
          <ul className="signal-list">
            <li>Need {formatScore(brief.need_score)}.</li>
            <li>Capacity {formatScore(brief.capacity_score)}.</li>
            <li>Mismatch {formatScore(brief.mismatch_score, true)}.</li>
            <li>Radar {brief.matched_signal_families}/5 famílias.</li>
          </ul>
        </article>
        <article className="panel manager-section">
          <h2>Cautelas</h2>
          {brief.quality_cautions.length > 0 ? (
            brief.quality_cautions.map((item) => <p key={item}>{item}</p>)
          ) : (
            <p>Sem cautela de qualidade adicional neste release.</p>
          )}
        </article>
      </section>
      <Questions brief={brief} />
      <section className="panel manager-report">
        <button className="text-button" type="button" onClick={onCopy}>
          Copiar link desta análise
        </button>
        <a
          className="primary-button"
          href={`/api/v1/health-regions/${brief.region.health_region_code}/report.pdf`}
        >
          Baixar relatório territorial
        </a>
      </section>
    </>
  );
}

function CompareMode({
  compare,
  compareCodes,
  compareQuery,
  metric,
  onMetric,
  onCompareQuery,
  onAdd,
  onRemove,
}: {
  compare: ManagerCompareResponse | null;
  compareCodes: string[];
  compareQuery: string;
  metric: MetricId;
  onMetric: (metric: MetricId) => void;
  onCompareQuery: (query: string) => void;
  onAdd: () => void;
  onRemove: (code: string) => void;
}) {
  const config = getMetricConfig(metric);
  return (
    <section className="panel manager-section" aria-labelledby="compare-title">
      <p className="eyebrow">Comparar territórios</p>
      <h2 id="compare-title">2 a 4 Regiões de Saúde</h2>
      <div className="manager-compare-controls">
        <label className="control-group">
          <span className="field-label">Indicador</span>
          <select className="input" value={metric} onChange={(event) => onMetric(event.target.value as MetricId)}>
            {METRICS.map((item) => <option key={item.id} value={item.id}>{item.shortLabel}</option>)}
          </select>
        </label>
        <label className="control-group">
          <span className="field-label">Adicionar região</span>
          <input
            className="input"
            value={compareQuery}
            onChange={(event) => onCompareQuery(event.target.value)}
            placeholder="Nome, código ou município"
          />
        </label>
        <button className="text-button" type="button" onClick={onAdd} disabled={compareCodes.length >= 4}>
          Adicionar
        </button>
      </div>
      <div className="selected-tags">
        {compareCodes.map((code) => (
          <button key={code} type="button" onClick={() => onRemove(code)}>{code} ×</button>
        ))}
      </div>
      {compare && (
        <>
          <div className="compare-dotplot" aria-label={`Comparação de ${config.shortLabel}`}>
            {compare.regions.map((region) => {
              const item = metricValue(region.indicators, metric);
              return (
                <div className="compare-row" key={region.identity.health_region_code}>
                  <span>{region.identity.health_region_name}</span>
                  <strong>{formatMetricValue(item?.value, config.scale)}</strong>
                  <small>{item?.percentile == null ? "sem percentil" : formatPercentile(item.percentile)}</small>
                  <em>Radar {region.matched_signal_families}/5</em>
                </div>
              );
            })}
          </div>
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Tabela de comparação">
          <table className="manager-table">
            <caption>Tabela acessível de comparação, na ordem escolhida.</caption>
            <thead>
              <tr>
                <th>Métrica</th>
                {compare.regions.map((region) => <th key={region.identity.health_region_code}>{region.identity.health_region_code}</th>)}
              </tr>
            </thead>
            <tbody>
              {METRICS.map((item) => (
                <tr key={item.id}>
                  <th>{item.shortLabel}</th>
                  {compare.regions.map((region) => {
                    const value = metricValue(region.indicators, item.id);
                    return (
                      <td key={region.identity.health_region_code}>
                        {formatMetricValue(value?.value, item.scale)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </>
      )}
    </section>
  );
}

function metricValue(items: ManagerMetricValue[], metric: MetricId) {
  return items.find((item) => item.metric_id === metric);
}

function MetricChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-chip">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function parseCompare(value?: string) {
  const codes = (value ? value.split(",") : COMPARE_DEFAULTS)
    .map((item) => item.trim())
    .filter((item) => /^\d{5}$/.test(item));
  return Array.from(new Set(codes)).slice(0, 4);
}

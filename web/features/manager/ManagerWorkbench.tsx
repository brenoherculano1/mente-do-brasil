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
import { publicLanguage } from "@/lib/public-language";
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
  title = "Painel para gestores",
  eyebrow = "Decisões orientadas por dados",
  description = "Entenda os principais desafios da sua região, compare contextos e prepare perguntas para investigação e reuniões de planejamento.",
  comparisonOnly = false,
}: {
  initialRegionCode?: string;
  initialCompare?: string;
  title?: string;
  eyebrow?: string;
  description?: string;
  comparisonOnly?: boolean;
}) {
  const [activeTab, setActiveTab] = useState<Tab>(comparisonOnly || initialCompare ? "compare" : "territorial");
  const [query, setQuery] = useState(initialRegionCode ?? "");
  const [selectedCode, setSelectedCode] = useState(initialRegionCode);
  const [brief, setBrief] = useState<ManagerBrief | null>(null);
  const [suggestions, setSuggestions] = useState<HealthRegionLookup[]>([]);
  const [compareCodes, setCompareCodes] = useState(() => parseCompare(initialCompare));
  const [compareQuery, setCompareQuery] = useState("");
  const [compare, setCompare] = useState<ManagerCompareResponse | null>(null);
  const [compareBriefs, setCompareBriefs] = useState<ManagerBrief[]>([]);
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
        setQuery(data.region.health_region_name);
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
      void Promise.all([
        getManagerCompare(codes),
        Promise.all(codes.map((code) => getManagerBrief(code))),
      ])
        .then(([comparison, briefs]) => {
          setCompare(comparison);
          setCompareBriefs(briefs.filter(Boolean));
        })
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
        <p className="eyebrow">{eyebrow}</p>
        <h1 id="manager-title">{title}</h1>
        <p>{description}</p>
      </section>

      {!comparisonOnly && <section className="panel manager-selector" aria-label="Selecionar território">
        <label className="control-group manager-search">
          <span className="field-label">Região ou município</span>
          <input
            className="input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ex.: Alto Acre ou Rio Branco"
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
                {item.health_region_name} · {item.uf}
              </button>
            ))}
          </div>
        )}
      </section>}

      {!comparisonOnly && <div className="manager-tabs" role="tablist" aria-label="Seções do painel para gestores">
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
      </div>}

      {message && <p className="small-text" role="status">{message}</p>}
      {loading && <p className="small-text">Carregando leitura territorial...</p>}

      {activeTab === "territorial" && (
        <TerritorialMode brief={brief} selectedMetric={selectedMetric.shortLabel} />
      )}
      {activeTab === "compare" && (
        <CompareMode
          compare={compare}
          briefs={compareBriefs}
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
        <p>Busque pelo nome da Região de Saúde ou de um município.</p>
      </section>
    );
  }
  return (
    <>
      <QuickRead brief={brief} />
      <section className="manager-grid">
        <article className="panel manager-section">
          <p className="eyebrow">O que merece investigação?</p>
          <h2>Sinais prioritários</h2>
          {brief.radar_triggers.length > 0 ? (
            <ul className="signal-list">
              {brief.radar_triggers.map((trigger) => <li key={trigger}>{publicLanguage(trigger)}</li>)}
            </ul>
          ) : (
            <p>Nenhum dos cinco critérios predefinidos de atenção foi identificado.</p>
          )}
          {brief.radar_subsignals.length > 0 && (
            <ul className="signal-list compact">
              {brief.radar_subsignals.map((item) => <li key={item}>{publicLanguage(item)}</li>)}
            </ul>
          )}
        </article>
        <article className="panel manager-section">
          <p className="eyebrow">O que explica a leitura?</p>
          <h2>Contribuição dos indicadores</h2>
          <ContributionBars items={brief.decomposition} />
        </article>
      </section>
      <section className="manager-grid">
        <article className="panel manager-section">
          <p className="eyebrow">Regiões semelhantes</p>
          <h2>Comparação padrão: {selectedMetric}</h2>
          <p>
            A referência usa 10 regiões semelhantes por população, densidade
            populacional e número de municípios.
          </p>
          <Link className="text-button" href={`/regiao/${brief.region.health_region_code}#peers`}>
            Ver comparação no perfil
          </Link>
        </article>
        <article className="panel manager-section">
          <p className="eyebrow">Contexto espacial</p>
          <h2>Padrão nas regiões vizinhas</h2>
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
        <p>{publicLanguage(brief.deterministic_summary)}</p>
        <p className="small-text">
          {brief.region.uf} · população{" "}
          {formatInteger(brief.region.population)} · {brief.region.municipality_count} municípios
        </p>
      </div>
      <div className="manager-metrics" aria-label="Indicadores sintéticos">
        <MetricChip label="Necessidade" value={formatScore(brief.need_score)} />
        <MetricChip label="Estrutura" value={formatScore(brief.capacity_score)} />
        <MetricChip label="Diferença" value={formatScore(brief.mismatch_score, true)} />
        <MetricChip label="Grupos de atenção" value={`${brief.matched_signal_families}/5`} />
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
      <p className="small-text">Contribuições matemáticas; não indicam causa.</p>
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
        <p className="small-text">Síntese baseada nos mesmos dados exibidos neste painel.</p>
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
  if (!brief) return <TerritorialMode brief={brief} selectedMetric="Diferença necessidade-capacidade" />;
  return (
    <>
      <QuickRead brief={brief} />
      <section className="manager-grid">
        <article className="panel manager-section">
          <h2>Fatos para abrir a reunião</h2>
          <ul className="signal-list">
            <li>Necessidade {formatScore(brief.need_score)}.</li>
            <li>Estrutura {formatScore(brief.capacity_score)}.</li>
            <li>Diferença necessidade-capacidade {formatScore(brief.mismatch_score, true)}.</li>
            <li>{brief.matched_signal_families}/5 grupos de atenção.</li>
          </ul>
        </article>
        <article className="panel manager-section">
          <h2>Cautelas</h2>
          {brief.quality_cautions.length > 0 ? (
            brief.quality_cautions.map((item) => <p key={item}>{item}</p>)
          ) : (
            <p>Sem cautela de qualidade adicional para os dados exibidos.</p>
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
  briefs,
  compareCodes,
  compareQuery,
  metric,
  onMetric,
  onCompareQuery,
  onAdd,
  onRemove,
}: {
  compare: ManagerCompareResponse | null;
  briefs: ManagerBrief[];
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
      <p className="eyebrow">Compare regiões</p>
      <h2 id="compare-title">Selecione de 2 a 4 Regiões de Saúde</h2>
      <p>Veja diferenças de população, necessidade, estrutura, evolução e recursos gerais de saúde sem criar um ranking.</p>
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
            placeholder="Nome da região ou município"
          />
        </label>
        <button className="text-button" type="button" onClick={onAdd} disabled={compareCodes.length >= 4}>
          Adicionar
        </button>
      </div>
      <div className="selected-tags">
        {compareCodes.map((code) => (
          <button key={code} type="button" onClick={() => onRemove(code)}>
            {compare?.regions.find((region) => region.identity.health_region_code === code)?.identity.health_region_name ?? "Região selecionada"} ×
          </button>
        ))}
      </div>
      {compare && (
        <>
          <div className="compare-dotplot" aria-label={`Comparação de ${config.shortLabel}`}>
            {compare.regions.map((region) => {
              const item = metricValue(region.indicators, metric);
              return (
                <div className="compare-row" key={region.identity.health_region_code}>
                  <Link href={`/regiao/${region.identity.health_region_code}`}>{region.identity.health_region_name}</Link>
                  <strong>{formatMetricValue(item?.value, config.scale)}</strong>
                  <small>{item?.percentile == null ? "sem percentil" : formatPercentile(item.percentile)}</small>
                  <em>{region.matched_signal_families}/5 grupos de atenção</em>
                </div>
              );
            })}
          </div>
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Tabela de comparação">
          <table className="manager-table">
            <caption>Tabela acessível de comparação, na ordem escolhida.</caption>
            <thead>
              <tr>
                <th>Indicador</th>
                {compare.regions.map((region) => <th key={region.identity.health_region_code}>{region.identity.health_region_name}</th>)}
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>População</th>
                {compare.regions.map((region) => <td key={region.identity.health_region_code}>{formatInteger(region.identity.population)}</td>)}
              </tr>
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
          <ComparisonContext briefs={briefs} />
        </>
      )}
    </section>
  );
}

function ComparisonContext({ briefs }: { briefs: ManagerBrief[] }) {
  if (briefs.length === 0) return null;
  return (
    <div className="manager-grid comparison-context">
      <div>
        <h3>Evolução recente</h3>
        {briefs.map((brief) => {
          const change = brief.change_summary;
          return (
            <p key={brief.region.health_region_code}>
              <strong>{brief.region.health_region_name}:</strong>{" "}
              {change
                ? `de 2022 a 2024, necessidade ${formatScore(change.delta_need_score, true)}, estrutura ${formatScore(change.delta_capacity_score, true)} e diferença ${formatScore(change.delta_mismatch_score, true)}.`
                : "Série não disponível."}
            </p>
          );
        })}
      </div>
      <div>
        <h3>Recursos gerais de saúde</h3>
        {briefs.map((brief) => {
          const latest = brief.financing_context?.records.find((record) => record.year === 2024);
          return (
            <p key={brief.region.health_region_code}>
              <strong>{brief.region.health_region_name}:</strong>{" "}
              {latest?.health_expenditure_per_capita_brl == null
                ? "Dado por habitante indisponível."
                : `${new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(latest.health_expenditure_per_capita_brl)} por habitante em 2024.`}
            </p>
          );
        })}
        <p className="small-text">Contexto geral da saúde; não corresponde a gasto específico em saúde mental.</p>
      </div>
    </div>
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

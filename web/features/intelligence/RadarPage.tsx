"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getRadarHealthRegions } from "@/lib/api/client";
import { SharePanel } from "@/features/share/SharePanel";
import { formatInteger, formatScore } from "@/lib/format";
import { describeMismatch, publicLanguage } from "@/lib/public-language";
import { toneForDirection, toneForMismatch, toneLabel, type RelativeTone } from "@/lib/indicator-tone";
import { VALID_UFS } from "@/lib/states";
import type { RadarRegion, RadarResponse, RadarSignalFamily } from "@/types/api";
import { RadarMap } from "./RadarMap";

const SIGNAL_OPTIONS: Array<{ value: RadarSignalFamily; label: string }> = [
  { value: "NEED_HIGH", label: "Necessidade relativamente alta" },
  { value: "CAPACITY_LOW", label: "Estrutura relativamente baixa" },
  { value: "MISMATCH_MARKED_POSITIVE", label: "Diferença acentuada" },
  { value: "CAPACITY_COMPONENT_LOW", label: "Componente da estrutura em faixa baixa" },
  { value: "SPATIAL_HH_MISMATCH", label: "Padrão semelhante entre regiões vizinhas" },
];

const SIGNAL_LABELS: Array<[keyof RadarRegion["signals"], string]> = [
  ["need_high", "Necessidade em faixa relativamente alta"],
  ["capacity_low", "Estrutura de atendimento em faixa relativamente baixa"],
  ["mismatch_marked_positive", "Necessidade acima da estrutura na comparação nacional"],
  ["capacity_component_low", "Ao menos um componente da estrutura está em faixa baixa"],
  ["spatial_hh_mismatch", "Regiões vizinhas também apresentam diferença elevada"],
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
        minSignalFamilies: query.trim() ? 0 : minFamilies,
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
      setError("Não foi possível carregar as regiões em atenção agora.");
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
        <p className="eyebrow">Sinais para investigação territorial</p>
        <h1 id="radar-title">Onde os sinais de atenção se acumulam?</h1>
        <p>
          O Radar verifica cinco sinais predefinidos em cada Região de Saúde e mostra
          onde vários deles aparecem juntos. Ele ajuda a escolher quais perfis investigar.
        </p>
        <div className="radar-steps" aria-label="Como usar o Radar">
          <p><strong>1. Verifique:</strong> o sistema procura cinco sinais nos dados.</p>
          <p><strong>2. Filtre:</strong> escolha quantos sinais devem aparecer juntos.</p>
          <p><strong>3. Investigue:</strong> abra o perfil da região para entender o contexto.</p>
        </div>
      </section>

      <section className="radar-grid" aria-label="Radar de atenção em saúde mental">
        <aside className="panel radar-controls" aria-label="Controles do Radar">
          <div className="radar-method-note">
            <strong>Este radar não é um ranking.</strong>
            <p className="small-text">
              Ele reúne sinais para orientar perguntas. Não mede qualidade do cuidado
              nem recomenda automaticamente onde aplicar recursos.
            </p>
            <Link href="/metodologia#radar" className="inline-link">
              Como esta análise funciona
            </Link>
          </div>

          <label className="control-group">
            <span className="field-label">Área</span>
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
            <span className="field-label">Mínimo de sinais encontrados</span>
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
            <span className="field-label">Motivo de atenção</span>
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
              placeholder="Nome da Região de Saúde"
              autoComplete="off"
            />
          </label>
          {query.trim() && data && (
            <p className="search-selection" role="status">
              {data.total_matching === 0
                ? "Nenhuma Região de Saúde encontrada com esse nome."
                : data.regions.some((region) => region.matched_signal_families < minFamilies)
                  ? `Busca encontrada. Para localizar o território, a busca ignora temporariamente o mínimo de ${minFamilies} sinais.`
                  : `${data.total_matching} Região de Saúde encontrada.`}
            </p>
          )}

          <label className="control-group">
            <span className="field-label">Ordenar por</span>
            <select
              className="input"
              value={sort}
              onChange={(event) => setSort(event.target.value as "signals" | "mismatch" | "name")}
            >
              <option value="signals">Mais sinais encontrados</option>
              <option value="mismatch">Maior diferença necessidade-capacidade</option>
              <option value="name">Nome da região</option>
            </select>
          </label>
        </aside>

        <div className="radar-main">
          <div className="map-frame radar-map-frame">
            {loading && <div className="map-overlay"><div className="map-status">Carregando regiões...</div></div>}
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

      {selected && (
        <SharePanel
          title={`${selected.health_region_name} no Radar | Mente do Brasil`}
          text={`${selected.health_region_name} apresenta ${selected.matched_signal_families} de 5 sinais de atenção no Radar do Mente do Brasil. A leitura é territorial, descritiva e não constitui ranking.`}
        />
      )}

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
                <span className="small-text">{region.uf}</span>
              </span>
              <span className="radar-count">{attentionLabel(region.matched_signal_families)}</span>
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
        {region.uf} · população {formatInteger(region.population)}
      </p>
      <div className="metric-row">
        <Metric label="Necessidade" value={formatScore(region.need_score)} tone={toneForDirection(region.need_score, "need")} />
        <Metric label="Estrutura" value={formatScore(region.capacity_score)} tone={toneForDirection(region.capacity_score, "capacity")} />
        <Metric label="Diferença" value={formatScore(region.mismatch_score, true)} tone={toneForMismatch(region.mismatch_score)} />
      </div>
      <p className="metric-interpretation">{describeMismatch(region.mismatch_score)}</p>
      <div className="attention-summary">
        <strong>{attentionLabel(region.matched_signal_families)}</strong>
        <span>{region.matched_signal_families} de 5 sinais encontrados</span>
      </div>
      {activeSignals.length > 0 ? (
        <>
          <h3>Quais sinais foram encontrados?</h3>
          <ul className="signal-list">
            {activeSignals.map(([, label]) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </>
      ) : (
        <p className="small-text">
          Esta região foi localizada pela busca e não apresenta nenhum dos cinco sinais
          com os filtros atuais.
        </p>
      )}
      {region.data_quality_flags.length > 0 && (
        <p className="small-text">Observações sobre os dados: {region.data_quality_flags.map(publicLanguage).join(" ")}</p>
      )}
      <div className="nav-links">
        <Link className="text-button" href={`/regiao/${region.health_region_code}#inteligencia`}>
          Ver análise completa
        </Link>
        <Link className="text-button" href={`/gestor?regiao=${region.health_region_code}`}>
          Painel para gestores
        </Link>
      </div>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: RelativeTone }) {
  return (
    <div className={`metric-chip metric-tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{toneLabel(tone)}</small>
    </div>
  );
}

function RadarLegend() {
  return (
    <div className="radar-legend" aria-label="Sinais encontrados">
      <span>Quantidade de sinais encontrados</span>
      {[0, 1, 2, 3, "4+"].map((label, index) => (
        <span className="radar-legend-item" key={label}>
          <span style={{ background: ["#eef1ed", "#d9ded4", "#bfc9bf", "#8da99f", "#446b68"][index] }} />
          {label}
        </span>
      ))}
    </div>
  );
}

function attentionLabel(count: number) {
  if (count >= 4) return "Alta atenção";
  if (count >= 2) return "Atenção moderada";
  return "Menor atenção relativa";
}

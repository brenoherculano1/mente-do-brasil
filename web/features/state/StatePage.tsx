"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getMapData } from "@/lib/api/client";
import { ACTIVE_RELEASE_ID } from "@/lib/api/config";
import { formatInteger, formatMetricValue, formatPercentile, formatScore } from "@/lib/format";
import { getScaleDomain } from "@/lib/map/color-scale";
import { DEFAULT_METRIC, getMetricConfig, type MetricConfig } from "@/lib/metrics";
import type {
  HealthRegionFeatureCollection,
  MetricId,
  StateProfile,
  StateRegion,
} from "@/types/api";
import { HealthRegionMap } from "@/features/explorer/HealthRegionMap";
import { MapLegend } from "@/features/explorer/MapLegend";
import { MetricSelector } from "@/features/explorer/MetricSelector";

const CLUSTER_LABELS: Record<string, string> = {
  HH: "HH",
  LL: "LL",
  HL: "HL",
  LH: "LH",
  "high-high": "HH",
  "low-low": "LL",
  "high-low": "HL",
  "low-high": "LH",
};

const FLAG_LABELS: Record<string, string> = {
  SMALL_SUICIDE_COUNT: "SMALL_SUICIDE_COUNT",
  ZERO_REGISTERED_BEDS: "ZERO_REGISTERED_BEDS",
};

export function StatePage({ stateProfile }: { stateProfile: StateProfile }) {
  const [metric, setMetric] = useState<MetricId>(DEFAULT_METRIC);
  const [mapData, setMapData] = useState<HealthRegionFeatureCollection | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [loadingMap, setLoadingMap] = useState(true);
  const [mapError, setMapError] = useState(false);
  const metricConfig = useMemo(() => getMetricConfig(metric), [metric]);
  const regions = useMemo(
    () =>
      [...stateProfile.regions].sort((left, right) =>
        left.health_region_name.localeCompare(right.health_region_name, "pt-BR"),
      ),
    [stateProfile.regions],
  );
  const selectedRegion = selectedCode
    ? regions.find((region) => region.health_region_code === selectedCode) ?? null
    : null;

  const loadMap = useCallback(async () => {
    setLoadingMap(true);
    setMapError(false);
    try {
      const data = await getMapData(metric, stateProfile.state.uf);
      setMapData(data);
    } catch {
      setMapError(true);
    } finally {
      setLoadingMap(false);
    }
  }, [metric, stateProfile.state.uf]);

  useEffect(() => {
    void loadMap();
  }, [loadMap]);

  const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
  const visibleRegions = normalizedQuery
    ? regions.filter((region) =>
        `${region.health_region_name} ${region.health_region_code}`
          .toLocaleLowerCase("pt-BR")
          .includes(normalizedQuery),
      )
    : regions;

  return (
    <div className="state-shell page-shell">
      <section className="intro state-hero" aria-labelledby="state-title">
        <p className="eyebrow">Estado</p>
        <h1 id="state-title">{stateProfile.state.state_name}</h1>
        <p>
          Explore como as Regiões de Saúde do {stateProfile.state.state_name} se
          distribuem nos indicadores do Mente do Brasil.
        </p>
        <div className="metadata-strip" aria-label="Metadados estaduais">
          <VersionTag label="UF" value={stateProfile.state.uf} />
          <VersionTag
            label="Regiões de Saúde"
            value={String(stateProfile.state.health_region_count)}
          />
          <VersionTag label="Release" value={stateProfile.release.release_id} />
        </div>
      </section>

      <main className="state-content">
        <section className="state-controls panel" aria-label="Controle de indicador estadual">
          <MetricSelector value={metric} onChange={setMetric} />
          <p className="small-text">{metricConfig.description}</p>
          {metric === "mismatch_score" && (
            <p className="small-text">
              Não é uma medida direta de déficit, acesso, qualidade ou necessidade não
              atendida.
            </p>
          )}
        </section>

        <section className="state-map-grid" aria-label="Mapa e contexto estadual">
          <div
            className="map-frame state-map-frame"
            aria-label="Mapa estadual das Regiões de Saúde"
            data-testid="map-frame"
          >
            {loadingMap && (
              <div className="map-overlay">
                <div className="map-status">Carregando mapa do estado...</div>
              </div>
            )}
            {mapError && (
              <div className="map-overlay">
                <div className="map-status" role="alert">
                  Não foi possível carregar os dados deste estado.{" "}
                  <button className="text-button" type="button" onClick={() => void loadMap()}>
                    Tentar novamente
                  </button>
                </div>
              </div>
            )}
            <HealthRegionMap
              data={mapData}
              metric={metricConfig}
              selectedCode={selectedCode}
              onSelectRegion={setSelectedCode}
            />
          </div>

          <aside className="panel state-context-panel" aria-label="Contexto estadual">
            <div className="state-summary-grid">
              <SummaryItem
                label="Regiões de Saúde"
                value={formatInteger(stateProfile.state.health_region_count)}
              />
              <SummaryItem
                label="População de referência"
                value={formatInteger(stateProfile.state.population)}
              />
              <SummaryItem
                label="Municípios associados"
                value={formatInteger(stateProfile.state.municipality_count)}
              />
            </div>
            <p className="small-text">
              População e municípios são somas administrativas das Regiões de Saúde
              retornadas para a UF no release. Não são score estadual.
            </p>
            <MapLegend
              metric={metricConfig}
              values={mapData?.features.map((feature) => feature.properties.value) ?? []}
            />
            {selectedRegion && (
              <div className="selected-state-region">
                <p className="field-label">Região selecionada</p>
                <strong>{selectedRegion.health_region_name}</strong>
                <p className="small-text">
                  {selectedRegion.uf} · {selectedRegion.health_region_code}
                </p>
                <Link className="text-button" href={`/regiao/${selectedRegion.health_region_code}`}>
                  Ver perfil da região
                </Link>
              </div>
            )}
          </aside>
        </section>

        <section className="state-section" aria-labelledby="distribution-title">
          <p className="eyebrow">Contexto nacional</p>
          <h2 id="distribution-title">Como as regiões se distribuem</h2>
          <p>
            As posições exibidas são relativas à distribuição nacional das 439 Regiões
            de Saúde. Elas não definem, isoladamente, adequação assistencial.
          </p>
          {metric === "mismatch_score" && (
            <p className="small-text">
              Mismatch &gt; 0: Need ocupa posição relativa superior à Capacity.
              Mismatch &lt; 0: Capacity ocupa posição relativa superior à Need. Zero:
              posições relativas semelhantes.
            </p>
          )}
          <StateDistribution
            regions={regions}
            metric={metric}
            metricConfig={metricConfig}
            selectedCode={selectedCode}
            onSelectRegion={setSelectedCode}
          />
        </section>

        <StateSignals stateProfile={stateProfile} regions={regions} />

        <section className="state-section" aria-labelledby="regions-title">
          <p className="eyebrow">Lista territorial</p>
          <h2 id="regions-title">Regiões de Saúde</h2>
          <label className="dictionary-search state-search">
            <span>Buscar Região de Saúde neste estado</span>
            <input
              className="input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Nome ou código da Região de Saúde"
              autoComplete="off"
            />
          </label>
          <p className="small-text" aria-live="polite">
            {visibleRegions.length} de {regions.length} Regiões de Saúde.
          </p>
          <div className="state-region-list">
            {visibleRegions.map((region) => (
              <article className="state-region-card" key={region.health_region_code}>
                <div>
                  <h3>{region.health_region_name}</h3>
                  <p className="small-text">
                    {region.uf} · {region.health_region_code}
                  </p>
                </div>
                <dl className="state-region-metrics">
                  <MetricRow label="População" value={formatInteger(region.population)} />
                  <MetricRow label="Municípios" value={formatInteger(region.municipality_count)} />
                  <MetricRow label="Need" value={formatScore(region.need_score)} />
                  <MetricRow label="Capacity" value={formatScore(region.capacity_score)} />
                  <MetricRow label="Mismatch" value={formatScore(region.mismatch_score, true)} />
                </dl>
                <div className="state-region-secondary">
                  {region.lisa_significant && region.lisa_cluster && (
                    <span>LISA {CLUSTER_LABELS[region.lisa_cluster] ?? region.lisa_cluster}</span>
                  )}
                  {region.data_quality_flags.length > 0 && <span>Dados com observação</span>}
                </div>
                <Link className="text-button" href={`/regiao/${region.health_region_code}`}>
                  Ver perfil
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="state-section state-method-links" aria-labelledby="state-method-title">
          <div>
            <p className="eyebrow">Método e dados</p>
            <h2 id="state-method-title">Como interpretar</h2>
            <p>
              Esta página organiza valores regionais já calculados no release{" "}
              {ACTIVE_RELEASE_ID}. Need, Capacity, Mismatch, LISA e flags não são
              recalculados aqui.
            </p>
          </div>
          <div className="about-link-grid">
            <Link className="text-button" href="/metodologia">
              Entenda o método
            </Link>
            <Link className="text-button" href="/dados">
              Ver dados e versões
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

function StateDistribution({
  regions,
  metric,
  metricConfig,
  selectedCode,
  onSelectRegion,
}: {
  regions: StateRegion[];
  metric: MetricId;
  metricConfig: MetricConfig;
  selectedCode: string | null;
  onSelectRegion: (code: string) => void;
}) {
  const values = regions.map((region) => distributionValue(region, metric));
  const validValues = values.filter((value): value is number => value != null);
  const mismatchDomain = getScaleDomain(validValues);
  const maxAbs = mismatchDomain.maxAbs || 1;
  return (
    <div className="state-distribution" data-testid="state-distribution">
      <div className="distribution-axis" aria-hidden="true">
        {metric === "mismatch_score" ? (
          <>
            <span>{formatScore(-maxAbs, true)}</span>
            <span>0</span>
            <span>{formatScore(maxAbs, true)}</span>
          </>
        ) : (
          <>
            <span>0</span>
            <span>posição relativa nacional</span>
            <span>100</span>
          </>
        )}
      </div>
      {regions.map((region) => {
        const value = distributionValue(region, metric);
        const left = distributionPosition(value, metric, maxAbs);
        return (
          <div className="distribution-row" key={region.health_region_code}>
            <span>{region.health_region_name}</span>
            <div className="distribution-track">
              {value == null ? (
                <span className="distribution-missing">Dado indisponível</span>
              ) : (
                <button
                  type="button"
                  className="distribution-dot"
                  style={{ left: `${left}%` }}
                  aria-label={`${region.health_region_name}, ${metricConfig.shortLabel}: ${distributionLabel(
                    value,
                    metric,
                  )}`}
                  aria-current={selectedCode === region.health_region_code}
                  onClick={() => onSelectRegion(region.health_region_code)}
                />
              )}
            </div>
            <strong>{distributionLabel(value, metric)}</strong>
          </div>
        );
      })}
    </div>
  );
}

function StateSignals({ stateProfile, regions }: { stateProfile: StateProfile; regions: StateRegion[] }) {
  const hasLisa = stateProfile.state.lisa_significant_count > 0;
  const hasFlags = Object.keys(stateProfile.state.quality_flag_counts).length > 0;
  if (!hasLisa && !hasFlags) return null;
  return (
    <section className="state-section state-signal-grid" aria-label="Contexto espacial e qualidade">
      {hasLisa && (
        <div>
          <p className="eyebrow">Contexto espacial</p>
          <h2>Contexto espacial</h2>
          <p>
            {stateProfile.state.lisa_significant_count} de {stateProfile.state.health_region_count}{" "}
            regiões com associação espacial local significativa no Mismatch.
          </p>
          <div className="state-chip-row">
            {Object.entries(stateProfile.state.lisa_cluster_counts).map(([cluster, count]) => (
              <span key={cluster}>
                {CLUSTER_LABELS[cluster] ?? cluster} {count}
              </span>
            ))}
          </div>
        </div>
      )}
      {hasFlags && (
        <div>
          <p className="eyebrow">Observações de qualidade</p>
          <h2>Observações de qualidade</h2>
          <div className="state-chip-row">
            {Object.entries(stateProfile.state.quality_flag_counts).map(([flag, count]) => (
              <span key={flag}>
                {FLAG_LABELS[flag] ?? flag} {count}
              </span>
            ))}
          </div>
          <p className="small-text">
            Zero leitos registrados nesta medida não implica necessariamente ausência de
            acesso regional a leitos.
          </p>
          <p className="small-text">
            Regiões com observações:{" "}
            {regions
              .filter((region) => region.data_quality_flags.length > 0)
              .map((region) => region.health_region_name)
              .join(", ")}
          </p>
        </div>
      )}
    </section>
  );
}

function distributionValue(region: StateRegion, metric: MetricId) {
  if (metric === "mismatch_score") return region.mismatch_score;
  if (metric === "need_score") return region.need_score;
  if (metric === "capacity_score") return region.capacity_score;
  if (metric === "suicide_asmr") return region.suicide_percentile;
  if (metric === "psychiatric_admission_rate") return region.psychiatric_admission_percentile;
  if (metric === "caps_rate") return region.caps_percentile;
  if (metric === "mental_health_beds_sus_rate") return region.beds_percentile;
  return region.psychiatrist_fte_percentile;
}

function distributionPosition(value: number | null, metric: MetricId, maxAbs: number) {
  if (value == null) return 0;
  if (metric === "mismatch_score") {
    return Math.max(0, Math.min(100, ((value + maxAbs) / (2 * maxAbs)) * 100));
  }
  return Math.max(0, Math.min(100, value * 100));
}

function distributionLabel(value: number | null, metric: MetricId) {
  if (value == null) return "Dado indisponível";
  if (metric === "mismatch_score") return formatMetricValue(value, "diverging");
  return formatPercentile(value).replace("º percentil", "/100");
}

function VersionTag({ label, value }: { label: string; value: string }) {
  return (
    <div className="version-pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-block">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

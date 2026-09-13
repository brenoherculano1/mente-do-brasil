"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getHealthRegionProfile, getMapData } from "@/lib/api/client";
import { DEFAULT_METRIC, getMetricConfig, METRICS } from "@/lib/metrics";
import type { HealthRegionFeatureCollection, HealthRegionProfile, MetricId } from "@/types/api";
import { HealthRegionMap } from "./HealthRegionMap";
import { MapLegend } from "./MapLegend";
import { MetricSelector } from "./MetricSelector";
import { SelectedRegionPanel } from "./SelectedRegionPanel";
import { TerritorySearch } from "./TerritorySearch";

export function ExplorerPage({ initialMetric }: { initialMetric: MetricId }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [metric, setMetric] = useState<MetricId>(initialMetric || DEFAULT_METRIC);
  const [mapData, setMapData] = useState<HealthRegionFeatureCollection | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<HealthRegionProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const metricConfig = useMemo(() => getMetricConfig(metric), [metric]);

  useEffect(() => {
    const indicator = searchParams.get("indicador");
    const allowed = METRICS.some((item) => item.id === indicator);
    if (indicator && allowed && indicator !== metric) {
      setMetric(indicator as MetricId);
    }
  }, [metric, searchParams]);

  const loadMap = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMapData(metric);
      setMapData(data);
    } catch {
      setError("Não foi possível carregar os dados agora.");
    } finally {
      setLoading(false);
    }
  }, [metric]);

  useEffect(() => {
    void loadMap();
  }, [loadMap]);

  const selectRegion = useCallback(async (code: string) => {
    setSelectedCode(code);
    try {
      const profile = await getHealthRegionProfile(code);
      setSelectedProfile(profile);
    } catch {
      setSelectedProfile(null);
    }
  }, []);

  const onMetricChange = (nextMetric: MetricId) => {
    setMetric(nextMetric);
    const params = new URLSearchParams(searchParams.toString());
    params.set("indicador", nextMetric);
    router.replace(`/?${params.toString()}`, { scroll: false });
  };

  const selectedFeature = mapData?.features.find(
    (feature) => feature.properties.health_region_code === selectedCode,
  );

  return (
    <div className="page-shell">
      <section className="intro public-home-intro" aria-labelledby="home-title">
        <p className="eyebrow">Saúde mental no território brasileiro</p>
        <h1 id="home-title">Mente do Brasil</h1>
        <p>
          Explore dados públicos de mortalidade, atendimento e estrutura assistencial
          nas regiões brasileiras.
        </p>
        <h2>Como está a saúde mental da minha região e quais são os principais desafios?</h2>
        <div className="home-actions">
          <a className="button" href="#mapa">Explore sua região</a>
          <Link className="text-button" href="/comparar">Compare territórios</Link>
          <Link className="text-button" href="/radar">Entenda os desafios</Link>
        </div>
        <dl className="home-facts" aria-label="Cobertura da plataforma">
          <div><dt>439</dt><dd>Regiões de Saúde analisadas</dd></div>
          <div><dt>5.570</dt><dd>Municípios considerados</dd></div>
          <div><dt>27</dt><dd>Unidades da Federação</dd></div>
          <div><dt>8</dt><dd>Indicadores para explorar</dd></div>
        </dl>
      </section>

      <section className="map-section-heading" id="mapa" aria-labelledby="map-title">
        <p className="eyebrow">Veja o mapa do Brasil</p>
        <h2 id="map-title">Quais regiões apresentam maiores desafios em saúde mental?</h2>
        <p>Escolha uma forma de observar o território e selecione uma região para abrir seu perfil.</p>
      </section>

      <section className="explorer-grid" aria-label="Explorador territorial">
        <aside className="panel controls-panel" aria-label="Controles do mapa">
          <TerritorySearch onSelectRegion={selectRegion} />
          <MetricSelector value={metric} onChange={onMetricChange} />
        </aside>

        <div className="map-frame" aria-label="Mapa nacional das Regiões de Saúde" data-testid="map-frame">
          {loading && (
            <div className="map-overlay">
              <div className="map-status">Carregando mapa nacional...</div>
            </div>
          )}
          {error && (
            <div className="map-overlay">
              <div className="map-status" role="alert">
                {error} <button className="text-button" onClick={() => void loadMap()}>Tentar novamente</button>
              </div>
            </div>
          )}
          <HealthRegionMap
            data={mapData}
            metric={metricConfig}
            selectedCode={selectedCode}
            onSelectRegion={selectRegion}
          />
        </div>

        <aside className="panel support-panel" aria-label="Informações do mapa">
          <SelectedRegionPanel
            feature={selectedFeature}
            profile={selectedProfile}
            loading={Boolean(selectedCode && !selectedProfile)}
          />
          <div className="control-group">
            <p className="field-label">Indicador selecionado</p>
            <strong>{metricConfig.label}</strong>
            <p className="small-text">{metricConfig.description}</p>
            <p className="small-text">{metricConfig.secondary}</p>
          </div>
          <MapLegend
            metric={metricConfig}
            values={mapData?.features.map((f) => f.properties.value) ?? []}
          />
          <p className="small-text">
            Dados de 2022 a 2024 e registros de dezembro de 2024, conforme o indicador.
            Consulte a metodologia para conhecer fontes, períodos e limitações.
          </p>
          <AccessibleRegionList
            features={mapData?.features ?? []}
            selectedCode={selectedCode}
            onSelectRegion={selectRegion}
          />
        </aside>
      </section>
    </div>
  );
}

function AccessibleRegionList({
  features,
  selectedCode,
  onSelectRegion,
}: {
  features: HealthRegionFeatureCollection["features"];
  selectedCode: string | null;
  onSelectRegion: (code: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [filter, setFilter] = useState("");
  const normalizedFilter = filter.trim().toLocaleLowerCase("pt-BR");
  const visibleFeatures = normalizedFilter
    ? features.filter((feature) => {
        const properties = feature.properties;
        return `${properties.health_region_name} ${properties.uf} ${properties.health_region_code}`
          .toLocaleLowerCase("pt-BR")
          .includes(normalizedFilter);
      })
    : features;
  if (features.length === 0) return null;
  return (
    <div className="control-group accessible-region-panel" aria-labelledby="region-list-title">
      <button
        className="text-button disclosure-button"
        type="button"
        aria-expanded={expanded}
        aria-controls="accessible-region-list"
        onClick={() => setExpanded((current) => !current)}
      >
        Ver lista de Regiões de Saúde
      </button>
      <p className="small-text" id="region-list-title">
        Alternativa textual ao mapa. A lista completa fica recolhida para não empurrar
        o mapa para baixo.
      </p>
      {expanded && (
        <div id="accessible-region-list" className="accessible-list-shell">
          <label className="control-group">
            <span className="field-label">Filtrar lista</span>
            <input
              className="input"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Nome da região ou UF"
              autoComplete="off"
            />
          </label>
          <p className="small-text" aria-live="polite">
            {visibleFeatures.length} de {features.length} Regiões de Saúde.
          </p>
          <ul className="accessible-list" aria-label="Lista textual de Regiões de Saúde">
            {visibleFeatures.map((feature) => (
              <li key={feature.id}>
                <button
                  className="result-button"
                  onClick={() => onSelectRegion(feature.properties.health_region_code)}
                  aria-current={selectedCode === feature.properties.health_region_code}
                >
                  <strong>{feature.properties.health_region_name}</strong>
                  <span className="small-text">{feature.properties.uf}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

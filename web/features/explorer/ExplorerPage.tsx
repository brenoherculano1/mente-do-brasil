"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getHealthRegionProfile, getMapData } from "@/lib/api/client";
import { ACTIVE_RELEASE_ID } from "@/lib/api/config";
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
      <section className="intro" aria-labelledby="home-title">
        <p className="eyebrow">Explorar o Brasil</p>
        <h1 id="home-title">Mente do Brasil</h1>
        <p>
          Inteligência territorial em saúde mental no Brasil. Explore diferenças
          territoriais entre indicadores de necessidade medida e capacidade registrada
          nas 439 Regiões de Saúde do país.
        </p>
      </section>

      <section className="explorer-grid" aria-label="Explorador territorial">
        <aside className="panel" aria-label="Controles do mapa">
          <TerritorySearch onSelectRegion={selectRegion} />
          <MetricSelector value={metric} onChange={onMetricChange} />
          <div className="control-group">
            <p className="field-label">Indicador selecionado</p>
            <strong>{metricConfig.label}</strong>
            <p className="small-text">{metricConfig.description}</p>
            <p className="small-text">{metricConfig.secondary}</p>
          </div>
          <MapLegend metric={metricConfig} values={mapData?.features.map((f) => f.properties.value) ?? []} />
          <p className="small-text">
            Dados: 2022-2024 / dezembro de 2024 conforme indicador. Release:{" "}
            {ACTIVE_RELEASE_ID}.
          </p>
          <SelectedRegionPanel
            feature={selectedFeature}
            profile={selectedProfile}
            loading={Boolean(selectedCode && !selectedProfile)}
          />
          <AccessibleRegionList
            features={mapData?.features ?? []}
            selectedCode={selectedCode}
            onSelectRegion={selectRegion}
          />
        </aside>

        <div className="map-frame" aria-label="Mapa nacional das Regiões de Saúde">
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
  if (features.length === 0) return null;
  return (
    <div className="control-group" aria-labelledby="region-list-title">
      <p className="field-label" id="region-list-title">
        Lista acessível
      </p>
      <ul className="accessible-list">
        {features.slice(0, 8).map((feature) => (
          <li key={feature.id}>
            <button
              className="result-button"
              onClick={() => onSelectRegion(feature.properties.health_region_code)}
              aria-current={selectedCode === feature.properties.health_region_code}
            >
              <strong>{feature.properties.health_region_name}</strong>
              <span className="small-text">
                {feature.properties.uf} · {feature.properties.health_region_code}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <p className="small-text">
        A busca acima permite acessar as demais Regiões de Saúde sem depender do mapa.
      </p>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import maplibregl, { Map, Popup } from "maplibre-gl";
import { formatMetricValue } from "@/lib/format";
import { getScaleDomain, mapLibreFillExpression } from "@/lib/map/color-scale";
import type { MetricConfig } from "@/lib/metrics";
import type { HealthRegionFeatureCollection } from "@/types/api";

const SOURCE_ID = "health-regions";
const FILL_LAYER_ID = "health-regions-fill";
const LINE_LAYER_ID = "health-regions-line";
const SELECTED_LAYER_ID = "health-regions-selected";

export function HealthRegionMap({
  data,
  metric,
  selectedCode,
  onSelectRegion,
}: {
  data: HealthRegionFeatureCollection | null;
  metric: MetricConfig;
  selectedCode: string | null;
  onSelectRegion: (code: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const popupRef = useRef<Popup | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [{ id: "background", type: "background", paint: { "background-color": "#f5f7f2" } }],
      },
      center: [-54, -14.5],
      zoom: 3.2,
      minZoom: 2.6,
      maxZoom: 9,
      attributionControl: false,
    });
    popupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      className: "map-tooltip",
    });
    mapRef.current = map;
    return () => {
      popupRef.current?.remove();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;
    const domain = getScaleDomain(data.features.map((feature) => feature.properties.value));
    const applyData = () => {
      const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
      if (source) {
        source.setData(data);
      } else {
        map.addSource(SOURCE_ID, { type: "geojson", data });
        map.addLayer({
          id: FILL_LAYER_ID,
          type: "fill",
          source: SOURCE_ID,
          paint: {
            "fill-color": mapLibreFillExpression(metric, domain) as maplibregl.ExpressionSpecification,
            "fill-opacity": 0.86,
          },
        });
        map.addLayer({
          id: LINE_LAYER_ID,
          type: "line",
          source: SOURCE_ID,
          paint: {
            "line-color": "#ffffff",
            "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.35, 7, 1.1],
            "line-opacity": 0.78,
          },
        });
        map.addLayer({
          id: SELECTED_LAYER_ID,
          type: "line",
          source: SOURCE_ID,
          filter: ["==", ["get", "health_region_code"], ""],
          paint: {
            "line-color": "#16201c",
            "line-width": 2.8,
          },
        });
        map.on("mouseenter", FILL_LAYER_ID, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", FILL_LAYER_ID, () => {
          map.getCanvas().style.cursor = "";
          popupRef.current?.remove();
        });
        map.on("mousemove", FILL_LAYER_ID, (event) => {
          const feature = event.features?.[0];
          if (!feature || !event.lngLat) return;
          const properties = feature.properties as Record<string, unknown>;
          const hasFlags = String(properties.data_quality_flags ?? "").length > 2;
          popupRef.current
            ?.setLngLat(event.lngLat)
            .setHTML(
              `<div class="tooltip"><strong>${properties.health_region_name} — ${properties.uf}</strong><span>${metric.shortLabel}: ${formatMetricValue(Number(properties.value), metric.scale)}</span>${hasFlags ? "<span>Dados com observação</span>" : ""}</div>`,
            )
            .addTo(map);
        });
        map.on("click", FILL_LAYER_ID, (event) => {
          const feature = event.features?.[0];
          const code = feature?.properties?.health_region_code;
          if (typeof code === "string") onSelectRegion(code);
        });
        const bounds = getBounds(data);
        if (bounds) {
          map.fitBounds(bounds, { padding: 32, duration: 0 });
        }
      }
      if (map.getLayer(FILL_LAYER_ID)) {
        map.setPaintProperty(
          FILL_LAYER_ID,
          "fill-color",
          mapLibreFillExpression(metric, domain) as maplibregl.ExpressionSpecification,
        );
      }
    };
    if (map.isStyleLoaded()) {
      applyData();
    } else {
      map.once("load", applyData);
    }
  }, [data, metric, onSelectRegion]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer(SELECTED_LAYER_ID)) return;
    map.setFilter(SELECTED_LAYER_ID, ["==", ["get", "health_region_code"], selectedCode ?? ""]);
  }, [selectedCode]);

  return (
    <>
      <div ref={containerRef} className="map-container" data-testid="health-region-map" />
      <div className="map-zoom-controls" aria-label="Controles de zoom do mapa">
        <button type="button" aria-label="Aproximar mapa" onClick={() => mapRef.current?.zoomIn()}>
          +
        </button>
        <button type="button" aria-label="Afastar mapa" onClick={() => mapRef.current?.zoomOut()}>
          -
        </button>
      </div>
    </>
  );
}

function getBounds(data: HealthRegionFeatureCollection) {
  const bounds = new maplibregl.LngLatBounds();
  let hasCoordinate = false;
  for (const feature of data.features) {
    for (const coordinate of coordinatesFromGeometry(feature.geometry)) {
      bounds.extend(coordinate as [number, number]);
      hasCoordinate = true;
    }
  }
  return hasCoordinate ? bounds : null;
}

function* coordinatesFromGeometry(geometry: GeoJSON.Geometry): Generator<[number, number]> {
  if (geometry.type === "GeometryCollection") {
    for (const child of geometry.geometries) {
      yield* coordinatesFromGeometry(child);
    }
    return;
  }
  yield* flattenCoordinates(geometry.coordinates);
}

function* flattenCoordinates(coordinates: unknown): Generator<[number, number]> {
  if (!Array.isArray(coordinates)) return;
  if (
    coordinates.length >= 2 &&
    typeof coordinates[0] === "number" &&
    typeof coordinates[1] === "number"
  ) {
    yield [coordinates[0], coordinates[1]];
    return;
  }
  for (const child of coordinates) {
    yield* flattenCoordinates(child);
  }
}

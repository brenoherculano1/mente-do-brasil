"use client";

import { useEffect, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";
import { IBGE_GEOMETRY_ATTRIBUTION } from "@/lib/map/attribution";
import type { RadarResponse } from "@/types/api";

const SOURCE_ID = "radar-regions";
const FILL_LAYER_ID = "radar-regions-fill";
const LINE_LAYER_ID = "radar-regions-line";
const SELECTED_LAYER_ID = "radar-regions-selected";

const COLORS = ["#eef1ed", "#d9ded4", "#bfc9bf", "#8da99f", "#446b68"];

export function RadarMap({
  data,
  selectedCode,
  onSelectRegion,
}: {
  data: RadarResponse["geometry"] | null;
  selectedCode: string | null;
  onSelectRegion: (code: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [{ id: "background", type: "background", paint: { "background-color": "#f7f7f2" } }],
      },
      center: [-54, -14.5],
      zoom: 3.2,
      minZoom: 2.6,
      maxZoom: 9,
      attributionControl: false,
    });
    map.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: IBGE_GEOMETRY_ATTRIBUTION }),
      "bottom-right",
    );
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;
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
            "fill-color": [
              "step",
              ["get", "matched_signal_families"],
              COLORS[0],
              1,
              COLORS[1],
              2,
              COLORS[2],
              3,
              COLORS[3],
              4,
              COLORS[4],
            ],
            "fill-opacity": 0.88,
          },
        });
        map.addLayer({
          id: LINE_LAYER_ID,
          type: "line",
          source: SOURCE_ID,
          paint: {
            "line-color": "#ffffff",
            "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.35, 7, 1],
            "line-opacity": 0.8,
          },
        });
        map.addLayer({
          id: SELECTED_LAYER_ID,
          type: "line",
          source: SOURCE_ID,
          filter: ["==", ["get", "health_region_code"], ""],
          paint: { "line-color": "#111c18", "line-width": 3 },
        });
        map.on("mouseenter", FILL_LAYER_ID, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", FILL_LAYER_ID, () => {
          map.getCanvas().style.cursor = "";
        });
        map.on("click", FILL_LAYER_ID, (event) => {
          const code = event.features?.[0]?.properties?.health_region_code;
          if (typeof code === "string") onSelectRegion(code);
        });
      }
      const bounds = getBounds(data);
      if (bounds) map.fitBounds(bounds, { padding: 32, duration: 0 });
    };
    if (map.isStyleLoaded()) applyData();
    else map.once("load", applyData);
  }, [data, onSelectRegion]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer(SELECTED_LAYER_ID)) return;
    map.setFilter(SELECTED_LAYER_ID, ["==", ["get", "health_region_code"], selectedCode ?? ""]);
  }, [selectedCode]);

  return <div ref={containerRef} className="map-container" data-testid="radar-map" />;
}

function getBounds(data: NonNullable<RadarResponse["geometry"]>) {
  const bounds = new maplibregl.LngLatBounds();
  let hasCoordinate = false;
  for (const feature of data.features) {
    for (const coordinate of coordinatesFromGeometry(feature.geometry)) {
      bounds.extend(coordinate);
      hasCoordinate = true;
    }
  }
  return hasCoordinate ? bounds : null;
}

function* coordinatesFromGeometry(geometry: GeoJSON.Geometry): Generator<[number, number]> {
  if (geometry.type === "GeometryCollection") {
    for (const child of geometry.geometries) yield* coordinatesFromGeometry(child);
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
  for (const child of coordinates) yield* flattenCoordinates(child);
}

"use client";

import { useEffect, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";

export function OverviewMap({ data, selected, field, onSelect, money = false }: {
  data: GeoJSON.FeatureCollection | null; selected: string | null;
  field: string; onSelect: (code: string) => void; money?: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const instance = useRef<Map | null>(null);
  const selectRef = useRef(onSelect);
  useEffect(() => { selectRef.current = onSelect; }, [onSelect]);
  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({ container: container.current, center: [-53, -15], zoom: 3,
      style: { version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f2f4f6" } }] },
      attributionControl: false, minZoom: 2, maxZoom: 10 });
    instance.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    return () => { map.remove(); instance.current = null; };
  }, []);
  useEffect(() => {
    const map = instance.current;
    if (!map || !data) return;
    const update = () => {
      const source = map.getSource("regions") as maplibregl.GeoJSONSource | undefined;
      if (source) source.setData(data);
      else {
        map.addSource("regions", { type: "geojson", data });
        map.addLayer({ id: "fill", type: "fill", source: "regions", paint: {
          "fill-color": ["case", ["==", ["get", field], null], "#e1e1e1",
            ["step", ["get", field], "#dce5ed", money ? 1000 : 1, "#bbcedd",
              money ? 2000 : 2, "#8baabe", money ? 4000 : 3, "#597d97", money ? 8000 : 4, "#294b63"]],
          "fill-outline-color": "#ffffff" } });
        map.addLayer({ id: "selected", type: "line", source: "regions", paint: { "line-color": "#161c21", "line-width": 2.5 } });
        map.on("click", "fill", (event) => {
          const code = event.features?.[0]?.properties?.health_region_code;
          if (typeof code === "string") selectRef.current(code);
        });
        map.on("mouseenter", "fill", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "fill", () => { map.getCanvas().style.cursor = ""; });
      }
      map.setFilter("selected", ["==", ["get", "health_region_code"], selected ?? ""]);
      const bounds = new maplibregl.LngLatBounds();
      const walk = (coordinates: unknown): void => {
        if (!Array.isArray(coordinates)) return;
        if (typeof coordinates[0] === "number" && typeof coordinates[1] === "number") bounds.extend([coordinates[0], coordinates[1]]);
        else coordinates.forEach(walk);
      };
      data.features.forEach(({ geometry }) => { if (geometry && "coordinates" in geometry) walk(geometry.coordinates); });
      if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 25, duration: 0 });
    };
    if (map.isStyleLoaded()) update(); else map.once("load", update);
    return () => { map.off("load", update); };
  }, [data, field, money, selected]);
  return <div ref={container} className="map-container" style={{ minHeight: 360, height: 460 }} aria-label="Mapa das Regiões de Saúde" />;
}

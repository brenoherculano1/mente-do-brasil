# Web Geometry V1

Status: validated local derived visualization layer.

`MDB_WEB_GEOMETRY_V1` is a derived geometry layer for browser rendering. It does
not replace the locked scientific geometry and must not be used for analytical
area, metrics, Moran, LISA, or any scientific recalculation.

## Source

- Table: `geo.health_regions`
- Geography version: `BR_HEALTH_REGIONS_END2024_V1`
- Source CRS: EPSG:4674 / SIRGAS 2000
- Source features: 439
- Source vertices: 5,796,847
- Source validity: 439/439 valid

The source geometry fingerprint is recorded in
`metadata/web_geometry/MDB_WEB_GEOMETRY_V1_manifest.yaml`.

## Baseline

- Scientific GeoJSON: 146,065,496 bytes
- Scientific GeoJSON gzip: 42,643,251 bytes
- API full response: 146,130,031 bytes

The full scientific geometry is too large for normal frontend map rendering.

## Method

The build uses PostGIS `ST_CoverageSimplify` after transforming the locked
geometry to EPSG:5880 for meter-based simplification. The derived result is then
transformed to EPSG:4326 for web use.

The method preserves shared coverage topology when the candidate passes
coverage QC. No `ST_MakeValid`, manual editing, redrawing, dissolving, region
merge, or source mutation is used.

## Candidate Results

- 5000 m: PASS, 23,789 vertices, 99.5896% vertex reduction
- 2000 m: PASS, 53,365 vertices, 99.0794% vertex reduction
- 1000 m: PASS, 103,715 vertices, 98.2108% vertex reduction
- 500 m: TIMEOUT at 120 seconds
- 250 m, 100 m, 50 m: skipped after the finer-than-selected candidate timed out

## Selected Profiles

- `overview`: 5000 m
- `detail`: 1000 m
- `full`: not stored in `web`; read explicitly from locked scientific geometry

`overview` is selected for national map rendering because it is very small and
preserves 439 regions, valid geometries, EPSG:4326, and shared coverage QC.

`detail` is selected for state/regional zoom because it keeps more boundary
detail while remaining much smaller than full geometry.

## Output Assets

Generated assets are under `data/web/MDB_WEB_GEOMETRY_V1/` and are ignored by
Git. Hashes and sizes are recorded in the manifest.

Each static Feature contains only:

- `health_region_code`
- `health_region_name`
- `uf`

Metrics remain in the API/serving layer.

## API Contract

`GET /api/v1/map/health-regions` supports:

- `include_geometry=false`: no geometry
- `include_geometry=true`: defaults to `geometry_profile=overview`
- `geometry_profile=overview`: web geometry, EPSG:4326
- `geometry_profile=detail`: web geometry, EPSG:4326
- `geometry_profile=full`: scientific geometry, EPSG:4674; blocked by default
  on the operational HTTP API.

Full geometry is for audit only. Do not use full geometry for normal web map
rendering.

## Visual QC

Technical SVG overlays are stored in `docs/web_geometry_qc_2026-08-24/`.
They compare a visual reference outline against the derived geometry for Brazil,
coastal/complex regions, and dense internal boundaries.

## Limitations

This layer is for visualization. It does not alter or validate scientific
interpretation, does not create frontend behavior, and does not optimize vector
tiles or map-specific caching.

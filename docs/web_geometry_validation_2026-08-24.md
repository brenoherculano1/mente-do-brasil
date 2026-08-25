# Web Geometry Validation 2026-08-24

Project: Mente do Brasil

Web geometry version: `MDB_WEB_GEOMETRY_V1`

## Source Geometry

- Source table: `geo.health_regions`
- Source geography version: `BR_HEALTH_REGIONS_END2024_V1`
- Source SRID: 4674
- Source features: 439
- Source unique codes: 439
- Source vertices: 5,796,847
- Source validity: 439/439
- Source unchanged after build: PASS

## Baseline

- Scientific GeoJSON: 146,065,496 bytes
- Scientific GeoJSON gzip: 42,643,251 bytes
- API full response: 146,130,031 bytes

## Candidate Benchmark

- 5000 m: PASS; 23,789 vertices; 99.5896% vertex reduction; coverage invalid edges 0
- 2000 m: PASS; 53,365 vertices; 99.0794% vertex reduction; coverage invalid edges 0
- 1000 m: PASS; 103,715 vertices; 98.2108% vertex reduction; coverage invalid edges 0
- 500 m: TIMEOUT at 120 seconds
- 250 m: skipped after 500 m timeout
- 100 m: skipped after 500 m timeout
- 50 m: skipped after 500 m timeout

## Selected Profiles

- Overview: 5000 m
- Detail: 1000 m

## Output Payloads

- Overview GeoJSON: 682,734 bytes
- Overview gzip: 189,864 bytes
- Detail GeoJSON: 2,690,097 bytes
- Detail gzip: 887,284 bytes

## API Payloads

- No geometry: 108,467 bytes
- Overview: 756,156 bytes
- Overview HTTP gzip: 200,382 bytes
- Detail: 2,763,517 bytes
- Full: 146,130,129 bytes
- Final local response times: overview approximately 60 ms, detail approximately
  165 ms, full approximately 19.4 seconds

## QC

- Overview feature count: 439
- Detail feature count: 439
- Overview SRID: 4326
- Detail SRID: 4326
- Overview validity: 439/439
- Detail validity: 439/439
- Overview empty geometries: 0
- Detail empty geometries: 0
- Coverage invalid edges: 0 for both selected profiles
- Visual QC SVGs: generated

## Scientific Regression

- Health Regions: 439
- Municipalities: 5570
- LISA significant: 135
- HH: 60
- LL: 66
- HL: 4
- LH: 5
- `SMALL_SUICIDE_COUNT`: 7
- `ZERO_REGISTERED_BEDS`: 275
- Locked Moran I: 0.525494388844
- Invalid old Moran I remains prohibited: 0.218740812099

## Verdict

PASS. `MDB_WEB_GEOMETRY_V1` is acceptable as a derived local web visualization
layer. Full geometry remains available only by explicit request for audit.

# API v1 Contract

Status: internal local read-only API, not public, not deployed.

The API exposes the locked `MDB_ANALYTICAL_2024_1` serving database through a
small FastAPI surface. It does not recalculate science, mutate data, authenticate
users, create a frontend, or expose raw/canonical files.

## Runtime

- Host: `127.0.0.1`
- Default port: `8000`
- Framework: FastAPI
- Database driver: psycopg 3
- Pool: psycopg pool, min 1 and max 4 connections
- Database role: `mente_do_brasil_api`
- Database access: read-only
- Statement timeout: 30 seconds
- CORS: explicit local origins only; wildcard origins are rejected

Sensitive values live only in local `.env`, which is ignored by Git.

## Endpoints

- `GET /health`
- `GET /ready`
- `GET /api/v1/releases`
- `GET /api/v1/releases/{release_id}`
- `GET /api/v1/indicators`
- `GET /api/v1/indicators/{indicator_id}`
- `GET /api/v1/health-regions`
- `GET /api/v1/health-regions/{health_region_code}`
- `GET /api/v1/map/health-regions`
- `GET /api/v1/municipalities/{municipality_code_ibge}/health-region`
- `GET /api/v1/ufs`

No ranking, recommendation, chatbot, authentication, dashboard, or write
endpoint exists in this API version.

## Query Guards

- `health_region_code`: five digits
- `municipality_code_ibge`: seven digits
- `uf`: two letters
- `limit`: 1 to 100
- `offset`: 0 or greater
- `metric`: closed allowlist only

Allowed map metrics:

- `need_score`
- `capacity_score`
- `mismatch_score`
- `suicide_asmr`
- `psychiatric_admission_rate`
- `caps_rate`
- `mental_health_beds_sus_rate`
- `psychiatrist_fte_rate`

## Error Contract

Errors use a stable JSON shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters."
  }
}
```

The `metric` parameter uses a closed enum. Invalid map metrics return
`INVALID_METRIC`.

## Geometry

`include_geometry=false` is the default for map data. When
`include_geometry=true`, the API returns a GeoJSON FeatureCollection.

`geometry_profile` controls which geometry is returned:

- omitted with `include_geometry=true`: `overview`
- `overview`: `MDB_WEB_GEOMETRY_V1` derived web geometry, EPSG:4326
- `detail`: `MDB_WEB_GEOMETRY_V1` derived web geometry, EPSG:4326
- `full`: locked scientific geometry, EPSG:4674

Every GeoJSON response includes:

```json
{
  "geometry_metadata": {
    "profile": "overview",
    "version": "MDB_WEB_GEOMETRY_V1",
    "crs": "EPSG:4326"
  }
}
```

Full geometry is preserved for audit only. Do not use `geometry_profile=full`
for normal web map rendering.

## Run Locally

```bash
docker compose up -d
uv run --extra geo python scripts/load_serving_database.py
uv run python scripts/provision_api_db_role.py
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
uv run python scripts/validate_api.py
```

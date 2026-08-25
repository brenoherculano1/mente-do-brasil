# API Validation 2026-08-24

Project: Mente do Brasil

Release: `MDB_ANALYTICAL_2024_1`

Scope: first internal local read-only API validation against the validated local
PostgreSQL/PostGIS serving database.

## Locked Scientific States

- `release_status`: `VALIDATING`
- `quality_status`: `VALIDATED`
- `release_gate`: `PASS`
- `release_readiness`: `READY`
- `public_release_status`: `NOT_RELEASED`
- `serving_database_status`: `VALIDATED_LOCAL`

## Local Runtime

- API host: `127.0.0.1`
- API port: `8000`
- API status: `VALIDATED_LOCAL`
- Python: `3.13.5`
- FastAPI: `0.141.1`
- Pydantic: `2.13.4`
- Uvicorn: `0.52.4`
- psycopg: `3.3.4`
- psycopg_pool: `3.3.1`
- Database role: `mente_do_brasil_api`
- Role mode: read-only
- PostgreSQL: `18.6`
- PostGIS: `3.6.4`
- CORS: explicit local origins, no wildcard

## Validation Results

- Health endpoint: PASS
- Readiness endpoint: PASS
- Releases endpoint: PASS
- Indicators endpoint: PASS
- Health-region list endpoint: PASS
- Health-region profile endpoint: PASS
- Municipality lookup endpoint: PASS
- UF lookup endpoint: PASS
- Map metadata endpoint: PASS
- GeoJSON map endpoint: PASS
- Default geometry profile: `overview`
- Overview geometry: PASS, 439 features, EPSG:4326
- Detail geometry: PASS, 439 features, EPSG:4326
- Full geometry: PASS, 439 features, EPSG:4674
- HTTP gzip: PASS
- Error contract: PASS
- Parameter guards: PASS
- Invalid metric error code: `INVALID_METRIC`
- Read-only write rejection: PASS
- SQL injection smoke: PASS
- Scientific regression smoke: PASS

## Counts Confirmed

- Health Regions: 439
- Municipalities: 5570
- Map features with geometry: 439
- LISA significant: 135
- LISA HH: 60
- LISA LL: 66
- LISA HL: 4
- LISA LH: 5
- `SMALL_SUICIDE_COUNT`: 7
- `ZERO_REGISTERED_BEDS`: 275

## Smoke Benchmark

- `/health`: PASS
- `/ready`: PASS
- no geometry map: 108,467 bytes, approximately 127 ms locally
- overview map: 756,156 bytes, approximately 60 ms locally
- overview map with HTTP gzip: 200,382 bytes
- detail map: 2,763,517 bytes, approximately 165 ms locally
- full scientific map: 146,130,129 bytes, approximately 19.4 seconds locally

The full GeoJSON payload remains heavy. It is explicitly preserved for audit,
not normal frontend map rendering.

## Commands

```bash
uv run python scripts/validate_api.py
uv run pytest tests/api/test_api_contract.py
uv run ruff check api scripts tests
```

## Boundary

No frontend, deployment, authentication layer, cloud database, new indicator, or
scientific recalculation was created in this phase.

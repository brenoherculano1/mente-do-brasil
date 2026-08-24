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
- `/api/v1/map/health-regions?include_geometry=true&metric=mismatch_score`:
  439 features, 146,130,031 bytes, approximately 22.3 seconds locally after
  increasing the API role statement timeout to 30 seconds.

The full GeoJSON payload is heavy. It was documented and preserved without
simplification, reprojection, rounding, or geometry repair.

## Commands

```bash
uv run python scripts/validate_api.py
uv run pytest tests/api/test_api_contract.py
uv run ruff check api scripts tests
```

## Boundary

No frontend, deployment, authentication layer, cloud database, new indicator, or
scientific recalculation was created in this phase.

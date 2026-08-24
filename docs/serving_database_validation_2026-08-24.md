# Serving Database Validation - 2026-08-24

Status: `VALIDATED_LOCAL`

## Runtime

- Docker Desktop / Engine: running locally.
- Docker Engine: `29.7.2`.
- Docker Compose: `v5.4.0`.
- Host architecture: `arm64`.
- PostgreSQL exposure: `127.0.0.1:5432 -> 5432/tcp`.
- Local `.env`: present, ignored by Git, mode `0600`; password not documented.

## Image

- Official `postgis/postgis:18-3.6` index digest:
  `sha256:8d67cc8fe5f45808d54fe95cc210b05ce6b3ea3682e9a97c36362f3e1b8ff939`.
- Official `postgis/postgis:18-3.6` does not publish a `linux/arm64/v8`
  manifest, so it was not used on this Apple Silicon host.
- Local serving image: `mente-do-brasil-postgis:18-3.6.4`.
- Effective local image digest:
  `mente-do-brasil-postgis@sha256:efbe9919290ea632ce1acb3145d984935d73c1976e882b14b806a6ee3e35dd4e`.
- Compose image manifest:
  `sha256:5d375c314fd95fe6262c27ead543e54c7c05d4714503bce4885edead31a4afd7`.
- Base image: official `postgres:18`.
- Base image digest:
  `postgres@sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941`.
- Image architecture: `arm64`.
- PostgreSQL 18 image metadata: `PGDATA=/var/lib/postgresql/18/docker`;
  image volume: `/var/lib/postgresql`.

## Database Versions

- PostgreSQL: `18.6 (Debian 18.6-1.pgdg13+2)`.
- PostGIS: `3.6.4 94d984b`.
- `SELECT version()` and `SELECT PostGIS_Full_Version()` were executed against
  the live database.

## Load And Validation

- `uv run --extra geo python scripts/load_serving_database.py`: `PASS`.
- First load status: `NEW LOAD`.
- Second load status: `PASS / NO CHANGE`.
- `uv run --extra geo python scripts/validate_serving_database.py`: `PASS`.
- `uv run python scripts/validate_foundation.py`: `PASS`, 53 tests.
- `python3 scripts/validate_foundation.py`: `PASS`, 53 tests with 12 skips
  because system Python lacks Parquet dependencies.
- `py_compile` for changed Python scripts: `PASS`.

## Live Counts

- `meta.releases`: 1 for `MDB_ANALYTICAL_2024_1`.
- `geo.health_regions`: 439 for `BR_HEALTH_REGIONS_END2024_V1`.
- `geo.municipality_health_region_crosswalk`: 5570 for
  `BR_HEALTH_REGIONS_END2024_V1`.
- `analytics.health_region_metrics`: 439 for `MDB_ANALYTICAL_2024_1`.
- `serving.health_region_profile`: 439.
- `serving.health_region_map`: 439.
- `serving.health_region_lookup`: 439.

## Geometry

- Non-null geometries: 439/439.
- `ST_SRID(geom) = 4674`: 439/439.
- `ST_IsValid(geom)`: 439/439.
- Geometry type smoke test: `MULTIPOLYGON`.
- Loader WKB comparison against canonical locked geometry: `PASS`.

## Scientific Locks

- Global Moran I: `0.525494388844`.
- pseudo-p: `0.0001`.
- LISA significant: 135.
- HH: 60.
- LL: 66.
- HL: 4.
- LH: 5.
- Invalid old Moran value `0.218740812099`: not used as primary.

## Flags

- `SMALL_SUICIDE_COUNT`: 7.
- `ZERO_REGISTERED_BEDS`: 275.

## Guardrails

- Idempotent reload: `PASS / NO CHANGE`.
- Immutability guard: `IMMUTABILITY VIOLATION` triggered using a rollback-only
  temporary mutation of stored release hashes.
- Constraint tests with rollback: invalid health-region code, negative
  population, percentile > 1, mismatch > 1, and wrong SRID were rejected.

## Smoke Tests

- Region lookup by `health_region_code`: `12001`, Alto Acre, AC.
- UF lookup: AC returned 3 health regions.
- Technical mismatch ordering query: executed without creating a public ranking.
- `serving.health_region_profile`: queried for `12001`.
- `serving.health_region_map`: queried for `12001` without serializing full
  geometry.
- `serving.health_region_lookup`: 439 rows.
- Municipality crosswalk: `1100015`, Alta Floresta D'Oeste -> `11005`, Zona da Mata.

No raw, canonical, or scientific release status files were modified.

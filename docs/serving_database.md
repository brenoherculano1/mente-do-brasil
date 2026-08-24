# Serving Database

The Mente do Brasil local serving database sits after the canonical layer:

```text
RAW
  -> CANONICAL
  -> POSTGRESQL/POSTGIS SERVING DATABASE
  -> API [future]
  -> WEB [future]
```

The serving database does not recalculate scientific outputs. It copies the
locked canonical Parquet files, validates hashes, imports the locked geography,
and exposes read-oriented serving views for a future API.

## Schemas

- `meta`: release metadata and indicator registry.
- `geo`: locked health-region geography and municipality crosswalk.
- `analytics`: release-specific analytical metrics.
- `serving`: read-oriented views for future API consumption.

## Tables

- `meta.releases`: one row per analytical release. Stores canonical hashes and
  the locked release states.
- `meta.indicators`: indicator registry populated only from
  `metadata/indicators/*.yaml`.
- `geo.health_regions`: locked health-region dimension with PostGIS
  `MultiPolygon` geometry in SRID 4674.
- `geo.municipality_health_region_crosswalk`: locked municipality-to-health-
  region crosswalk.
- `analytics.health_region_metrics`: release-specific metrics keyed by
  `release_id` and `health_region_code`.

## Views

- `serving.health_region_profile`: complete non-geometry profile for each
  health region and release.
- `serving.health_region_map`: map-ready view with full locked geometry.
- `serving.health_region_lookup`: compact lookup/autocomplete source.

## Keys

- `geo.health_regions`: `(geography_version, health_region_code)`.
- `geo.municipality_health_region_crosswalk`:
  `(geography_version, municipality_code_ibge)`.
- `analytics.health_region_metrics`: `(release_id, health_region_code)`.

`analytics.health_region_metrics.geography_version` is a technical integrity
field. It allows the database to enforce that a release's metrics reference the
same locked geography as `meta.releases`.

## Immutability

For `MDB_ANALYTICAL_2024_1`, the loader compares stored canonical hashes before
loading. If the same `release_id` already exists with different hashes, it stops
with `IMMUTABILITY VIOLATION`. Corrections must use a new `release_id`.

## Local Startup

Docker was not available in the current environment, so the database was not
started here. When Docker is available:

```bash
cp .env.example .env
docker compose up -d
uv run --extra geo python scripts/load_serving_database.py
uv run --extra geo python scripts/validate_serving_database.py
```

The Compose service uses the stable PostGIS image configured in
`compose.yaml`: `postgis/postgis:18-3.6`.

## Reset Local Database

This only destroys the local Docker database volume:

```bash
docker compose down -v
```

Do not delete raw or canonical source files to reset the database.

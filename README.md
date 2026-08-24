# Mente do Brasil

Mente do Brasil is a Brazilian public data and territorial intelligence project for mental health.

The repository is at local serving-database preparation stage. It currently
defines the technical structure, metadata contracts, release/version
conventions, canonical analytical layer, and PostgreSQL/PostGIS serving schema
needed to support a future read-only API. It does not yet contain a public
website, dashboard, authentication, API, cloud database, or deployed service.

## Scientific Scope

The initial analytical release is designed for Brazil's 439 Health Regions, using `health_region_code` as the canonical geographic key. Region names must never be used as primary keys.

Initial locked versions:

- `geography_version`: `BR_HEALTH_REGIONS_END2024_V1`
- `method_version`: `MDB_METHOD_1.0`
- `release_id`: `MDB_ANALYTICAL_2024_1`

The first analytical release is intended to be immutable once published. Corrections must create a new release rather than overwriting released outputs.

## Repository Structure

```text
data/
  raw/          immutable source files, not tracked by Git
  staging/      derived intermediate files
  canonical/    cleaned canonical analytical tables
  releases/     immutable public/final release artifacts

db/
  migrations/   SQL migrations for the local PostgreSQL/PostGIS serving database

pipeline/
  geography/    geographic crosswalk and geometry preparation
  population/   population denominators
  sim/          mortality source processing
  sih/          hospital admissions source processing
  cnes/         facilities, beds, and workforce source processing
  metrics/      indicators, percentile ranks, composites
  spatial/      spatial output storage interfaces

metadata/
  indicators/   YAML indicator definitions
  sources/      source manifests
  releases/     release manifests

tests/
  geography/    geography structural tests
  data_quality/ metric and missingness tests
  regression/   locked result regression tests

web/
  reserved only; no frontend exists yet
```

Current product data flow:

```text
RAW
  -> CANONICAL
  -> POSTGRESQL/POSTGIS SERVING
  -> API [future]
  -> WEB [future]
```

The API and frontend have not been built.

## Data Philosophy

`data/raw/` is immutable. Raw files must be copied into the project exactly as obtained, with source provenance recorded separately. Do not edit, normalize, or overwrite raw files.

Derived files should move through:

1. `data/staging/`
2. `data/canonical/`
3. `data/releases/`

Missingness must be explicit. The project distinguishes:

- `0`
- `NA`
- `not_available`
- `not_applicable`
- `suppressed`

Missing values must not be silently converted to zero.

## Initial Indicators

Need:

- `suicide_asmr`
- `psychiatric_admission_rate`

Capacity:

- `caps_rate`
- `mental_health_beds_sus_rate`
- `psychiatrist_fte_rate`

Composite definitions are documented in `metadata/releases/MDB_ANALYTICAL_2024_1.yaml`.

## Locked Spatial Result Placeholders

This repository foundation does not recalculate spatial statistics. It records placeholders for the already validated results:

- Global Moran I: `0.525494388844`
- pseudo-p: `0.0001`
- permutations: `9999`
- seed: `20260823`
- weights: queen contiguity, row-standardized
- islands: `0`
- FDR-significant LISA regions: `135`
- HH: `60`
- LL: `66`
- HL: `4`
- LH: `5`

The invalid old Moran value `0.218740812099` must never be used.

## Running Tests

The initial test suite uses Python's standard library `unittest` so it can run before scientific dependencies are installed:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

After setting up a scientific environment, the same rules can be migrated or mirrored in `pytest`.

## What Does Not Exist Yet

This repository does not yet include:

- raw DATASUS/CNES/IBGE files;
- frontend or dashboard;
- public API;
- authentication;
- cloud database;
- deployment;
- recalculated spatial analyses.

Placeholders are explicit where source URLs, file hashes, extraction timestamps, or final generated artifacts are not yet available.

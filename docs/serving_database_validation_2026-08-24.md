# Serving Database Validation - 2026-08-24

Status: `BLOCKED_BY_LOCAL_DOCKER`

Docker check:

- `docker --version`: unavailable, command not found.
- `docker compose version`: unavailable because Docker is not installed.

Implemented and statically validated:

- SQL migrations for `meta`, `geo`, `analytics`, and `serving`.
- Local `compose.yaml` for PostgreSQL/PostGIS.
- Reproducible loader with canonical hash checks.
- Standalone serving database validator.
- Static regression tests for migrations, views, scripts, and environment
  configuration.

Not executed in this environment:

- Starting PostgreSQL/PostGIS.
- Applying migrations to a live database.
- Loading canonical data into PostgreSQL.
- Post-load SQL validation.
- Idempotent live reload.
- Live immutability-violation simulation.

Direct script checks:

- `uv run --extra geo python scripts/load_serving_database.py`: failed at local
  PostgreSQL connection because no server was available on `localhost:5432`.
- `uv run --extra geo python scripts/validate_serving_database.py`: failed at
  the same local PostgreSQL connection boundary.

No raw, canonical, or scientific release files were modified.

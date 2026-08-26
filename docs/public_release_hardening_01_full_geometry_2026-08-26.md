# Public Release Hardening 01 - Full Geometry Restriction

## Scope

This hardening round changes only the operational HTTP exposure of
`geometry_profile=full`.

The locked scientific geometry remains preserved in
`BR_HEALTH_REGIONS_END2024_V1`. The web geometry release remains
`MDB_WEB_GEOMETRY_V1`.

## Policy

- `overview`: allowed by default.
- `detail`: allowed by default for the current V1.
- `full`: blocked by default on the operational API.
- Internal opt-in requires the server-only environment variable
  `MDB_API_ALLOW_FULL_GEOMETRY=true`.

The setting is intentionally not prefixed with `NEXT_PUBLIC_`. Request
parameters, headers, cookies, request bodies, and frontend state cannot enable
full geometry.

## Default Behavior

With `MDB_API_ALLOW_FULL_GEOMETRY=false`, absent, or invalid:

```text
GET /api/v1/map/health-regions?include_geometry=true&geometry_profile=full
status: 403
error: FULL_GEOMETRY_RESTRICTED
```

The guard runs before `list_map_data`, preventing the heavy full geometry query
and serialization path from executing.

## Validation Results

- Default `full` request: `403`.
- Default `full` response size: `112` bytes.
- Default `full` elapsed time: `1.84` ms in targeted policy validation.
- `env=false` behavior: blocked.
- `env=true` direct policy behavior: allowed through the internal code path.
- Heavy-query short circuit: `0` calls to `list_map_data` while blocked.
- `overview`: `200`, `439` features, `756,156` bytes.
- `detail`: `200`, `439` features, `2,763,517` bytes.
- Invalid profile remains `422`.
- Frontend production request references to `geometry_profile=full`: `0`.

## Regression Evidence

- `audit_results/full_geometry_policy_validation.txt`
- `audit_results/full_geometry_guard_short_circuit.txt`
- `audit_results/api_surface_after_full_hardening.txt`
- `audit_results/full_geometry_frontend_usage.txt`
- `audit_results/full_geometry_env_validation.txt`
- `audit_results/api_regression.txt`
- `audit_results/scientific_regression.txt`
- `audit_results/frontend_unit.txt`
- `audit_results/frontend_e2e.txt`
- `audit_results/production_e2e.txt`
- `audit_results/lint.txt`
- `audit_results/typecheck.txt`
- `audit_results/production_build.txt`
- `audit_results/release_status_validation.txt`

## Release Status

`public_release_status` remains `NOT_RELEASED`.

The website remains not release-ready because production same-origin/CORS,
security headers, rate limits, cache policy, robots/indexing, privacy/contact,
observability, and backup/restore work are still outside this hardening round.

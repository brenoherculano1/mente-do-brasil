# Frontend Validation 2026-08-25

Frontend status: `VALIDATED_LOCAL`.

## Scope

This round only closes the existing Frontend V1 vertical slice:

- `/`
- `/regiao/[codigo]`

No new routes, indicators, rankings, calculations, reports, downloads, API
surfaces, or scientific variables were added.

## Runtime Versions

- Node: `v22.15.0`
- npm: `10.9.2`
- Next.js: `16.3.2`
- eslint-config-next: `16.3.2`
- React: `19.2.8`
- React DOM: `19.2.8`
- MapLibre GL JS: `5.24.0`

## UX Corrections

- Mobile home order: intro, territorial search, metric selector, map,
  selected-region summary, legend/explanations, accessible list.
- Mobile map top: `658.328125` px in a `390 x 844` viewport.
- Mobile map height: `520` px.
- Mobile home full page height: `2336` px.
- Elements before mobile map: header, intro, territorial search, metric selector.
- The map appears before the expanded accessible textual list.
- Desktop map top: `278.234375` px in a `1440 x 1000` viewport.
- Desktop map height: `760` px.
- Desktop home full page height: `1636` px.
- Desktop explorer keeps controls/support on the left and the map as the primary
  right-column surface.

## Accessible List

- Previous arbitrary `features.slice(0, 8)` list removed.
- List is collapsed by default, so it no longer pushes the map down.
- Expanded list exposes all `439` Health Regions.
- List filter supports Health Region name, UF, and Health Region code.
- Regression checked with `Alto Acre`: filtered result `1 of 439`.

## Mobile Profile

- Profile metric cards use two columns on mobile where width allows.
- Labels and values remain visible.
- No labels, metrics, scientific fields, or profile sections were removed.
- Mobile profile screenshot height: `10172` px.

## Security

- Map tooltip HTML injection removed.
- Tooltip is created with DOM elements and `textContent`.
- Unit regression includes payload `<img src=x onerror=alert(1)>` and verifies
  no image element is inserted.

## Search Copy

The search placeholder now says:

```text
Região de Saúde ou código IBGE do município
```

This matches V1 behavior: Health Region name/code search plus direct 7-digit
municipality IBGE lookup.

## Metadata Semantics

`commit_basis` was replaced with:

- `base_commit: fc0a6a2`
- `frontend_foundation_commit: 5674db2`

The metadata does not self-reference the commit being produced in this
validation round.

## Map Contract

- Endpoint: `/api/v1/map/health-regions`
- Metric default: `mismatch_score`
- Geometry profile: `overview`
- Geometry version: `MDB_WEB_GEOMETRY_V1`
- Feature count: `439`
- HTTP payload: `756156` bytes
- gzip payload: `200382` bytes
- Source geometry: 439/439 valid, SRID `4674`
- Web overview geometry: 439/439 valid, SRID `4326`
- API GeoJSON CRS: `EPSG:4326`
- Full geometry in normal frontend: not used

## Screenshots

Saved under `docs/frontend_qc_2026-08-25/`:

- `desktop_home.png`
- `mobile_home.png`
- `desktop_profile.png`
- `mobile_profile.png`
- `desktop_home_accessible_list.png`
- `mobile_home_accessible_list.png`
- `desktop_home_metrics.json`
- `mobile_home_metrics.json`

Screenshots were generated from the production Next server (`npm run start`),
not `next dev`. The Next dev indicator was not present.

## Frontend Gates

- `npm ci`: PASS
- `npm run lint`: PASS
- `npm run typecheck`: PASS
- `npm run test`: PASS, 12 tests
- `npm run build`: PASS
- `npm run test:e2e`: PASS, 8 tests, production server
- `npm audit --omit=dev`: PASS, 0 vulnerabilities

## Backend Regression

- `uv run pytest`: PASS, 65 tests
- `uv run ruff check .`: PASS
- `uv run python scripts/validate_api.py`: PASS
- `uv run python scripts/validate_serving_database.py`: PASS
- `uv run python scripts/validate_foundation.py`: PASS

## Guardrails

- No scientific recalculation introduced.
- No ranking introduced.
- No Mismatch deficit/access/quality/unmet-need claim introduced.
- Null map values remain missing, not zero.
- The frontend still uses 439 Health Regions from the API.
- `/estado/[uf]`, `/metodologia`, `/dados`, and `/sobre` remain future work.

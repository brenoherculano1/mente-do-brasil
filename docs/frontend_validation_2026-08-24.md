# Frontend Validation 2026-08-24

Frontend status: `VALIDATED_LOCAL`.

## Runtime Versions

- Node: `v22.15.0`
- npm: `10.9.2`
- Next.js: `16.3.2`
- React: `19.2.8`
- React DOM: `19.2.8`
- MapLibre GL JS: `5.24.0`

## Implemented Routes

- `/`: PASS
- `/regiao/[codigo]`: PASS
- `/regiao/12001`: PASS, Alto Acre loaded from API.
- Invalid region route: PASS, user-facing not-found state.

## Map

- Endpoint: `/api/v1/map/health-regions`
- Metric default: `mismatch_score`
- Geometry profile: `overview`
- Geometry version: `MDB_WEB_GEOMETRY_V1`
- Feature count: `439`
- HTTP payload: `756156` bytes
- gzip payload: `200382` bytes
- CRS: `EPSG:4326`
- Full geometry in normal frontend: not used

Map behavior validated:

- hover/tooltip: implemented
- click selection: implemented
- selected region outline: implemented
- zoom/pan: implemented
- link to region profile: implemented
- Brazil fit: visually checked in desktop and mobile screenshots

## Search

- Health Region name/code search: PASS
- Search term `Alto Acre`: PASS
- 7-digit IBGE municipality lookup path: implemented
- Free-text municipality search: intentionally not implemented; no API endpoint.

## Profile 12001

- Health Region: Alto Acre
- UF: AC
- municipality count: 4
- population: 75243
- Need: `0.3401826484018265`
- Capacity: `0.3470319634703196`
- Mismatch: `-0.0068493150684931`
- LISA significant: true
- LISA cluster rendered as `LH`
- Flags: `ZERO_REGISTERED_BEDS`

## Screenshots

Saved under `docs/frontend_qc_2026-08-24/`:

- `desktop_home.png`
- `mobile_home.png`
- `desktop_profile.png`
- `mobile_profile.png`

## Frontend Gates

- `npm run lint`: PASS
- `npm run typecheck`: PASS
- `npm run test`: PASS, 11 tests
- `npm run build`: PASS
- `npm run test:e2e`: PASS, 6 tests
- `npm audit --omit=dev`: PASS, 0 vulnerabilities

## Backend Regression

- `uv run pytest`: PASS, 65 tests
- `uv run ruff check .`: PASS
- `uv run python scripts/validate_api.py`: PASS
- `uv run python scripts/validate_serving_database.py`: PASS
- `uv run python scripts/validate_foundation.py`: PASS

## Accessibility Checks

- Semantic landmarks: PASS
- Labels for search and metric selector: PASS
- Visible focus: PASS
- Keyboard-accessible search/listing path: PASS
- Color is not the only navigation path: PASS
- Reduced-motion rule: PASS
- Stack traces hidden from user-facing error states: PASS

## Lighthouse

Not run in this validation. This is not a blocker for the local vertical slice.

## Guardrails

- No ranking introduced.
- No Mismatch deficit/access/quality claim introduced.
- Null map values are styled as missing, not zero.
- Frontend does not recalculate locked scientific outputs.
- `/estado/[uf]`, `/metodologia`, `/dados`, and `/sobre` remain future work.

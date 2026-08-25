# Methodology Page 2026-08-25

Status: validated locally.

## Objective

Create `/metodologia` as a public, readable, audit-oriented explanation of the
locked Mente do Brasil method. The page is not a manuscript methods section and
does not add calculations, indicators, maps, API calls, downloads, or new product
features.

## Internal Sources Consulted

- `metadata/releases/MDB_ANALYTICAL_2024_1.yaml`
- `metadata/releases/MDB_ANALYTICAL_2024_1_canonical.yaml`
- `metadata/releases/MDB_ANALYTICAL_2024_1_serving.yaml`
- `metadata/publication/manuscript_status.yaml`
- `metadata/indicators/suicide_asmr.yaml`
- `metadata/indicators/psychiatric_admission_rate.yaml`
- `metadata/indicators/caps_rate.yaml`
- `metadata/indicators/mental_health_beds_sus_rate.yaml`
- `metadata/indicators/psychiatrist_fte_rate.yaml`
- `src/mente_do_brasil/quality.py`
- `src/mente_do_brasil/constants.py`
- `data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle/IMPORT_MANIFEST.json`
- `/Users/brenoherculano/Desktop/Brazil Mental Health Spatial Inequality Project/phase1_method_lock/analysis_config_LOCKED.yaml`
- `/Users/brenoherculano/Desktop/Brazil Mental Health Spatial Inequality Project/phase1_method_lock/method_decision_ledger.md`
- `/Users/brenoherculano/Desktop/Brazil Mental Health Spatial Inequality Project/phase1_method_lock/METHODS_LOCKED_SNAPSHOT.md`

The Desktop Phase 1 files were used because the repository provenance manifest
points to the locked Phase 1 configuration and script hashes, and the local import
bundle preserves result artifacts rather than the full original analysis config.

## Verified Technical Details

| Item | Verified Definition | Source |
| --- | --- | --- |
| psychiatric_admission_rate denominator | admissions per 100,000 person-years; population person-years from locked DATASUS/IBGE denominators | `metadata/indicators/psychiatric_admission_rate.yaml` |
| caps_rate denominator | CAPS per 100,000 residents; 2024 population denominator | `metadata/indicators/caps_rate.yaml` |
| mental_health_beds_sus_rate denominator | SUS beds per 100,000 residents; 2024 population denominator | `metadata/indicators/mental_health_beds_sus_rate.yaml` |
| psychiatrist_fte_rate denominator | psychiatrist FTE per 100,000 residents; 2024 population denominator | `metadata/indicators/psychiatrist_fte_rate.yaml` |
| standard population | `WHO_standard_population` | `analysis_config_LOCKED.yaml` |
| percentile algorithm | observed values sorted; missing values preserved; percentile = `(less + (equal - 1) / 2) / max(n_observed - 1, 1)` | `src/mente_do_brasil/quality.py` |
| percentile ties | average position for tied values | `src/mente_do_brasil/quality.py` and `analysis_config_LOCKED.yaml` |
| percentile null handling | semantic missing values preserved; valid zeros retained | `src/mente_do_brasil/quality.py` |

## Locked Values Rendered

- Health Regions: 439.
- Municipalities: 5,570.
- Method: `MDB_METHOD_1.0`.
- Analytical release: `MDB_ANALYTICAL_2024_1`.
- Canonical: `MDB_CANONICAL_1.0`.
- Geography: `BR_HEALTH_REGIONS_END2024_V1`.
- Web geometry: `MDB_WEB_GEOMETRY_V1`.
- Global Moran I: `0.525494388844`.
- Global Moran pseudo-p: `0.0001`.
- LISA significant: 135.
- LISA HH/LL/HL/LH: 60/66/4/5.
- `SMALL_SUICIDE_COUNT`: 7.
- `ZERO_REGISTERED_BEDS`: 275.
- Manuscript status public claim: `Status: manuscrito submetido ao Health & Place.`

`MDB_DATA_CONTRACT_V1.0` was not rendered because it was not found as a
versioned identifier in the repository.

## Manuscript Provenance

The public manuscript claim is backed by
`metadata/publication/manuscript_status.yaml`. The record was incorporated from
externally verified Google Drive evidence supplied in the task instructions,
with private administrative fields excluded. The public page deliberately states
only the stable historical event of submission and does not display mutable
editorial workflow state.

## UX Decisions

- Desktop uses a restrained sticky section index and a single main reading
  column.
- Mobile uses a compact `Nesta página` disclosure with `aria-expanded`.
- Technical details use native `details/summary`.
- Tables remain semantic and are wrapped for narrow screens.
- No external images, maps, MapLibre components, or data API calls are used by
  `/metodologia`.

## Hard Stops Evaluated

- Standard population: located.
- Denominators: located.
- Percentile algorithm: located.
- Moran and LISA values: matched locked constants and release metadata.
- Flag counts: matched serving validation metadata and regression tests.
- 439 Health Regions and 5,570 municipalities: preserved.
- No DOI, publication claim, URL reconstruction, or Health & Place acceptance
  claim was introduced.

## Tests And QA

Final local validation:

- `npm run lint`: PASS.
- `npm run typecheck`: PASS.
- `npm run test`: PASS, 18/18.
- `npm run build`: PASS; `/metodologia` prerendered as static content.
- `npm run test:e2e`: PASS, 10/10 executed, 2 project-scope skips.
- `npm audit --omit=dev`: PASS, 0 vulnerabilities.
- `uv run pytest`: PASS, 65/65.
- `uv run ruff check .`: PASS.
- `uv run python scripts/validate_api.py`: PASS.
- `uv run python scripts/validate_serving_database.py`: PASS.
- `uv run python scripts/validate_foundation.py`: PASS, 53/53.

Screenshots generated from the production Next server:

- `docs/methodology_qc_2026-08-25/desktop_methodology_full.png`
- `docs/methodology_qc_2026-08-25/desktop_methodology_top.png`
- `docs/methodology_qc_2026-08-25/desktop_methodology_need_capacity.png`
- `docs/methodology_qc_2026-08-25/desktop_methodology_spatial.png`
- `docs/methodology_qc_2026-08-25/desktop_methodology_limitations.png`
- `docs/methodology_qc_2026-08-25/mobile_methodology_full.png`
- `docs/methodology_qc_2026-08-25/mobile_methodology_top.png`
- `docs/methodology_qc_2026-08-25/mobile_methodology_mid.png`
- `docs/methodology_qc_2026-08-25/mobile_methodology_bottom.png`
- `docs/methodology_qc_2026-08-25_final/desktop_methodology_scientific_basis.png`
- `docs/methodology_qc_2026-08-25_final/mobile_methodology_scientific_basis.png`

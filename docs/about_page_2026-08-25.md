# /sobre V1 implementation

## Objective

Implement the static institutional `/sobre` route for Mente do Brasil without changing science, API, database, geography, release status, data contract, canonical data, or methodology.

## Positioning

Rendered positioning:

> O Mente do Brasil é uma infraestrutura independente de dados e inteligência territorial em saúde mental construída a partir de dados públicos brasileiros.

The page describes the project as infrastructure, not as a dashboard, commercial landing page, official government system, clinical tool, founder biography, or MedLegacy product.

## Independence Statement

Rendered independence statement:

> O Mente do Brasil é uma iniciativa independente. Utiliza dados públicos produzidos por sistemas e instituições oficiais, mas não é um sistema oficial do Ministério da Saúde, DATASUS, IBGE ou de governos estaduais ou municipais.

Rendered government disclaimer:

> O uso desses dados não implica vínculo institucional, endosso ou participação dessas instituições no desenvolvimento do projeto.

No government logos, official affiliation claims, partnerships, endorsements, sponsors, team, founder, or governance bodies were introduced.

## Current Scope

- Primary analytical unit: Região de Saúde.
- Health Regions: 439.
- Municipalities associated with the release geography: 5,570.
- Need period: 2022–2024.
- Capacity reference: December 2024 for CNES components.
- Need: suicide mortality plus psychiatric admissions registered in SUS.
- Capacity: CAPS plus SUS mental-health beds in general hospitals plus SUS psychiatrist FTE.
- Mismatch: relative territorial misalignment signal between measured need and registered capacity.

## Claim Boundaries

The page states that Mente do Brasil is not:

- an official government system;
- an individual diagnostic tool;
- a direct measure of mental-disorder prevalence;
- a standalone measure of care quality or access;
- a ranking of territories;
- an automatic resource-allocation recommendation system;
- a patient service directory.

Claim audit passed for:

- no care-deficit claim;
- no unmet-need claim;
- no disease-hotspot claim;
- no automatic allocation recommendation;
- no official-platform claim;
- no commercial impact claim.

## Sources Consulted

Versioned metadata and source constants used by the implementation:

- `metadata/releases/MDB_ANALYTICAL_2024_1.yaml`
- `metadata/canonical/health_regions_v1.yaml`
- `metadata/canonical/municipality_health_region_crosswalk_v1.yaml`
- `metadata/contracts/MDB_DATA_CONTRACT_V1.0.yaml`
- `metadata/publication/manuscript_status.yaml`
- `web/lib/data-page.ts`
- `web/lib/methodology.ts`

## Publication Status

Public release status remains:

`NOT_RELEASED`

Rendered public copy:

> O release analítico atual foi validado, mas ainda não foi publicado publicamente.

Manuscript status rendered conservatively:

> Status: manuscrito submetido ao Health & Place.

No accepted, published, in press, or peer-reviewed claim was added.

## Tests

Validation logs:

- Unit tests: `audit_results/unit_tests.txt`
- E2E: `audit_results/e2e.txt`
- Production E2E: `audit_results/production_e2e.txt`
- Lint: `audit_results/lint.txt`
- Typecheck: `audit_results/typecheck.txt`
- Production build: `audit_results/production_build.txt`
- Production serving: `audit_results/production_serving.txt`
- API regression: `audit_results/api_regression.txt`
- Scientific regression: `audit_results/scientific_regression.txt`
- Existing frontend regression: `audit_results/existing_frontend_regression.txt`
- Independence claim validation: `audit_results/independence_claim_validation.txt`
- Government affiliation validation: `audit_results/government_affiliation_validation.txt`
- Publication claim validation: `audit_results/publication_claim_validation.txt`
- Scientific claim validation: `audit_results/scientific_claim_validation.txt`
- Link validation: `audit_results/about_links_validation.txt`
- Accessibility validation: `audit_results/accessibility_validation.txt`

Results:

- Unit tests: 31/31 passed.
- E2E: 14 passed, 6 skipped.
- Production E2E: 14 passed, 6 skipped.
- Existing frontend regression: 12 passed, 4 skipped.
- Scientific regression: 69/69 passed.
- Lint, typecheck, production build, production serving, API regression, claim audits, links, and accessibility validation passed.

## Screenshots

Screenshots generated from production serving:

`docs/about_page_qc_2026-08-25/`

Included files:

- `desktop_about_top.png`
- `desktop_about_principles.png`
- `desktop_about_scope.png`
- `desktop_about_independence.png`
- `desktop_about_bottom.png`
- `desktop_about_full.png`
- `mobile_about_top.png`
- `mobile_about_scope.png`
- `mobile_about_bottom.png`
- `mobile_about_full.png`

## Known Future Work

Next route to specify separately:

`/estado/[uf]`

No `/estado/[uf]`, Radar Territorial, peer regions, automatic reports, time series, financing, flows, Modo Gestor, public API, or downloads were implemented in this task.

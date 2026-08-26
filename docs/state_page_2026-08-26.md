# State Page V1 - 2026-08-26

## Scope

This file documents the V1 implementation of `/estado/[uf]` for Mente do Brasil.
The page is a state-level explorer of already computed Health Region indicators.
It does not introduce a state score, state rank, state index, new indicator, or
new scientific rule.

## Route Contract

- Route: `/estado/[uf]`
- Valid UFs: 27 Brazilian federation units.
- Canonical URL: uppercase UF.
- Lowercase input such as `/estado/ac` redirects to `/estado/AC`.
- Invalid UF such as `/estado/XX` renders the state not-found state.

## API Contract

The state page uses:

- `GET /api/v1/states/{uf}`
- `GET /api/v1/map/health-regions?uf={UF}&include_geometry=true&geometry_profile=overview`

The state endpoint returns the selected UF, state display name, release id,
administrative state aggregates, and the Health Region rows for that UF.

Returned regional values are locked values from the serving database. Need,
Capacity, Mismatch, LISA, percentiles, and quality flags are not recalculated in
the frontend.

## Administrative Aggregations

The following state-level values are administrative summaries only:

- Health Region count.
- Population, computed by summing returned Health Region population.
- Municipality count, computed by summing returned Health Region municipality
  counts.
- LISA significant count and cluster counts, computed from existing regional
  LISA fields.
- Quality flag counts, computed from existing regional quality flags.

These summaries are not scores and are not used for ranking.

## Geometry

The map uses only Health Region overview geometry from `MDB_WEB_GEOMETRY_V1`.

- Geometry profile: `overview`
- CRS: `EPSG:4326`
- Feature filter: selected UF only
- Acre validation: 3 Health Regions and 3 map features
- Sao Paulo validation: 62 Health Regions and 62 map features
- Distrito Federal validation: 1 Health Region

## Indicators

The page exposes the same metric family already used by the national explorer:

- Mismatch
- Need
- Capacity
- Suicide
- Psychiatric admissions in SUS
- CAPS
- SUS mental health beds
- SUS psychiatrist FTE

Metric definitions, labels, and color behavior reuse the existing metric
configuration.

## Distribution Plot

The distribution panel shows the selected state's Health Regions against the
national context of 439 Health Regions.

Percentile metrics are displayed on a 0-100 relative national position scale.
Mismatch uses the raw `mismatch_score` scale centered at 0 and is not converted
to a percentile.

The distribution is descriptive. It does not define adequacy, access, quality,
or unmet need by itself.

## Region List

The Health Region list is ordered alphabetically by Health Region name, then
code. The search field filters by region name or Health Region code. Each row
links to the existing region profile.

No ordering by score, rank, best, or worst is implemented.

## Profile Link

The existing region profile now includes a state link:

- `Ver estado: Acre` -> `/estado/AC` for Acre regions.

The link is navigation only and does not alter the profile's scientific content.

## Null And Quality Semantics

Null or missing values are rendered as unavailable data, not as zero. Quality
flags are surfaced from existing regional fields. The zero-bed disclaimer is
preserved:

`Zero leitos registrados nesta medida nao implica necessariamente ausencia de
acesso regional a leitos.`

## Validation Summary

Validated items:

- 27 valid UFs accepted by the state endpoint.
- `/estado/ac` redirects to `/estado/AC`.
- `/estado/XX` is rejected.
- Acre has exactly 3 Health Regions.
- Acre map returns exactly 3 overview features.
- Sao Paulo large-state case returns 62 Health Regions.
- Distrito Federal renders as one Health Region.
- No rendered state score, ranking, best-region, or worst-region language.
- API invalid release remains isolated.
- SQL injection-shaped UF input is rejected.
- Desktop and mobile screenshots captured.
- Existing frontend flows remain passing.
- Scientific regression suite remains passing.

## Evidence Files

- `audit_results/state_contract_validation.txt`
- `audit_results/state_ac_validation.txt`
- `audit_results/state_large_validation.txt`
- `audit_results/state_df_validation.txt`
- `audit_results/no_state_score_validation.txt`
- `audit_results/sql_safety_validation.txt`
- `audit_results/release_isolation_validation.txt`
- `audit_results/accessibility_validation.txt`
- `audit_results/null_semantics_validation.txt`
- `audit_results/mobile_map_position.txt`
- `audit_results/state_screenshots.txt`
- `audit_results/unit_tests.txt`
- `audit_results/e2e.txt`
- `audit_results/production_e2e.txt`
- `audit_results/lint.txt`
- `audit_results/typecheck.txt`
- `audit_results/production_build.txt`
- `audit_results/production_serving.txt`
- `audit_results/api_regression.txt`
- `audit_results/scientific_regression.txt`
- `audit_results/existing_frontend_regression.txt`

Screenshots:

- `docs/state_page_qc_2026-08-26/desktop_state_ac_full.png`
- `docs/state_page_qc_2026-08-26/desktop_state_ac_top.png`
- `docs/state_page_qc_2026-08-26/desktop_state_ac_distribution.png`
- `docs/state_page_qc_2026-08-26/desktop_state_ac_regions.png`
- `docs/state_page_qc_2026-08-26/desktop_state_large_top.png`
- `docs/state_page_qc_2026-08-26/desktop_state_large_distribution.png`
- `docs/state_page_qc_2026-08-26/mobile_state_ac_full.png`
- `docs/state_page_qc_2026-08-26/mobile_state_ac_top.png`
- `docs/state_page_qc_2026-08-26/mobile_state_ac_distribution.png`
- `docs/state_page_qc_2026-08-26/mobile_state_ac_regions.png`
- `docs/state_page_qc_2026-08-26/mobile_state_large.png`

## V1 Non-Scope

Not implemented in this phase:

- State ranking.
- State score, grade, index, or typology.
- Radar Territorial.
- Peer regions.
- Reports.
- Time series.
- Financing.
- Patient flows.
- Modo Gestor.
- Downloads.
- External public API.
- `/estados` index route.

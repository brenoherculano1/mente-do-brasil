# Historical selection correction

Starting commit: `119e06e`. Scope: restore historical consultation; no 2025 scientific work.

## Distinct contracts

- Historical anchors: 2022, 2023, 2024; absence of `ano` means 2024. Invalid or repeated values are rejected by the historical UI instead of substituted.
- Analytical release: the existing `MDB_ANALYTICAL_2024_2`, unchanged. Release identity is not the selector year.
- Future update: `/atualizacao-2025`, explicitly labelled as under validation and gated to review environments. Explicit legacy `ano=2025` links still show only availability, never historical values.
- Indicator availability: the preserved 2025 catalogue. No observation, interpolated value, geometry or release was created for 2025.

## Retrieval and page behavior

`GET /api/v1/historical/health-regions?year=2022&metric=mismatch_score&include_geometry=true`
reads frozen `analytics.health_region_temporal` records and joins the existing overview geometry by its frozen geography version. It requires exactly 439 rows and the requested year. No scientific calculation is performed. Spatial significance fields are absent, not fabricated for historical anchors.

| Page | Time contract |
| --- | --- |
| `/` | Real frozen map observations for each selected anchor, including 2024 |
| `/comparar` | Historical indicators for 2022/2023; existing complete 2024 workbench preserved |
| `/regiao/[codigo]` | Historical indicators for 2022/2023; existing complete 2024 profile preserved |
| `/mudancas` | Existing 2022 to 2023, 2023 to 2024, 2022 to 2024 pairs; no global selector |
| `/financiamento` | Own fiscal-year and comparison controls; no global selector |
| `/fluxos` | Aggregate 2022 to 2024, not annual observations |
| `/radar` | Frozen 2024 product, explicitly labelled; no fabricated historical Radar |
| `/dados` | Historical anchors, analytical release and future availability explained separately |

Need uses a three-year window ending at the selected anchor; Capacity uses December of that anchor. The geography remains `BR_HEALTH_REGIONS_END2024_V1`. Historical views do not borrow 2024 Radar, peer or LISA results.

## Preservation evidence

Pre-edit reads confirmed 1,317 database observations. The original loader serializes pandas JSON with `double_precision=15`; the database matches that serialization exactly. Tiny binary differences between Parquet and database floats predate this change and were not corrected or rounded again.

The private temporal artifact matches its immutable database manifest. All exported public fields match that artifact, accounting only for the original pipe-delimited flag representation. Both public temporal artifacts are byte-identical to `119e06e^`. The private temporal Parquet is not tracked by Git; its evidence is the immutable database hash plus the frozen public export, not an invented Git comparison.

The 2024 reproduction is byte-identical, SHA-256 `1b8ad1a0e0e56ffc9ace172c34100ce3300b64f9adf212bf26b5d525453edb58`. All 35 columns match exactly, including scores and spatial statistics. This reproduction uses the frozen prior canonical data, cached SIM age counts and original population source; it is not a new raw-source extraction.

Evidence is under `audit_results/historical_selection_2026_09_19/`. The integrity audit is repeatable with `python -m scripts.audit_historical_selection --output <path>` against the existing local database.

Five initial integration-test failures were outdated expectations for the former default 2024 release and former manager/intelligence versions. Assertions now explicitly expect the already-existing current versions; the parametrized coverage for both releases remains. No API version or scientific data was changed to satisfy those tests.

Historical requests have regression coverage for real values, year identity, row count, unsupported years, absent fallback and fixed geography. Browser checks cover the default, all selectors, all time-specific products, explicit future status, desktop and mobile. Preview remains protected and is not a public launch.

Local validation: 174 Python tests and 97 frontend tests passed; TypeScript, lint and production build passed. The browser matrix has 30 applicable scenarios and 8 viewport-excluded combinations. Two new test locators were corrected to use the observed combobox accessible role; the corresponding desktop/mobile scenarios passed on rerun. One 430px scenario exceeded its 60-second limit in the broad run and passed on the isolated rerun in 29.9 seconds. Four existing home-navigation checks also passed. Initial failure evidence is retained rather than overwritten.

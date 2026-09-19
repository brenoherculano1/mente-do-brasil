# 2025 modular: implementation and scientific boundary

Status: PARTIAL. No regional 2025 value is public-ready. This is not an analytical
release and not a completed observed-data pipeline. Public release: NOT_RELEASED.
Starting commit: ca98903. The preceding full-release preflight remains historical evidence.

## Source evidence

- CNES: 27 ST, 27 LT, 27 PF December 2025 files decoded. No selected duplicate
  CAPS identifiers across files or selected duplicate bed rows. PF has no exact
  link duplicates and no collision with the locked total-hours key in this snapshot.
  Cross-UF identity review and SUS-linked versus SUS-exclusive hours remain explicit.
- SIH: all 324 UF/month files decoded, 14,647,505 processing records. Selected
  psychiatric records: 249,632. Repeated AIH identifiers are reported, not silently
  deduplicated. These are processing records, not unique people. Pooled 2023–2025
  regional denominators and comparisons have not been built.
- POPSVS: 902,502 cells, 5,571 municipalities, 213,421,037 population. Lowercase
  field names were normalized only in the new reader. No regional rates published.
- SIOPS: all 6,697,852 detailed CSV rows read, 5,569 municipality codes. Hierarchical
  accounts and expenditure phases must not be added together. Existing report-total
  semantics, duplicate accounting grain and coverage still require reconciliation.
- Geography: current MGDI has 5,570 municipalities and seven changed associations
  against locked 2024, with no historical validity dates. CNES December 2025 municipality
  table lacks health-region assignments; establishment labels are conflicting.
  Neither source is accepted as a validated 2025 crosswalk. The change CSV explicitly
  compares CURRENT versus 2024 and is NOT 2025 lineage.

All 406 source receipts and national QC are in audit_results/modular_2025.
Raw files and private PF caches contain identifiers and must NEVER enter Git,
the audit ZIP, Drive, or an open-data release. Audit receipts contain only schemas,
hashes, source URLs and aggregate QC. Source access is not itself a reuse license;
version-specific source-rights review remains pending. No row-level file redistributed.

## Availability and API

The 2025 registry has 21 source/derived entries and explicit dependencies. Capacity
has no dependency on SIM or LISA reproduction. The complete Radar depends on the
complete scientific model; capacity-only signals are distinguished, but not computed
until their own gates pass. No reweighting or proxy scores were introduced.

Preview-only GET /api/v1/observations/availability?year=2025 returns the registry.
GET /api/v1/observations/unavailable?year=2025 returns value:null for every entry.
Other years return 422 on these new endpoints; historical endpoints remain unchanged.
They are a fail-closed unavailable-data contract, NOT a completed multi-year value API.
Future AVAILABLE values require a validated observed-data adapter and regional metadata;
the UI refuses to render AVAILABLE without that adapter instead of inventing a value.

## UI scope

Home, region, comparison, Radar, financing, changes, flows and sources have a
2024/2025 preview selector. 2025 does not mount the old map or values. Unavailable
rows use an em dash, explain the reason and reference the previous available year.
No comparison conclusion or temporal line is calculated from missing data.
Production rejects the 2025 view; no deployment to production is authorized.

This checkpoint does NOT claim regional 2025 metrics, complete source QC, fully
functional partial AVAILABLE rendering, a complete two-year metadata registry,
a public launch. Each pending item needs its own evidence.

## 2024 reproduction: resolved within the documented harness

The isolated historical runtime (numpy 2.3.5, numba 0.63.1, pyarrow 21.0.0,
pandas 3.0.5, esda 2.7.1, libpysal 4.13.0, geopandas 1.1.4) reproduced all
35 columns exactly, including LISA p/q, and the entire Parquet byte-for-byte.
SHA256: 1b8ad1a0e0e56ffc9ace172c34100ce3300b64f9adf212bf26b5d525453edb58.
Moran: 0.5256454566660947; pseudo-p: 0.0001; LISA: 136 (60 HH, 65 LL, 5 HL, 6 LH).
No protected file changed. Evidence: reproduction_2024_historical_runtime.json.
This is the correction-builder reproduction from frozen prior canonical, cached
SIM age counts and original population inputs, not a new full raw extraction.
The preceding failed-runtime receipt is preserved; no historical result was patched.

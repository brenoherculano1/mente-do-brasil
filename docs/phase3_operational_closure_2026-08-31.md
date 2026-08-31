# Phase 3 Operational Closure: BLOCKED

Execution root: `/Users/brenoherculano/Projects/mente-do-brasil`.
Starting commit: `3b1bfa7ca5b5bac9df547b0a0e3d81f5bd4055a2`.
Branch: `phase3-local-closure`. FileProvider blocker: **RESOLVED**.
No old repository reads, no rsync-incomplete source-of-truth substitution,
no backup deletion, no source reacquisition, no scientific-method changes.

## Actual blocker and exact recovery action

Copy the **previously validated, byte-identical** data assets into this new
repository, preserving the relative paths below. Restore from the owner's
validated backup; do not regenerate them from serving tables. The agent did
not read the prohibited old repository or use the incomplete rsync tree.

- `data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet`
- `data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet`
- The entire validated `data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle/`, including `geography/health_regions_LOCKED.gpkg`.
- `data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_temporal.parquet`
- `data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_changes.parquet`
- `data/product_intelligence/MDB_ANALYTICAL_2024_2/hospitalization_flows.parquet`
- `data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_flow_summary.parquet`
- `data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl`

Expected hashes, where independently recorded, are in
`audit_results/phase3_closure/source_inventory.json`. The four advanced hashes
come from the serving version registry, not newly reconstructed Parquets.
Recovery must also preserve the source assets referenced by the existing
provenance manifests before any claim of full scientific reproducibility.

The disposable EMPTY database rebuild failed on the missing historical
crosswalk. It did not use a restored database. Its output and exit status are
in `audit_results/database_rebuild.txt`. The source snapshot was a clean Git
archive of the starting commit, extracted successfully on the local filesystem.
This is a missing-artifact failure, not a filesystem timeout.

After recovery, validate hashes, run the complete historical/current/advanced
loader chain into an empty disposable database, then rerun full regressions.
The legacy `scripts/rebuild_serving_db.sh` alone loads only the historical
release; it is not sufficient evidence of a full advanced rebuild.

## Recovered diff audit

The only recovered modification was `uv.lock`: **KEEP**, synchronizing the
already declared `sources` extra. No recovered changes existed in financing
schemas, financing service, or the SIOPS fetch script. No unexplained residual
code was accepted. No recovered file was reverted.

Additional closure repairs: **KEEP**, narrowly scoped to proven failures:

- Declare the previously used spatial test dependencies (`esda==2.7.1`, `libpysal==4.13.0`) and their Python >=3.11 requirement; make the existing script imports resolvable in pytest. The lock retains the sources extra.
- Select Intelligence 1.1 for corrected-release Radar/explanation/peers, preserving 1.0 for historical release queries. Add both-release API regressions.
- Replace the false-positive substring check for `nan` inside `financing` with JSON non-finite-number validation.
- Display the existing advanced regional sections in current-release Manager mode, without changing analytical values.
- Constrain profile/manager grid tracks and make the comparison table locally scrollable and keyboard-focusable.
- Size ReportLab tables for their actual number of columns. Bump the rendering generator to 1.1 to invalidate presentation caches; report/science versions remain unchanged. Add a two/three-column width regression.
- Repair sitemap count, environment cleanup, ambiguous E2E selectors, and old QA output path assumptions.
- Add reproducible local audit helpers and preserve both failed and corrected evidence.

## Evidence boundaries

Current serving and independently restored database: 439 regions, 5570
municipalities, 439 current metrics, 439 valid geometries at SRID 4674,
three serving views each with 439 current rows. Temporal/change/financing:
1317 each. Flow contributions: 20907; summaries: 439. LISA: 136
(HH60, LL65, HL5, LH6). Flags: SMALL_SUICIDE_COUNT=7,
ZERO_REGISTERED_BEDS=275. Both releases remain registered.

Fresh backup: 83,631,201 bytes, PostgreSQL pg_dump 18.6,
SHA256 `1d2ad313681cd4678d774a8b9a8294d787adb5d9a581c3872b50fa5e97e5f9a2`.
The separate restore passed count, advanced-content-hash, views, lookup,
read-only privilege, and rolled-back constraint checks. Disposable databases
were dropped; the private dump remains outside Git and the audit ZIP. See
`audit_results/restore_drill.txt` for the actual retained path.

Full backend run: **87 passed, 4 failed, 24 skipped**. Four failures require
missing historical canonical/SIOPS files. The canonical regression class skips
when its raw import bundle is absent. These are NOT counted as successful
regression coverage. Earlier 111-pass evidence is historical, not the result
of this execution. ReportLab `ast.NameConstant` warning: DOCUMENTED_UPSTREAM.

Current-source scientific recomputation, idempotent file reload, and file-copy
immutability retest cannot be claimed anew while those input files are absent.
The restored database's internal consistency is not an independent rebuild.
Earlier temporal reproduction and full flow reconciliation remain explicitly
**prior evidence**, included as such in the ZIP.

## SIOPS hash transition

Accepted financing SHA256:
`09e6182fa527a73e53691c97d65e30e2fc6f2740fffdd36b0d09baa59e680860`.
Superseded:
`e0268253e318473824312ed3125a01ea73be8d795457ac6e09f568ab9b140985`.
All 1317 rows changed population denominator/coverage fields; 1310 gained
per-capita expenditure values. Total expenditure and municipal coverage did
not change. Column order and row-key order did not change; population dtypes
did. This was the correction of the seven-digit POPSVS municipality mapping,
not mere serialization and not a new financing methodology. Full/partial
coverage remains 1310/7. See the explicit hash-transition ledger.

## QA evidence interpretation

Authoritative final UI captures: `docs/phase3_closure_qc_2026-08-31/verified_ui/`.
Earlier root captures may precede WebGL painting; they are not the accepted
visual proof. Separate canvas PNGs and pixel checks confirm actual rendered
geometries/connections, including the valid single-point destination view.
Tables remain horizontally scrollable within their containers on mobile.

Authoritative final PDFs: `docs/phase3_closure_qc_2026-08-31/pdf_final/`.
All eight pages of each of five reports were rendered and inspected visually.
The initial `pdf/` captures demonstrate the now-fixed table clipping and are
preserved, not claimed as passing QA. The corrected 40 pages have no observed
clipping/overlap, retain Portuguese accents/release IDs, and include financing
and flow limitations. Text bounding checks find zero words outside safe page
bounds. Eight sparse pages are intentional existing pagination, not blank loss.

Frontend unit: 57 tests (`frontend_unit_accepted.log`). Build, lint, typecheck
and entire production E2E results are in the final `*_verified.log` files.
Production E2E: **30 passed, 14 viewport-specific skips, zero failures**. The E2E project
matrix deliberately skips desktop-only cases in mobile and vice versa; skips
must be listed separately. These E2Es run against Next production start,
FastAPI and real PostGIS, not mocked responses. No separate development-server
E2E run is presented as having occurred.

Accessibility is bounded operational QA, not a WCAG certification or screen
reader audit. Captions, names, native controls, table/map alternatives and
keyboard-focused comparison scrolling are covered; complete contrast and
assistive-technology certification are not claimed.
The dedicated keyboard probe is **PARTIAL**: the comparison table retained
focus, showed a 3px outline and scrolled 40px with ArrowRight, but simulated
native-select keys did not change the period in headless Chromium. The period
control does pass selection/change E2E. A native-keyboard/assistive-technology
check remains pending; this is not silently promoted to an accessibility PASS.

## Release decision

**ADVANCED_TERRITORIAL_PHASE_3 != LOCKED_LOCAL**.
Public release remains **NOT_RELEASED**. Open Platform remains **NOT_STARTED**.
No deployment, domain, indexing activation, or new scientific variable.
The new package is named **BLOCKED**, not LOCKED, to prevent a false release
signal. `AUDIT_CONTEXT.json` records the final commit and exact evidence state;
the cryptographic manifest covers all packaged files except itself.

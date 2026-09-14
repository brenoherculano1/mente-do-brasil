# Annual analytical update

## Current preparation: 2025

Status: **BLOCKED_FOR_2025_OFFICIAL_RELEASE**, checked 2026-09-14.
Current edition remains `MDB_ANALYTICAL_2024_2`. No candidate, official 2025
release, current-pointer update, API change or public year selector was created.
This runbook and the preflight utilities are reusable preparation, **not a tested
end-to-end 2025 builder**. Do not describe the annual pipeline as fully ready.

Read `metadata/annual_updates/2025/source_readiness.csv`,
`metadata/annual_updates/2025/preparation.json` and
`audit_results/annual_2025_2026-09-14/reproduction_2024.json`.
The CSV's PARTIAL classification means incomplete validation evidence; for SIH,
CNES and POPSVS it does not mean files were demonstrated to be incomplete.

## 1. Historical gate and source availability

Before building any new edition, run in the project environment:

```sh
PYTHONPATH=.:scripts .venv/bin/python -m scripts.reproduce_annual_baseline --output audit_results/annual_retry/reproduction_2024.json
.venv/bin/python -m scripts.audit_annual_source_catalogs --year 2025 --output audit_results/annual_retry/catalogs
.venv/bin/python -m scripts.validate_annual_preflight --matrix metadata/annual_updates/2025/source_readiness.csv --reproduction audit_results/annual_retry/reproduction_2024.json
```

Use a fresh output directory each time. Capture subprocess exit codes. The source
catalog tool uses the existing BeautifulSoup installation; the baseline also uses
the scientific packages already used by the correction builder. No global install.
The baseline checks exact field and Parquet-byte equality, not merely headline
statistics. It reads frozen population files without automatic downloads and writes
reconstructed data only in a temporary directory. Its scope is the current correction
builder: it reuses the validated prior canonical and SIM age cache, not a new raw
extraction of every SIH/CNES/SIM file. Raw provenance must separately be verified.

2026-09-14 result: 33/35 columns exactly equal, including all scores, local I,
significance and cluster labels. `lisa_p` and `lisa_q` differ. Moran is exactly
0.5256454566660947, pseudo-p 0.0001, and LISA membership is 136 (60/65/5/6).
Canonical SHA remains `1b8ad1a0e0e56ffc9ace172c34100ce3300b64f9adf212bf26b5d525453edb58`.
No protected canonical/release/method file changed. Exact reproduction FAIL remains
a hard stop; matching summaries are not a waiver.

Runtime differs from the archived validated runtime: numpy 2.5.2 vs 2.3.5,
pyarrow 25.0.1 vs 21.0.0, numba absent vs 0.63.1. These are observed differences,
not proof of a specific cause. Next technical investigation: reconstruct the archived
environment in an isolated project-local environment and rerun without changing
seed, permutation algorithm or tolerance. Do not repair this by copying stored p/q
into a new output or overwriting 2024. Initial invocation errors (module search path
and absent numba package metadata) were corrected in the harness, not in the science.

## 2. Acquisition

Do not bulk download while SIM is officially preliminary. After it becomes suitable,
acquire all 81 SIM UF-year files, 972 SIH UF-month files for 2023-2025, 81 CNES
files (ST/LT/PF, 27 UFs, December 2025), and three POPSVS national archives.
Reuse `scripts/acquire_phase3_sources.py` acquisition/schema helpers after explicit
period parameterization; its existing catalog is historical and must not be mistaken
for a 2025 builder. No November substitution or gap filling. Snapshot dated geography
and optional municipal SIOPS 2025 separately. Preserve original downloads locally.

## 3. Provenance and rights

For every file record official/final URL, retrieval UTC, source vintage, competence,
size, SHA256, schema fingerprint, decoder/runtime and generating Git commit.
Recheck dataset-specific rights for each new vintage. The previous rights matrix is
context only, not clearance for 2025. Portal page CC BY-ND wording is not a blanket
license for derived datasets. No raw microdata, source mesh, credentials, environment
files or WHO publication in public exports. This preparation collected catalog text
and filenames only; no 2025 patient/professional records or geometry were acquired.

## 4. QC and territorial comparability

Require complete years/UFs and validate actual rows, schema, duplicates, denominators,
missingness, nonfinite/negative values, unmatched municipalities, multiple assignments,
zero inflation and outliers. Report min/p1/p5/median/p95/p99/max against 2024.
Do not discard genuine large changes automatically. CNES FTE: audit exact link
duplicates, multi-establishment professionals, all three hour fields, individual
totals, implausible hours and SUS-link interpretation; no arbitrary cap.

Use a documented December-2025 crosswalk, not the rolling current resource (observed
updated 2026-09-13). Produce added_municipalities, removed_municipalities,
changed_health_region_assignment, renamed_regions, new_regions, removed_regions,
code_changes and explicit lineage. Counts are unknown until audited, not forced to
439/5570. IBGE references municipal changes including Boa Esperanca do Norte;
do not infer all health-region changes from this municipal fact. Review boundary
changes and historical population comparability. Scientific and display geometry
have different provenance and publication permissions.

## 5. Canonical

Never overwrite the old release. New versioned paths and manifests must enforce
immutable writes. Set expected counts only after geography approval. Keep
`MDB_CANONICAL_1.1` unless schema actually evolves; version any schema change.

## 6. Analytical

Preserve `MDB_METHOD_1.1` unless a real approved methodological change occurs.
SIM X60-X84 residence, pooled 2023-2025, direct WHO Table 4 age standardization,
0-4 through 75-79 then 80+, terminal raw weight 1.545; unknown age excluded from
standardization but retained in crude-count QC. SIH F00-F09/F20-F99 excluding
F10-F19, MUNIC_RES, admissions not unique patients, per 100k person-years.
CAPS TP_UNID70 unique CNES; beds TP_UNID05/CODLEITO87/QT_SUS;
psychiatry CBO225133/PROF_SUS1, exact-link-deduplicated weekly hours/40.
Capacity rates use appropriate 2025 population. Percentile is
`(less + (equal - 1)/2)/max(n_observed - 1, 1)`; prove ties/missing equivalence.
Need: equal halves; capacity: equal thirds; difference: need minus capacity.
No access/quality/deficit/investment-priority inference.

## 7. Spatial

Explicit sorted region-ID alignment for data, geometry and Queen W; row standardized,
zero islands, continuous standardized difference, 9999 permutations, seed20260823,
same local procedure and FDR as the locked builder. Recalculate Moran, p, all local
statistics, FDR and memberships; verify reproducibility in the recorded environment.

## 8. Temporal and contextual layers

Label edition separately from pooled window. Compare 2024/2025 distributions and
component changes, Moran and every LISA transition; never causal interpretation.
Keep existing Change Radar thresholds/ruleset. Recompute peers only following the
existing population/density/municipality-count contract and approved geography; version
new outputs. No 2025 peers computed yet. Version complete SIH flows separately with
existing suppression. SIOPS requires its own coverage/rights gate and is optional:
"Esta camada descreve o contexto geral de financiamento da saude e nao mede gasto
especifico em saude mental." Values are nominal, not inflation-adjusted. An incomplete
SIOPS layer stays on its prior reference year, clearly labeled.

## 9. Database and API

Only after science passes, implement immutable coexistence and explicit release
selection using existing contracts. Never replace historical rows. Default remains
2024 until explicit approval. Test missing/unknown year, cache separation, old endpoints
and prevention of mixed editions.

## 10. Frontend

Only approved editions selectable. Load by edition on demand. Update map, profiles,
comparison, Radar, sources, methodology and scope consistently. Distinguish absolute
counts/rates/relative positions and overlapping Need windows. Test deep links,
back/forward, keyboard/focus, screen readers and overflow at 375/390/430px.
No frontend changes were appropriate during this blocked preflight.

## 11. Audit and Open Data

Test source coverage, geography, formulas, flags, spatial, historical immutability,
release isolation, UI and exports. New Open Data package only after all gates;
CSV/Parquet semantic equality, dictionary, manifest/checksums, provenance/rights.
Never overwrite `MDB_OPEN_DATA_2024_1`. Package only allowed audit files; scan secrets
and raw leakage, verify ZIP integrity/hash and Drive upload metadata.

## 12. Release / next retry condition

No automatic publication: preflight PASS is not release PASS. Resume when SIM 2025
is officially consolidated/suitable for the requested final edition AND exact 2024
reproduction is restored. Then complete record QC, historical crosswalk/lineage and
rights review. Only after full science/backend/frontend validation and explicit
approval may the current pointer change. No human Mac action or paid service is
required now; waiting for publication is not permission to relax the gates.

Official evidence: [SIM](https://dadosabertos.saude.gov.br/dataset/sim),
[population](https://www.gov.br/saude/pt-br/composicao/seidigi/demas/dados-populacionais),
[SIOPS](https://portalfns.saude.gov.br/siops/siops-downloads/),
[crosswalk](https://dadosabertos.saude.gov.br/dataset/macrorregiao-de-saude/resource/3bd28e64-0a82-44d9-8de1-4894634f2b6a),
[IBGE territorial changes](https://agenciadenoticias.ibge.gov.br/media/com_mediaibge/arquivos/8383bdedce5a6d972e60dd32671e533a.pdf).
IBGE display product page returned HTTP403 directly; new geometry rights and full
2025 geography diff remain pending, not approved by this catalog audit.

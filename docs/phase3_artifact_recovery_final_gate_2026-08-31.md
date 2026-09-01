# Phase 3 artifact recovery: BLOCKED

Starting commit: `de9754440c5a9eff56272ff2a5198a182cc044e2`.
Branch: `phase3-local-closure`. The operational repository is under `Projects`.
Its working tree was clean before this recovery. FileProvider workspace issue:
RESOLVED. This run did not execute donor code or use its environment, Git or DB.

## Recovered and verified

- Six allowlisted Parquets match the exact user-locked SHA256 values before and
  after temporary copy and atomic rename. Existing financing was not overwritten.
- All 19 bundle members validated against IMPORT_MANIFEST bytes and hashes before
  any bundle copy. The manifest was also copied and verified. No unknown member.
- GPKG: 93,306,880 bytes; SHA256
  `657355adb0df88dfcfff2400751eff6ae97b367effe8e90223d0267e0437ba48`.
- SIOPS JSONL: 16,710 unique municipality/year keys, 16,703 successes, seven
  explicit missing/error records. Exact requested missing keys validated. No
  missing expenditure was converted to zero. All rows were parsed.
- Four previously failing tests: 4 passed, 0 failed, 0 skipped. The new recovery
  and preflight suite: 6 passed, 0 failed, 0 skipped.

## Exact blocker

`scripts/build_financing_context.py::populations` requires the original municipal
POPSVS denominators, not just SIOPS JSONL and the regional temporal Parquet.
These three files are absent from the new repository and outside the authorized
artifact recovery allowlist:

| Proposed local recovery file | Bytes | Locked SHA256 |
| --- | ---: | --- |
| `data/raw/scientific_correction_recovery/POPSBR22.zip` | 3378657 | `8619497c4adcb87133aab68666ed6604209b812047e9b51e3608db00a2c8e731` |
| `data/raw/scientific_correction_recovery/POPSBR23.zip` | 3360669 | `c49b35794dc235bad8a4a0dbc530a82aeae589e03a366a3c17a8325e6c24d5f4` |
| `data/raw/scientific_correction_recovery/POPSBR24.zip` | 3342323 | `cbf5549a5f9b37160e2fe3a5f97123a7747e371d4c433a8aa8a3276ad41dcc53` |

Provenance: `metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv`.
No donor files outside the allowlist were inspected or copied. No download,
database export, population reconstruction or alternative financing calculation
was attempted. The builder was deliberately not invoked because its existing
source resolver can access external legacy paths and download missing data.

The observed SIOPS candidate SHA256 is
`60def3ab60e036d0c7e05f2feb56a9eb5c3cfee68c602f74123c445f4cd79d73`.
It is NOT an independently historical hash and is NOT frozen as accepted.
Exact financing reproduction remains NOT_RUN. The existing financing Parquet
still matches `09e6182fa527a73e53691c97d65e30e2fc6f2740fffdd36b0d09baa59e680860`.

## Reproducibility boundary

CODE REPOSITORY != COMPLETE DATA RELEASE PACKAGE.

`metadata/provenance/required_local_artifacts_v1.json` inventories 60 inputs,
including all data consumed by the serving loader chain, versioned loader
dependencies, the complete bundle, and the pending SIOPS source acceptance gate.
Paths are repository-relative; no personal absolute paths occur in this inventory.
Large ignored data must be distributed as an independently verified artifact
package, not force-added to Git. Redistribution eligibility is NOT_ASSESSED.

`scripts/preflight_local_artifacts.py` checks every inventory entry and reports all
failures together. Currently: three MISSING files and one PENDING_ACCEPTANCE.
`scripts/rebuild_serving_db.sh` now executes this check before any database command.
Tests prove a failed preflight cannot reach Docker and that bad recovery hashes
cannot overwrite a destination. Passing these guard tests does NOT mean the
actual required-artifact gate passes.

The existing shell rebuild still has historical-only orchestration; extending it
to the full current loader chain remains pending. No complete rebuild is claimed.
The inventory is a serving/acceptance inventory, not a claim that all original
SIM/SIH/CNES sources for end-to-end raw science regeneration were recovered.

## Gates not advanced

No database was created, dropped, loaded or exported. Clean rebuild, advanced
source/DB identity, reload, immutability, constraints and fresh restore: NOT_RUN.
Prior restore evidence and previous BLOCKED ZIP are preserved unchanged.
Full backend, scientific regeneration, production build/E2E, API/security and
accessibility follow-up: NOT_RUN in this recovery attempt. Prior evidence must
not be relabeled as a fresh pass. Accessibility remains pending, without a
custom widget or an unsupported WCAG claim.

Phase: ADVANCED_TERRITORIAL_PHASE_3. Lock: NOT_LOCKED.
Public release: NOT_RELEASED. Open Platform: NOT_STARTED.
ReportLab remains DOCUMENTED_UPSTREAM; no dependency patch attempted.

## Exact next action

Authorize recovery of the three original, hash-locked POPSVS ZIPs listed above
into the new repository, extending only the artifact allowlist. Then rerun the
existing financing builder offline in temporary output storage, require the
accepted Parquet hash, and resume the still-pending final gates. Do not start
Open Platform or declare LOCKED_LOCAL before those gates pass.

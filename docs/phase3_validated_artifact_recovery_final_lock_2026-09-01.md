# Advanced Territorial Phase 3: Final Local Lock

Status: `PASS`

Phase: `ADVANCED_TERRITORIAL_PHASE_3`

Lock: `LOCKED_LOCAL`

Public release: `NOT_RELEASED`

Open Platform: `NOT_STARTED`

## Closure basis

- The three authorized POPSVS archives were recovered byte-for-byte and matched their locked sizes and SHA-256 values.
- The SIOPS snapshot passed semantic validation and was frozen only after exact offline reproduction of the accepted financing artifact.
- The required-artifact preflight passed 60 of 60 inputs with no missing, pending, or hash-mismatched entry.
- A clean empty database rebuild loaded both analytical releases and all advanced products. Stable source-to-database content comparisons passed.
- Idempotent reload, immutable-version rejection, rollback-safe constraints, runtime read-only access, fresh backup, and fresh restore passed.
- Scientific, temporal, change, financing, flow, backend, frontend, production E2E, API, security, accessibility, PDF, and UI regression gates passed within their documented scopes.

## Locked current state

The current analytical release remains `MDB_ANALYTICAL_2024_2`; `MDB_ANALYTICAL_2024_1` is preserved. The corrected release contains 439 health regions, 5,570 municipalities, 439 current metrics, 439 valid SRID 4674 geometries, 1,317 temporal rows, 1,317 change rows, 1,317 financing rows, 20,907 flow contributions, and 439 flow summaries.

The corrected spatial result remains Moran's I `0.5256454566660947`, pseudo-p `0.0001`, and 136 significant LISA regions: HH 60, LL 65, HL 5, and LH 6. Quality flags remain `SMALL_SUICIDE_COUNT=7` and `ZERO_REGISTERED_BEDS=275`.

## Scope qualifications

Accessibility is `PASS_WITH_SCOPE`: focused automated checks confirmed native control semantics, accessible naming, functional selection, keyboard focus, and a visible table-region focus indicator. This is not a formal WCAG certification.

ReportLab remains `DOCUMENTED_UPSTREAM`; no monkey patch was introduced. PDF and UI checks in this execution were regression spot checks because no report layout or visual implementation changed.

## Artifact governance

The local Git repository alone is insufficient for a complete rebuild. Rebuildability requires the code plus the versioned inventory and a separately validated, hash-locked data/artifact bundle. This is not a Phase 3 scientific failure. Formal distribution, licensing, attribution, and preservation belong to the future Open Platform and data-governance phase.

No public release or Open Platform work was started by this lock.

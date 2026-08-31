# Advanced Territorial Phase 3

Status: VALIDATED_LOCAL for the corrected analytical release `MDB_ANALYTICAL_2024_2`.

The phase materializes three observed temporal anchors (2022, 2023, 2024), a deterministic 2022-to-2024 change radar, the accepted hospitalization contribution file, and the general-health financing context. It does not add a causal model, ranking, recommendation, or public release.

## Validation record

- temporal product: 1,317 rows; source inventory: 2,003 files; 2024 reproduction tolerances <= 1e-12;
- change product: 1,317 rows; 2022-to-2024 matched families: 0 in 362 regions, 1 in 47, 2 in 11, 3 in 17, 4 in 2;
- financing product: 1,317 rows; 1,310 complete and 7 partial records; municipal population denominators present for all years;
- flow product: 20,907 contribution rows, 4,292 regional pairs, 695,320 eligible admissions, 11,987 suppressed contributions;
- serving database: 439 health regions, 5,570 municipalities, 439 current-release metrics, 439/439 valid geometries at SRID 4674;
- current corrected LISA lock: 136 significant regions, HH 60, LL 65, HL 5, LH 6;
- flags: `SMALL_SUICIDE_COUNT=7`, `ZERO_REGISTERED_BEDS=275`;
- reload: `IDENTICAL_RELOAD` for all four advanced products and `PASS / NO CHANGE` for the base serving release;
- immutability: modified temporary copy blocked with `IMMUTABILITY VIOLATION`; raw and canonical inputs unchanged;
- constraints: invalid flow row rejected as `CheckViolation` and transaction rolled back;
- API role: write attempt rejected with `InsufficientPrivilege`;
- Manager V2: five distinct eight-page PDFs generated; repeated generation produced identical SHA-256;
- tests: 111 passed, 1 deprecation warning; frontend TypeScript and production build passed in isolated dependency checkout.

## Runtime

- Docker Desktop engine 29.7.2;
- Docker Compose v5.4.0;
- PostgreSQL 18.6;
- PostGIS 3.6.4;
- requested `postgis/postgis:18-3.6` digest (amd64 pull): `sha256:60f6ad1d21ea86a67d47780b9a0d1e1d200500f62b19293fa834d0dea80b8677`;
- local runtime image digest: `sha256:efbe9919290ea632ce1acb3145d984935d73c1976e882b14b806a6ee3e35dd4e`;
- database published only on `127.0.0.1:5432`; credentials remain in ignored `.env`.

Historical releases remain preserved. Open Platform, API expansion beyond the implemented read-only routes, and public release are outside this phase.

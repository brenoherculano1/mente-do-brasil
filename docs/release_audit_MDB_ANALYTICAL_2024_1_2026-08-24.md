# Release Audit MDB_ANALYTICAL_2024_1

Audit date: 2026-08-24

## Findings

- ZIP file accounting: PASS. The bundle contains 20 files: 19 scientific payload files listed in `IMPORT_MANIFEST.json` plus `IMPORT_MANIFEST.json` itself.
- Bundle hashes: PASS. All 19 manifest-listed payload hashes matched the imported files.
- Municipality count: PASS, 5570/5570.
- Health Region count: PASS, 439/439.
- Global Moran: PASS, `0.5254943888435958`; locked rounded value `0.525494388844`.
- LISA: PASS, 135 FDR-significant regions; HH 60, LL 66, HL 4, LH 5.
- Old Moran guardrail: PASS. Invalid value `0.218740812099` is documented only as invalidated output and is not the primary result.
- Source provenance recovered: PASS. Phase 2 raw provenance manifest contains 1137 source-file records with access date `2026-08-23`.
- Release gate: PASS.
- Public release: NOT YET.

## Known Limitation

Original exact CNES download URLs were not preserved in Phase 2 provenance because those files came from the validated Paper 1 DATASUS cache. Filename, source system, competence, size and SHA-256 are preserved.

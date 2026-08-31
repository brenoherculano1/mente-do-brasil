# Hospital Flow Field Ledger - 2026-08-29

Status: BLOCKED

Source system: SIH/SUS RD.

Official source page checked:

- https://datasus.saude.gov.br/acesso-a-informacao/producao-hospitalar-sih-sus/

## Validated Current Field

The locked analytical release uses `MUNIC_RES` for residence-based psychiatric admission rates.

## Missing Field Validation

Phase 3 hospital flows require a verified destination or hospital-location municipality field, plus documentation that it is appropriate for origin-destination aggregation. The current local Phase 2 provenance preserves `MUNIC_RES` and `DIAG_PRINC` for the residence indicator. It does not preserve a validated destination field ledger.

## Decision

Flow product implementation is blocked until SIH/SUS destination-field documentation and schema-level validation are added.

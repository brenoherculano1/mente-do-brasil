# Hospital Flow Field Ledger

Updated: 2026-08-31. Historical first gate preserved in commit `ead5ec6`.

Status: DOCUMENTARY_DEFINITION_AND_NATIONAL_SAMPLE_VALIDATED;
POOLED_ORIGIN_RECONCILIATION_NOT_COMPLETED_AFTER_TEMPORAL_SCIENTIFIC_STOP.

Source: official SIH/SUS RD and CNES ST dissemination files.

## Documentary evidence

Official URL: `ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Doc/IT_SIHSUS_1603.pdf`.
Acquired from the official Doc listing, not GitHub. PDF, hash and original URL are preserved.

| Field | Official meaning | Type and format | Role |
| --- | --- | --- | --- |
| MUNIC_RES | Municipality of patient residence | char(6); municipal IBGE code without check digit | Origin |
| MUNIC_MOV | Municipality of the establishment | char(6); municipal IBGE code without check digit | Destination |
| CNES | Establishment identifier | Seven-digit identifier in the observed RD/ST files | Empirical linkage key |
| DIAG_PRINC | Primary diagnosis, ICD-10 | char(4) | Locked inclusion F00-F09 or F20-F99 |

MUNIC_MOV is defined in Table 1, field 49. CNES ST provides the comparison municipality in CODUFMUN. New 2020-2021 RD headers and available locked-year headers are inventoried with deterministic signatures. Unmaterialized old cloud-cache files are explicitly identified rather than counted as inspected.

## Empirical evidence

Sample: all 27 UFs, December 2024, matching CNES ST competence.

- 1,111,437 RD records.
- 1,111,437 linked to an unambiguous CNES establishment municipality.
- 1,111,437 exact MUNIC_MOV/CODUFMUN matches.
- Zero unmatched records, ambiguous CNES identifiers or municipality disagreements.
- 19,671 non-substance psychiatric records; all linked and matched exactly.

The test reads only location, diagnosis and establishment fields. It does not export patient identifiers. Per-UF aggregate evidence is in `audit_results/phase3_munic_mov_empirical_validation.json`.

## Mapping and remaining gate

Map six-digit origin/destination municipality codes to the frozen end-2024 Health Region crosswalk. Do not substitute hospital location for residence in the Need numerator. Before releasing pooled flows, reconcile 2022-2024 origin counts exactly to the locked numerator and handle unmatched locations explicitly.

The December national sample is strong empirical support for destination semantics, not proof that every 2020-2024 record or every historical establishment is correctly linked. Full pooled reconciliation, public edge suppression below five, and disclosure controls remain mandatory before a flow product can pass. No patient-level product, flow edge output, API or map was released.

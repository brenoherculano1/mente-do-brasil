# Phase 3 Source Viability - 2026-08-29

Project: Mente do Brasil

Phase: TEMPORAL INTELLIGENCE, CHANGE RADAR, FINANCING CONTEXT AND HOSPITAL FLOWS - PHASE 3

Status: BLOCKED

## Scope

This pre-flight audit evaluates whether Phase 3 can be implemented without changing the locked science and without inventing data. It does not modify `MDB_ANALYTICAL_2024_1`, canonical geography, Territorial Intelligence, Manager Mode, or the territorial report.

## Official Source Systems Checked

- DATASUS Transferencia de Arquivos: https://datasus.saude.gov.br/transferencia-de-arquivos/
- DATASUS SIH/SUS: https://datasus.saude.gov.br/acesso-a-informacao/producao-hospitalar-sih-sus/
- CNES downloads: https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp
- SIOPS Gov.br: https://www.gov.br/saude/pt-br/acesso-a-informacao/siops
- FNS SIOPS Dados Abertos downloads: https://portalfns.saude.gov.br/siops/siops-downloads/

Official source systems exist for the requested domains. The blocker is not source-system existence; it is the lack of a complete, validated, hash-preserved local Phase 3 source set and field ledger sufficient to build the requested product in this execution.

## Existing Validated Local Source Coverage

Local validated provenance: `metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv`

Observed coverage:

- DATASUS IBGE POPSVS: 2022, 2023, 2024 only; 3 files.
- SIM/DATASUS DORES: 2022, 2023, 2024 only; 27 UF files per year, 81 files total.
- SIH/SUS RD: 2022-01 through 2024-12 only; 27 UF-month files per month, 972 files total.
- CNES ST: 2024-12 only; 27 UF files.
- CNES LT: 2024-12 only; 27 UF files.
- CNES PF: 2024-12 only; 27 UF files.

## Temporal Module

Source system: SIM, SIH/SUS, CNES, DATASUS/IBGE POPSVS.

Official publisher: Ministerio da Saude / DATASUS; CNES.

Required by Phase 3:

- SIM 2020, 2021, 2022, 2023, 2024.
- SIH RD 2020, 2021, 2022, 2023, 2024.
- CNES ST, LT, PF for Dec 2022, Dec 2023, Dec 2024.
- Population 2020-2024 with age structure for suicide standardization.

Available validated local coverage:

- SIM 2022-2024 only.
- SIH RD 2022-2024 only.
- CNES Dec 2024 only.
- Population 2022-2024 only.

Required variables:

- SIM: residence municipality, underlying cause, age.
- SIH RD: `MUNIC_RES`, principal diagnosis, admission/AIH record.
- CNES ST: municipality, unit type, CNES establishment.
- CNES LT: municipality, unit type, bed code, SUS bed count.
- CNES PF: municipality, CBO, `PROF_SUS`, `HORA_AMB`, `HORAHOSP`, `HORAOUTR`.
- Population: municipality, year, sex, age, population.

Viability verdict: BLOCKED.

Reason: anchor-year 2022 requires 2020-2022 rolling windows and Dec 2022 capacity. Anchor-year 2023 requires 2021-2023 rolling windows and Dec 2023 capacity. The validated local source set does not contain 2020-2021 SIM/SIH/population data or Dec 2022/Dec 2023 CNES ST/LT/PF files with hashes and preserved provenance.

## Financing Module

Source system: SIOPS.

Official publisher: Ministerio da Saude / SIOPS / Fundo Nacional de Saude.

Exact source URL checked:

- https://www.gov.br/saude/pt-br/acesso-a-informacao/siops
- https://portalfns.saude.gov.br/siops/siops-downloads/

Required by Phase 3:

- Municipal annual SIOPS data for 2022-2024.
- Field ledger defining the defensible health-financing metric.
- National reconciliation against official totals.
- Health Region aggregation through locked end-2024 municipality crosswalk.

Available validated local coverage:

- No SIOPS raw files in `metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv`.
- No SIOPS field ledger or reconciliation file in the repository.

Viability verdict: BLOCKED.

Reason: SIOPS is a defensible official source for general health-financing context, but this repository does not yet have a validated SIOPS raw manifest, field definitions, or reconciliation evidence. Phase 3 also explicitly forbids unsupported "mental-health expenditure" claims; no RAPS-specific transfer layer was validated.

## Flow Module

Source system: SIH/SUS RD.

Official publisher: Ministerio da Saude / DATASUS.

Required by Phase 3:

- Psychiatric admission records filtered by the locked diagnosis rule.
- Residence Health Region from `MUNIC_RES`.
- Destination/hospital location field verified from official SIH documentation or a validated schema.
- Suppression of small counts and no patient identifiers in outputs.

Available validated local coverage:

- Phase 2 SIH provenance preserves `MUNIC_RES` and `DIAG_PRINC` for the locked residence-based admission indicator.
- The existing repository pipeline documentation only declares residence processing.
- No validated destination/hospital municipality field ledger is present.

Viability verdict: BLOCKED.

Reason: hospital-flow output depends on a verified origin-destination pair. Residence is validated, but the destination field was not validated in the locked local provenance/schema. Implementing flows now would risk using an unverified SIH field.

## Overall Verdict

Status: BLOCKED.

The official source systems are plausible and should be used in the next phase, but Phase 3 cannot be implemented safely in the current execution without downloading, hashing, validating, and documenting a new source package first. No temporal, financing, flow, database, API, frontend, or report product changes were made.

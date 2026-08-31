# Phase 3 source acquisition and scientific gate

Status: BLOCKED_SCIENTIFIC_AGE_BAND_INCOMPATIBILITY

Base commit: `ead5ec6c217e885efcb8bc691d6ec1eb21493afe`.
The initial working tree was clean. The Phase 2 audit repair remains locked and was not repeated.

## Acquisition result

The missing-local-file interpretation from the first gate is superseded. Official acquisition succeeded:

| Family | New primary files | Period |
| --- | ---: | --- |
| SIM DORES | 54 | 2020, 2021, 27 UFs |
| SIH RD | 648 | Jan 2020 through Dec 2021, 27 UFs |
| CNES ST/LT/PF | 162 | Dec 2022 and Dec 2023, 27 UFs |
| POPSVS | 2 | 2020, 2021 |
| SIOPS municipal ZIP | 3 | 2022, 2023, 2024; sixth bimestre |
| Total primary downloads | 869 | |

Three official technical PDFs were also acquired. Original ZIPs and extracted SIOPS CSVs are retained separately. The source manifest preserves URL, final redirect, filename, time, size, SHA256 and schema fingerprint. Raw sources remain outside Git under the existing ignored `data/raw/phase3/` policy. No private mirror was used.

Official FTP catalogs were requested before selecting filenames. The CNES catalog uses separate ST, LT and PF subdirectories. SIM files were obtained from consolidated `SIM/CID10/DORES/`, not a preliminary-data directory. Download success alone is not a scientific PASS.

Some existing and newly created files were evicted by macOS cloud storage. Read attempts returned `TimeoutError: [Errno 60] Operation timed out`. Locked files needed for the audit were reacquired into a separate recovery cache only after checking official catalogs; their hashes matched the previous locked manifest. This environment issue is not the scientific blocker. Current header coverage and any unmaterialized locked files are explicitly listed in `audit_results/phase3_schema_validation.txt`.

## Population series: compatible extension, incompatible locked age handling

The official FTP provides POPSBR20/21/22/23/24 in the same revised 2000-2024 series. All five inspected DBFs contain 902,340 rows, 5,570 municipalities, two sexes, and the same five fields and schema fingerprint. National populations are 209,164,889; 210,103,642; 210,862,983; 211,695,158; and 212,583,750, respectively. No negative populations were observed. There is no need to concatenate the obsolete 2018 projection vintage with the revised series.

The [current official methodological note](http://tabnet.datasus.gov.br/cgi/IBGE/NT-Ripsa_01_2025_Estimativas_Populacionais.PDF) and the archived official FTP note `IBGE/doc/NT-POPULACAO-RESIDENTE-2000-2024.pdf` define single ages 0-79 and one terminal category **80 years and over**. The actual DBFs contain `IDADE=000` through `080`, with no 85-89 or 90+ denominator categories.

The locked method metadata instead requires five-year groups through 90+. Its preserved source script has SHA256 `8612690ed9e6dfb70be526c307d1696a04c7550e3c27a3bda57f1a1bb6a44e4e`. The implementation treats `080` as an exact age, maps all 80+ population to the label `80-84`, and left-joins deaths onto available population groups. Thus it omits the 85-89 and 90+ death strata from ASMR, while retaining their deaths in the overall suicide numerator. This is not merely a naming issue or a vintage discontinuity.

The old `population_QC.md` already reported missing groups `85-89` and `90+` despite its overall PASS label. No prior audit or canonical data were edited to conceal this discrepancy.

## Quantified impact

The independent audit read all 81 locked SIM files for 2022-2024 and checked their hashes. It retained the locked diagnosis, residence mapping and geography.

| Check | Result |
| --- | ---: |
| Health Regions | 439 |
| Mapped suicide deaths at ages 80-84 | 650 |
| Mapped suicide deaths at ages 85-89 | 352 |
| Mapped suicide deaths at ages 90+ | 143 |
| Deaths age 85+ excluded from locked ASMR | 495 |
| Regions containing these age 85+ deaths | 223 |
| Reconstructed old ASMR vs canonical, maximum absolute difference | 3.552713678800501e-15 |
| Diagnostic 80+ ASMR vs canonical, maximum absolute difference | 0.7407065930032477 |
| Regions whose ASMR changes by more than 1e-12 | 327 |
| Regions whose Need changes by more than 1e-12 | 367 |
| Maximum absolute Need difference | 0.0365296803652968 |

The diagnostic alternative collapses the final three WHO weights into 80+, includes all 80+ deaths, and uses the observed 80+ population. It was calculated solely in audit outputs. It is not an authorized method change, temporal release, published result or replacement canonical.

The old calculation reproduces the locked release within the required tolerance; a scientifically coherent terminal-age treatment does not. Therefore unchanged locked science, valid age standardization, and exact reproduction cannot all be satisfied under the current instructions.

## Other source gates

MUNIC_MOV: official SIH documentation defines it as establishment municipality. A national December 2024 comparison of RD.CNES with CNES ST covered 1,111,437 records across all 27 UFs. All records linked, with 1,111,437 exact municipality matches and zero disagreements; the psychiatric subset had 19,671 exact matches. This resolves documentary and sampled empirical destination semantics. Full pooled 2022-2024 origin reconciliation is not claimed and was not completed after the temporal stop.

SIOPS: all three original official ZIPs were downloaded, CRC-checked, extracted and inventoried in full. There are 6,212,593 / 6,501,866 / 6,539,095 rows and 5,567 / 5,568 / 5,567 municipalities in 2022 / 2023 / 2024. All files have the same 14 columns, UTF-8 BOM, semicolon delimiter and dot decimal. Missingness is zero within the observed rows, but absence of a municipality is not zero expenditure.

The files mix hierarchical nature totals/components and seven budget/expenditure stages. Summing all rows is invalid. Root-category diagnostics are not yet reconciled financing measures. The 2024 file includes a single current-expenditure/liquidated row of BRL 382,587,171,024,568.00 for Senhora dos Remedios and a paid row of BRL 4,719,547,615,230.72 for Juarez Tavora. These are source-observed anomalies, not parser rounding errors. They were not capped, removed, repaired or silently avoided by choosing another stage. Independent official reconciliation and a defensible stage decision remain open; SIOPS is not declared impossible.

RAPS_SPECIFIC_TRANSFER_LAYER = NOT_IMPLEMENTED_SOURCE_NOT_DEFENSIBLE. No validated stable RAPS transfer identifier was established from the bounded official-source review. This optional layer is not the blocker.

## Alternatives assessed

1. Reuse the same revised population series for 2020-2024: feasible, but does not supply the missing terminal age splits.
2. Use the older population vintage: rejected because it would introduce a methodological break and does not repair the already locked 2022-2024 ASMR.
3. Disaggregate 80+ with assumed shares or treat absent denominators as zero: rejected as fabricated municipal age structure.
4. Keep the old calculation solely to satisfy exact reproduction: rejected as a scientific PASS because the observed age mismatch would remain.
5. Collapse to 80+ consistently: defensible diagnostic candidate, but changes the scientific method and 2024 canonical values; requires a newly authorized versioned correction.

## Scope preserved and next action

No database migration, API, frontend, Manager V2, Report V2 or advanced release was created. No Open Platform work was started. The canonical release, Territorial Intelligence and Manager Phase 2 remain byte-preserved; `NOT_RELEASED` remains unchanged. Byte preservation does not certify the newly identified scientific defect as correct.

Next action: authorize a separate versioned ASMR correction using the supported 80+ terminal group, retain `MDB_ANALYTICAL_2024_1` as historical evidence, validate a corrected successor, and update the Phase 3 exact-reproduction target explicitly. Then resume the remaining SIOPS reconciliation, pooled flow reconciliation and full Phase 3 implementation. Do not silently change the existing lock to force a PASS.

The complete product test, visual QA, PDF QA, database restore and deployment suites are not claimed: their Phase 3 artifacts were not implemented after this scientific stop. Source-unit tests, diagnostic reproduction, sampled flow linkage, hashes and package-manifest checks are recorded separately.

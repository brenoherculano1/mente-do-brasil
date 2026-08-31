# Versioned scientific correction: ASMR 80+

Authorization: explicit user instruction of 2026-08-31. Historical release and metadata are immutable.

## Defect and source evidence

POPSVS revised 2000-2024 has single ages 0-79 and terminal code 080 = 80 years and over. The historical implementation incorrectly assigned that denominator to 80-84 and omitted 85-89 and 90+ death contributions. The counts were retained in crude totals. The source-acquisition audit and official population technical notes are preserved in `metadata/provenance/phase3_catalogs`.

The correction includes 495 mapped deaths age 85+ in the ASMR. All 50,133 mapped suicide deaths remain in crude counts; 33 mapped deaths of unknown age remain excluded only from ASMR. The existing exclusion of 82 geographically unmapped deaths is unchanged and remains a limitation, not missing data converted to zero.

## Corrected method

`MDB_METHOD_1.1` uses 17 observable bands: 0-4 through 75-79, then 80+. Pooled deaths and population person-years use the same bands. The terminal denominator is used once. ICD-10 X60-X84, residence, years, geography and unknown-age handling are unchanged.

Primary standard: [WHO, Ahmad et al., 2001, Table 4](https://cdn.who.int/media/docs/default-source/gho-documents/global-health-estimates/gpe_discussion_paper_series_paper31_2001_age_standardization_rates.pdf), printed page 12. PDF SHA256: `9eccbc24e4771e2b161233ca3a190f0fb3400437eaa0b19b98371de037b2caa7`.

The five terminal published weights sum exactly to 1.545: 0.91 + 0.44 + 0.15 + 0.04 + 0.005. The entire published vector sums to 100.035 because of publication rounding. Normalize the collapsed vector to one; terminal weight = 0.015444594391962814. No pseudo-group 0.23 or diagnostic terminal 1.58 is used.

The Table 1 rounding sensitivity uses 1.54, normalizing its complete vector independently. Maximum absolute differences: ASMR 0.002771999163066141; percentile 0.0045662100456621; Need/Mismatch 0.0022831050228310223. Moran difference 0.00008662839673534428. LISA membership and labels are unchanged. This is a descriptive rounding sensitivity, not an equivalence test with an invented post-hoc threshold.

## Impact

| Measure | Historical | Corrected |
| --- | --- | --- |
| Median ASMR | 8.702376645130828 | 8.794678614973424 |
| ASMR IQR | 4.37 (submitted rounded value) | 4.353897453200618 |
| Moran I | 0.5254943888435958 | 0.5256454566660947 |
| Global pseudo-p | 0.0001 | 0.0001 |
| Significant LISA | 135 | 136 |
| HH / LL / HL / LH | 60 / 66 / 4 / 5 | 60 / 65 / 5 / 6 |

ASMR changes in 439 regions because both the terminal group and normalization of the official vector are corrected. Suicide percentile, Need and Mismatch change in 366 regions. Capacity, admissions, geography, crude suicide counts and flags are identical. `SMALL_SUICIDE_COUNT=7`; `ZERO_REGISTERED_BEDS=275`.

Significant-set Jaccard = 135/136 = 0.9926470588235294. HH-set Jaccard = 1. Garcas Araguaia (51005, MT) enters as LH; Sao Joao Nepomuceno/Bicas (31047, MG) changes LL to HL. The five highest within-UF IQRs become AM, PE, MT, MG, SP, versus historical AM, PE, RO, MT, SP. This is a heterogeneity comparison, not performance ranking.

All nine prespecified sensitivity algorithms were rerun. Global Moran remains positive with pseudo-p 0.0001 throughout. Existing limitations are disclosed rather than repaired opportunistically: S3 is count-weighted shrinkage, not an estimated empirical-Bayes model; S8 averages leave-one-out capacity means and is algebraically equivalent to the primary mean; S9 flags low counts but does not remove them. Their descriptions in any revised manuscript must reflect implementation.

## Spatial runtime reproducibility limitation

The original historical spatial function and the new function yield identical local pseudo-p arrays in the current pinned runtime. Relative to the stored historical output, 16 p values differ by at most 0.0002, and 22 BH q values by at most 0.00031811594202896254. Moran and all historical cluster memberships reproduce. The original archive does not fully pin ESDA/Numba. The exact cause of the sub-permutation-level numerical comparison difference is not established. Historical outputs are not rewritten. A paired current-runtime baseline isolates this difference from the ASMR correction; new outputs require their own deterministic rerun.

## Versioning and downstream propagation

New scientific artifacts: `MDB_ANALYTICAL_2024_2`, `MDB_CANONICAL_1.1`, `MDB_TERRITORIAL_INTELLIGENCE_1.1`. Radar, decomposition and peer algorithms remain version 1.0. All 4,390 peer relationships, ranks and distances are exactly unchanged; capacity-related benchmarks are unchanged. New Radar family counts remain 71, 38, 68, 184, 60, although individual non-HH membership must be read from the impact CSV.

The historical canonical and three intelligence hashes remain preserved. The corrected crosswalk references the existing historical file; no unnecessary serialization. Candidate generation is not current-release promotion. Promotion requires validated scientific gates and serving integration. Public status remains `NOT_RELEASED`.

## Paper implications

See `health_and_place_scientific_correction_impact_2026-08-31.md`, sentence ledger and local replacement draft. No submitted document was changed, and no editorial action was executed. The new Phase 3 scientific target is the corrected release, conditional on its validation, never the defective historical numbers.

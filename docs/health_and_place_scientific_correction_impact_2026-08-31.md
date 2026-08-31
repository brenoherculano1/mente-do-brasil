# Health & Place scientific correction impact

## Baseline

Read-only local submission package: `phase3b_health_and_place_submission/Health_and_Place_Main_Manuscript.docx` in the original spatial-inequality project. SHA256 `776f1871abe67a06b340f2b12c0ec2f50a3fcee1b84ea646b345231934cc42a3`. Supplement SHA256 `429fc944c216a98c71f1b8f2c4287ff1362ea83842c319dec9f8b576c99bd13a`. This is the preserved submission version; identity with the journal's current portal bytes has not been independently confirmed. No Drive manuscript, journal portal or email was modified.

## Defect

The manuscript explicitly specifies five-year bands with a 90-plus terminal category. POPSVS only provides a terminal 80+ denominator. The historical calculation discarded the age-specific contribution of 495 mapped deaths aged 85+, while retaining crude counts.

## Corrected method

Use 0-4 through 75-79 and terminal 80+, for numerator and denominator. Collapse detailed WHO 2001 Table 4 weights to raw terminal 1.545 and normalize the entire published vector (100.035) to one. Preserve other indicator definitions and unknown-age handling.

## Why correction was required

A denominator for 80+ cannot represent 80-84 alone, nor can unavailable 85+ denominators justify dropping observed deaths. Preserving old values is not a defensible objective.

## Legacy vs corrected ASMR

Median 8.702376645130828 -> 8.794678614973424 per 100,000 person-years. New IQR 4.353897453200618. All 439 rates change; maximum delta 0.7215003398359787. Published values 8.70 and 4.37 become 8.79 and 4.35.

## Need impact

366 regions change, delta range -0.01255707762557079 to +0.0365296803652968. Median delta -0.0011415525114154557. Admissions remain identical.

## Mismatch impact

366 regions change; median changes from -0.0125570776255709 to -0.00951293759512939. Capacity is unchanged in 439/439 regions. No causal, access or performance interpretation is introduced.

## Moran impact

0.5254943888435958 -> 0.5256454566660947. Pseudo-p remains 0.0001. Rounded manuscript Moran must change from 0.525 to 0.526. Independent matrix identity passed.

## LISA impact

135 -> 136 significant; HH 60 -> 60, LL 66 -> 65, HL 4 -> 5, LH 5 -> 6. Garcas Araguaia (51005, MT) enters as LH. Sao Joao Nepomuceno/Bicas (31047, MG) changes LL to HL. Significant-set Jaccard 0.9926470588235294.

## HH set impact

The exact 60-member HH set and UF distribution are unchanged: PR 20, SC 12, RS 11, SP 7, MS 6, TO 2, AC 1, RO 1. Jaccard 1.0. Their ASMR, Need, Mismatch, local statistics and sensitivity benchmark values still require regeneration.

## State heterogeneity impact

Highest five within-UF IQRs: historical AM, PE, RO, MT, SP; corrected AM, PE, MT, MG, SP. Corrected values: AM 0.36834094368340936; PE 0.2966133942161339; MT 0.2797754946727549; MG 0.27853881278538817; SP 0.27711187214611865. RO is now 0.27207001522070023.

## Sensitivity impact

All S1-S9 rerun; all global pseudo-p=0.0001. Moran values range from 0.45428404222028906 to 0.5637691286604688. ASMR-only S4 retains 39/60 primary HH members and Spearman 0.8233994679329878. Headcount S5 retains 51/60, rho 0.9745348607218787. KNN S6 retains 57/60. The original local dependency classifications remain moderate for admissions and minor for workforce/weights by the original overlap rules.

The rounding sensitivity causes no LISA membership or class change. Preserve disclosure of the small historical/runtime local-p discrepancy recorded in the scientific correction documentation. Do not claim that archived p values reproduced exactly.

Additional pre-existing wording mismatches found while rerunning: S3 uses count-weighted shrinkage, not a fitted EB estimator; S8 averaged leave-one-out specifications collapse to the original capacity mean; S9 is flag-only rather than an exclusion analysis. Algorithms were preserved. A corrected draft must not overstate these checks.

## Conclusion robustness

Positive global autocorrelation: YES. Significance: YES. HH clustering: YES. Central ecological conclusion preserved: YES. This does not validate access, quality or unmet-need claims.

## Every manuscript statement requiring update

The companion CSV ledger identifies Methods, Abstract Results, indicator distribution, Moran, LISA, within-UF heterogeneity, Discussion, sensitivity terminology, supplementary material and numerical figure content. The claim of 60 HH and its UF distribution remains valid. The statement that all nine algorithms support the global pattern remains valid, subject to honest description of S3/S8/S9.

## Figures requiring regeneration

Figures 1 (Need), 3 (Mismatch), 4 (LISA) and 5 (within-UF IQR). Figure 2 (Capacity) is numerically unaffected; retain it after verifying consistent release labeling.

## Tables requiring regeneration

The main DOCX has no embedded tables. Supplement tables under Corrected Spatial Summary, Complete Sensitivity Summary, Corrected High-High Regions and Corrected State-Masking Summary require regeneration. The small-number table's underlying counts/membership remain unchanged but derived columns and labeling require verification. Corrected Spatial QC must distinguish historical/runtime limitations from the new deterministic run.

## Supplement requiring regeneration

YES: Health_and_Place_Supplement.docx and Health_and_Place_Supplementary_Data_All_439_Health_Regions.csv. This execution prepares replacement text and data evidence only; it does not overwrite those submitted files.

## Recommended editorial action

Materiality: MODERATE_RESULT_SET_CHANGE. Rule: MAJOR if the global sign/significance or central conclusion changes; MODERATE if local class membership or the highest-heterogeneity UF set changes despite preserved central conclusion; otherwise MINOR_NUMERICAL. Both moderate triggers apply.

JOURNAL_ACTION_REQUIRED: YES.

Recommendation: CONTACT_EDITOR_WITH_CORRECTED_FILES, subject to human approval and confirmation of submission status. Reason: a material Methods defect changes numerical findings, local classifications and within-state summary statements in an already submitted manuscript. No withdrawal recommendation is warranted solely by these results because the central conclusion persists. No contact, email, manuscript upload or portal action was performed.

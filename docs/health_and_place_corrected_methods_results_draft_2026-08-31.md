# Local replacement draft: not submitted

Based on MDB_METHOD_1.1 and MDB_ANALYTICAL_2024_2. For human review before any editorial action. Submitted files remain unchanged.

## ASMR method

Suicide deaths were defined by residence and ICD-10 underlying-cause codes X60-X84. We directly age-standardized pooled 2022-2024 mortality using five-year groups from 0-4 through 75-79 years and a terminal group aged 80 years or older, matching the observed POPSVS denominator. The WHO 2001 World Standard Population (Ahmad et al., Table 4) was collapsed to these bands. Published weights for 80-84, 85-89, 90-94, 95-99 and 100+ summed to 1.545; the complete collapsed vector was normalized to sum to one to account for rounding in the published table. All mapped deaths aged 80+ contributed to the terminal numerator. Deaths of unknown age were excluded from age-specific rates and retained in QC. We also evaluated the alternative rounded terminal weight of 1.54 from WHO Table 1 without changing the primary method.

## Abstract Results

Mismatch scores showed positive spatial autocorrelation (Moran's I=0.526; permutation pseudo-p=0.0001). Local Moran analysis identified 136 FDR-significant Health Regions, including 60 High-High mismatch clusters. The highest within-UF mismatch IQRs occurred in AM, PE, MT, MG and SP. Prespecified sensitivity algorithms retained positive global spatial autocorrelation, although removal of admissions moderately affected local HH membership.

## Indicator distributions

Median suicide ASMR was 8.79 per 100,000 person-years (IQR 4.35). Other indicator distributions were unchanged: median psychiatric admission rate 85.05 (IQR 110.02), CAPS rate 2.02, SUS mental-health bed rate 0.00 and psychiatrist FTE rate 3.02, in their respective rate units. Counts of flagged regions remained seven with fewer than ten pooled suicide deaths and 275 with zero registered SUS mental-health beds.

## Global and local spatial results

Global Moran's I was 0.5256454566660947 (pseudo-p=0.0001; 9,999 permutations). Independent matrix verification agreed within numerical tolerance. At BH FDR q=0.10, 136 regions were significant: 60 HH, 65 LL, five HL and six LH. The HH set was identical to the historical analysis; its composition by UF remained PR 20, SC 12, RS 11, SP 7, MS 6, TO 2, AC 1 and RO 1. Garcas Araguaia (MT) entered the significant set as LH, and Sao Joao Nepomuceno/Bicas (MG) changed from LL to HL.

## Within-UF heterogeneity

The largest mismatch IQRs occurred in AM (0.368), PE (0.297), MT (0.280), MG (0.279) and SP (0.277). SP still included 62 Health Regions. These quantities describe internal heterogeneity, not health-system performance.

## Sensitivity summary

Global Moran's I remained positive in all nine prespecified algorithms (range 0.4543-0.5638), with pseudo-p=0.0001 throughout. The ASMR-only specification retained 39 of 60 primary HH regions; the headcount specification retained 51, and KNN retained 57. The WHO rounding sensitivity changed ASMR by at most 0.002772 per 100,000, Need and Mismatch by at most 0.002284, and did not change LISA membership or classes.

The shrinkage sensitivity uses a prespecified count-weighted formula rather than an estimated empirical-Bayes model. The averaged leave-one-out capacity specification is algebraically equivalent to the primary capacity mean. The low-count specification flags regions rather than removing them; it must not be described as demonstrating robustness to their exclusion.

## Discussion and conclusion

The correction changes the age-standardization method and numerical findings, but preserves positive significant global spatial autocorrelation and the exact primary HH set. It changes the significant local set and the highest-heterogeneity UF set. The central conclusion remains that relative need-capacity mismatch has spatial structure at the Health Region scale. These ecological indicators do not directly measure individual access, quality or unmet need.

## Reproducibility disclosure

The corrected release was rebuilt deterministically in a pinned runtime. Running the historical spatial routine in that runtime reproduced its Moran and all cluster memberships, but some archived local pseudo-p and q values differed slightly; the historical artifacts remain preserved. Full scientific/runtime provenance accompanies the correction package.

## Editorial boundary

JOURNAL_ACTION_REQUIRED: YES. Recommended action is CONTACT_EDITOR_WITH_CORRECTED_FILES after human approval and confirmation of submission status. No email, journal contact or manuscript upload has occurred.

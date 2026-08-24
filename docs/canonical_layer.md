# Canonical Layer

`RAW` is the frozen scientific evidence imported from the validated release bundle.

`CANONICAL` is a normalized product representation of that evidence. It does not
recalculate methodology, update source data, alter scores, or change spatial results.

The canonical health-region table is:

`data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet`

The canonical municipality-to-health-region crosswalk is:

`data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet`

## Mapping

| source field | canonical field |
| --- | --- |
| constant `MDB_ANALYTICAL_2024_1` | `release_id` |
| constant `MDB_METHOD_1.0` | `method_version` |
| constant `BR_HEALTH_REGIONS_END2024_V1` | `geography_version` |
| `health_region_code` | `health_region_code` |
| `health_region_name` | `health_region_name` |
| first two digits of `health_region_code` | `uf_code` |
| `UF` | `uf` |
| `municipality_count` | `municipality_count` |
| `population_2024` | `population` |
| `area_km2` | `area_km2` |
| `population_density_2024` | `population_density` |
| `deaths_pooled` | `suicide_deaths` |
| `ASMR` | `suicide_asmr` |
| `suicide_percentile` | `suicide_percentile` |
| `admission_n` | `psychiatric_admissions` |
| `admission_rate` | `psychiatric_admission_rate` |
| `admissions_percentile` | `psychiatric_admission_percentile` |
| `unique_CAPS_n` | `caps_count` |
| `CAPS_rate_per_100k` | `caps_rate` |
| `CAPS_percentile` | `caps_percentile` |
| `SUS_mental_health_beds_n` | `mental_health_beds_sus_count` |
| `bed_rate_per_100k` | `mental_health_beds_sus_rate` |
| `beds_percentile` | `beds_percentile` |
| `psychiatrist_FTE` | `psychiatrist_fte` |
| `FTE_rate_per_100k` | `psychiatrist_fte_rate` |
| `FTE_percentile` | `psychiatrist_fte_percentile` |
| `Need_r` | `need_score` |
| `Capacity_r` | `capacity_score` |
| `Mismatch_r` | `mismatch_score` |
| `local_I` | `lisa_local_i` |
| `raw_pseudo_p` | `lisa_p` |
| `BH_adjusted_q` | `lisa_q` |
| `significant_at_q_0.10` | `lisa_significant` |
| `cluster_label` | `lisa_cluster` |
| `small_number_flag`; `SUS_mental_health_beds_n` | `data_quality_flags` |

The canonical build uses
`corrected_Supplement_All_439_Health_Regions.csv` only as an independent
cross-check. It does not use old invalidated spatial outputs.

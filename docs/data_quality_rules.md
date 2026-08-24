# Data Quality Rules

Initial structural rules:

1. `municipality_count == 5570`
2. `health_region_count == 439`
3. each municipality belongs to exactly one Health Region
4. `health_region_code` cannot be null
5. `health_region_code` must be unique in aggregate territorial tables
6. joins cannot silently drop municipalities
7. UF must be valid for all regions
8. population values cannot be negative
9. CAPS counts cannot be negative
10. bed counts cannot be negative
11. psychiatrist FTE cannot be negative
12. percentile ranks must be between 0 and 1
13. `need_score` must be between 0 and 1
14. `capacity_score` must be between 0 and 1
15. `mismatch_score` must be between -1 and 1
16. missing values must not be automatically converted to zero

Supported data-quality flags:

- `SMALL_SUICIDE_COUNT`
- `EXTREME_PSYCHIATRIST_HOURS`
- `ZERO_REGISTERED_BEDS`
- `SOURCE_INCOMPLETE`
- `GEOGRAPHY_CROSSWALK_WARNING`
- `PROVISIONAL_SOURCE`

Flags coexist with observations. A flag is not an instruction to delete a row.

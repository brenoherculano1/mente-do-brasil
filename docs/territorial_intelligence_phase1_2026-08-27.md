# Territorial Intelligence Phase 1

## Scope

This phase adds a local product intelligence layer for Radar Territorial,
deterministic region explanations, exact Mismatch decomposition, structural peers,
and descriptive peer benchmarks.

No canonical science, weights, geography, public release status, downloads,
public API publication, DNS, or deployment were changed.

## Versions

- Intelligence: `MDB_TERRITORIAL_INTELLIGENCE_1.0`
- Radar ruleset: `MDB_RADAR_RULESET_1.0`
- Decomposition: `MDB_MISMATCH_DECOMPOSITION_1.0`
- Peer method: `MDB_PEER_METHOD_1.0`
- Source release: `MDB_ANALYTICAL_2024_1`
- Source method: `MDB_METHOD_1.0`
- Source geography: `BR_HEALTH_REGIONS_END2024_V1`
- Web geometry: `MDB_WEB_GEOMETRY_V1`

## Inputs

Primary input:

`data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet`

SHA-256:

`a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515`

No new external data source was introduced.

## Radar Methodology

The Radar answers where signals deserve more careful territorial investigation.
It is not a ranking, risk score, priority score, or resource recommendation.

`matched_signal_families` is the unweighted count of five transparent boolean
families. It ranges from 0 to 5.

## Signal Families

- `NEED_HIGH`: `need_score >= 0.75`
- `CAPACITY_LOW`: `capacity_score <= 0.25`
- `MISMATCH_MARKED_POSITIVE`: `mismatch_score >= 0.25`
- `CAPACITY_COMPONENT_LOW`: CAPS, beds, or psychiatrist FTE percentile `<= 0.25`
- `SPATIAL_HH_MISMATCH`: significant LISA HH Mismatch context

Data-quality flags are shown as cautions and do not increment
`matched_signal_families`. `ZERO_REGISTERED_BEDS` remains a badge/caution, not a
sixth family.

## Why No Ranking

The product presents confluence of transparent criteria. It does not number
regions as best/worst and does not infer adequacy or prescribe action.

## Mismatch Decomposition

Let:

- `S = suicide_percentile`
- `A = psychiatric_admission_percentile`
- `C = caps_percentile`
- `B = beds_percentile`
- `P = psychiatrist_fte_percentile`

Then:

- `suicide_contribution = 0.5 * (S - 0.5)`
- `admissions_contribution = 0.5 * (A - 0.5)`
- `caps_contribution = -(1/3) * (C - 0.5)`
- `beds_contribution = -(1/3) * (B - 0.5)`
- `psychiatrist_contribution = -(1/3) * (P - 0.5)`

## Mathematical Identity

For all 439 Health Regions:

`sum(contributions) == mismatch_score`

Validated maximum absolute error:

`2.498001805406602e-16`

## Peer Methodology

Peers answer whether the selected region is descriptively unusual among
territories with similar structure. Outcomes are not used for peer selection.

## Structural Variables

- `population`
- `population_density`
- `municipality_count`

## Transformations

Each structural variable is transformed with `log1p`, then standardized with
national z-scores using population standard deviation `ddof=0`.

## Distance

Euclidean distance across the three transformed structural dimensions, with equal
dimension weighting.

For each Health Region, self is excluded and the 10 nearest peers are selected.
Ties are resolved deterministically by `health_region_code`.

## Peer Benchmarks

Benchmarks are long-format and include eight existing metrics:

- `need_score`
- `capacity_score`
- `mismatch_score`
- `suicide_asmr`
- `psychiatric_admission_rate`
- `caps_rate`
- `mental_health_beds_sus_rate`
- `psychiatrist_fte_rate`

For each metric, peer median, Q1, Q3, min, max, observed peer count, and
relative-to-IQR category are calculated. Quantiles use numpy `method=linear`.

Minimum observed peers for benchmark statistics: 5.

## Limitations

Peers V1 does not incorporate income, formal urbanization, age profile, social
vulnerability, or financing. Similar means similar only across the three
documented structural dimensions.

Capacity is registered capacity, not measured access or quality. Need is based
on measured indicators and is not prevalence.

## Data Outputs

- `data/product_intelligence/MDB_ANALYTICAL_2024_1/health_region_intelligence.parquet`
- `data/product_intelligence/MDB_ANALYTICAL_2024_1/health_region_peers.parquet`
- `data/product_intelligence/MDB_ANALYTICAL_2024_1/peer_benchmarks.parquet`
- `data/product_intelligence/MDB_ANALYTICAL_2024_1/territorial_intelligence_qc.json`
- `metadata/product_intelligence/MDB_TERRITORIAL_INTELLIGENCE_1.0.yaml`

## Database

New serving tables:

- `meta.product_intelligence_versions`
- `analytics.health_region_intelligence`
- `analytics.health_region_peers`
- `analytics.health_region_peer_benchmarks`

The load is idempotent and protected by an immutability check on product output
hashes.

## API

- `GET /api/v1/radar/health-regions`
- `GET /api/v1/health-regions/{code}/explanation`
- `GET /api/v1/health-regions/{code}/peers`
- `GET /api/v1/intelligence/methods`

Radar geometry uses overview web geometry only.

## UX

- New route: `/radar`
- New navigation item: Radar
- Region profile now includes Radar triggers, exact Mismatch decomposition, and
  structural peer comparison.
- State pages link to state-filtered Radar.

## Tests

Validated:

- Python regression and product intelligence tests
- Serving database validation
- API contract validation
- Frontend unit tests
- Typecheck, lint, production build
- Playwright E2E with production Next start and live FastAPI/DB

## QC

Key QC files are in `audit_results/`.

New screenshots are in:

`docs/territorial_intelligence_qc_2026-08-27/`

## Remaining Product Phases

- Automatic territorial report
- Manager mode
- Additional peer dimensions only if new locked inputs are added in a future
  versioned release

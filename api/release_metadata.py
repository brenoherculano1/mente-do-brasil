# ruff: noqa: E501
"""Byte-identical locked release metadata for Python deployment bundles."""

RELEASE_JSON = r'''{
  "open_platform_version": "MDB_OPEN_PLATFORM_1.0",
  "open_data_release_id": "MDB_OPEN_DATA_2024_1",
  "public_api_version": "MDB_PUBLIC_API_V1",
  "data_governance_version": "MDB_DATA_GOVERNANCE_1.0",
  "analytical_release_id": "MDB_ANALYTICAL_2024_2",
  "method_version": "MDB_METHOD_1.1",
  "geography_version": "BR_HEALTH_REGIONS_END2024_V1",
  "web_geometry_version": "MDB_WEB_GEOMETRY_V1",
  "built_at": "2026-09-01T00:00:00Z",
  "published_at": null,
  "status": "LOCKED_LOCAL",
  "public_release_status": "NOT_RELEASED",
  "writer": {
    "pyarrow": "25.0.1",
    "pandas": "3.0.5"
  },
  "license": "CC BY 4.0 for licensable Mente do Brasil original/derived rights; third-party exclusions apply.",
  "source_matrix_version": "MDB_SOURCE_RIGHTS_MATRIX_1.0",
  "datasets": {
    "health_regions_current": {
      "rows": 439,
      "fields": [
        "release_id",
        "method_version",
        "geography_version",
        "health_region_code",
        "health_region_name",
        "uf",
        "municipality_count",
        "population",
        "area_km2",
        "population_density",
        "suicide_asmr",
        "suicide_percentile",
        "psychiatric_admission_rate",
        "psychiatric_admission_percentile",
        "caps_count",
        "caps_rate",
        "caps_percentile",
        "mental_health_beds_sus_count",
        "mental_health_beds_sus_rate",
        "beds_percentile",
        "psychiatrist_fte",
        "psychiatrist_fte_rate",
        "psychiatrist_fte_percentile",
        "need_score",
        "capacity_score",
        "mismatch_score",
        "lisa_local_i",
        "lisa_p",
        "lisa_q",
        "lisa_significant",
        "lisa_cluster",
        "data_quality_flags"
      ],
      "key": [
        "health_region_code"
      ],
      "semantic_sha256": "454abc5ebe5daaaf4efe9a76c5a8aef7ed983e2850192ec096392090868ae457",
      "caveat": "Territorial intelligence, not prevalence, direct access, quality, or unmet need.",
      "distributions": [
        {
          "path": "health_regions_current.csv",
          "bytes": 216846,
          "sha256": "16f59cb2a57a113c2904b45f1f30396cefd243e4c77f341eb9b244858fa1930a"
        },
        {
          "path": "health_regions_current.parquet",
          "bytes": 73957,
          "sha256": "936ac3fb4d5ce4a4714a9648fb1c7abdab7195188a69c3461ae30bca5d47a826"
        }
      ]
    },
    "health_region_temporal": {
      "rows": 1317,
      "fields": [
        "health_region_code",
        "health_region_name",
        "uf",
        "geography_version",
        "population",
        "person_years",
        "suicide_asmr",
        "psychiatric_admissions",
        "psychiatric_admission_rate",
        "caps_count",
        "mental_health_beds_sus_count",
        "psychiatrist_fte",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
        "suicide_percentile",
        "psychiatric_admission_percentile",
        "caps_percentile",
        "beds_percentile",
        "psychiatrist_fte_percentile",
        "need_score",
        "capacity_score",
        "mismatch_score",
        "year",
        "need_window_start",
        "need_window_end",
        "capacity_competence",
        "temporal_version",
        "release_id",
        "quality_flags"
      ],
      "key": [
        "year",
        "health_region_code"
      ],
      "semantic_sha256": "beade4ea1f936c90ac421a603586e0e6764b844aea748956d77e5d0884499a8d",
      "caveat": "Anchored descriptive comparisons; no causal or real-time interpretation.",
      "distributions": [
        {
          "path": "health_region_temporal.csv",
          "bytes": 553931,
          "sha256": "3da99c96d42867a649eace6d53b79adaab56d5ef7ae0b68ce5a100e61463722e"
        },
        {
          "path": "health_region_temporal.parquet",
          "bytes": 115634,
          "sha256": "5fe8ab0dcdd2b1aa22eecafa3465bda931d4de60787cb79e7034369cf3bee282"
        }
      ]
    },
    "health_region_changes": {
      "rows": 1317,
      "fields": [
        "health_region_code",
        "delta_need_score",
        "delta_capacity_score",
        "delta_mismatch_score",
        "delta_suicide_percentile",
        "delta_psychiatric_admission_percentile",
        "delta_caps_percentile",
        "delta_beds_percentile",
        "delta_psychiatrist_fte_percentile",
        "NEED_POSITION_UP",
        "CAPACITY_POSITION_DOWN",
        "MISMATCH_POSITION_UP",
        "NEED_COMPONENT_POSITION_UP",
        "CAPACITY_COMPONENT_POSITION_DOWN",
        "matched_change_families",
        "from_year",
        "to_year",
        "change_version"
      ],
      "key": [
        "from_year",
        "to_year",
        "health_region_code"
      ],
      "semantic_sha256": "53691ef403525499b8a6e841918c9853d10d1407d5975fc937ef5cf25ec1b2e8",
      "caveat": "Position-change signals; not improvement or deterioration labels.",
      "distributions": [
        {
          "path": "health_region_changes.csv",
          "bytes": 325373,
          "sha256": "de2b800328b35313247b40d208306b1315360debdc01b38e523e800c933761a7"
        },
        {
          "path": "health_region_changes.parquet",
          "bytes": 40986,
          "sha256": "88d771a92cc345a5977c0adef7931749a1dcaaf66734c8b494393a39da46091d"
        }
      ]
    },
    "health_region_financing": {
      "rows": 1317,
      "fields": [
        "financing_version",
        "siops_snapshot_id",
        "year",
        "health_region_code",
        "municipalities_expected",
        "municipalities_observed",
        "population_expected",
        "population_covered",
        "coverage_share",
        "coverage_population_share",
        "total_health_expenditure_brl",
        "health_expenditure_per_capita_brl",
        "headline_available",
        "quality_flags",
        "source_period",
        "source_indicator"
      ],
      "key": [
        "year",
        "health_region_code"
      ],
      "semantic_sha256": "af10986b2fa123c3f709c5c876e5396943614c0024d11194088d49f255faf03c",
      "caveat": "General health financing, not mental-health-specific spending; current BRL, not inflation-adjusted.",
      "distributions": [
        {
          "path": "health_region_financing.csv",
          "bytes": 252165,
          "sha256": "ca3e2cd63fd0f9ae37238b1115ade43a8c407e0bccea3e93bf8b4f9317152d45"
        },
        {
          "path": "health_region_financing.parquet",
          "bytes": 32951,
          "sha256": "678172af5615c88287b6db3376749a04505e1260866445ba7ebefe6a70e1ddb3"
        }
      ]
    },
    "health_region_flow_summary": {
      "rows": 439,
      "fields": [
        "flow_version",
        "health_region_code",
        "total_admissions",
        "within_region_share",
        "outflow_share",
        "cross_state_outflow_share",
        "nonsuppressed_destinations",
        "unit"
      ],
      "key": [
        "health_region_code"
      ],
      "semantic_sha256": "aebac00aab9afd461e13161b5d808d82e7ed447ddcf48bb19c250a9b0a64953f",
      "caveat": "AIHs/admissions are not unique patients.",
      "distributions": [
        {
          "path": "health_region_flow_summary.csv",
          "bytes": 55627,
          "sha256": "6dacc88e1199a26a4ea3e1663034409a8f3f7f6fe8111e50b799c1bcacf58453"
        },
        {
          "path": "health_region_flow_summary.parquet",
          "bytes": 15339,
          "sha256": "e4e77d80018feded092ae48a278f2395657b959a40408ed79b8fbf716396666f"
        }
      ]
    },
    "hospitalization_flows_public": {
      "rows": 8920,
      "fields": [
        "origin_region",
        "destination_region",
        "admissions",
        "flow_version",
        "contribution_id"
      ],
      "key": [
        "contribution_id"
      ],
      "semantic_sha256": "9c552aafdad4609da4ed4ba86da6b7da03118314bbbcb25a868cb7fcf48276c2",
      "caveat": "Only exact cells with admissions >=5; suppressed contributions are excluded.",
      "distributions": [
        {
          "path": "hospitalization_flows_public.csv",
          "bytes": 439251,
          "sha256": "1c103e6792699885d51c139f5cfb44c295f7413433045a8685a119f4a9cd89aa"
        },
        {
          "path": "hospitalization_flows_public.parquet",
          "bytes": 38967,
          "sha256": "7636088e96aef78a95dbf10a38e97c0560cee05eeb0dd55a63a9c609607c6d6b"
        }
      ]
    },
    "municipality_health_region_crosswalk": {
      "rows": 5570,
      "fields": [
        "municipality_code_ibge",
        "municipality_name",
        "uf",
        "health_region_code",
        "health_region_name"
      ],
      "key": [
        "municipality_code_ibge"
      ],
      "semantic_sha256": "5d1b7112b025ccd5e1f9006484b0c784597eeeb43593b62534fd73be34311a45",
      "caveat": "Membership under fixed end-2024 health-region geography.",
      "distributions": [
        {
          "path": "municipality_health_region_crosswalk.csv",
          "bytes": 261464,
          "sha256": "b3662535162b771559688b92f9b95caee32ab31e6fef874df709fe1b356eab00"
        },
        {
          "path": "municipality_health_region_crosswalk.parquet",
          "bytes": 66594,
          "sha256": "352ee94d914dcda52965bc019f43f3a9bfb222502f85e66b826fa78dabfcb024"
        }
      ]
    },
    "territorial_intelligence": {
      "rows": 439,
      "fields": [
        "release_id",
        "geography_version",
        "intelligence_version",
        "radar_ruleset_version",
        "decomposition_version",
        "peer_method_version",
        "health_region_code",
        "health_region_name",
        "uf",
        "need_high",
        "capacity_low",
        "mismatch_marked_positive",
        "capacity_component_low",
        "spatial_hh_mismatch",
        "zero_registered_beds",
        "small_suicide_count",
        "matched_signal_families",
        "suicide_contribution",
        "admissions_contribution",
        "caps_contribution",
        "beds_contribution",
        "psychiatrist_contribution",
        "decomposition_sum"
      ],
      "key": [
        "health_region_code"
      ],
      "semantic_sha256": "d974b1a5a8dc7026c6cf239f9fe1c18710d612ea069e6eee18ef6875f9b95ed2",
      "caveat": "Investigation signals; no automatic policy recommendation.",
      "distributions": [
        {
          "path": "territorial_intelligence.csv",
          "bytes": 153959,
          "sha256": "de620b76c167683d2102b4ca3541dd9f4ba23d8c6c20534270e561466f03c089"
        },
        {
          "path": "territorial_intelligence.parquet",
          "bytes": 30632,
          "sha256": "516f538227940280f711d784da3b7e41a87e8e54202eb7515fcadce74aed61e1"
        }
      ]
    },
    "health_region_peers": {
      "rows": 4390,
      "fields": [
        "release_id",
        "peer_method_version",
        "health_region_code",
        "peer_health_region_code",
        "peer_rank",
        "structural_distance"
      ],
      "key": [
        "health_region_code",
        "peer_rank"
      ],
      "semantic_sha256": "56cbc80355a08ede84b7863053c82a6497d659650b4fadd55ab9862ac0b979da",
      "caveat": "Structural comparators, not similar performance.",
      "distributions": [
        {
          "path": "health_region_peers.csv",
          "bytes": 333589,
          "sha256": "05bcfe2b0a3bd46be3b6041f93a6ac30afb099b20b398fe28d67c01476795e9e"
        },
        {
          "path": "health_region_peers.parquet",
          "bytes": 37320,
          "sha256": "a8f11081fc8991b51cf6c607a17d74f3ee36792c0bae9824a36ef8a746ba91c2"
        }
      ]
    }
  },
  "geometry_downloads": "NOT_PUBLISHED_PENDING_EXACT_SOURCE_RIGHTS",
  "supersedes": null,
  "superseded_by": null
}
'''

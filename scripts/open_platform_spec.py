# ruff: noqa: E501
"""Locked public-disclosure specification for MDB_OPEN_DATA_2024_1."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPEN_PLATFORM_VERSION = "MDB_OPEN_PLATFORM_1.0"
OPEN_DATA_RELEASE = "MDB_OPEN_DATA_2024_1"
PUBLIC_API_VERSION = "MDB_PUBLIC_API_V1"
DATA_GOVERNANCE_VERSION = "MDB_DATA_GOVERNANCE_1.0"
FIELD_REGISTRY_VERSION = "MDB_PUBLIC_FIELD_REGISTRY_1.0"
SOURCE_RIGHTS_VERSION = "MDB_SOURCE_RIGHTS_MATRIX_1.0"
ANALYTICAL_RELEASE = "MDB_ANALYTICAL_2024_2"
GEOGRAPHY_VERSION = "BR_HEALTH_REGIONS_END2024_V1"
WEB_GEOMETRY_VERSION = "MDB_WEB_GEOMETRY_V1"
PUBLIC_RELEASE_DIR = ROOT / "artifacts/public_releases" / OPEN_DATA_RELEASE

DATASETS = {
    "health_regions_current": {
        "source": ROOT / "data/canonical/MDB_ANALYTICAL_2024_2/health_regions.parquet",
        "rows": 439,
        "key": ["health_region_code"],
        "columns": [
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
            "data_quality_flags",
        ],
    },
    "health_region_temporal": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_temporal.parquet",
        "rows": 1317,
        "key": ["year", "health_region_code"],
        "exclude": ["suicide_deaths"],
    },
    "health_region_changes": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_changes.parquet",
        "rows": 1317,
        "key": ["from_year", "to_year", "health_region_code"],
    },
    "health_region_financing": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_financing.parquet",
        "rows": 1317,
        "key": ["year", "health_region_code"],
        "round": {
            "total_health_expenditure_brl": 2,
            "health_expenditure_per_capita_brl": 2,
        },
    },
    "health_region_flow_summary": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_flow_summary.parquet",
        "rows": 439,
        "key": ["health_region_code"],
    },
    "hospitalization_flows_public": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/hospitalization_flows.parquet",
        "filter": "public_flows",
        "columns": [
            "origin_region",
            "destination_region",
            "admissions",
            "flow_version",
            "contribution_id",
        ],
        "key": ["contribution_id"],
    },
    "municipality_health_region_crosswalk": {
        "source": ROOT
        / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet",
        "rows": 5570,
        "columns": [
            "municipality_code_ibge",
            "municipality_name",
            "uf",
            "health_region_code",
            "health_region_name",
        ],
        "key": ["municipality_code_ibge"],
    },
    "territorial_intelligence": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_intelligence.parquet",
        "rows": 439,
        "key": ["health_region_code"],
        "columns": [
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
            "decomposition_sum",
        ],
    },
    "health_region_peers": {
        "source": ROOT
        / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_peers.parquet",
        "rows": 4390,
        "key": ["health_region_code", "peer_rank"],
    },
}

FORBIDDEN_PUBLIC_FIELDS = {
    "suicide_deaths",
    "hidden_count",
    "raw_count",
    "original_count",
    "suppressed_exact_count",
    "suppressed",
}

CORE_DESCRIPTIONS = {
    "need_score": (
        "Escore relativo de necessidade medida; não representa prevalência.",
        "Relative measured-need score; it is not prevalence.",
    ),
    "capacity_score": (
        "Escore relativo de capacidade registrada no setor público.",
        "Relative registered public-sector capacity score.",
    ),
    "mismatch_score": (
        "Sinal de desalinhamento territorial relativo entre necessidade medida e capacidade registrada.",
        "Relative territorial misalignment signal between measured need and registered capacity.",
    ),
    "suicide_asmr": (
        "Taxa de mortalidade por suicídio padronizada por idade.",
        "Age-standardized suicide mortality rate.",
    ),
    "psychiatric_admission_rate": (
        "Taxa de AIHs/internações psiquiátricas; não representa pacientes únicos.",
        "Psychiatric AIH/admission rate; it does not represent unique patients.",
    ),
    "lisa_cluster": (
        "Classe LISA local; HH não equivale a hotspot de doença.",
        "Local LISA class; HH is not equivalent to a disease hotspot.",
    ),
    "mental_health_beds_sus_count": (
        "Leitos SUS registrados sob a definição travada; zero não prova ausência de oferta.",
        "SUS beds registered under the locked definition; zero does not prove no supply.",
    ),
    "admissions": (
        "AIHs/internações agregadas, com células menores que cinco excluídas.",
        "Aggregated AIHs/admissions, with cells below five excluded.",
    ),
    "structural_distance": (
        "Distância entre comparadores estruturais baseada apenas nas variáveis estruturais travadas.",
        "Distance between structural comparators using only locked structural features.",
    ),
}

DATASET_CAVEATS = {
    "health_regions_current": "Territorial intelligence, not prevalence, direct access, quality, or unmet need.",
    "health_region_temporal": "Anchored descriptive comparisons; no causal or real-time interpretation.",
    "health_region_changes": "Position-change signals; not improvement or deterioration labels.",
    "health_region_financing": "General health financing, not mental-health-specific spending; current BRL, not inflation-adjusted.",
    "health_region_flow_summary": "AIHs/admissions are not unique patients.",
    "hospitalization_flows_public": "Only exact cells with admissions >=5; suppressed contributions are excluded.",
    "municipality_health_region_crosswalk": "Membership under fixed end-2024 health-region geography.",
    "territorial_intelligence": "Investigation signals; no automatic policy recommendation.",
    "health_region_peers": "Structural comparators, not similar performance.",
}

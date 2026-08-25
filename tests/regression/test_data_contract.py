from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "metadata/contracts/MDB_DATA_CONTRACT_V1.0.yaml"
HEALTH_REGIONS_SCHEMA = REPO_ROOT / "metadata/canonical/health_regions_v1.yaml"
CROSSWALK_SCHEMA = REPO_ROOT / "metadata/canonical/municipality_health_region_crosswalk_v1.yaml"


def load_contract():
    with CONTRACT_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_data_contract_identifier_and_versions_are_locked():
    contract = load_contract()

    assert contract["contract_id"] == "MDB_DATA_CONTRACT_V1.0"
    assert contract["status"] == "LOCKED"
    assert contract["primary_release"] == "MDB_ANALYTICAL_2024_1"
    assert contract["method_version"] == "MDB_METHOD_1.0"
    assert contract["geography_version"] == "BR_HEALTH_REGIONS_END2024_V1"
    assert contract["canonical_version"] == "MDB_CANONICAL_1.0"


def test_data_contract_schema_refs_are_real_and_preserve_shape():
    contract = load_contract()
    with HEALTH_REGIONS_SCHEMA.open(encoding="utf-8") as handle:
        health_regions_schema = yaml.safe_load(handle)

    assert contract["canonical_schema"] == "metadata/canonical/health_regions_v1.yaml"
    assert contract["crosswalk_schema"] == (
        "metadata/canonical/municipality_health_region_crosswalk_v1.yaml"
    )
    assert HEALTH_REGIONS_SCHEMA.exists()
    assert CROSSWALK_SCHEMA.exists()

    assert contract["health_region_count"] == 439
    assert len(health_regions_schema["columns"]) == 35
    assert contract["schema_references"]["health_regions"]["column_count"] == 35
    assert contract["schema_references"]["municipality_health_region_crosswalk"][
        "row_count"
    ] == 5570
    assert contract["schema_references"]["municipality_health_region_crosswalk"][
        "column_count"
    ] == 9


def test_data_contract_null_science_and_isolation_rules_are_preserved():
    contract = load_contract()

    assert contract["null_semantics"] == {
        "null_is_not_zero": True,
        "missing_is_preserved": True,
    }
    assert contract["scientific_recalculation_rule"][
        "consumers_must_not_recalculate_locked_scientific_outputs"
    ]
    assert contract["release_isolation"]["release_id_required"]
    assert contract["geography_isolation"]["geography_version_required"]
    assert contract["data_quality_flags_type"] == "list<string>"


def test_data_contract_provenance_records_materialized_locked_decision():
    contract = load_contract()

    assert contract["provenance"]["origin"] == "project_locked_decision"
    assert "already defined as a locked project identifier" in contract["provenance"]["note"]
    assert "does not introduce a new methodological version" in contract["provenance"]["note"]

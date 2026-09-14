import pytest

from scripts.validate_annual_preflight import REQUIRED, blockers


def complete_rows():
    return [
        {
            "SOURCE": name,
            "COMPLETENESS": "COMPLETE_ENOUGH_FOR_OFFICIAL_RELEASE",
            "SCHEMA_COMPATIBLE": "YES",
            "OFFICIAL_RELEASE_READY": "YES",
        }
        for name in sorted(REQUIRED)
    ]


def reproduction():
    return {"status": "PASS", "byte_identical": True, "protected_changed": []}


@pytest.mark.parametrize("status", ["PARTIAL", "PROVISIONAL", "UNAVAILABLE", "INCONSISTENT"])
def test_incomplete_source_blocks(status):
    rows = complete_rows()
    rows[0]["COMPLETENESS"] = status
    assert blockers(rows, reproduction())


def test_missing_and_duplicate_sources_block():
    rows = complete_rows()
    assert blockers(rows[1:], reproduction())
    assert blockers(rows + [rows[0]], reproduction())


def test_nonidentical_or_mutated_baseline_blocks():
    assert blockers(complete_rows(), {**reproduction(), "byte_identical": False})
    assert blockers(complete_rows(), {**reproduction(), "protected_changed": ["historical"]})
    assert blockers(complete_rows(), {})


def test_unverified_schema_blocks_even_with_ready_label():
    rows = complete_rows()
    rows[0]["SCHEMA_COMPATIBLE"] = "NOT_VERIFIED"
    assert blockers(rows, reproduction())


def test_complete_preflight_is_not_release_publication():
    assert blockers(complete_rows(), reproduction()) == []

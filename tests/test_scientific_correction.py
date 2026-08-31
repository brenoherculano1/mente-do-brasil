"""Scientific correction invariants, without invoking the historical builder."""

import json
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from scripts.build_scientific_correction import (
    AUDIT,
    NEW,
    OLD,
    ROOT,
    WHO_TABLE4,
    asmr_from_bands,
    corrected_frame,
    percentile,
    verify_history,
    weights,
)


def test_who_table4_exact_and_normalized():
    assert WHO_TABLE4 == (
        "8.86",
        "8.69",
        "8.60",
        "8.47",
        "8.22",
        "7.93",
        "7.61",
        "7.15",
        "6.59",
        "6.04",
        "5.37",
        "4.55",
        "3.72",
        "2.96",
        "2.21",
        "1.52",
        "0.91",
        "0.44",
        "0.15",
        "0.04",
        "0.005",
    )
    assert sum(map(Decimal, WHO_TABLE4[16:])) == Decimal("1.545")
    assert sum(map(Decimal, WHO_TABLE4)) == Decimal("100.035")
    assert "0.23" not in WHO_TABLE4
    assert weights().sum() == pytest.approx(1, abs=1e-15)
    assert weights()[-1] == float(Decimal("1.545") / Decimal("100.035"))


def test_terminal_deaths_denominator_used_once():
    idx = pd.MultiIndex.from_product([["11001"], range(17)], names=["health_region_code", "band"])
    population = pd.Series(1000, index=idx)
    deaths = pd.Series(0, index=idx)
    deaths.loc[("11001", 16)] = 650 + 352 + 143
    result = asmr_from_bands(deaths, population)
    assert result.iloc[0] == pytest.approx(1145 / 1000 * 100000 * weights()[-1])


def test_duplicate_age_denominator_rejected():
    idx = pd.MultiIndex.from_tuples(
        [("11001", 16), ("11001", 16)], names=["health_region_code", "band"]
    )
    with pytest.raises(ValueError, match="Duplicate"):
        asmr_from_bands(pd.Series([1, 2], index=idx), pd.Series([100, 100], index=idx))


def test_percentile_ties_and_missing():
    assert np.allclose(percentile(pd.Series([1, 1, 3])).to_numpy(), [0.25, 0.25, 1])
    assert pd.isna(percentile(pd.Series([1, np.nan])).iloc[1])


def test_correction_changes_only_expected_fields():
    old = pd.DataFrame(
        {
            "health_region_code": ["a", "b"],
            "release_id": ["old"] * 2,
            "method_version": ["old"] * 2,
            "suicide_asmr": [1.0, 2.0],
            "suicide_percentile": [0.0, 1.0],
            "suicide_deaths": [10, 20],
            "psychiatric_admission_percentile": [0.1, 0.9],
            "capacity_score": [0.2, 0.8],
            "need_score": [0.05, 0.95],
            "mismatch_score": [-0.15, 0.15],
        }
    )
    new = corrected_frame(old, pd.Series([3.0, 2.0], index=["a", "b"]))
    for col in ["suicide_deaths", "psychiatric_admission_percentile", "capacity_score"]:
        pd.testing.assert_series_equal(old[col], new[col])
    assert np.allclose(new.need_score, [0.55, 0.45])
    assert np.allclose(new.mismatch_score, [0.35, -0.35])
    assert old.release_id.eq("old").all()


def test_historical_bytes_preserved():
    assert len(verify_history()) == 5


def test_actual_corrected_release_invariants():
    old = pd.read_parquet(ROOT / f"data/canonical/{OLD}/health_regions.parquet")
    new = pd.read_parquet(ROOT / f"data/canonical/{NEW}/health_regions.parquet")
    assert len(new) == new.health_region_code.nunique() == 439
    for col in [
        "suicide_deaths",
        "psychiatric_admissions",
        "psychiatric_admission_rate",
        "psychiatric_admission_percentile",
        "capacity_score",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
    ]:
        pd.testing.assert_series_equal(old[col], new[col], check_exact=True)
    assert (
        np.max(
            np.abs(
                new.need_score - (new.suicide_percentile + new.psychiatric_admission_percentile) / 2
            )
        )
        <= 1e-12
    )
    assert np.max(np.abs(new.mismatch_score - (new.need_score - new.capacity_score))) <= 1e-12
    qc = json.loads((AUDIT / "age_source_qc.json").read_text())
    assert qc["restored_85plus_deaths"] == 495
    assert qc["unknown_age_excluded"] == 33
    assert new.lisa_significant.sum() == 136
    assert new.lisa_cluster.value_counts().to_dict() == {
        "not_significant": 303,
        "high-high": 60,
        "low-low": 65,
        "high-low": 5,
        "low-high": 6,
    }


def test_corrected_determinism_and_rounding():
    result = json.loads((AUDIT / "determinism.json").read_text())
    assert result["status"] == "PASS" and result["mismatches"] == []
    rounding = json.loads((AUDIT / "who_rounding_sensitivity.json").read_text())
    assert rounding["lisa_membership_difference"] == rounding["lisa_label_difference"] == 0


def test_manuscript_impact_is_quantified_and_not_sent():
    doc = (ROOT / "docs/health_and_place_scientific_correction_impact_2026-08-31.md").read_text()
    for value in [
        "0.5256454566660947",
        "0.0001",
        "136",
        "60",
        "8.794678614973424",
        "AM, PE, MT, MG, SP",
        "MODERATE_RESULT_SET_CHANGE",
        "JOURNAL_ACTION_REQUIRED: YES",
    ]:
        assert value in doc
    assert "No contact, email, manuscript upload or portal action was performed" in doc
    assert "provisional display" not in doc

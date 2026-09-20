import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi import HTTPException

from api.services.advanced import historical_regions

ROOT = Path(__file__).resolve().parents[1]


class FrozenDatabase:
    def rows(self, query, params):
        assert "analytics.health_region_temporal" in query
        assert "t.year=%s" in query
        assert params[-2] == "MDB_TEMPORAL_2022_2024_1"
        frame = pd.read_parquet(
            ROOT / "web/public/releases/MDB_OPEN_DATA_2024_1/health_region_temporal.parquet"
        )
        frame = frame[frame.year == params[-1]]
        self.expected = json.loads(frame.to_json(orient="records", double_precision=15))
        return [
            {"values": r, "geometry": {"type": "Polygon", "coordinates": []}} for r in self.expected
        ]


@pytest.mark.parametrize("year", [2022, 2023, 2024])
@pytest.mark.parametrize("geometry", [False, True])
def test_frozen_observations_are_returned_without_recalculation(year, geometry):
    db = FrozenDatabase()
    result = historical_regions(db, year, "mismatch_score", geometry)
    assert result["reference_year"] == year
    assert result["count"] == 439
    assert result["records"] == db.expected
    if geometry:
        assert result["geometry"]["reference_year"] == year
        assert len(result["geometry"]["features"]) == 439
        for feature, record in zip(result["geometry"]["features"], db.expected, strict=True):
            assert feature["properties"]["value"] == record["mismatch_score"]
            assert "lisa_cluster" not in feature["properties"]


@pytest.mark.parametrize("year", [2021, 2025, 2026])
def test_unsupported_year_has_no_silent_fallback(year):
    with pytest.raises(HTTPException) as error:
        historical_regions(FrozenDatabase(), year, "mismatch_score", False)
    assert error.value.status_code == 422


def test_incomplete_anchor_fails_closed():
    class EmptyDatabase:
        def rows(self, *_):
            return []

    with pytest.raises(HTTPException) as error:
        historical_regions(EmptyDatabase(), 2022, "mismatch_score", False)
    assert error.value.status_code == 503


def test_multiple_regions_have_different_real_values_in_each_year():
    values = {}
    for year in (2022, 2023, 2024):
        result = historical_regions(FrozenDatabase(), year, "mismatch_score", False)
        values[year] = {r["health_region_code"]: r for r in result["records"]}
    for code in ("11001", "26003", "26004"):
        assert len({values[y][code]["mismatch_score"] for y in values}) == 3

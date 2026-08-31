import json
from pathlib import Path

import pandas as pd

from scripts.fetch_siops_official_api import parse_brl

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl"
FINANCING = ROOT / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_financing.parquet"


def test_locale_safe_currency_parser():
    assert parse_brl("R$ 1.477,32") == 1477.32
    assert parse_brl("31.753.563,38") == 31753563.38


def test_snapshot_is_unique_and_missing_is_not_zero():
    rows = [json.loads(line) for line in SNAPSHOT.open() if line.strip()]
    keys = [(row["municipality"], int(row["year"])) for row in rows]
    assert len(rows) == 16710
    assert len(set(keys)) == len(keys)
    assert sum(row["status"] == "ok" for row in rows) == 16703
    assert all(row.get("status") == "ok" or "group 17 TOTAL absent" in row["error"] for row in rows)


def test_financing_output_has_explicit_partial_coverage():
    frame = pd.read_parquet(FINANCING)
    assert len(frame) == 1317
    assert frame.health_region_code.nunique() == 439
    assert frame.year.nunique() == 3
    assert frame.headline_available.sum() == 1310
    assert frame.loc[~frame.headline_available, "total_health_expenditure_brl"].isna().all()
    assert frame.loc[~frame.headline_available, "quality_flags"].eq("PARTIAL_SIOPS_COVERAGE").all()

"""Validate public DB views against the locked open-data projections."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

from scripts.build_open_data_release import public_frame, semantic_fingerprint
from scripts.load_serving_database import connect
from scripts.open_platform_spec import ANALYTICAL_RELEASE, DATASETS

VIEW_QUERIES = {
    "health_regions_current": (
        "v_public_health_regions_current",
        "WHERE release_id = %s",
        (ANALYTICAL_RELEASE,),
    ),
    "health_region_temporal": ("v_public_temporal", "", ()),
    "health_region_changes": ("v_public_changes", "", ()),
    "health_region_financing": ("v_public_financing", "", ()),
    "health_region_flow_summary": ("v_public_flow_summary", "", ()),
    "hospitalization_flows_public": ("v_public_flow_edges", "", ()),
    "municipality_health_region_crosswalk": ("v_public_municipality_crosswalk", "", ()),
    "health_region_peers": ("v_public_peers", "WHERE release_id = %s", (ANALYTICAL_RELEASE,)),
}


def normalize(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in output.columns:
        output[column] = output[column].map(
            lambda value: (
                "|".join(map(str, value))
                if isinstance(value, list)
                else float(value)
                if isinstance(value, Decimal)
                else value
            )
        )
    return output.astype(object).where(pd.notna(output), None)


def validate() -> dict:
    results = {}
    with connect() as connection:
        for name, (view, where, params) in VIEW_QUERIES.items():
            source = public_frame(name, DATASETS[name])
            columns = list(source.columns)
            selected = ",".join(f'"{column}"' for column in columns)
            sql = f"SELECT {selected} FROM serving.{view} {where}"
            rows = connection.execute(sql, params).fetchall()
            database = pd.DataFrame(rows, columns=columns)
            database = database.sort_values(
                DATASETS[name]["key"], kind="stable"
            ).reset_index(drop=True)
            pd.testing.assert_frame_equal(
                normalize(database), normalize(source), check_dtype=False, rtol=1e-13
            )
            results[name] = {
                "rows": len(database),
                "semantic_sha256": semantic_fingerprint(source),
                "status": "PASS",
            }
        columns = {
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'serving' AND table_name LIKE 'v_public_%'"
            ).fetchall()
        }
    forbidden = sorted(
        columns
        & {"suicide_deaths", "suppressed", "raw_count", "original_count", "hidden_count"}
    )
    if forbidden:
        raise AssertionError(f"Forbidden public DB columns: {forbidden}")
    return {"status": "PASS", "views": results, "forbidden_columns": forbidden}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    result = validate()
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

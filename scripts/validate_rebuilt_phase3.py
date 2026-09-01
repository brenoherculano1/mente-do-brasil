"""Validate complete Phase 3 rebuild and source-to-serving advanced identity."""

import hashlib
import json
from collections.abc import Mapping
from decimal import Decimal

import pandas as pd
from psycopg.rows import dict_row

from scripts.audit_phase3_recovery import database_checks
from scripts.build_advanced_temporal import OUT
from scripts.load_advanced_territorial import EXPECTED, PRODUCTS, product_records
from scripts.load_serving_database import connect


def normalized(value):
    if hasattr(value, "obj"):
        return normalized(value.obj)
    if isinstance(value, Mapping):
        return {key: normalized(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [normalized(item) for item in value]
    if isinstance(value, float):
        return None if pd.isna(value) else value
    if isinstance(value, Decimal):
        return float(value)
    return value


def digest(records):
    payload = json.dumps(normalized(records), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def serving_projection(table, records):
    if table == "hospitalization_flows":
        projected = []
        for record in records:
            item = dict(record)
            item["admissions"] = None if item["admissions"] is None else int(item["admissions"])
            projected.append(item)
        return projected
    if table != "health_region_financing":
        return records
    projected = []
    for record in records:
        item = dict(record)
        for column in ("total_health_expenditure_brl", "health_expenditure_per_capita_brl"):
            value = item[column]
            item[column] = None if pd.isna(value) else round(float(value), 2)
        projected.append(item)
    return projected


def advanced_identity(connection):
    results = {}
    key_columns = {
        "health_region_temporal": ("year", "health_region_code"),
        "health_region_changes": ("from_year", "to_year", "health_region_code"),
        "health_region_financing": ("year", "health_region_code"),
        "hospitalization_flows": ("contribution_id",),
        "health_region_flow_summary": ("health_region_code",),
    }
    for version, names in PRODUCTS.items():
        for table in names:
            frame = pd.read_parquet(OUT / f"{table}.parquet")
            source = serving_projection(table, list(product_records(table, frame)))
            columns = list(source[0])
            version_column = next(
                name
                for name in columns
                if name.endswith("_version") and name != "geography_version"
            )
            query = (
                f"SELECT {','.join(columns)} FROM analytics.{table} "
                f"WHERE {version_column}=%s ORDER BY {','.join(columns)}"
            )
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, (version,))
                database = list(cursor.fetchall())
            keys = key_columns[table]
            source_map = {tuple(row[key] for key in keys): normalized(row) for row in source}
            database_map = {tuple(row[key] for key in keys): normalized(row) for row in database}
            ordered_keys = sorted(source_map)
            source_hash = digest([source_map[key] for key in ordered_keys])
            database_hash = digest([database_map[key] for key in ordered_keys])
            if (
                len(source_map) != len(source)
                or len(database_map) != len(database)
                or set(source_map) != set(database_map)
                or any(source_map[key] != database_map[key] for key in ordered_keys)
                or len(source) != EXPECTED[table]
            ):
                raise AssertionError(
                    f"Advanced content mismatch: {table}; source={source_hash}; db={database_hash}"
                )
            results[table] = {
                "rows": len(database),
                "source_content_sha256": source_hash,
                "database_content_sha256": database_hash,
                "serving_projection": (
                    "NUMERIC(20,2) quantization"
                    if table == "health_region_financing"
                    else "BIGINT cast"
                    if table == "hospitalization_flows"
                    else "identity"
                ),
                "status": "PASS",
            }
    return results


def main() -> None:
    with connect() as connection:
        checks = database_checks(connection)
        identity = advanced_identity(connection)
        release_ids = [
            row[0]
            for row in connection.execute(
                "SELECT release_id FROM meta.releases ORDER BY release_id"
            ).fetchall()
        ]
        if release_ids != ["MDB_ANALYTICAL_2024_1", "MDB_ANALYTICAL_2024_2"]:
            raise AssertionError(f"Release set mismatch: {release_ids}")
    print(json.dumps({"status": "PASS", "checks": checks, "advanced_identity": identity}, indent=2))


if __name__ == "__main__":
    main()

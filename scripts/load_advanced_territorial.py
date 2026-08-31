"""Transactional immutable loading of frozen advanced territorial products."""

import hashlib
import json

import pandas as pd
from psycopg import sql
from psycopg.types.json import Jsonb

from scripts.build_advanced_temporal import CURRENT, OUT, ROOT
from scripts.load_serving_database import apply_migrations, connect, sha256_file

GEOGRAPHY = "BR_HEALTH_REGIONS_END2024_V1"
PRODUCTS = {
    "MDB_TEMPORAL_2022_2024_1": ["health_region_temporal"],
    "MDB_CHANGE_RADAR_RULESET_1.0": ["health_region_changes"],
    "MDB_FINANCING_CONTEXT_1.0": ["health_region_financing"],
    "MDB_HOSPITAL_FLOW_METHOD_1.0": ["hospitalization_flows", "health_region_flow_summary"],
}
EXPECTED = dict(
    zip(
        [
            "health_region_temporal",
            "health_region_changes",
            "health_region_financing",
            "hospitalization_flows",
            "health_region_flow_summary",
        ],
        [1317, 1317, 1317, 20907, 439],
        strict=True,
    )
)


def product_records(table, frame):
    records = json.loads(frame.to_json(orient="records", double_precision=15))
    for item in records:
        if table == "health_region_financing":
            item["quality_flags"] = [f for f in item["quality_flags"].split("|") if f]
            yield item
        elif table == "hospitalization_flows":
            yield {**item, "geography_version": GEOGRAPHY}
        else:
            keys = {
                "health_region_temporal": ["temporal_version", "release_id", "year"],
                "health_region_changes": [
                    "change_version",
                    "from_year",
                    "to_year",
                    "matched_change_families",
                ],
                "health_region_flow_summary": ["flow_version"],
            }[table]
            yield {
                **{k: item[k] for k in keys},
                "health_region_code": item["health_region_code"],
                "geography_version": GEOGRAPHY,
                "values": Jsonb(item),
            }


def load():
    products = {}
    for version, names in PRODUCTS.items():
        files = {name: sha256_file(OUT / f"{name}.parquet") for name in names}
        digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
        frames = {name: pd.read_parquet(OUT / f"{name}.parquet") for name in names}
        for name, frame in frames.items():
            if len(frame) != EXPECTED[name]:
                raise ValueError(f"Invalid product count: {name}")
        products[version] = (files, digest, frames)
    modes = {}
    with connect() as connection:
        with connection.transaction():
            apply_migrations(connection, ROOT)
            connection.execute("SELECT pg_advisory_xact_lock(20260831, 3)")
            for version, (files, digest, frames) in products.items():
                existing = connection.execute(
                    "SELECT content_sha256 FROM meta.advanced_versions WHERE version_id=%s",
                    (version,),
                ).fetchone()
                if existing and existing[0] != digest:
                    raise ValueError(f"IMMUTABILITY VIOLATION: {version}")
                modes[version] = "IDENTICAL_RELOAD" if existing else "NEW_LOAD"
                connection.execute(
                    "INSERT INTO meta.advanced_versions(version_id,release_id,content_sha256,files) "
                    "VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (version, CURRENT, digest, Jsonb(files)),
                )
                for table, frame in frames.items():
                    records = list(product_records(table, frame))
                    columns = list(records[0])
                    command = sql.SQL(
                        "INSERT INTO analytics.{} ({}) VALUES ({}) ON CONFLICT DO NOTHING"
                    ).format(
                        sql.Identifier(table),
                        sql.SQL(",").join(map(sql.Identifier, columns)),
                        sql.SQL(",").join(sql.Placeholder(c) for c in columns),
                    )
                    with connection.cursor() as cursor:
                        cursor.executemany(command, records)
                    version_column = next(
                        c for c in columns if c.endswith("_version") and c != "geography_version"
                    )
                    count = connection.execute(
                        sql.SQL("SELECT count(*) FROM analytics.{} WHERE {}=%s").format(
                            sql.Identifier(table), sql.Identifier(version_column)
                        ),
                        (version,),
                    ).fetchone()[0]
                    if count != EXPECTED[table]:
                        raise ValueError(f"Serving count mismatch: {table}")
    return {"status": "PASS", "modes": modes, "counts": EXPECTED}


if __name__ == "__main__":
    print(json.dumps(load(), indent=2))

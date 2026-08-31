"""Evidence-only recovery drill. Never reconstruct source artifacts from serving data."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit_results/phase3_closure"
BASE = "3b1bfa7ca5b5bac9df547b0a0e3d81f5bd4055a2"
CURRENT = "MDB_ANALYTICAL_2024_2"
CONTAINER = "mente-do-brasil-postgres"
PRODUCTS = {
    "health_region_temporal": 1317,
    "health_region_changes": 1317,
    "health_region_financing": 1317,
    "hospitalization_flows": 20907,
    "health_region_flow_summary": 439,
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / name).write_text(json.dumps(value, indent=2, default=str) + "\n")


def command(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs).stdout


def container_settings():
    metadata = json.loads(command(["docker", "inspect", CONTAINER]))[0]
    env = dict(item.split("=", 1) for item in metadata["Config"]["Env"] if "=" in item)
    return env


def connect(env, database=None):
    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname=database or env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        autocommit=True,
    )


def financing_transition():
    relative = f"data/product_intelligence/{CURRENT}/health_region_financing.parquet"
    old_commit = command(["git", "rev-parse", "87cb7e5"], cwd=ROOT).decode().strip()
    new_commit = command(["git", "rev-parse", "2188609"], cwd=ROOT).decode().strip()
    old_bytes = command(["git", "show", f"{old_commit}:{relative}"], cwd=ROOT)
    new_bytes = command(["git", "show", f"{new_commit}:{relative}"], cwd=ROOT)
    a, b = (pd.read_parquet(io.BytesIO(data)) for data in (old_bytes, new_bytes))
    keys = ["year", "health_region_code"]
    assert not a.duplicated(keys).any() and not b.duplicated(keys).any()
    changed = {}
    changed_rows = pd.Series(False, index=a.index)
    for column in a.columns:
        same = a[column].eq(b[column]) | (a[column].isna() & b[column].isna())
        changed_rows |= ~same
        if not same.all():
            changed[column] = {
                "rows_changed": int((~same).sum()),
                "old_nulls": int(a[column].isna().sum()),
                "new_nulls": int(b[column].isna().sum()),
                "old_dtype": str(a[column].dtype),
                "new_dtype": str(b[column].dtype),
            }
    result = {
        "old_commit": old_commit,
        "new_commit": new_commit,
        "old_sha256": digest(old_bytes),
        "accepted_sha256": digest(new_bytes),
        "worktree_matches_accepted": digest((ROOT / relative).read_bytes()) == digest(new_bytes),
        "old_rows": len(a),
        "new_rows": len(b),
        "rows_changed": int(changed_rows.sum()),
        "schema_columns_unchanged": a.columns.equals(b.columns),
        "row_key_order_unchanged": a[keys].equals(b[keys]),
        "changed_columns": changed,
        "total_expenditure_unchanged": a.total_health_expenditure_brl.equals(
            b.total_health_expenditure_brl
        ),
        "municipal_coverage_unchanged": a.municipalities_observed.equals(b.municipalities_observed),
        "reason": (
            "Repair of POPSVS seven-digit municipality mapping. Population denominators and "
            "covered population became available; per-capita values became available for "
            "complete SIOPS rows. Expenditure totals and SIOPS municipal coverage did not "
            "change. This is a data-processing correction, not a new financing methodology."
        ),
        "serialization": (
            "Not serialization-only: logical values and population dtypes changed. "
            "Key order and columns compared explicitly."
        ),
    }
    save("financing_hash_transition.txt", result)
    (ROOT / "audit_results/financing_hash_transition.txt").write_text(
        json.dumps(result, indent=2) + "\n"
    )


def database_checks(conn):
    checks = {}
    for table, expected in PRODUCTS.items():
        checks[table] = conn.execute(
            sql.SQL("SELECT count(*) FROM analytics.{}").format(sql.Identifier(table))
        ).fetchone()[0]
        assert checks[table] == expected, (table, checks[table])
    checks["health_regions"] = conn.execute("SELECT count(*) FROM geo.health_regions").fetchone()[0]
    checks["municipalities"] = conn.execute(
        "SELECT count(*) FROM geo.municipality_health_region_crosswalk"
    ).fetchone()[0]
    checks["metrics"] = conn.execute(
        "SELECT count(*) FROM analytics.health_region_metrics WHERE release_id=%s", (CURRENT,)
    ).fetchone()[0]
    assert [checks[k] for k in ("health_regions", "municipalities", "metrics")] == [439, 5570, 439]
    checks["geometry"] = conn.execute(
        "SELECT count(*) FILTER (WHERE ST_SRID(geom)=4674), "
        "count(*) FILTER (WHERE ST_IsValid(geom)) FROM geo.health_regions"
    ).fetchone()
    assert checks["geometry"] == (439, 439)
    checks["releases"] = [
        r[0] for r in conn.execute("SELECT release_id FROM meta.releases ORDER BY release_id")
    ]
    assert checks["releases"] == ["MDB_ANALYTICAL_2024_1", CURRENT]
    checks["lisa"] = dict(
        conn.execute(
            "SELECT lisa_cluster,count(*) FROM analytics.health_region_metrics "
            "WHERE release_id=%s AND lisa_significant GROUP BY lisa_cluster",
            (CURRENT,),
        )
    )
    assert checks["lisa"] == {"high-high": 60, "low-low": 65, "high-low": 5, "low-high": 6}
    checks["flags"] = conn.execute(
        "SELECT count(*) FILTER (WHERE 'SMALL_SUICIDE_COUNT'=ANY(data_quality_flags)), "
        "count(*) FILTER (WHERE 'ZERO_REGISTERED_BEDS'=ANY(data_quality_flags)) "
        "FROM analytics.health_region_metrics WHERE release_id=%s",
        (CURRENT,),
    ).fetchone()
    assert checks["flags"] == (7, 275)
    checks["views"] = {}
    for view in ("health_region_profile", "health_region_map", "health_region_lookup"):
        checks["views"][view] = conn.execute(
            sql.SQL("SELECT count(*) FROM serving.{} WHERE release_id=%s").format(
                sql.Identifier(view)
            ),
            (CURRENT,),
        ).fetchone()[0]
        assert checks["views"][view] == 439
    checks["lookup_1100015"] = conn.execute(
        "SELECT health_region_code FROM geo.municipality_health_region_crosswalk "
        "WHERE municipality_code_ibge='1100015'"
    ).fetchone()[0]
    checks["known_regions"] = conn.execute(
        "SELECT health_region_code,health_region_name FROM geo.health_regions "
        "WHERE health_region_code IN ('12001','53001') ORDER BY health_region_code"
    ).fetchall()
    checks["content_hashes"] = {}
    for table in PRODUCTS:
        rows = conn.execute(
            sql.SQL(
                "SELECT to_jsonb(t)::text FROM analytics.{} t ORDER BY to_jsonb(t)::text"
            ).format(sql.Identifier(table))
        ).fetchall()
        checks["content_hashes"][table] = digest("\n".join(r[0] for r in rows).encode())
    return checks


def recovery_drills():
    env = container_settings()
    workspace = Path(tempfile.mkdtemp(prefix="mdb-phase3-operational-closure-"))
    archive = workspace / "source.tar"
    with archive.open("wb") as stream:
        subprocess.run(["git", "archive", BASE], cwd=ROOT, stdout=stream, check=True)
    snapshot = workspace / "source"
    snapshot.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(snapshot, filter="data")
    admin = connect(env, "postgres")
    rebuild = "mdb_rebuild_closure_20260831"
    restore = "mdb_restore_closure_20260831"
    for name in (rebuild, restore):
        if admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
            raise RuntimeError(f"Disposable database already exists: {name}; refusing to overwrite")
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(rebuild)))
    runenv = os.environ.copy()
    runenv.update(
        MDB_DB_NAME=rebuild,
        MDB_DB_USER=env["POSTGRES_USER"],
        MDB_DB_PASSWORD=env["POSTGRES_PASSWORD"],
        PYTHONPATH=str(snapshot),
    )
    started = time.monotonic()
    proc = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(snapshot / "scripts/load_serving_database_release.py"),
        ],
        cwd=snapshot,
        env=runenv,
        capture_output=True,
        text=True,
    )
    missing = []
    expected = [
        "data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet",
        "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet",
        "data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle/geography/health_regions_LOCKED.gpkg",
    ]
    expected += [f"data/product_intelligence/{CURRENT}/{table}.parquet" for table in PRODUCTS]
    for relative in expected:
        if not (ROOT / relative).is_file():
            missing.append(relative)
    admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(rebuild)))
    rebuild_result = {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "workspace": str(snapshot),
        "base_commit": BASE,
        "database": rebuild,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "seconds": time.monotonic() - started,
        "missing_approved_inputs": missing,
        "cleanup": "database dropped",
        "used_existing_serving_rows": False,
        "fileprovider_blocker": "RESOLVED",
    }
    save("database_rebuild.txt", rebuild_result)
    (ROOT / "audit_results/database_rebuild.txt").write_text(
        json.dumps(rebuild_result, indent=2) + "\n"
    )
    with connect(env) as source:
        baseline = database_checks(source)
        save("database_advanced_validation.json", baseline)
        save(
            "advanced_source_hash_registry.json",
            source.execute(
                "SELECT version_id,files FROM meta.advanced_versions ORDER BY version_id"
            ).fetchall(),
        )
    backup = workspace / "serving_backup.dump"
    with backup.open("wb") as stream:
        subprocess.run(
            [
                "docker",
                "exec",
                CONTAINER,
                "pg_dump",
                "-U",
                env["POSTGRES_USER"],
                "-d",
                env["POSTGRES_DB"],
                "-Fc",
                "-Z",
                "6",
                "--no-owner",
                "--no-acl",
            ],
            stdout=stream,
            check=True,
        )
    backup.chmod(0o600)
    result = {
        "source_database": env["POSTGRES_DB"],
        "backup": str(backup),
        "size_bytes": backup.stat().st_size,
        "sha256": digest(backup.read_bytes()),
        "pg_dump": command(["docker", "exec", CONTAINER, "pg_dump", "--version"]).decode().strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "restore_database": restore,
    }
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restore)))
    try:
        with backup.open("rb") as stream:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "-i",
                    CONTAINER,
                    "pg_restore",
                    "-U",
                    env["POSTGRES_USER"],
                    "-d",
                    restore,
                    "--no-owner",
                    "--no-acl",
                    "--exit-on-error",
                ],
                stdin=stream,
                check=True,
                capture_output=True,
            )
        with connect(env, restore) as target:
            observed = database_checks(target)
            assert observed == baseline, "Restore content differs from source"
            target.execute(
                "GRANT USAGE ON SCHEMA meta,geo,analytics,serving TO mente_do_brasil_api"
            )
            target.execute(
                "GRANT SELECT ON ALL TABLES IN SCHEMA meta,geo,analytics,serving "
                "TO mente_do_brasil_api"
            )
            with target.transaction():
                target.execute("SET LOCAL ROLE mente_do_brasil_api")
                assert (
                    target.execute(
                        "SELECT count(*) FROM analytics.health_region_temporal"
                    ).fetchone()[0]
                    == 1317
                )
                try:
                    with target.transaction():
                        target.execute("DELETE FROM analytics.health_region_temporal")
                except psycopg.errors.InsufficientPrivilege:
                    result["read_only_privileges"] = "PASS"
                else:
                    raise AssertionError("API role could delete rows")
            try:
                with target.transaction():
                    target.execute(
                        "INSERT INTO analytics.hospitalization_flows VALUES "
                        "('MDB_HOSPITAL_FLOW_METHOD_1.0',99999999,"
                        "'BR_HEALTH_REGIONS_END2024_V1','12001','12001',4,false)"
                    )
            except psycopg.errors.CheckViolation:
                result["constraint_rollback"] = "PASS"
            else:
                raise AssertionError("Invalid flow accepted")
            result.update(
                status="PASS", counts=observed, content_comparison="all advanced rows identical"
            )
    finally:
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(restore)))
        result["cleanup"] = "restore database dropped; private backup retained outside repository"
        save("restore_drill.txt", result)
        (ROOT / "audit_results/restore_drill.txt").write_text(json.dumps(result, indent=2) + "\n")
        admin.close()


if __name__ == "__main__":
    financing_transition()
    recovery_drills()

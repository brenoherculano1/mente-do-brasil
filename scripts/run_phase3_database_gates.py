"""Run final idempotence, immutability, constraint and runtime-role gates."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from scripts.audit_phase3_recovery import database_checks
from scripts.load_serving_database import connect

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "data/product_intelligence/MDB_ANALYTICAL_2024_2"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(script):
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / script)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def idempotence():
    with connect() as connection:
        before = database_checks(connection)
    outputs = {
        name: command(name)
        for name in (
            "scripts/load_serving_database.py",
            "scripts/load_serving_database_release.py",
            "scripts/load_advanced_territorial.py",
        )
    }
    with connect() as connection:
        after = database_checks(connection)
    if before != after or "PASS / NO CHANGE" not in outputs["scripts/load_serving_database.py"]:
        raise AssertionError("Idempotent reload changed serving content")
    if "IDENTICAL_RELOAD" not in outputs["scripts/load_advanced_territorial.py"]:
        raise AssertionError("Advanced products did not report identical reload")
    return {"status": "PASS", "before": before, "after": after, "loader_outputs": outputs}


def immutability():
    from scripts import load_advanced_territorial as loader

    files = sorted(ADVANCED.glob("*.parquet"))
    original_hashes = {path.name: sha256(path) for path in files}
    with connect() as connection:
        before = database_checks(connection)
    with tempfile.TemporaryDirectory(prefix="mdb-immutability-") as directory:
        temporary = Path(directory)
        for path in files:
            shutil.copyfile(path, temporary / path.name)
        changed = temporary / "health_region_temporal.parquet"
        frame = pd.read_parquet(changed)
        frame.loc[0, "need_score"] += 0.001
        frame.to_parquet(changed, index=False)
        prior = loader.OUT
        loader.OUT = temporary
        try:
            try:
                loader.load()
            except ValueError as error:
                message = str(error)
                if "IMMUTABILITY VIOLATION" not in message:
                    raise
            else:
                raise AssertionError("Changed immutable artifact was accepted")
        finally:
            loader.OUT = prior
    with connect() as connection:
        after = database_checks(connection)
    final_hashes = {path.name: sha256(path) for path in files}
    if before != after or original_hashes != final_hashes:
        raise AssertionError("Immutability attempt changed accepted content")
    return {
        "status": "PASS",
        "rejection": message,
        "rollback": before == after,
        "original_files_unchanged": original_hashes == final_hashes,
    }


def constraints_and_role():
    checks = {}
    with connect() as connection:
        tests = {
            "invalid_temporal_year": (
                "INSERT INTO analytics.health_region_temporal "
                "SELECT temporal_version,release_id,geography_version,health_region_code,"
                "2025,values "
                "FROM analytics.health_region_temporal LIMIT 1"
            ),
            "invalid_financing_coverage": (
                "INSERT INTO analytics.health_region_financing "
                "SELECT financing_version,siops_snapshot_id,year+100,health_region_code,1,2,"
                "population_expected,population_covered,coverage_share,coverage_population_share,"
                "total_health_expenditure_brl,health_expenditure_per_capita_brl,headline_available,"
                "quality_flags,source_period,source_indicator "
                "FROM analytics.health_region_financing WHERE headline_available LIMIT 1"
            ),
        }
        for name, statement in tests.items():
            try:
                with connection.transaction():
                    connection.execute(statement)
            except Exception as error:  # noqa: BLE001 - expected database rejection
                checks[name] = {"status": "PASS", "rejected_by": type(error).__name__}
            else:
                raise AssertionError(f"Invalid constraint insert succeeded: {name}")
        try:
            with connection.transaction():
                connection.execute("SET LOCAL ROLE mente_do_brasil_api")
                connection.execute("DELETE FROM analytics.health_region_financing")
        except Exception as error:  # noqa: BLE001 - expected privilege rejection
            checks["runtime_read_only"] = {"status": "PASS", "rejected_by": type(error).__name__}
        else:
            raise AssertionError("Runtime role performed a write")
        count = connection.execute(
            "SELECT count(*) FROM analytics.health_region_financing"
        ).fetchone()[0]
    if count != 1317:
        raise AssertionError("Rollback did not preserve financing rows")
    return {"status": "PASS", "checks": checks, "financing_rows_after": count}


def main():
    results = {
        "idempotence": idempotence(),
        "immutability": immutability(),
        "constraints_and_runtime_role": constraints_and_role(),
    }
    (ROOT / "audit_results/phase3_database_final_gates.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    print(json.dumps({key: value["status"] for key, value in results.items()}, indent=2))


if __name__ == "__main__":
    main()

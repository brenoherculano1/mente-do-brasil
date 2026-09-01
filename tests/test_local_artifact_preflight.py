import hashlib
import json
import subprocess

import pytest

from scripts.preflight_local_artifacts import ROOT, inspect_artifacts
from scripts.recover_phase3_artifacts import copy_verified, fingerprint, safe_relative


def entry(path, data=b"locked"):
    return {"relative_path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def test_all_present_and_hashed(tmp_path):
    (tmp_path / "a").write_bytes(b"locked")
    result = inspect_artifacts(tmp_path, {"artifacts": [entry("a")]})
    assert result["status"] == "PASS"
    assert result["database_operations"] == 0


def test_lists_all_missing_mismatch_and_pending(tmp_path):
    (tmp_path / "bad").write_bytes(b"modified")
    (tmp_path / "candidate").write_bytes(b"locked")
    rows = [
        entry("missing_a"),
        entry("missing_b"),
        entry("bad"),
        {**entry("candidate"), "sha256": None, "acceptance_status": "PENDING"},
    ]
    result = inspect_artifacts(tmp_path, {"artifacts": rows})
    assert [r["status"] for r in result["failures"]] == [
        "MISSING",
        "MISSING",
        "HASH_OR_SIZE_MISMATCH",
        "PENDING_ACCEPTANCE",
    ]
    assert result["database_operations"] == 0


def test_fail_closed_invalid_paths_and_empty(tmp_path):
    for path in ("/outside", "../outside"):
        assert inspect_artifacts(tmp_path, {"artifacts": [entry(path)]})["status"] == "BLOCKED"
        with pytest.raises(ValueError):
            safe_relative(path)
    assert inspect_artifacts(tmp_path, {"artifacts": []})["status"] == "BLOCKED"


def test_rebuild_preflight_failure_cannot_reach_docker(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".venv/bin").mkdir(parents=True)
    script = tmp_path / "scripts/rebuild_serving_db.sh"
    script.write_bytes((ROOT / "scripts/rebuild_serving_db.sh").read_bytes())
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.write_text('#!/bin/sh\nprintf "ALL_MISSING_INPUTS\\n"\nexit 1\n')
    interpreter.chmod(0o700)
    fake_docker = tmp_path / "docker"
    fake_docker.write_text('#!/bin/sh\nprintf "DATABASE_MUTATION\\n"\nexit 99\n')
    fake_docker.chmod(0o700)
    completed = subprocess.run(
        ["/bin/bash", str(script), "mdb_rebuild_test"],
        env={"PATH": f"{tmp_path}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "ALL_MISSING_INPUTS" in completed.stdout
    assert "DATABASE_MUTATION" not in completed.stdout


def test_copy_hash_guard_and_existing_destination_preserved(tmp_path):
    source, dest = tmp_path / "source", tmp_path / "dest"
    source.write_bytes(b"locked")
    expected = fingerprint(source)
    copy_verified(source, dest, expected)
    assert fingerprint(dest) == expected
    assert copy_verified(source, dest, expected) == "ALREADY_IDENTICAL"
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        copy_verified(source, dest, expected)
    with pytest.raises(ValueError, match="will not overwrite"):
        copy_verified(source, dest, fingerprint(source))
    assert dest.read_bytes() == b"locked"


def test_current_inventory_reports_complete_known_blocker():
    inventory = json.loads(
        (ROOT / "metadata/provenance/required_local_artifacts_v1.json").read_text()
    )
    result = inspect_artifacts(ROOT, inventory)
    # Recovery may later be completed; no data-dependent skip is allowed.
    failures = {r["relative_path"]: r["status"] for r in result["failures"]}
    allowed = {"data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl": "PENDING_ACCEPTANCE"}
    allowed.update(
        {f"data/raw/scientific_correction_recovery/POPSBR{y}.zip": "MISSING" for y in (22, 23, 24)}
    )
    assert all(allowed.get(path) == status for path, status in failures.items())
    assert len(result["checked"]) == len(inventory["artifacts"])

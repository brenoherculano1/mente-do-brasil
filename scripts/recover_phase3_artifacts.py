"""Read-only allowlisted artifact recovery; never execute donor code."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path("data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle")
SNAPSHOT = "data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl"
LOCKS = {
    "data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet": (
        "a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515"
    ),
    "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet": (
        "acd7ab896566d5ea730719eb46a079b0571d73fec617ef1d39db93099bd06b15"
    ),
    "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_temporal.parquet": (
        "cb617db011ce192b22f2d0ae33315ca7ff59a6da16dbef8b5b0c03abc855a25a"
    ),
    "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_changes.parquet": (
        "dca6e4c778977745e9287ccc93717c081d853f30778a6afd31afe7610b672e68"
    ),
    "data/product_intelligence/MDB_ANALYTICAL_2024_2/hospitalization_flows.parquet": (
        "04eb3d4a967b9050c701b62026c4959c437ab8bf52e799c67546ff74c066ed27"
    ),
    "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_flow_summary.parquet": (
        "d2f66800f16f715e068cf60e01e1743d7cb64152268ced63b8b3ade2649134bf"
    ),
}
FINANCING_HASH = "09e6182fa527a73e53691c97d65e30e2fc6f2740fffdd36b0d09baa59e680860"


def fingerprint(path):
    with path.open("rb") as stream:
        return {
            "bytes": path.stat().st_size,
            "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
        }


def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe artifact path: {value}")
    return path


def copy_verified(source, destination, expected):
    observed = fingerprint(source)
    if observed != expected:
        raise ValueError(f"BLOCKED_ARTIFACT_HASH_MISMATCH: {source.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if fingerprint(destination) != expected:
            raise ValueError(f"Existing destination mismatch; will not overwrite: {destination}")
        return "ALREADY_IDENTICAL"
    fd, name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        shutil.copyfile(source, temporary)
        if fingerprint(temporary) != expected:
            raise ValueError(f"Copy verification failed: {destination.name}")
        temporary.rename(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return "SOURCE_HASH_TEMP_COPY_DEST_HASH_ATOMIC_RENAME"


def snapshot_semantics(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    keys = [(str(row["municipality"]), int(row["year"])) for row in rows]
    missing = [row for row in rows if row["status"] != "ok"]
    expected = {
        ("220045", 2022),
        *(("260545", y) for y in (2022, 2023, 2024)),
        *(("530010", y) for y in (2022, 2023, 2024)),
    }
    assert len(rows) == len(set(keys)) == 16710
    assert len(missing) == 7
    assert {(str(r["municipality"]), int(r["year"])) for r in missing} == expected
    assert all(r["status"] == "error" and "group 17 TOTAL absent" in r["error"] for r in missing)
    assert all(r.get("group17_total_brl") is None for r in missing)
    for row in rows:
        assert row["period"] == "2"
        assert row["endpoint"] == "http://siops.datasus.gov.br/consdetalhereenvio2.php"
        assert row.get("retrieved_at")
        if row["status"] == "ok":
            assert row["stage"] == "empenhada" and row["group"] == "17"
            assert len(row["response_sha256"]) == 64
            assert isinstance(row["group17_total_brl"], (int, float))
    return {
        "rows": len(rows),
        "successes": 16703,
        "missing": 7,
        "missing_keys": sorted(expected),
        "missing_not_zero": True,
        "semantic_validation": "PASS",
        "derived_reproduction": "PENDING",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor", type=Path, required=True)
    args = parser.parse_args()
    ledger = []
    audit = ROOT / "audit_results"

    def recover(relative, expected, status="PASS"):
        source, destination = args.donor / relative, ROOT / relative
        observed = fingerprint(source)
        row = {
            "relative_path": str(relative),
            "source_location": str(source),
            "source_bytes": observed["bytes"],
            "source_sha256": observed["sha256"],
            "expected_sha256": expected["sha256"] if status == "PASS" else None,
        }
        row["recovery_method"] = copy_verified(source, destination, expected)
        copied = fingerprint(destination)
        row.update(
            destination_bytes=copied["bytes"], destination_sha256=copied["sha256"], status=status
        )
        ledger.append(row)
        (audit / "phase3_artifact_recovery.txt").write_text(json.dumps(ledger, indent=2) + "\n")
        print(f"{status}: {relative}", flush=True)

    for relative, expected_hash in LOCKS.items():
        observed = fingerprint(args.donor / relative)
        recover(relative, {"bytes": observed["bytes"], "sha256": expected_hash})
    manifest_path = args.donor / BUNDLE / "IMPORT_MANIFEST.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    entries = manifest["files"]
    expected_paths = {safe_relative(e["path"]) for e in entries}
    assert len(expected_paths) == len(entries)
    actual = {
        p.relative_to(args.donor / BUNDLE) for p in (args.donor / BUNDLE).rglob("*") if p.is_file()
    }
    assert actual == expected_paths | {Path("IMPORT_MANIFEST.json")}, "Bundle unknown/missing files"
    for entry in entries:
        assert fingerprint(args.donor / BUNDLE / entry["path"]) == {
            "bytes": entry["bytes"],
            "sha256": entry["sha256"],
        }, entry["path"]
    by_path = {e["path"]: e for e in entries}
    assert (
        by_path["geography/health_regions_LOCKED.gpkg"]["sha256"]
        == "657355adb0df88dfcfff2400751eff6ae97b367effe8e90223d0267e0437ba48"
    )
    assert by_path["geography/health_regions_LOCKED.gpkg"]["bytes"] == 93306880
    assert (
        by_path["geography/health_region_crosswalk_LOCKED.csv"]["sha256"]
        == "71239b3c9ec6d08422273e950b1227e31fca856fa8ee7aedb69ac0f8157377cb"
    )
    # Copy nothing from the bundle until every listed source file has validated.
    for entry in entries:
        recover(BUNDLE / entry["path"], {"bytes": entry["bytes"], "sha256": entry["sha256"]})
    recover(
        BUNDLE / "IMPORT_MANIFEST.json",
        {"bytes": len(manifest_bytes), "sha256": hashlib.sha256(manifest_bytes).hexdigest()},
    )
    (audit / "phase3_import_bundle_validation.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "files_validated": len(entries),
                "source": "allowlisted_donor_directory",
                "zip_sha256_locked_reference": (
                    "3658182b92a90466bc27d6ce3252e796fd25b54f2023d3ac1abe6eb356f7c6cc"
                ),
                "zip_read_this_run": False,
                "files": entries,
            },
            indent=2,
        )
        + "\n"
    )
    semantics = snapshot_semantics(args.donor / SNAPSHOT)
    recover(SNAPSHOT, fingerprint(args.donor / SNAPSHOT), "PENDING_DERIVED_REPRODUCTION")
    assert snapshot_semantics(ROOT / SNAPSHOT) == semantics
    (audit / "phase3_siops_snapshot_validation.json").write_text(
        json.dumps(semantics, indent=2) + "\n"
    )
    assert (
        fingerprint(
            ROOT / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_financing.parquet"
        )["sha256"]
        == FINANCING_HASH
    )


if __name__ == "__main__":
    main()

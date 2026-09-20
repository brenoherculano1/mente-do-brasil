"""Read-only proof of historical preservation before/after the UI correction."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import psycopg
from psycopg.rows import dict_row

from api.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
VERSION = "MDB_TEMPORAL_2022_2024_1"


def audit():
    private = (
        ROOT / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_temporal.parquet"
    )
    public = ROOT / "web/public/releases/MDB_OPEN_DATA_2024_1/health_region_temporal.parquet"
    frame = pd.read_parquet(private)
    exported = pd.read_parquet(public)
    # Match the original immutable loader, not a new rounding policy.
    records = json.loads(frame.to_json(orient="records", double_precision=15))
    expected = {(r["year"], r["health_region_code"]): r for r in records}
    with psycopg.connect(get_settings().dsn, row_factory=dict_row) as db:
        rows = db.execute(
            'SELECT "values" FROM analytics.health_region_temporal WHERE temporal_version=%s',
            (VERSION,),
        ).fetchall()
        manifest = db.execute(
            "SELECT files FROM meta.advanced_versions WHERE version_id=%s", (VERSION,)
        ).fetchone()
    actual = {(r["values"]["year"], r["values"]["health_region_code"]): r["values"] for r in rows}
    assert len(rows) == len(actual) == len(expected) == 1317
    assert actual == expected, "Stored observations differ from original loader output"
    digest = hashlib.sha256(private.read_bytes()).hexdigest()
    assert manifest["files"]["health_region_temporal"] == digest
    for column in exported:
        original = frame[column].tolist()
        if column == "quality_flags":
            original = ["|".join(flags) for flags in original]
        assert exported[column].tolist() == original, column
    paths = [
        "web/public/releases/MDB_OPEN_DATA_2024_1/health_region_temporal.csv",
        "web/public/releases/MDB_OPEN_DATA_2024_1/health_region_temporal.parquet",
        "data/canonical/MDB_ANALYTICAL_2024_2/health_regions.parquet",
        "scripts/load_advanced_territorial.py",
    ]
    hashes = {}
    for path in paths:
        old = subprocess.check_output(["git", "show", f"119e06e^:{path}"], cwd=ROOT)
        current = (ROOT / path).read_bytes()
        assert current == old, path
        hashes[path] = hashlib.sha256(current).hexdigest()
    protected = subprocess.check_output(
        [
            "git",
            "diff",
            "119e06e^",
            "--name-only",
            "--",
            "data/canonical",
            "data/product_intelligence",
            "metadata/releases",
            "metadata/methods",
            "web/public/releases",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert not protected, protected
    counts = frame.groupby("year").size().to_dict()
    assert counts == {2022: 439, 2023: 439, 2024: 439}
    return {
        "status": "PASS",
        "starting_commit": "119e06e",
        "reference": "119e06e^",
        "temporal_version": VERSION,
        "counts": counts,
        "database_exact_loader_match": True,
        "private_manifest_sha256": digest,
        "unchanged_file_hashes": hashes,
        "protected_changes": protected,
        "precision_note": "Original pandas JSON double_precision=15 serialization; unchanged.",
        "geography": sorted(frame.geography_version.unique()),
        "sample_anchors": [
            r for r in records if r["health_region_code"] in ("11001", "26003", "26004")
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "sample_anchors"}, indent=2))

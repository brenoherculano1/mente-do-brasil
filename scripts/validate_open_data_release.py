"""Validate public release identity, privacy, rights, and package integrity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import yaml

from scripts.build_open_data_release import public_frame, semantic_fingerprint
from scripts.open_platform_spec import (
    DATASETS,
    FORBIDDEN_PUBLIC_FIELDS,
    OPEN_DATA_RELEASE,
    PUBLIC_RELEASE_DIR,
    ROOT,
)

FORBIDDEN_NAMES = re.compile(r"(?:\.env|POPSBR|\.dbc$|\.gpkg$|\.dump$|SIOPS.*\.jsonl$)", re.I)
PII_FIELDS = {"cpf", "cns", "name_patient", "patient_name", "address", "email", "phone"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(output: Path = PUBLIC_RELEASE_DIR) -> dict:
    manifest = json.loads((output / "MANIFEST.json").read_text())
    expected = {entry["relative_path"] for entry in manifest["files"]}
    actual = {path.name for path in output.iterdir() if path.is_file()} - {
        "MANIFEST.json",
        "CHECKSUMS.sha256",
    }
    missing, extra = expected - actual, actual - expected
    size_mismatches, hash_mismatches = [], []
    for entry in manifest["files"]:
        data = (output / entry["relative_path"]).read_bytes()
        if len(data) != entry["bytes"]:
            size_mismatches.append(entry["relative_path"])
        if digest(data) != entry["sha256"]:
            hash_mismatches.append(entry["relative_path"])
    identity = {}
    field_registry = yaml.safe_load(
        (ROOT / "metadata/open_platform/public_field_registry_v1.yaml").read_text()
    )
    registered = {(row["dataset"], row["field_name"]) for row in field_registry["fields"]}
    public_fields = set()
    for name, spec in DATASETS.items():
        source = public_frame(name, spec)
        string_columns = {
            column: "string"
            for column in source.columns
            if isinstance(source[column].dtype, pd.StringDtype) or source[column].dtype == object
        }
        csv_frame = pd.read_csv(
            output / f"{name}.csv", dtype=string_columns, dtype_backend="numpy_nullable"
        )
        parquet_frame = pd.read_parquet(output / f"{name}.parquet")
        assert list(csv_frame.columns) == list(parquet_frame.columns) == list(source.columns)
        assert len(csv_frame) == len(parquet_frame) == len(source)
        csv_normalized = csv_frame.astype(object).where(pd.notna(csv_frame), None)
        parquet_normalized = parquet_frame.astype(object).where(pd.notna(parquet_frame), None)
        source_normalized = source.astype(object).where(pd.notna(source), None)
        for column in string_columns:
            csv_normalized[column] = csv_normalized[column].fillna("")
            parquet_normalized[column] = parquet_normalized[column].fillna("")
            source_normalized[column] = source_normalized[column].fillna("")
        pd.testing.assert_frame_equal(
            csv_normalized, source_normalized, check_dtype=False, rtol=1e-13
        )
        pd.testing.assert_frame_equal(parquet_normalized, source_normalized, check_dtype=False)
        public_fields |= {(name, field) for field in source.columns}
        identity[name] = {
            "rows": len(source),
            "semantic_sha256": semantic_fingerprint(source),
            "status": "PASS",
        }
    assert public_fields == registered
    all_fields = {field.lower() for _, field in public_fields}
    pii = sorted(all_fields & PII_FIELDS)
    forbidden_fields = sorted(all_fields & FORBIDDEN_PUBLIC_FIELDS)
    flows = pd.read_parquet(output / "hospitalization_flows_public.parquet")
    flow_leaks = int((flows["admissions"] < 5).sum())
    assert flow_leaks == 0 and not pii and not forbidden_fields
    assert not any(FORBIDDEN_NAMES.search(path.name) for path in output.iterdir())
    for path in output.iterdir():
        if path.suffix in {".md", ".json", ".yaml", ".yml", ".csv", ".cff", ".sha256"}:
            text = path.read_text(errors="ignore")
            assert "/Users/" not in text and "MDB_DB_PASSWORD" not in text
    rights = yaml.safe_load(
        (ROOT / "metadata/legal/source_redistribution_matrix_v1.yaml").read_text()
    )
    distributed_unknown = [
        source["source_id"]
        for source in rights["sources"]
        if source["public_download_use"] == "YES" and source["license_confidence"] == "UNKNOWN"
    ]
    assert not distributed_unknown
    archive = output.parent / f"{OPEN_DATA_RELEASE}.zip"
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        zip_names = set(package.namelist())
        assert zip_names == {path.name for path in output.iterdir() if path.is_file()}
        for path in output.iterdir():
            assert package.read(path.name) == path.read_bytes()
    result = {
        "status": "PASS",
        "datasets": identity,
        "field_registry": "PASS",
        "csv_parquet_identity": "PASS",
        "pii_fields": pii,
        "forbidden_public_fields": forbidden_fields,
        "public_exact_flow_below_5": flow_leaks,
        "raw_source_leaks": 0,
        "distributed_unknown_rights": distributed_unknown,
        "manifest": {
            "missing": len(missing),
            "extra": len(extra),
            "size_mismatches": len(size_mismatches),
            "hash_mismatches": len(hash_mismatches),
        },
        "zip": {
            "filename": archive.name,
            "bytes": archive.stat().st_size,
            "sha256": digest(archive.read_bytes()),
        },
    }
    assert all(value == 0 for value in result["manifest"].values())
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PUBLIC_RELEASE_DIR)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    result = validate(args.output)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

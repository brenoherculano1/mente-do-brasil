"""Validation helpers for the locked validated import bundle.

The functions in this module verify imported files and frozen result values only.
They do not recalculate Mente do Brasil scientific metrics.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import (
    EXPECTED_HEALTH_REGION_COUNT,
    EXPECTED_MUNICIPALITY_COUNT,
    GEOGRAPHY_VERSION,
    INVALID_SPATIAL_VALUES,
    LOCKED_SPATIAL_RESULTS,
    METHOD_VERSION,
    RELEASE_ID,
)

BUNDLE_ID = "MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24"
BUNDLE_DRIVE_FILE_ID = "1Q90JOpkU4IzlqQ4lhFe5Ir8hXdG0X4Q5"
BUNDLE_ZIP_SIZE_BYTES = 67516917
BUNDLE_ZIP_SHA256 = "3658182b92a90466bc27d6ce3252e796fd25b54f2023d3ac1abe6eb356f7c6cc"
BUNDLE_ORIGIN = "Google Drive scientific validated import bundle"
BUNDLE_STATUS = "VALIDATING"

RAW_IMPORT_RELATIVE_ROOT = Path("data/raw/imported") / BUNDLE_ID / "mdb_import_bundle"

CRITICAL_FILES = {
    "IMPORT_MANIFEST.json",
    "geography/health_region_crosswalk_LOCKED.csv",
    "geography/health_regions_LOCKED.gpkg",
    "analytical_release/health_region_analysis_dataset_corrected.csv",
    "analytical_release/mismatch_scores_corrected.csv",
    "analytical_release/global_moran_primary_corrected.json",
    "analytical_release/LISA_primary_corrected.csv",
    "analytical_release/CORRECTED_RESULT_LOCK.md",
    "analytical_release/corrected_result_freeze_hashes.txt",
    "analytical_release/phase2c_summary.json",
    "analytical_release/corrected_Supplement_All_439_Health_Regions.csv",
}


@dataclass(frozen=True)
class BundlePaths:
    repo_root: Path
    raw_root: Path


def repo_root_from(path: Path | None = None) -> Path:
    """Return the repository root for a file path or current working directory."""

    start = Path.cwd() if path is None else path
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def bundle_paths(repo_root: Path | None = None) -> BundlePaths:
    """Return canonical paths for the imported bundle."""

    root = repo_root or repo_root_from()
    return BundlePaths(repo_root=root, raw_root=root / RAW_IMPORT_RELATIVE_ROOT)


def sha256_file(path: Path) -> str:
    """Hash a file without loading large artifacts into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(raw_root: Path) -> dict[str, Any]:
    """Load the bundle manifest from the imported raw package."""

    with (raw_root / "IMPORT_MANIFEST.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def manifest_file_entries(raw_root: Path) -> list[dict[str, Any]]:
    """Return manifest file entries after checking the locked bundle identity."""

    manifest = load_manifest(raw_root)
    if manifest.get("bundle_id") != BUNDLE_ID:
        raise AssertionError(f"Unexpected bundle_id: {manifest.get('bundle_id')}")
    return list(manifest["files"])


def validate_manifest_integrity(raw_root: Path) -> None:
    """Validate manifest paths, bytes, and hashes against imported raw files."""

    manifest_paths = {entry["path"] for entry in manifest_file_entries(raw_root)}
    missing_critical = sorted(CRITICAL_FILES - manifest_paths - {"IMPORT_MANIFEST.json"})
    if missing_critical:
        raise AssertionError(f"Critical files missing from manifest: {missing_critical}")

    for entry in manifest_file_entries(raw_root):
        path = raw_root / entry["path"]
        if not path.exists():
            raise AssertionError(f"Manifest file missing from raw import: {entry['path']}")
        if path.stat().st_size != entry["bytes"]:
            raise AssertionError(f"Byte count mismatch for {entry['path']}")
        if sha256_file(path) != entry["sha256"]:
            raise AssertionError(f"SHA-256 mismatch for {entry['path']}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file as dictionaries."""

    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def crosswalk_rows(raw_root: Path) -> list[dict[str, str]]:
    return read_csv_rows(raw_root / "geography/health_region_crosswalk_LOCKED.csv")


def analytical_rows(raw_root: Path) -> list[dict[str, str]]:
    return read_csv_rows(
        raw_root / "analytical_release/health_region_analysis_dataset_corrected.csv"
    )


def lisa_rows(raw_root: Path) -> list[dict[str, str]]:
    return read_csv_rows(raw_root / "analytical_release/LISA_primary_corrected.csv")


def gpkg_health_region_count(raw_root: Path) -> tuple[int, int, int]:
    """Return GPKG row count, unique code count, and null code count."""

    gpkg = raw_root / "geography/health_regions_LOCKED.gpkg"
    connection = sqlite3.connect(gpkg)
    try:
        row_count = connection.execute("select count(*) from health_regions").fetchone()[0]
        unique_codes = connection.execute(
            "select count(distinct health_region_code) from health_regions"
        ).fetchone()[0]
        null_codes = connection.execute(
            """
            select count(*)
            from health_regions
            where health_region_code is null or health_region_code = ''
            """
        ).fetchone()[0]
    finally:
        connection.close()
    return row_count, unique_codes, null_codes


def validate_geography_alignment(raw_root: Path) -> None:
    """Validate geography counts and crosswalk-to-dataset alignment."""

    crosswalk = crosswalk_rows(raw_root)
    dataset = analytical_rows(raw_root)

    municipality_codes = [row["municipality_code_ibge"] for row in crosswalk]
    region_codes = [row["health_region_code"] for row in crosswalk]
    dataset_codes = [row["health_region_code"] for row in dataset]

    if len(set(municipality_codes)) != EXPECTED_MUNICIPALITY_COUNT:
        raise AssertionError("Municipality count is not 5570.")
    if len(municipality_codes) != len(set(municipality_codes)):
        raise AssertionError("A municipality appears in more than one crosswalk row.")
    if any(not code for code in region_codes):
        raise AssertionError("Crosswalk contains null health_region_code values.")
    if len(set(region_codes)) != EXPECTED_HEALTH_REGION_COUNT:
        raise AssertionError("Crosswalk does not contain 439 unique health regions.")

    gpkg_rows, gpkg_unique_codes, gpkg_null_codes = gpkg_health_region_count(raw_root)
    if (gpkg_rows, gpkg_unique_codes, gpkg_null_codes) != (EXPECTED_HEALTH_REGION_COUNT, 439, 0):
        raise AssertionError("GPKG health-region layer failed count or null-code checks.")

    missing_from_dataset = sorted(set(region_codes) - set(dataset_codes))
    extra_in_dataset = sorted(set(dataset_codes) - set(region_codes))
    if missing_from_dataset or extra_in_dataset:
        raise AssertionError(
            "Crosswalk and analytical dataset health_region_code sets differ: "
            f"missing={missing_from_dataset[:10]}, extra={extra_in_dataset[:10]}"
        )


def validate_analytical_dataset(raw_root: Path) -> None:
    """Validate frozen analytical dataset structure and bounded score fields."""

    rows = analytical_rows(raw_root)
    codes = [row["health_region_code"] for row in rows]
    if len(rows) != EXPECTED_HEALTH_REGION_COUNT:
        raise AssertionError("Analytical dataset does not contain 439 rows.")
    if len(codes) != len(set(codes)):
        raise AssertionError("Analytical dataset health_region_code is not unique.")
    if any(not code for code in codes):
        raise AssertionError("Analytical dataset contains null health_region_code values.")

    bounded_0_1 = [
        "Need_r",
        "Capacity_r",
        "suicide_percentile",
        "admissions_percentile",
        "CAPS_percentile",
        "beds_percentile",
        "FTE_percentile",
    ]
    for row in rows:
        for field in bounded_0_1:
            value = row[field]
            if value == "":
                raise AssertionError(f"{field} is missing; it must not be coerced to zero.")
            number = float(value)
            if not 0 <= number <= 1:
                raise AssertionError(f"{field} is outside [0, 1].")
        mismatch = row["Mismatch_r"]
        if mismatch == "":
            raise AssertionError("Mismatch_r is missing; it must not be coerced to zero.")
        if not -1 <= float(mismatch) <= 1:
            raise AssertionError("Mismatch_r is outside [-1, 1].")


def load_primary_moran(raw_root: Path) -> dict[str, Any]:
    with (raw_root / "analytical_release/global_moran_primary_corrected.json").open(
        encoding="utf-8"
    ) as handle:
        return json.load(handle)


def validate_locked_spatial_results(raw_root: Path) -> None:
    """Validate frozen Global Moran and LISA outputs."""

    moran = load_primary_moran(raw_root)
    if abs(float(moran["I"]) - LOCKED_SPATIAL_RESULTS["global_moran_i"]) > 1e-12:
        raise AssertionError("Primary Global Moran I differs from the locked value.")
    if abs(float(moran["I"]) - INVALID_SPATIAL_VALUES["old_global_moran_i"]) < 1e-12:
        raise AssertionError("Invalidated Global Moran I reappeared as primary.")
    if float(moran["pseudo_p"]) != LOCKED_SPATIAL_RESULTS["pseudo_p"]:
        raise AssertionError("Primary Global Moran pseudo-p differs from the locked value.")
    if int(moran["permutations"]) != LOCKED_SPATIAL_RESULTS["permutations"]:
        raise AssertionError("Primary Global Moran permutations differ from the locked value.")
    if int(moran["seed"]) != LOCKED_SPATIAL_RESULTS["seed"]:
        raise AssertionError("Primary Global Moran seed differs from the locked value.")

    significant = [row for row in lisa_rows(raw_root) if row["significant_at_q_0.10"] == "True"]
    counts = {
        "lisa_fdr_significant": len(significant),
        "hh": sum(row["cluster_label"] == "high-high" for row in significant),
        "ll": sum(row["cluster_label"] == "low-low" for row in significant),
        "hl": sum(row["cluster_label"] == "high-low" for row in significant),
        "lh": sum(row["cluster_label"] == "low-high" for row in significant),
    }
    expected = {
        key: LOCKED_SPATIAL_RESULTS[key] for key in ["lisa_fdr_significant", "hh", "ll", "hl", "lh"]
    }
    if counts != expected:
        raise AssertionError(f"LISA locked counts differ: got={counts}, expected={expected}")


def imported_file_records(raw_root: Path, imported_at: str) -> list[dict[str, Any]]:
    """Build provenance records for all manifest-listed imported files."""

    records: list[dict[str, Any]] = []
    for entry in manifest_file_entries(raw_root):
        records.append(
            {
                "name": Path(entry["path"]).name,
                "raw_path": str(RAW_IMPORT_RELATIVE_ROOT / entry["path"]),
                "sha256": entry["sha256"],
                "bundle_id": BUNDLE_ID,
                "release_id": RELEASE_ID,
                "geography_version": GEOGRAPHY_VERSION,
                "method_version": METHOD_VERSION,
                "origin": BUNDLE_ORIGIN,
                "google_drive_file_id": BUNDLE_DRIVE_FILE_ID,
                "imported_at": imported_at,
                "size_bytes": entry["bytes"],
                "validation_status": BUNDLE_STATUS,
            }
        )
    return records

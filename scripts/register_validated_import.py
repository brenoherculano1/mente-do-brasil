"""Register provenance for the validated Mente do Brasil import bundle."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mente_do_brasil.import_validation import (  # noqa: E402
    BUNDLE_DRIVE_FILE_ID,
    BUNDLE_ID,
    BUNDLE_ORIGIN,
    BUNDLE_STATUS,
    BUNDLE_ZIP_SHA256,
    BUNDLE_ZIP_SIZE_BYTES,
    GEOGRAPHY_VERSION,
    METHOD_VERSION,
    RELEASE_ID,
    bundle_paths,
    crosswalk_rows,
    gpkg_health_region_count,
    imported_file_records,
    lisa_rows,
    load_primary_moran,
    validate_analytical_dataset,
    validate_geography_alignment,
    validate_locked_spatial_results,
    validate_manifest_integrity,
)


def _yaml_scalar(value: object) -> str:
    text = str(value)
    if isinstance(value, (int, float)):
        return text
    return json.dumps(text, ensure_ascii=False)


def write_metadata(records: list[dict[str, object]], imported_at: str, destination: Path) -> None:
    lines = [
        f"bundle_id: {_yaml_scalar(BUNDLE_ID)}",
        f"release_id: {_yaml_scalar(RELEASE_ID)}",
        f"geography_version: {_yaml_scalar(GEOGRAPHY_VERSION)}",
        f"method_version: {_yaml_scalar(METHOD_VERSION)}",
        f"status: {_yaml_scalar(BUNDLE_STATUS)}",
        f"origin: {_yaml_scalar(BUNDLE_ORIGIN)}",
        f"google_drive_file_id: {_yaml_scalar(BUNDLE_DRIVE_FILE_ID)}",
        f"bundle_zip_size_bytes: {BUNDLE_ZIP_SIZE_BYTES}",
        f"bundle_zip_sha256: {_yaml_scalar(BUNDLE_ZIP_SHA256)}",
        f"imported_at: {_yaml_scalar(imported_at)}",
        "files:",
    ]
    for record in records:
        lines.append(f"  - name: {_yaml_scalar(record['name'])}")
        for key in [
            "raw_path",
            "sha256",
            "bundle_id",
            "release_id",
            "geography_version",
            "method_version",
            "origin",
            "google_drive_file_id",
            "imported_at",
            "size_bytes",
            "validation_status",
        ]:
            lines.append(f"    {key}: {_yaml_scalar(record[key])}")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(raw_root: Path, imported_at: str, destination: Path) -> None:
    moran = load_primary_moran(raw_root)
    crosswalk_count = len(crosswalk_rows(raw_root))
    gpkg_rows, gpkg_unique, gpkg_null = gpkg_health_region_count(raw_root)
    significant = [row for row in lisa_rows(raw_root) if row["significant_at_q_0.10"] == "True"]
    lisa_counts = {
        "total": len(significant),
        "HH": sum(row["cluster_label"] == "high-high" for row in significant),
        "LL": sum(row["cluster_label"] == "low-low" for row in significant),
        "HL": sum(row["cluster_label"] == "high-low" for row in significant),
        "LH": sum(row["cluster_label"] == "low-high" for row in significant),
    }
    destination.write_text(
        "\n".join(
            [
                "# Validated Import Bundle QC",
                "",
                f"- bundle_id: `{BUNDLE_ID}`",
                f"- release_id: `{RELEASE_ID}`",
                f"- geography_version: `{GEOGRAPHY_VERSION}`",
                f"- method_version: `{METHOD_VERSION}`",
                f"- status: `{BUNDLE_STATUS}`",
                f"- imported_at: `{imported_at}`",
                f"- origin: `{BUNDLE_ORIGIN}`",
                f"- Google Drive file ID: `{BUNDLE_DRIVE_FILE_ID}`",
                f"- bundle ZIP size: `{BUNDLE_ZIP_SIZE_BYTES}` bytes",
                f"- bundle ZIP SHA-256: `{BUNDLE_ZIP_SHA256}`",
                f"- municipalities validated: `{crosswalk_count}/5570`",
                f"- health-region GPKG rows: `{gpkg_rows}`",
                f"- health-region GPKG unique codes: `{gpkg_unique}`",
                f"- health-region GPKG null codes: `{gpkg_null}`",
                f"- Global Moran I: `{moran['I']}`",
                f"- pseudo-p: `{moran['pseudo_p']}`",
                f"- permutations: `{moran['permutations']}`",
                f"- seed: `{moran['seed']}`",
                "- LISA FDR-significant: "
                f"`{lisa_counts['total']}` "
                f"(HH `{lisa_counts['HH']}`, LL `{lisa_counts['LL']}`, "
                f"HL `{lisa_counts['HL']}`, LH `{lisa_counts['LH']}`)",
                "",
                "No scientific metric was recalculated or overwritten during this registration.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    paths = bundle_paths()
    validate_manifest_integrity(paths.raw_root)
    validate_geography_alignment(paths.raw_root)
    validate_analytical_dataset(paths.raw_root)
    validate_locked_spatial_results(paths.raw_root)

    imported_at = os.environ.get("MDB_IMPORTED_AT")
    if not imported_at:
        imported_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    records = imported_file_records(paths.raw_root, imported_at)
    metadata_path = paths.repo_root / "metadata/sources/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24.yaml"
    report_path = paths.repo_root / "docs/validated_import_bundle_qc_2026-08-24.md"
    write_metadata(records, imported_at, metadata_path)
    write_report(paths.raw_root, imported_at, report_path)

    print(f"registered_files={len(records)}")
    print(f"metadata={metadata_path}")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

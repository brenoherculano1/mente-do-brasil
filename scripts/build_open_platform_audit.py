"""Build and validate the locked-local Open Platform audit package."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2026, 9, 1, 0, 0, 0)

INCLUDE_FILES = [
    "CITATION.cff",
    "db/migrations/011_public_open_platform.sql",
    "db/migrations/012_public_role_hardening.sql",
    "db/migrations/013_public_temporal_type_alignment.sql",
    "docs/api_deprecation_policy.md",
    "docs/data_correction_policy.md",
    "docs/data_update_policy.md",
    "docs/legal_research_2026-09-01.md",
    "docs/licensing_and_attribution.md",
    "docs/open_data_attribution.md",
    "docs/open_data_readme_en.md",
    "docs/open_data_readme_pt.md",
    "docs/open_data_sources.md",
    "docs/privacy_and_disclosure_policy.md",
    "docs/third_party_notices.md",
    "metadata/legal/source_redistribution_matrix_v1.yaml",
    "scripts/build_open_data_release.py",
    "scripts/open_platform_spec.py",
    "scripts/validate_open_data_release.py",
    "scripts/validate_public_database.py",
]
INCLUDE_TREES = [
    "audit_results/open_platform",
    "metadata/open_platform",
]
RELEASE_EVIDENCE = [
    "CHECKSUMS.sha256",
    "MANIFEST.json",
    "release.json",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for relative in INCLUDE_FILES:
        files[relative] = (ROOT / relative).read_bytes()
    for tree in INCLUDE_TREES:
        for path in sorted((ROOT / tree).rglob("*")):
            if path.is_file():
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    release_root = ROOT / "artifacts/public_releases/MDB_OPEN_DATA_2024_1"
    for name in RELEASE_EVIDENCE:
        files[f"open_data_release_evidence/{name}"] = (release_root / name).read_bytes()
    return files


def build(commit: str, output: Path) -> dict:
    files = package_files()
    files["AUDIT_README.md"] = (
        b"# Mente do Brasil Open Platform audit\n\n"
        b"Evidence package for the locked-local Open Platform candidate. It is not the "
        b"public data release and does not indicate deployment or publication.\n"
    )
    context = {
        "status": "LOCKED_LOCAL",
        "public_release_status": "NOT_RELEASED",
        "open_platform_version": "MDB_OPEN_PLATFORM_1.0",
        "open_data_release": "MDB_OPEN_DATA_2024_1",
        "public_api_version": "MDB_PUBLIC_API_V1",
        "data_governance_version": "MDB_DATA_GOVERNANCE_1.0",
        "starting_commit": "7e21154031063442f0f41a08d3681e24d5f0b10f",
        "final_commit": commit,
        "branch": "open-platform-complete",
        "evidence_date": "2026-09-01",
    }
    files["AUDIT_CONTEXT.json"] = (json.dumps(context, indent=2) + "\n").encode()
    entries = [
        {"relative_path": name, "size_bytes": len(data), "sha256": sha256(data)}
        for name, data in sorted(files.items())
    ]
    manifest = {"schema_version": "1.0", "files": entries}
    files["AUDIT_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)

    with tempfile.TemporaryDirectory() as temporary:
        with zipfile.ZipFile(output) as archive:
            archive.extractall(temporary)
        extracted = Path(temporary)
        actual = {
            path.relative_to(extracted).as_posix(): path
            for path in extracted.rglob("*")
            if path.is_file() and path.name != "AUDIT_MANIFEST.json"
        }
        expected = {entry["relative_path"]: entry for entry in entries}
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        size_mismatches = [
            name for name in expected.keys() & actual.keys()
            if actual[name].stat().st_size != expected[name]["size_bytes"]
        ]
        hash_mismatches = [
            name for name in expected.keys() & actual.keys()
            if sha256(actual[name].read_bytes()) != expected[name]["sha256"]
        ]
    result = {
        "status": "PASS" if not any((missing, extra, size_mismatches, hash_mismatches)) else "FAIL",
        "filename": output.name,
        "size_bytes": output.stat().st_size,
        "sha256": sha256(output.read_bytes()),
        "audit_files_excluding_manifest": len(entries),
        "manifest_entries": len(entries),
        "missing": len(missing),
        "extra": len(extra),
        "size_mismatches": len(size_mismatches),
        "hash_mismatches": len(hash_mismatches),
    }
    if result["status"] != "PASS":
        raise RuntimeError(json.dumps(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.commit, args.output), indent=2))


if __name__ == "__main__":
    main()

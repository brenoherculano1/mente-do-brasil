#!/usr/bin/env python3
"""Validate the immutable public release bundled with the web application."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RELEASE_ID = "MDB_OPEN_DATA_2024_1"
EXPECTED_ZIP_BYTES = 914_294
EXPECTED_ZIP_SHA256 = "2b3b1fc749bfd71181115c2cd9467bf26cb1572bd0c0e9687dabccffab3775bc"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    release_dir = root / "web" / "public" / "releases" / RELEASE_ID
    archive = release_dir / f"{RELEASE_ID}.zip"
    manifest = json.loads((release_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    failures: list[str] = []

    if manifest.get("release") != RELEASE_ID:
        failures.append("manifest release ID mismatch")
    for entry in manifest.get("files", []):
        path = release_dir / entry["relative_path"]
        if not path.is_file():
            failures.append(f"missing: {entry['relative_path']}")
            continue
        if path.stat().st_size != entry["bytes"]:
            failures.append(f"size mismatch: {entry['relative_path']}")
        if sha256(path) != entry["sha256"]:
            failures.append(f"SHA mismatch: {entry['relative_path']}")

    if not archive.is_file() or archive.stat().st_size != EXPECTED_ZIP_BYTES:
        failures.append("immutable ZIP size mismatch")
    elif sha256(archive) != EXPECTED_ZIP_SHA256:
        failures.append("immutable ZIP SHA mismatch")

    if failures:
        print("COMMITTED OPEN DATA RELEASE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("COMMITTED OPEN DATA RELEASE: PASS")
    print(f"release={RELEASE_ID}")
    print(f"zip_bytes={EXPECTED_ZIP_BYTES}")
    print(f"zip_sha256={EXPECTED_ZIP_SHA256}")
    print(f"manifest_files={len(manifest['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

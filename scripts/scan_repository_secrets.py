#!/usr/bin/env python3
"""Scan tracked worktree and historical Git blobs without printing secret values."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

MAX_BLOB_BYTES = 8 * 1024 * 1024
FORBIDDEN_SUFFIXES = {".dump", ".backup", ".pem", ".key", ".p12", ".pfx"}
SECRET_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "slack_token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "supabase_service_key": re.compile(rb"\b(?:sb_secret_|sb_publishable_)[A-Za-z0-9_-]{20,}\b"),
    "database_url_with_password": re.compile(
        rb"(?:postgres(?:ql)?|mysql)://[^\s:/@]+:([^\s/@]+)@[^\s]+", re.IGNORECASE
    ),
}
PLACEHOLDER_PASSWORDS = {b"password", b"example", b"changeme", b"set_a_local_password"}
ALLOWLIST_PATHS = {"web/tests/unit/public-foundation.test.ts"}
LOCAL_ABSOLUTE_PATH = re.compile(rb"/(?:Users|home)/[^\s\"']+")


def git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, input=input_bytes, check=True, capture_output=True
    ).stdout


def suspicious_path(path: str) -> str | None:
    normalized = path.lower()
    name = Path(normalized).name
    if name.startswith(".env") and name not in {".env.example", ".env.sample"}:
        return "tracked_env_file"
    if Path(normalized).suffix in FORBIDDEN_SUFFIXES:
        return "tracked_secret_or_dump_extension"
    if normalized.startswith("data/raw/") and name != ".gitkeep":
        return "tracked_raw_source"
    return None


def findings_for_blob(path: str, data: bytes) -> set[str]:
    findings: set[str] = set()
    for label, pattern in SECRET_PATTERNS.items():
        matches = pattern.finditer(data)
        for match in matches:
            if label == "database_url_with_password":
                password = match.group(1).lower()
                if password in PLACEHOLDER_PASSWORDS or path in ALLOWLIST_PATHS:
                    continue
            findings.add(label)
            break
    return findings


def blob_metadata(root: Path, object_ids: list[str]) -> dict[str, tuple[str, int]]:
    payload = ("\n".join(object_ids) + "\n").encode()
    lines = git(root, "cat-file", "--batch-check", input_bytes=payload).decode().splitlines()
    metadata: dict[str, tuple[str, int]] = {}
    for line in lines:
        sha, object_type, size = line.split()
        metadata[sha] = (object_type, int(size))
    return metadata


def read_blobs(root: Path, object_ids: list[str]):
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(("\n".join(object_ids) + "\n").encode())
    process.stdin.close()
    for expected_sha in object_ids:
        header = process.stdout.readline().decode().strip().split()
        sha, object_type, size = header
        if sha != expected_sha or object_type != "blob":
            raise RuntimeError("Unexpected git cat-file batch response.")
        data = process.stdout.read(int(size))
        process.stdout.read(1)
        yield sha, data
    if process.wait() != 0:
        assert process.stderr is not None
        raise RuntimeError(process.stderr.read().decode(errors="replace"))


def scan(root: Path) -> dict:
    object_lines = git(root, "rev-list", "--objects", "--all").decode().splitlines()
    blob_paths: dict[str, set[str]] = {}
    for line in object_lines:
        sha, _, path = line.partition(" ")
        if path:
            blob_paths.setdefault(sha, set()).add(path)

    findings: list[dict[str, str]] = []
    local_path_warnings: set[str] = set()
    skipped_large = 0
    metadata = blob_metadata(root, list(blob_paths))
    selected_blobs: list[str] = []
    for sha, paths in blob_paths.items():
        for path in paths:
            reason = suspicious_path(path)
            if reason:
                findings.append({"scope": "history", "path": path, "kind": reason})
        object_type, size = metadata[sha]
        if object_type != "blob":
            continue
        if size > MAX_BLOB_BYTES:
            skipped_large += 1
            continue
        selected_blobs.append(sha)

    for sha, data in read_blobs(root, selected_blobs):
        paths = blob_paths[sha]
        for path in paths:
            if LOCAL_ABSOLUTE_PATH.search(data):
                local_path_warnings.add(path)
            for kind in findings_for_blob(path, data):
                findings.append({"scope": "history", "path": path, "kind": kind})

    tracked = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")
    for raw_path in tracked:
        if not raw_path:
            continue
        path = raw_path.decode()
        reason = suspicious_path(path)
        if reason:
            findings.append({"scope": "worktree", "path": path, "kind": reason})
        disk_path = root / path
        if disk_path.is_file() and disk_path.stat().st_size <= MAX_BLOB_BYTES:
            data = disk_path.read_bytes()
            if LOCAL_ABSOLUTE_PATH.search(data):
                local_path_warnings.add(path)
            for kind in findings_for_blob(path, data):
                findings.append({"scope": "worktree", "path": path, "kind": kind})

    unique = sorted({(item["scope"], item["path"], item["kind"]) for item in findings})
    return {
        "status": "PASS" if not unique else "FAIL",
        "findings": [{"scope": scope, "path": path, "kind": kind} for scope, path, kind in unique],
        "historical_blobs_scanned": len(blob_paths),
        "large_blobs_skipped_for_content": skipped_large,
        "local_absolute_path_warning_files": sorted(local_path_warnings),
        "max_blob_bytes": MAX_BLOB_BYTES,
        "note": "Values are intentionally never emitted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = scan(root)
    serialized = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline, aggregate input validation before any rebuild database operation."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = Path("metadata/provenance/required_local_artifacts_v1.json")


def inspect_artifacts(root, inventory):
    failures = []
    checked = []
    seen = set()
    for entry in inventory["artifacts"]:
        relative = entry["relative_path"]
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or relative in seen:
            failures.append({"relative_path": relative, "status": "INVALID_INVENTORY_PATH"})
            continue
        seen.add(relative)
        target = root / path
        result = {"relative_path": relative, "status": "PASS"}
        if not target.is_file():
            result["status"] = "MISSING"
        else:
            with target.open("rb") as stream:
                observed = hashlib.file_digest(stream, "sha256").hexdigest()
            result.update(bytes=target.stat().st_size, sha256=observed)
            if entry.get("acceptance_status", "ACCEPTED") != "ACCEPTED":
                result["status"] = "PENDING_ACCEPTANCE"
            elif not entry.get("sha256") or not isinstance(entry.get("bytes"), int):
                result["status"] = "MISSING_LOCK"
            elif observed != entry["sha256"] or result["bytes"] != entry["bytes"]:
                result["status"] = "HASH_OR_SIZE_MISMATCH"
        checked.append(result)
        if result["status"] != "PASS":
            failures.append(result)
    if not seen:
        failures.append({"status": "EMPTY_INVENTORY"})
    return {
        "status": "PASS" if not failures else "BLOCKED",
        "checked": checked,
        "failures": failures,
        "database_operations": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, default=INVENTORY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        inventory = json.loads((args.root / args.inventory).read_text())
        result = inspect_artifacts(args.root, inventory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {
            "status": "BLOCKED",
            "failures": [{"status": "INVALID_INVENTORY", "detail": str(error)}],
            "database_operations": 0,
        }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

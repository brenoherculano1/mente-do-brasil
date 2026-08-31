"""Verify preserved raw hashes; recover cloud-evicted bytes only from official URLs."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urlparse

from acquire_phase3_sources import AUDIT, PROV, RAW, ROOT, schema_header, sha256, stamp, write_json


def verify(item):
    path = ROOT / item["local_path"]
    cloud_evicted = bool(path.stat().st_flags & 0x40000000)
    recovered = False
    incomplete = path.stat().st_size != int(item["size_bytes"])
    if cloud_evicted or incomplete:
        with tempfile.TemporaryDirectory(prefix="mdb-hash-recovery-") as directory:
            target = Path(directory) / "source"
            result = subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    "--retry",
                    "2",
                    "--max-time",
                    "600",
                    "--output",
                    str(target),
                    "--write-out",
                    "%{url_effective}",
                    item["official_url"],
                ],
                capture_output=True,
                text=True,
            )
            host = urlparse(result.stdout).hostname or ""
            if result.returncode or not (
                host.endswith(".saude.gov.br") or host.endswith(".datasus.gov.br")
            ):
                raise RuntimeError(f"Official recovery failed {path.name}: {result.stderr}")
            if sha256(target) != item["sha256"]:
                raise ValueError(f"Official recovery SHA mismatch: {path.name}")
            staged = path.with_suffix(path.suffix + ".verified-restore")
            with target.open("rb") as source, staged.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            staged.replace(path)
            recovered = True
    actual = sha256(path)
    if actual != item["sha256"]:
        raise ValueError(f"Preserved raw SHA mismatch: {path.name}")
    schema = {"fingerprint": item.get("schema_fingerprint", "")}
    if path.suffix == ".dbc":
        with path.open("rb") as stream:
            schema = schema_header(stream)
        if item.get("schema_fingerprint") and schema["fingerprint"] != item["schema_fingerprint"]:
            raise ValueError(f"Preserved schema mismatch: {path.name}")
        item["schema_fingerprint"] = schema["fingerprint"]
    receipt = {
        **item,
        "size_bytes": path.stat().st_size,
        "schema": schema,
        "schema_fingerprint": schema["fingerprint"],
        "cache_reused": True,
        "attempts": [],
        "receipt_reconstructed_from_manifest": True,
        "verified_at": stamp(),
        "cloud_recovery": recovered,
    }
    write_json(path.with_suffix(path.suffix + ".json"), receipt)
    return {
        "file": item["local_path"],
        "sha256": actual,
        "match": True,
        "size_bytes": path.stat().st_size,
        "cloud_recovery": recovered,
    }


def main():
    manifest = PROV / "phase3_source_manifest.csv"
    rows = list(csv.DictReader(manifest.open()))
    rows = [r for r in rows if r["dataset"] != "SIOPS_extracted"]
    recovery = PROV / "phase3_locked_recovery.json"
    if recovery.exists() and not any(r["dataset"] == "locked_recovery" for r in rows):
        locked = {
            Path(r["filename"]).name: r
            for r in csv.DictReader((PROV / "phase2_raw_data_manifest_2026-08-23.csv").open())
        }
        for evidence in json.loads(recovery.read_text()):
            if not evidence.get("match"):
                raise ValueError("Unverified locked recovery cannot enter the manifest")
            previous = locked[evidence["filename"]]
            rows.append(
                {
                    "source_system": "DATASUS",
                    "dataset": "locked_recovery",
                    "period": previous["period"],
                    "uf": evidence["filename"][2:4],
                    "competence": previous["period"],
                    "official_url": previous["url"],
                    "final_url": previous["url"],
                    "retrieval_client": "curl",
                    "retrieved_at": "2026-08-31",
                    "original_filename": evidence["filename"],
                    "server_filename": evidence["filename"],
                    "size_bytes": previous["size"],
                    "sha256": previous["sha256"],
                    "schema_fingerprint": "",
                    "local_path": str(
                        (RAW / "locked_recovery" / evidence["filename"]).relative_to(ROOT)
                    ),
                    "notes": (
                        "Hash-exact recovery of a cloud-evicted source; date precision only. "
                        "Original locked bytes and manifest unchanged."
                    ),
                }
            )
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = []
        for i, result in enumerate(pool.map(verify, rows)):
            checks.append(result)
            if (i + 1) % 100 == 0:
                print("Verified original acquisition hashes", i + 1, flush=True)
    inventory = json.loads((PROV / "phase3_siops_schema_inventory.json").read_text())
    for inv in inventory:
        parent = next(r for r in rows if r["dataset"] == "SIOPS" and r["period"] == inv["year"])
        path = ROOT / parent["local_path"]
        extracted = path.with_suffix(".csv")
        if sha256(extracted) != inv["csv_sha256"]:
            raise ValueError(f"Extracted CSV mismatch: {extracted.name}")
        import hashlib

        signature = hashlib.sha256(
            json.dumps(inv["columns"], separators=(",", ":")).encode()
        ).hexdigest()
        parent["schema_fingerprint"] = signature
        rows.append(
            {
                **parent,
                "dataset": "SIOPS_extracted",
                "original_filename": inv["csv_member"],
                "sha256": inv["csv_sha256"],
                "size_bytes": inv["csv_size_bytes"],
                "local_path": str(extracted.relative_to(ROOT)),
                "notes": (
                    f"Extracted CSV; parent ZIP SHA256={parent['sha256']}; "
                    "UTF-8 BOM; semicolon; dot decimal."
                ),
            }
        )
        checks.append(
            {
                "file": str(extracted.relative_to(ROOT)),
                "sha256": inv["csv_sha256"],
                "match": True,
                "size_bytes": inv["csv_size_bytes"],
                "cloud_recovery": False,
            }
        )
    for r in rows:
        r["server_filename"] = unquote(urlparse(r["final_url"]).path.split("/")[-1])
        if r["dataset"] == "SIOPS":
            r["original_filename"] = r["server_filename"]
    columns = list(rows[0])
    with manifest.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_json(
        AUDIT / "phase3_raw_hash_validation.json",
        {
            "status": "PASS",
            "verified_at": stamp(),
            "manifest_rows": len(rows),
            "hash_mismatches": 0,
            "missing_files": 0,
            "cloud_evicted_files_recovered_hash_exact": sum(r["cloud_recovery"] for r in checks),
            "by_dataset": dict(Counter(r["dataset"] for r in rows)),
            "files": checks,
        },
    )
    print("Verified manifest rows", len(rows), flush=True)


if __name__ == "__main__":
    main()

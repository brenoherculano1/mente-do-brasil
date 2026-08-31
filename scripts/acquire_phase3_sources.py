#!/usr/bin/env python3
"""Catalog, acquire and hash official sources. Acquisition is not scientific approval."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/phase3"
PROV = ROOT / "metadata/provenance"
AUDIT = ROOT / "audit_results"
FTP = "ftp://ftp.datasus.gov.br/dissemin/publicos/"
UFS = set(
    "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + "\n")
    temp.replace(path)


def capture(url, name, listing=False):
    dest = PROV / "phase3_catalogs" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = ["curl", "-fsSL", "--connect-timeout", "15", "--max-time", "60", "--retry", "2"]
    result = subprocess.run(
        [*command, *(["--list-only"] if listing else []), url], capture_output=True
    )
    dest.write_bytes(result.stdout)
    write_json(
        dest.with_suffix(dest.suffix + ".json"),
        {
            "url": url,
            "retrieved_at": stamp(),
            "returncode": result.returncode,
            "stderr": result.stderr.decode(errors="replace"),
            "sha256": sha256(dest),
        },
    )
    if result.returncode:
        raise RuntimeError(f"{url}: {result.stderr.decode(errors='replace')}")
    return result.stdout.decode("utf-8", errors="replace")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs).get("href", ""))


def schema_header(stream):
    header = stream.read(32)
    if len(header) != 32 or header[0] not in {2, 3, 4, 5, 48, 49, 67, 131, 139, 245}:
        raise ValueError("Invalid DBF/DBC header")
    records, header_len, record_len = struct.unpack_from("<IHH", header, 4)
    if header_len < 33 or record_len < 1 or (header_len - 33) % 32:
        raise ValueError("Invalid DBF dimensions")
    fields = []
    for _ in range((header_len - 33) // 32):
        field = stream.read(32)
        if len(field) != 32:
            raise ValueError("Truncated DBF schema")
        fields.append(
            {
                "name": field[:11].split(b"\0")[0].decode("ascii"),
                "type": chr(field[11]),
                "length": field[16],
                "decimal": field[17],
            }
        )
    return {
        "fields": fields,
        "records": records,
        "record_length": record_len,
        "fingerprint": hashlib.sha256(
            json.dumps(fields, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def inspect_file(path):
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            if archive.testzip():
                raise ValueError("ZIP CRC failure")
            dbfs = [n for n in archive.namelist() if n.lower().endswith(".dbf")]
            if dbfs:
                with archive.open(dbfs[0]) as stream:
                    result = schema_header(stream)
            else:
                result = {"fingerprint": "", "status": "CSV_SCHEMA_PENDING"}
            result["members"] = [
                {"name": i.filename, "size": i.file_size} for i in archive.infolist()
            ]
            return result
    if path.suffix == ".dbc":
        with path.open("rb") as stream:
            return schema_header(stream)
    if path.suffix == ".pdf":
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("Not a PDF")
        return {"fingerprint": "", "status": "DOCUMENT"}
    raise ValueError(f"Unsupported source format {path.suffix}")


def download(item):
    folder = RAW / item["dataset"]
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / item["original_filename"]
    receipt = dest.with_suffix(dest.suffix + ".json")
    if dest.exists() and receipt.exists():
        previous = json.loads(receipt.read_text())
        if sha256(dest) == previous["sha256"]:
            return {**previous, "cache_reused": True}
        raise ValueError(f"CACHE_HASH_MISMATCH: {dest}")
    partial = dest.with_suffix(dest.suffix + ".part")
    attempts = []
    for _ in range(3):
        command = [
            "curl",
            "-fsSL",
            "--proto",
            "=ftp,http,https",
            "--proto-redir",
            "=ftp,http,https",
            "--connect-timeout",
            "20",
            "--max-time",
            "900",
            "--remote-time",
            "--continue-at",
            "-",
            "--output",
            str(partial),
            "--write-out",
            "%{json}",
            item["official_url"],
        ]
        result = subprocess.run(command, capture_output=True)
        attempts.append(
            {"returncode": result.returncode, "stderr": result.stderr.decode(errors="replace")}
        )
        if result.returncode == 0:
            response = json.loads(result.stdout)
            host = urlparse(response["url_effective"]).hostname or ""
            if not (host.endswith(".saude.gov.br") or host.endswith(".datasus.gov.br")):
                raise ValueError(f"Nonofficial redirect: {host}")
            partial.replace(dest)
            try:
                schema = inspect_file(dest)
            except Exception:
                dest.replace(dest.with_suffix(dest.suffix + ".rejected"))
                raise
            record = {
                **item,
                "source_system": item.get("source_system", "DATASUS"),
                "retrieval_client": "curl",
                "retrieved_at": stamp(),
                "final_url": response["url_effective"],
                "size_bytes": dest.stat().st_size,
                "server_filename": unquote(urlparse(response["url_effective"]).path.split("/")[-1]),
                "last_modified_epoch": dest.stat().st_mtime,
                "sha256": sha256(dest),
                "schema_fingerprint": schema["fingerprint"],
                "local_path": str(dest.relative_to(ROOT)),
                "schema": schema,
                "attempts": attempts,
                "cache_reused": False,
                "notes": "Acquisition only; scientific gates evaluated separately.",
            }
            write_json(receipt, record)
            return record
        if result.returncode in {33, 36}:
            partial.unlink(missing_ok=True)
    raise RuntimeError(json.dumps({"url": item["official_url"], "attempts": attempts}))


def catalog():
    specs = [
        ("SIM", "SIM/CID10/DORES/", r"DO([A-Z]{2})(2020|2021)\.dbc"),
        ("SIH", "SIHSUS/200801_/Dados/", r"RD([A-Z]{2})(20|21)(0[1-9]|1[012])\.dbc"),
        *[
            ("CNES", f"CNES/200508_/Dados/{m}/", rf"({m})([A-Z]{{2}})(22|23)12\.dbc")
            for m in ["ST", "LT", "PF"]
        ],
        ("population", "IBGE/POPSVS/", r"POPSBR(20|21)\.zip"),
        ("SIH_documentation", "SIHSUS/200801_/Doc/", r"IT_SIHSUS_1603\.pdf"),
    ]
    items = []
    for dataset, directory, pattern in specs:
        suffix = directory.rstrip("/").split("/")[-1] if dataset == "CNES" else ""
        listing = capture(FTP + directory, f"{dataset}{suffix}.txt", listing=True)
        selected = sorted(
            n.strip() for n in listing.splitlines() if re.fullmatch(pattern, n.strip(), re.I)
        )
        for name in selected:
            match = re.fullmatch(pattern, name, re.I)
            uf, period, competence = "", "", ""
            if dataset == "SIM":
                uf, period = match.group(1, 2)
            elif dataset == "SIH":
                uf, period = match.group(1), f"20{match.group(2)}-{match.group(3)}"
                competence = period
            elif dataset == "CNES":
                uf, period = match.group(2), f"20{match.group(3)}-12"
                competence = period
            elif dataset == "population":
                period = "20" + match.group(1)
            if uf and uf not in UFS:
                continue
            items.append(
                {
                    "dataset": dataset,
                    "period": period,
                    "uf": uf,
                    "competence": competence,
                    "official_url": FTP + directory + name,
                    "original_filename": name,
                }
            )
        print(f"Catalog {dataset}: {len(selected)}", flush=True)
    links = Links()
    links.feed(
        capture("https://portalfns.saude.gov.br/siops/siops-downloads/", "siops_downloads.html")
    )
    for year in (2022, 2023, 2024):
        matches = [u for u in links.links if f"municipais-{year}-6o-bimestre" in u]
        if len(matches) != 1:
            raise ValueError(f"SIOPS {year}: expected one official link, found {matches}")
        items.append(
            {
                "dataset": "SIOPS",
                "period": str(year),
                "uf": "",
                "competence": f"{year}-B6",
                "source_system": "SIOPS/FNS",
                "official_url": matches[0],
                "original_filename": f"SIOPS_municipal_{year}_B6.zip",
            }
        )
    write_json(PROV / "phase3_source_catalog.json", {"retrieved_at": stamp(), "files": items})
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--datasets", nargs="+")
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--refresh-catalog", action="store_true")
    args = parser.parse_args()
    saved = PROV / "phase3_source_catalog.json"
    items = (
        json.loads(saved.read_text())["files"]
        if saved.exists() and not args.refresh_catalog
        else catalog()
    )
    if args.catalog_only:
        return
    if args.datasets:
        items = [i for i in items if i["dataset"] in args.datasets]
    failures, results = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(download, item): item for item in items}
        for future in as_completed(pending):
            try:
                results.append(future.result())
            except Exception as error:
                failures.append({"item": pending[future], "error": str(error)})
                print(f"FAILED {pending[future]['original_filename']}: {error}", flush=True)
            if (len(results) + len(failures)) % 25 == 0:
                print(
                    f"Completed {len(results)}; failures {len(failures)} / {len(items)}", flush=True
                )
    all_records = [json.loads(p.read_text()) for p in sorted(RAW.glob("*/*.*.json"))]
    columns = [
        "source_system",
        "dataset",
        "period",
        "uf",
        "competence",
        "official_url",
        "final_url",
        "retrieval_client",
        "retrieved_at",
        "original_filename",
        "server_filename",
        "size_bytes",
        "sha256",
        "schema_fingerprint",
        "local_path",
        "notes",
    ]
    with (PROV / "phase3_source_manifest.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(all_records)
    summary = {
        "status": "ACQUIRED" if not failures else "ACQUISITION_ERRORS",
        "retrieved_at": stamp(),
        "files_requested": len(items),
        "files_found": len(items),
        "files_downloaded_this_run": sum(not r["cache_reused"] for r in results),
        "files_reused_this_run": sum(r["cache_reused"] for r in results),
        "raw_bytes": sum(r["size_bytes"] for r in all_records),
        "hash_count": len(all_records),
        "failures": failures,
        "retries_this_run": sum(len(r["attempts"]) - 1 for r in results if not r["cache_reused"]),
        "schema_validation": "Header/ZIP CRC only; full schema and scientific gates pending",
    }
    write_json(AUDIT / "phase3_source_acquisition.txt", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

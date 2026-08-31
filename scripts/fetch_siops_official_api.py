"""Acquire the official SIOPS calculated/report layer for the financing snapshot."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = (
    ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
)
SNAPSHOT = ROOT / "data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl"
MANIFEST = ROOT / "audit_results/siops_official_source_manifest.csv"
ENDPOINT = "http://siops.datasus.gov.br/consdetalhereenvio2.php"
SUBFUNCTION_ENDPOINT = "http://siops.datasus.gov.br/rel_ges_dt_municipal.php"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_brl(value: str) -> float:
    cleaned = re.sub(r"[^0-9,.-]", "", html.unescape(value)).strip()
    if not cleaned:
        raise ValueError("empty currency value")
    return float(cleaned.replace(".", "").replace(",", "."))


def post_form(url: str, fields: list[tuple[str, str]]) -> bytes:
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={"User-Agent": "Mente-do-Brasil/Phase3; SIOPS audit client"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"unexpected HTTP status {response.status}")
        return response.read()


def fetch_one(item: tuple[int, str, bool]) -> dict:
    year, municipality, validate_indicator = item
    fields = [
        ("cmbAno", str(year)),
        ("cmbUF", municipality[:2]),
        ("cmbPeriodo", "2"),
        ("cmbMunicipio[]", municipality),
        ("BtConsultar", "Consultar"),
    ]
    last_error = ""
    for attempt in range(3):
        try:
            indicator = b""
            per_capita = None
            if validate_indicator:
                indicator = post_form(ENDPOINT, fields)
                indicator_text = indicator.decode("iso-8859-15", "replace")
                row = re.search(r"<td[^>]*>\s*2\.1\s*</td>(.*?)</tr>", indicator_text, re.S | re.I)
                if row is None:
                    raise ValueError("indicator 2.1 absent")
                cells = re.findall(
                    r'<td[^>]*class="tdr caixa"[^>]*>(.*?)</td>',
                    row.group(1),
                    re.S | re.I,
                )
                if len(cells) != 1:
                    raise ValueError("indicator 2.1 value is not unique")
                per_capita = parse_brl(cells[0])

            total = post_form(
                SUBFUNCTION_ENDPOINT,
                [
                    ("cmbAno", str(year)),
                    ("cmbUF", municipality[:2]),
                    ("cmbPeriodo", "2"),
                    ("cmbMunicipio[]", municipality),
                    ("BtConsultar", "Consultar"),
                ],
            )
            total_text = total.decode("iso-8859-15", "replace")
            total_row = re.search(
                r'<td class="td2 caixa"\s+colspan=[\'\"]2[\'\"]\s*>TOTAL</td>(.*?)</tr>',
                total_text,
                re.S | re.I,
            )
            if total_row is None:
                raise ValueError("group 17 TOTAL absent")
            total_cells = re.findall(
                r'<td[^>]*class="tdr caixa"[^>]*>(.*?)</td>', total_row.group(1), re.S | re.I
            )
            if len(total_cells) != 10:
                raise ValueError(
                    f"group 17 TOTAL expected 10 source values, found {len(total_cells)}"
                )
            return {
                "municipality": municipality,
                "year": year,
                "period": "2",
                "indicator": "2.1",
                "indicator_description": (
                    "Despesa total com Saúde, sob a responsabilidade do Município, por habitante"
                ),
                "indicator_per_capita_brl": round(per_capita, 2)
                if per_capita is not None
                else None,
                "group": "17",
                "group_description": "Total",
                "group17_total_brl": round(parse_brl(total_cells[-1]), 2),
                "stage": "empenhada",
                "endpoint": ENDPOINT,
                "subfunction_endpoint": SUBFUNCTION_ENDPOINT,
                "response_sha256": digest_bytes(indicator + total),
                "indicator_validated_in_sample": validate_indicator,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "status": "ok",
            }
        except Exception as error:  # noqa: BLE001 - retry boundary for external source
            last_error = f"{type(error).__name__}: {error}"
            if attempt < 2:
                time.sleep(2**attempt)
    return {
        "municipality": municipality,
        "year": year,
        "period": "2",
        "endpoint": ENDPOINT,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "error": last_error,
    }


def main() -> None:
    crosswalk = pd.read_parquet(CROSSWALK)
    municipalities = sorted(crosswalk.municipality_code_datasus6.astype(str).str.zfill(6).unique())
    sample = set(municipalities[:200])
    sample.update({"316620", "250760"})
    jobs = [
        (year, municipality, municipality in sample)
        for year in (2022, 2023, 2024)
        for municipality in municipalities
    ]
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    if SNAPSHOT.exists():
        with SNAPSHOT.open() as stream:
            records = [json.loads(line) for line in stream if line.strip()]
    cached = {(int(row["year"]), row["municipality"]): row for row in records}
    pending = [
        job
        for job in jobs
        if job[:2] not in cached
        or cached[job[:2]].get("status") != "ok"
        or (job[2] and not cached[job[:2]].get("indicator_validated_in_sample"))
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_one, job): job for job in pending}
        for index, future in enumerate(as_completed(futures), start=1):
            row = future.result()
            cached[(int(row["year"]), row["municipality"])] = row
            if index % 100 == 0 or index == len(pending):
                with SNAPSHOT.open("w") as stream:
                    for job in jobs:
                        row_to_write = cached.get(job[:2])
                        if row_to_write:
                            stream.write(
                                json.dumps(row_to_write, ensure_ascii=True, sort_keys=True) + "\n"
                            )
                print(f"SIOPS fetched {index}/{len(pending)}", flush=True)
    ordered = [cached[job[:2]] for job in jobs]
    with SNAPSHOT.open("w") as stream:
        for row in ordered:
            stream.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "municipality",
                "year",
                "period",
                "endpoint",
                "response_sha256",
                "retrieved_at",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in writer.fieldnames} for row in ordered)
    failures = [row for row in ordered if row.get("status") != "ok"]
    print(
        json.dumps(
            {
                "requested": len(jobs),
                "successful": len(jobs) - len(failures),
                "errors": len(failures),
            },
            indent=2,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

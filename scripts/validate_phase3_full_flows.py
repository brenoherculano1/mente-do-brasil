"""Reconcile pooled psychiatric SIH origins and destinations without patient output."""

from __future__ import annotations

import csv
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from scripts.build_scientific_correction import ROOT, sha256
from scripts.validate_phase3_source_gate import locked_path, read_dbc

LOCKED = ROOT / "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv"
RECOVERY = Path("/tmp/mdb-flow-recovery-20260831")


def read_one(row):
    path = locked_path(row)
    try:
        digest = subprocess.run(
            ["shasum", "-a", "256", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        ).stdout.split()[0]
        valid = path.exists() and digest == row["sha256"]
    except (OSError, subprocess.TimeoutExpired):
        valid = False
    if not valid:
        path = RECOVERY / Path(row["filename"]).name
        if not path.exists() or sha256(path) != row["sha256"]:
            path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    "--connect-timeout",
                    "20",
                    "--max-time",
                    "900",
                    "--retry",
                    "2",
                    "--output",
                    str(path),
                    row["url"],
                ],
                check=True,
            )
        if sha256(path) != row["sha256"]:
            raise ValueError(f"SIH hash mismatch after recovery: {path}")
    data = read_dbc(path, ["MUNIC_RES", "MUNIC_MOV", "DIAG_PRINC"])
    diagnosis = data.DIAG_PRINC.str[:3]
    psych = diagnosis.between("F00", "F09") | diagnosis.between("F20", "F99")
    data = data.loc[psych, ["MUNIC_RES", "MUNIC_MOV"]]
    return data.groupby(["MUNIC_RES", "MUNIC_MOV"]).size().rename("admissions").reset_index()


def main():
    rows = [
        r
        for r in csv.DictReader(LOCKED.open())
        if r["source"] == "SIH/SUS RD" and r["period"][:4] in {"2022", "2023", "2024"}
    ]
    if len(rows) != 972:
        raise ValueError(f"Expected 972 SIH 2022-2024 source rows, found {len(rows)}")
    parts = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, part in enumerate(pool.map(read_one, rows), start=1):
            parts.append(part)
            if i % 108 == 0:
                print(f"SIH processed {i}/972", flush=True)
    edges = pd.concat(parts).groupby(["MUNIC_RES", "MUNIC_MOV"], as_index=False).admissions.sum()
    cross = pd.read_parquet(
        ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
    )
    mapping = dict(zip(cross.municipality_code_datasus6, cross.health_region_code, strict=True))
    edges["origin_region"] = edges.MUNIC_RES.map(mapping)
    edges["destination_region"] = edges.MUNIC_MOV.map(mapping)
    if edges[["origin_region", "destination_region"]].isna().any().any():
        raise ValueError("Unmapped flow municipality")
    origin = edges.groupby("origin_region").admissions.sum()
    canonical = pd.read_parquet(
        ROOT / "data/canonical/MDB_ANALYTICAL_2024_2/health_regions.parquet"
    )
    expected = canonical.set_index("health_region_code").psychiatric_admissions
    delta = origin.reindex(expected.index, fill_value=0) - expected
    suppressed = int((edges.admissions < 5).sum())
    edges.loc[edges.admissions < 5, "admissions"] = pd.NA
    edges[["origin_region", "destination_region", "admissions"]].to_csv(
        ROOT / "audit_results/scientific_correction/pooled_flow_edges_suppressed.csv", index=False
    )
    result = {
        "status": "PASS" if (delta.abs() <= 0).all() else "FAIL_ORIGIN_RECONCILIATION",
        "source_files": len(rows),
        "origin_regions": int(origin.index.nunique()),
        "eligible_psychiatric_admissions": int(expected.sum()),
        "pooled_edges_before_suppression": int(len(edges)),
        "suppressed_edges_lt5": suppressed,
        "exact_lt5_leaks": int(edges.admissions.dropna().lt(5).sum()),
        "origin_reconciliation_439_439": bool((delta == 0).all()),
        "max_origin_delta": int(delta.abs().max()),
        "unmapped_municipalities": 0,
        "patient_fields_exposed": [],
        "diagnosis_rule": "F00-F09 or F20-F99; F10-F19 excluded",
        "destination": "MUNIC_MOV mapped to Health Region via official crosswalk",
        "source_hash_manifest": "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv",
    }
    (ROOT / "audit_results/phase3_full_flow_reconciliation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2), flush=True)
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reproducible source checks and a read-only audit of locked ASMR age compatibility.

Diagnostic alternatives are not releases and never overwrite canonical artifacts.
Requires dbfread==2.0.7, pyreaddbc==1.2.0, numpy and pandas.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from acquire_phase3_sources import AUDIT, PROV, RAW, ROOT, schema_header, sha256, write_json
from dbfread import DBF
from pyreaddbc.readdbc import dbc2dbf

LOCKED_MANIFEST = PROV / "phase2_raw_data_manifest_2026-08-23.csv"
STAGING = ROOT / "data/staging/phase3"
WEIGHTS = [
    8.86,
    8.69,
    8.60,
    8.47,
    8.22,
    7.93,
    7.61,
    7.15,
    6.59,
    6.04,
    5.37,
    4.55,
    3.72,
    2.96,
    2.21,
    1.52,
    0.91,
    0.44,
    0.23,
]


def selected_dbf(path, columns):
    """Use dbfread's parsed record layout; decode only the requested fields."""
    table = DBF(str(path), encoding="latin1", raw=True)
    offset = 1
    layout = {}
    for field in table.fields:
        layout[field.name] = (offset, field.length)
        offset += field.length
    if offset != table.header.recordlen:
        raise ValueError("DBF record layout mismatch")
    expected = table.header.headerlen + table.header.numrecords * table.header.recordlen
    if path.stat().st_size < expected:
        raise ValueError("Truncated decompressed DBF")
    dtype = np.dtype(
        {
            "names": ["_deleted", *columns],
            "formats": ["S1", *[f"S{layout[c][1]}" for c in columns]],
            "offsets": [0, *[layout[c][0] for c in columns]],
            "itemsize": table.header.recordlen,
        }
    )
    records = np.memmap(
        path, dtype=dtype, mode="r", offset=table.header.headerlen, shape=(table.header.numrecords,)
    )
    keep = records["_deleted"] != b"*"
    data = pd.DataFrame({c: np.char.strip(records[c][keep].astype(str)) for c in columns})
    # Cross-check against the independent DBF row reader, not just our offsets.
    for i, reference in enumerate(table):
        if i == min(25, len(data)):
            break
        for c in columns:
            if data.iloc[i][c] != reference[c].decode("latin1").strip():
                raise ValueError(f"DBF reader disagreement: {c}")
    return data


def read_dbc(path, columns):
    with tempfile.TemporaryDirectory(prefix="mdb-source-") as directory:
        dbf = Path(directory) / "source.dbf"
        dbc2dbf(str(path), str(dbf))
        return selected_dbf(dbf, columns)


def locked_path(item):
    original = Path(item["filename"])
    recovered = RAW / "locked_recovery" / original.name
    return recovered if recovered.exists() else original


def schemas():
    required = {
        "SIM": {"CODMUNRES", "CAUSABAS", "IDADE", "SEXO"},
        "SIH": {"MUNIC_RES", "MUNIC_MOV", "CNES", "DIAG_PRINC"},
        "ST": {"CNES", "CODUFMUN", "TP_UNID"},
        "LT": {"CNES", "CODUFMUN", "TP_UNID", "CODLEITO", "QT_SUS"},
        "PF": {"CNES", "CODUFMUN", "CBO", "PROF_SUS", "HORA_AMB", "HORAHOSP", "HORAOUTR"},
    }
    rows, signatures = [], {}
    paths = [
        (p, p.parent.name if p.parent.name != "CNES" else p.name[:2], "new")
        for p in RAW.glob("*/*.dbc")
        if p.parent.name != "locked_recovery"
    ]
    for item in csv.DictReader(LOCKED_MANIFEST.open()):
        p = locked_path(item)
        if p.suffix == ".dbc":
            if p.stat().st_flags & 0x40000000:
                # macOS cloud placeholder: do not call this missing source or block on hydration.
                rows.append(
                    {
                        "filename": p.name,
                        "family": "SIH" if p.name.startswith("RD") else "SIM",
                        "origin": "locked",
                        "schema_fingerprint": None,
                        "records": None,
                        "missing_required": [],
                        "record_status": "CLOUD_PLACEHOLDER_NOT_READ",
                    }
                )
                continue
            family = (
                "SIM"
                if p.name.startswith("DO")
                else ("SIH" if p.name.startswith("RD") else p.name[:2])
            )
            paths.append((p, family, "locked"))
    for p, family, origin in paths:
        if p.stat().st_flags & 0x40000000:
            rows.append(
                {
                    "filename": p.name,
                    "family": family,
                    "origin": origin,
                    "schema_fingerprint": None,
                    "records": None,
                    "missing_required": [],
                    "record_status": "CLOUD_PLACEHOLDER_NOT_READ",
                }
            )
            continue
        with p.open("rb") as stream:
            schema = schema_header(stream)
        missing = required[family] - {f["name"] for f in schema["fields"]}
        signatures[schema["fingerprint"]] = schema["fields"]
        rows.append(
            {
                "filename": p.name,
                "family": family,
                "origin": origin,
                "schema_fingerprint": schema["fingerprint"],
                "records": schema["records"],
                "missing_required": sorted(missing),
            }
        )
    write_json(PROV / "phase3_schema_inventory.json", {"files": rows, "schemas": signatures})
    write_json(
        AUDIT / "phase3_schema_validation.txt",
        {
            "status": "PASS_INSPECTED_FILES"
            if all(not r["missing_required"] for r in rows)
            else "FAIL",
            "files": len(rows),
            "missing_required_fields_files": sum(bool(r["missing_required"]) for r in rows),
            "scope": (
                "Currently materialized DBC headers. All new DBC headers also checked "
                "during acquisition. Record-level validation reported separately."
            ),
            "cloud_placeholders_not_read": sum(
                r.get("record_status") == "CLOUD_PLACEHOLDER_NOT_READ" for r in rows
            ),
            "counts": dict(Counter((r["family"] + "_" + r["origin"]) for r in rows)),
        },
    )


def sim_aggregate(item):
    p = locked_path(item)
    if sha256(p) != item["sha256"]:
        raise ValueError(f"Locked source hash mismatch: {p.name}")
    data = read_dbc(p, ["CAUSABAS", "CODMUNRES", "IDADE", "SEXO"])
    cause = data.CAUSABAS.str[:3]
    data = data.loc[cause.between("X60", "X84")].copy()
    data["age"] = data.IDADE.map(parse_age)
    data["band"] = data.age.map(lambda a: -1 if pd.isna(a) else min(int(a) // 5, 18))
    return data.groupby(["CODMUNRES", "band"]).size().rename("deaths").reset_index()


def parse_age(value):
    if not value or len(value) < 2:
        return None
    value = value.zfill(3)
    if len(value) != 3 or not value.isdigit():
        return None
    if value[0] in "0123":
        return 0
    if value[0] == "4":
        return int(value[1:])
    if value[0] == "5":
        return 100 + int(value[1:])
    return None


def asmr_audit():
    locked = list(csv.DictReader(LOCKED_MANIFEST.open()))
    sim = [r for r in locked if r["source"] == "SIM/DATASUS DORES"]
    region = pd.read_parquet(ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet")
    cross = pd.read_parquet(
        ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
    )
    print("canonical columns", region.columns.tolist(), flush=True)
    print("crosswalk columns", cross.columns.tolist(), flush=True)
    mun_col = "municipality_code_ibge"
    if mun_col not in cross:
        mun_col = "municipality_code"
    mapping = dict(
        zip(cross[mun_col].astype(str).str[:6], cross.health_region_code.astype(str), strict=False)
    )
    cache = STAGING / "sim_locked_suicide_age.parquet"
    STAGING.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        deaths = pd.read_parquet(cache)
    else:
        parts = []
        with ProcessPoolExecutor(max_workers=3) as pool:
            for i, data in enumerate(pool.map(sim_aggregate, sim)):
                parts.append(data)
                if (i + 1) % 9 == 0:
                    print(f"SIM processed {i + 1}/{len(sim)}", flush=True)
        deaths = pd.concat(parts).groupby(["CODMUNRES", "band"], as_index=False).deaths.sum()
        deaths.to_parquet(cache, index=False)
    deaths["health_region_code"] = deaths.CODMUNRES.map(mapping)
    deaths = deaths.dropna(subset=["health_region_code"])
    d = deaths.groupby(["health_region_code", "band"]).deaths.sum()
    source_dir = Path(locked[0]["filename"]).parents[2]
    pop = pd.read_csv(
        source_dir / "data_intermediate/population_health_region_age.csv",
        dtype={"health_region_code": str},
    )
    pop["band"] = pop.age_band.str.split("-").str[0].astype(int) // 5
    p = pop.groupby(["health_region_code", "band"]).population.sum()
    joined = p.rename("population").to_frame().join(d, how="left").fillna({"deaths": 0})
    w = np.array(WEIGHTS) / sum(WEIGHTS)
    joined["contribution"] = (
        joined.deaths
        / joined.population
        * 1e5
        * joined.index.get_level_values("band").map(dict(enumerate(w)))
    )
    legacy = joined.groupby(level=0).contribution.sum()
    d80 = d[d.index.get_level_values("band") >= 16].groupby(level=0).sum()
    p80 = p[p.index.get_level_values("band") == 16].droplevel(1)
    legacy80 = joined[joined.index.get_level_values("band") == 16].contribution.droplevel(1)
    corrected = (
        legacy - legacy80 + d80.reindex(legacy.index, fill_value=0) / p80 * 1e5 * w[16:].sum()
    )
    canonical = region.set_index(region.health_region_code.astype(str)).suicide_asmr.reindex(
        legacy.index
    )
    differences = corrected - canonical
    canonical_rows = region.set_index(region.health_region_code.astype(str)).reindex(legacy.index)
    corrected_percentile = (corrected.rank(method="average") - 1) / (len(corrected) - 1)
    diagnostic_need = (corrected_percentile + canonical_rows.psychiatric_admission_percentile) / 2
    need_difference = diagnostic_need - canonical_rows.need_score
    audit = {
        "status": "BLOCKED_SCIENTIFIC_AGE_BAND_INCOMPATIBILITY",
        "source_definition": (
            "POPSVS IDADE=080 means 80 years and over; no 85-89 or 90+ denominators."
        ),
        "locked_implementation": (
            "Assigns IDADE=080 to 80-84; joins from population, omitting 85+ deaths from ASMR."
        ),
        "regions": len(legacy),
        "source_files_processed": len(sim),
        "deaths_age_80_84": int(d[d.index.get_level_values("band") == 16].sum()),
        "deaths_age_85_89": int(d[d.index.get_level_values("band") == 17].sum()),
        "deaths_age_90_plus": int(d[d.index.get_level_values("band") == 18].sum()),
        "regions_with_age_85_plus_deaths": int(
            (d[d.index.get_level_values("band") >= 17].groupby(level=0).sum() > 0).sum()
        ),
        "legacy_reproduction_max_abs_difference": float((legacy - canonical).abs().max()),
        "diagnostic_80_plus_max_abs_difference_from_canonical": float(differences.abs().max()),
        "diagnostic_80_plus_median_difference_from_canonical": float(differences.median()),
        "diagnostic_regions_different_gt_1e_minus12": int((differences.abs() > 1e-12).sum()),
        "diagnostic_need_regions_different_gt_1e_minus12": int(
            (need_difference.abs() > 1e-12).sum()
        ),
        "diagnostic_need_max_abs_difference": float(need_difference.abs().max()),
        "diagnostic_only": True,
        "decision": (
            "Cannot both preserve locked scientific definition/exact reproduction and apply "
            "valid 80+ age standardization. No canonical changes authorized or made."
        ),
    }
    write_json(AUDIT / "phase3_asmr_age_compatibility.json", audit)
    pd.DataFrame(
        {
            "legacy_reconstructed": legacy,
            "canonical": canonical,
            "diagnostic_80_plus": corrected,
            "absolute_difference": differences.abs(),
        }
    ).to_csv(AUDIT / "phase3_asmr_age_impact_by_region.csv", index_label="health_region_code")
    print(json.dumps(audit, indent=2), flush=True)


def siops_inventory():
    results = []
    for path in sorted(RAW.glob("SIOPS/*.zip")):
        year = path.name.split("_")[2]
        extracted = path.with_suffix(".csv")
        with zipfile.ZipFile(path) as archive:
            member = archive.namelist()[0]
            if not extracted.exists():
                with archive.open(member) as source, extracted.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
        values = {c: set() for c in ["Ano", "UF", "Fonte", "Subfuncao", "Fase", "Codigo"]}
        municipalities = set()
        rows, missing, invalid_values = 0, Counter(), 0
        roots, all_totals = Counter(), Counter()
        columns = None
        for chunk in pd.read_csv(
            extracted,
            encoding="utf-8-sig",
            sep=";",
            dtype=str,
            keep_default_na=False,
            chunksize=100000,
        ):
            columns = chunk.columns.tolist()
            rows += len(chunk)
            municipalities.update(chunk["Cód.Município"])
            for col in values:
                values[col].update(chunk[col])
            missing.update({c: int((chunk[c] == "").sum()) for c in chunk})
            valid = chunk.Valor.str.fullmatch(r"-?\d+\.\d{2}")
            invalid_values += int((~valid).sum())
            chunk = chunk.loc[valid].copy()
            chunk["cents"] = chunk.Valor.str.replace(".", "", regex=False).astype("int64")
            for phase, amount in chunk.groupby("Fase").cents.sum().items():
                all_totals[phase] += int(amount)
            top = chunk[chunk.Codigo.isin(["3.0.00.00.00.00", "4.0.00.00.00.00"])]
            for phase, amount in top.groupby("Fase").cents.sum().items():
                roots[phase] += int(amount)
        result = {
            "year": year,
            "zip_sha256": sha256(path),
            "csv_sha256": sha256(extracted),
            "csv_size_bytes": extracted.stat().st_size,
            "csv_member": member,
            "encoding": "utf-8-sig",
            "delimiter": ";",
            "decimal_separator": ".",
            "rows": rows,
            "columns": columns,
            "column_count": len(columns),
            "distinct": {c: sorted(v) for c, v in values.items()},
            "municipalities": len(municipalities),
            "missing_counts": dict(missing),
            "invalid_money_values": invalid_values,
            "all_rows_totals_cents_DIAGNOSTIC_NOT_VALID_AGGREGATION": dict(all_totals),
            "root_categories_totals_cents_NOT_YET_RECONCILED": dict(roots),
            "reconciliation": "NOT_COMPLETED_SCIENTIFIC_STOP_IN_TEMPORAL_GATE",
        }
        results.append(result)
        print(f"SIOPS {year}: {rows} rows; {len(municipalities)} municipalities", flush=True)
        write_json(PROV / "phase3_siops_schema_inventory.json", results)


def flow_sample_one(pair):
    rd_item, st_item = pair
    rd_path, st_path = locked_path(rd_item), locked_path(st_item)
    for path, item in [(rd_path, rd_item), (st_path, st_item)]:
        if sha256(path) != item["sha256"]:
            raise ValueError(f"Locked source hash mismatch: {path.name}")
    rd = read_dbc(rd_path, ["MUNIC_RES", "MUNIC_MOV", "CNES", "DIAG_PRINC"])
    st = read_dbc(st_path, ["CNES", "CODUFMUN"])
    unique = st.drop_duplicates()
    ambiguous = unique.CNES[unique.CNES.duplicated(keep=False)]
    mapping = unique.loc[~unique.CNES.isin(ambiguous)].set_index("CNES").CODUFMUN
    expected = rd.CNES.map(mapping)
    matchable = expected.notna()
    agreement = rd.MUNIC_MOV == expected
    diagnosis = rd.DIAG_PRINC.str[:3]
    psychiatric = diagnosis.between("F00", "F09") | diagnosis.between("F20", "F99")
    return {
        "uf": rd_path.name[2:4],
        "competence": "2024-12",
        "records": len(rd),
        "matchable": int(matchable.sum()),
        "agreement": int(agreement.sum()),
        "disagreement": int((matchable & ~agreement).sum()),
        "unmatched_cnes": int((~matchable).sum()),
        "ambiguous_cnes": int(ambiguous.nunique()),
        "psychiatric_records": int(psychiatric.sum()),
        "psychiatric_matchable": int((psychiatric & matchable).sum()),
        "psychiatric_agreement": int((psychiatric & agreement).sum()),
    }


def flow_sample():
    locked = list(csv.DictReader(LOCKED_MANIFEST.open()))
    st = {Path(r["filename"]).name[2:4]: r for r in locked if r["source"] == "CNES ST"}
    pairs = [
        (r, st[Path(r["filename"]).name[2:4]])
        for r in locked
        if r["source"] == "SIH/SUS RD" and r["period"] == "2024-12"
    ]
    rows = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        for result in pool.map(flow_sample_one, pairs):
            rows.append(result)
            print(
                "MUNIC_MOV sample",
                result["uf"],
                result["agreement"],
                result["disagreement"],
                flush=True,
            )
    sums = {k: sum(r[k] for r in rows) for k in rows[0] if k not in {"uf", "competence"}}
    write_json(
        AUDIT / "phase3_munic_mov_empirical_validation.json",
        {
            "status": "EMPIRICAL_SAMPLE_COMPLETED",
            "uf_count": len(rows),
            "competence": "2024-12",
            "official_definition": (
                "IT_SIHSUS_1603.pdf, Table 1, field 49: Municipio do Estabelecimento."
            ),
            "totals": sums,
            "agreement_rate_among_linked": sums["agreement"] / sums["matchable"],
            "psychiatric_agreement_rate_among_linked": sums["psychiatric_agreement"]
            / sums["psychiatric_matchable"],
            "by_uf": rows,
            "limitation": (
                "One national competence sample; pooled 2022-2024 reconciliation not completed "
                "because temporal scientific gate stopped implementation."
            ),
        },
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["schemas", "asmr", "siops", "flows"])
    args = parser.parse_args()
    {"schemas": schemas, "asmr": asmr_audit, "siops": siops_inventory, "flows": flow_sample}[
        args.mode
    ]()


if __name__ == "__main__":
    main()

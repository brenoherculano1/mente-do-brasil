"""Rebuild fixed-geography temporal anchors from hash-verified official sources."""

from __future__ import annotations

import csv
import json
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.acquire_phase3_sources import schema_header
from scripts.build_scientific_correction import (
    ROOT,
    asmr_from_bands,
    materialized_source,
    percentile,
    sha256,
    verify_history,
)
from scripts.validate_phase3_source_gate import parse_age, read_dbc, selected_dbf

CURRENT = "MDB_ANALYTICAL_2024_2"
VERSION = "MDB_TEMPORAL_2022_2024_1"
CACHE = ROOT / "data/staging/phase3/temporal"
OUT = ROOT / f"data/product_intelligence/{CURRENT}"
AUDIT = ROOT / "audit_results/advanced_temporal"
COMPONENTS = {
    "suicide_asmr": "suicide_percentile",
    "psychiatric_admission_rate": "psychiatric_admission_percentile",
    "caps_rate": "caps_percentile",
    "mental_health_beds_sus_rate": "beds_percentile",
    "psychiatrist_fte_rate": "psychiatrist_fte_percentile",
}


def source_rows():
    rows = []
    for item in csv.DictReader(
        (ROOT / "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv").open()
    ):
        name = Path(item["filename"]).name
        family = (
            "population"
            if name.startswith("POPS")
            else ("SIM" if name.startswith("DO") else "SIH" if name.startswith("RD") else name[:2])
        )
        rows.append(
            {
                "name": name,
                "family": family,
                "year": int(item["period"][:4]),
                "path": item["filename"],
                "url": item["url"],
                "sha256": item["sha256"],
            }
        )
    for item in csv.DictReader((ROOT / "metadata/provenance/phase3_source_manifest.csv").open()):
        if item["dataset"] not in {"SIM", "SIH", "CNES", "population"}:
            continue
        family = item["dataset"] if item["dataset"] != "CNES" else item["original_filename"][:2]
        rows.append(
            {
                "name": item["original_filename"],
                "family": family,
                "year": int(item["period"][:4]),
                "path": str(ROOT / item["local_path"]),
                "url": item["official_url"],
                "sha256": item["sha256"],
            }
        )
    names = [r["name"] for r in rows]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate source filename")
    expected = {"population": 5, "SIM": 135, "SIH": 1620, "ST": 81, "LT": 81, "PF": 81}
    counts = pd.Series([r["family"] for r in rows]).value_counts().to_dict()
    if counts != expected:
        raise ValueError(f"Incomplete temporal sources: {counts}")
    return sorted(rows, key=lambda r: r["name"])


def resolve_source(item):
    candidate = Path(item["path"])
    alternatives = [
        candidate,
        ROOT / "data/raw/phase3/locked_recovery" / item["name"],
        Path("/tmp/mdb-flow-recovery-20260831") / item["name"],
    ]
    for candidate in alternatives:
        if candidate.exists() and not (candidate.stat().st_flags & 0x40000000):
            if sha256(candidate) != item["sha256"]:
                raise ValueError(f"Source hash mismatch: {candidate}")
            return candidate
    url = item["url"]
    if not url.startswith(("ftp://", "https://", "http://")):
        raise ValueError(f"Source unavailable with no official recovery URL: {item['name']}")
    return materialized_source(Path(item["path"]), url, item["sha256"])


def aggregate_one(item):
    cached = CACHE / f"{item['name']}.{item['sha256']}.parquet"
    receipt = cached.with_suffix(".json")
    if cached.exists() and receipt.exists():
        metadata = json.loads(receipt.read_text())
        if metadata["output_sha256"] != sha256(cached):
            raise ValueError(f"Temporal cache corrupted: {cached.name}")
        return pd.read_parquet(cached), item
    path = resolve_source(item)
    family = item["family"]
    if family == "population":
        with tempfile.TemporaryDirectory(prefix="mdb-temporal-pop-") as directory:
            with zipfile.ZipFile(path) as archive:
                members = [n for n in archive.namelist() if n.lower().endswith(".dbf")]
                if len(members) != 1:
                    raise ValueError("Ambiguous population DBF")
                dbf = Path(directory) / "population.dbf"
                dbf.write_bytes(archive.read(members[0]))
            data = selected_dbf(dbf, ["COD_MUN", "ANO", "SEXO", "IDADE", "POP"])
        if data.duplicated(["COD_MUN", "ANO", "SEXO", "IDADE"]).any():
            raise ValueError("Duplicate population keys")
        if set(data.ANO) != {str(item["year"])} or set(data.IDADE.astype(int)) != set(range(81)):
            raise ValueError("Population year/age definition differs")
        data["municipality"] = data.COD_MUN.str[:6]
        data["band"] = np.minimum(data.IDADE.astype(int) // 5, 16)
        data["population"] = data.POP.astype("int64")
        result = data.groupby(["municipality", "band"], as_index=False).population.sum()
    elif family == "SIM":
        data = read_dbc(path, ["CODMUNRES", "CAUSABAS", "IDADE"])
        data = data.loc[data.CAUSABAS.str[:3].between("X60", "X84")].copy()
        data["band"] = data.IDADE.map(parse_age).map(
            lambda a: -1 if pd.isna(a) else min(int(a) // 5, 16)
        )
        result = data.groupby(["CODMUNRES", "band"]).size().rename("suicide_deaths").reset_index()
        result = result.rename(columns={"CODMUNRES": "municipality"})
    elif family == "SIH":
        data = read_dbc(path, ["MUNIC_RES", "MUNIC_MOV", "DIAG_PRINC"])
        code = data.DIAG_PRINC.str[:3]
        data = data.loc[code.between("F00", "F09") | code.between("F20", "F99")]
        result = data.groupby(["MUNIC_RES", "MUNIC_MOV"]).size().rename("admissions").reset_index()
        result = result.rename(columns={"MUNIC_RES": "municipality", "MUNIC_MOV": "destination"})
    elif family == "ST":
        data = read_dbc(path, ["CNES", "CODUFMUN", "TP_UNID"])
        result = data.loc[data.TP_UNID.eq("70"), ["CNES", "CODUFMUN"]]
        result = result.rename(columns={"CODUFMUN": "municipality"})
    elif family == "LT":
        data = read_dbc(path, ["CNES", "CODUFMUN", "TP_UNID", "CODLEITO", "QT_SUS"])
        result = data.loc[data.TP_UNID.eq("05") & data.CODLEITO.eq("87")].copy()
        result["beds"] = pd.to_numeric(result.QT_SUS.replace("", "0"), errors="raise")
        result = result.rename(columns={"CODUFMUN": "municipality"})[["municipality", "beds"]]
    else:
        with path.open("rb") as stream:
            fields = {f["name"] for f in schema_header(stream)["fields"]}
        identity = ["CNS_PROF", "CPF_PROF", "NOMEPROF"]
        linkage = ["VINCULAC", "VINCUL_C", "VINCUL_A", "VINCUL_N"]
        columns = ["CNES", "CODUFMUN", "CBO", "PROF_SUS", "HORA_AMB", "HORAHOSP", "HORAOUTR"]
        data = read_dbc(path, columns + [c for c in identity + linkage if c in fields])
        data = data.loc[data.CBO.eq("225133") & data.PROF_SUS.eq("1")].copy()
        for column in identity + linkage:
            if column not in data:
                data[column] = ""
        data["person"] = data.CNS_PROF.mask(data.CNS_PROF.eq(""), data.CPF_PROF)
        data["person"] = data.person.mask(data.person.eq(""), data.NOMEPROF)
        if data.person.eq("").any():
            raise ValueError("Cannot reproduce psychiatrist deduplication without identity")
        hours = (
            data[["HORA_AMB", "HORAHOSP", "HORAOUTR"]]
            .replace("", "0")
            .apply(pd.to_numeric, errors="raise")
        )
        if hours.lt(0).any().any():
            raise ValueError("Negative psychiatrist weekly hours")
        data["hours"] = hours.sum(axis=1)
        key = ["CNES", "person", "CBO", "PROF_SUS", "hours", *linkage]
        # Original scientific key, hashed locally. No identity is written to the cache.
        import hashlib

        data["link_key"] = data[key].apply(
            lambda row: hashlib.sha256(json.dumps(row.tolist()).encode()).hexdigest(), axis=1
        )
        result = data.rename(columns={"CODUFMUN": "municipality"})[
            ["municipality", "link_key", "hours"]
        ]
    result["year"] = item["year"]
    cached.parent.mkdir(parents=True, exist_ok=True)
    temporary = cached.with_suffix(".tmp")
    result.to_parquet(temporary, index=False)
    temporary.replace(cached)
    receipt.write_text(
        json.dumps({"source_sha256": item["sha256"], "output_sha256": sha256(cached)}) + "\n"
    )
    return result, item


def score(frame):
    frame = frame.copy()
    for metric, output in COMPONENTS.items():
        frame[output] = percentile(frame[metric])
    frame["need_score"] = (frame.suicide_percentile + frame.psychiatric_admission_percentile) / 2
    frame["capacity_score"] = (
        frame.caps_percentile + frame.beds_percentile + frame.psychiatrist_fte_percentile
    ) / 3
    frame["mismatch_score"] = frame.need_score - frame.capacity_score
    return frame


def changes(temporal):
    parts = []
    metrics = ["need_score", "capacity_score", "mismatch_score", *COMPONENTS.values()]
    for start, end in ((2022, 2023), (2023, 2024), (2022, 2024)):
        a = temporal.loc[temporal.year.eq(start)].set_index("health_region_code").sort_index()
        b = temporal.loc[temporal.year.eq(end)].set_index("health_region_code").sort_index()
        if not a.index.equals(b.index):
            raise ValueError("Temporal geography mismatch")
        frame = (b[metrics] - a[metrics]).add_prefix("delta_")
        frame["NEED_POSITION_UP"] = frame.delta_need_score.ge(0.15)
        frame["CAPACITY_POSITION_DOWN"] = frame.delta_capacity_score.le(-0.15)
        frame["MISMATCH_POSITION_UP"] = frame.delta_mismatch_score.ge(0.20)
        frame["NEED_COMPONENT_POSITION_UP"] = frame.delta_suicide_percentile.ge(
            0.20
        ) | frame.delta_psychiatric_admission_percentile.ge(0.20)
        frame["CAPACITY_COMPONENT_POSITION_DOWN"] = (
            frame[
                [
                    "delta_caps_percentile",
                    "delta_beds_percentile",
                    "delta_psychiatrist_fte_percentile",
                ]
            ]
            .le(-0.20)
            .any(axis=1)
        )
        families = [c for c in frame if c.isupper()]
        frame["matched_change_families"] = frame[families].sum(axis=1).astype(int)
        frame["from_year"], frame["to_year"] = start, end
        frame["change_version"] = "MDB_CHANGE_RADAR_RULESET_1.0"
        parts.append(frame.reset_index())
    return pd.concat(parts, ignore_index=True).sort_values(
        ["from_year", "to_year", "health_region_code"]
    )


def main():
    verify_history()
    rows = source_rows()
    AUDIT.mkdir(parents=True, exist_ok=True)
    cross = pd.read_parquet(
        ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
    )
    mapping = dict(zip(cross.municipality_code_datasus6, cross.health_region_code, strict=True))
    current = (
        pd.read_parquet(ROOT / f"data/canonical/{CURRENT}/health_regions.parquet")
        .set_index("health_region_code")
        .sort_index()
    )
    grouped = {f: [] for f in {r["family"] for r in rows}}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, (frame, item) in enumerate(pool.map(aggregate_one, rows), 1):
            frame["health_region_code"] = frame.municipality.str[:6].map(mapping)
            unmapped = frame.health_region_code.isna()
            if unmapped.any() and item["family"] not in {"SIM", "SIH"}:
                raise ValueError(f"Unmapped municipality in {item['name']}")
            grouped[item["family"]].append(frame.loc[~unmapped])
            if i % 100 == 0:
                print(f"Temporal sources {i}/{len(rows)}", flush=True)
    tables = {family: pd.concat(parts, ignore_index=True) for family, parts in grouped.items()}
    population = (
        tables["population"].groupby(["year", "health_region_code", "band"]).population.sum()
    )
    suicide = tables["SIM"]
    admissions = tables["SIH"]
    anchors = []
    for year in (2022, 2023, 2024):
        frame = current[["health_region_name", "uf", "geography_version"]].copy()
        pop = population.loc[year].groupby(level=0).sum()
        pooled_pop = (
            population.loc[list(range(year - 2, year + 1))].groupby(level=[1, 2]).sum().sort_index()
        )
        deaths = suicide.loc[suicide.year.between(year - 2, year)]
        bands = (
            deaths.loc[deaths.band.ge(0)]
            .groupby(["health_region_code", "band"])
            .suicide_deaths.sum()
            .reindex(pooled_pop.index, fill_value=0)
        )
        frame["population"] = pop
        frame["person_years"] = pooled_pop.groupby(level=0).sum()
        frame["suicide_deaths"] = (
            deaths.groupby("health_region_code")
            .suicide_deaths.sum()
            .reindex(frame.index, fill_value=0)
        )
        frame["suicide_asmr"] = asmr_from_bands(bands, pooled_pop)
        frame["psychiatric_admissions"] = (
            admissions.loc[admissions.year.between(year - 2, year)]
            .groupby("health_region_code")
            .admissions.sum()
            .reindex(frame.index, fill_value=0)
        )
        frame["psychiatric_admission_rate"] = (
            frame.psychiatric_admissions / frame.person_years * 100000
        )
        caps = tables["ST"].loc[tables["ST"].year.eq(year)]
        beds = tables["LT"].loc[tables["LT"].year.eq(year)]
        pf = tables["PF"].loc[tables["PF"].year.eq(year)].drop_duplicates("link_key")
        frame["caps_count"] = (
            caps.groupby("health_region_code").CNES.nunique().reindex(frame.index, fill_value=0)
        )
        frame["mental_health_beds_sus_count"] = (
            beds.groupby("health_region_code").beds.sum().reindex(frame.index, fill_value=0)
        )
        # Preserve the original ordered floating-point accumulation, not just its algebra.
        fte = {}
        for link in pf.itertuples(index=False):
            fte[link.health_region_code] = fte.get(link.health_region_code, 0.0) + link.hours / 40.0
        frame["psychiatrist_fte"] = pd.Series(fte).reindex(frame.index, fill_value=0)
        for count, rate in (
            ("caps_count", "caps_rate"),
            ("mental_health_beds_sus_count", "mental_health_beds_sus_rate"),
            ("psychiatrist_fte", "psychiatrist_fte_rate"),
        ):
            frame[rate] = frame[count] / frame.population * 100000
        frame = score(frame)
        frame["year"] = year
        frame["need_window_start"], frame["need_window_end"] = year - 2, year
        frame["capacity_competence"] = f"{year}-12"
        frame["temporal_version"] = VERSION
        frame["release_id"] = CURRENT
        frame["quality_flags"] = frame.apply(
            lambda row: [
                flag
                for flag, match in (
                    ("SMALL_SUICIDE_COUNT", row.suicide_deaths < 10),
                    ("ZERO_REGISTERED_BEDS", row.mental_health_beds_sus_count == 0),
                )
                if match
            ],
            axis=1,
        )
        anchors.append(frame.reset_index())
    temporal = pd.concat(anchors, ignore_index=True)
    numeric = [
        "suicide_deaths",
        "psychiatric_admissions",
        "caps_count",
        "mental_health_beds_sus_count",
        "psychiatrist_fte",
        "need_score",
        "capacity_score",
        "mismatch_score",
        *COMPONENTS,
        *COMPONENTS.values(),
    ]
    reproduced = temporal.loc[temporal.year.eq(2024)].set_index("health_region_code").sort_index()
    deltas = {c: float((reproduced[c] - current[c]).abs().max()) for c in numeric}
    result = {
        "status": "PASS" if all(v <= 1e-12 for v in deltas.values()) else "FAIL_2024_REPRODUCTION",
        "rows": len(temporal),
        "max_abs_diff": deltas,
    }
    (AUDIT / "temporal_2024_reproduction.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    if result["status"] != "PASS":
        raise ValueError("Temporal 2024 does not reproduce the corrected release")
    if len(temporal) != 1317 or temporal[numeric].isna().any().any():
        raise ValueError("Temporal count/null validation failed")
    temporal.to_parquet(OUT / "health_region_temporal.parquet", index=False)
    changes(temporal).to_parquet(OUT / "health_region_changes.parquet", index=False)
    # Preserve unsuppressed municipal counts only in the private staging layer.
    admissions.to_parquet(CACHE / "annual_municipal_admissions.parquet", index=False)


if __name__ == "__main__":
    main()

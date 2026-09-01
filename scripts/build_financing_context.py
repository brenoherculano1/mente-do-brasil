"""Build the frozen, regional SIOPS financing context from official report totals."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

from scripts.build_scientific_correction import materialized_source, selected_dbf, sha256

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl"
LOCKED = ROOT / "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv"
CROSSWALK = (
    ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
)
CANONICAL = ROOT / "data/canonical/MDB_ANALYTICAL_2024_2/health_regions.parquet"
OUT = ROOT / "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_financing.parquet"


def populations(*, offline: bool = False) -> pd.DataFrame:
    cross = pd.read_parquet(CROSSWALK)
    mapping = dict(
        zip(cross.municipality_code_ibge.astype(str), cross.health_region_code, strict=True)
    )
    manifest = list(csv.DictReader(LOCKED.open()))
    parts = []
    for year in (2022, 2023, 2024):
        item = next(
            r for r in manifest if r["source"] == "DATASUS IBGE POPSVS" and r["period"] == str(year)
        )
        if offline:
            path = ROOT / "data/raw/scientific_correction_recovery" / Path(item["filename"]).name
            if not path.is_file() or sha256(path) != item["sha256"]:
                raise ValueError(f"Offline POPSVS source missing or hash mismatch: {path.name}")
        else:
            path = materialized_source(Path(item["filename"]), item["url"], item["sha256"])
        with tempfile.TemporaryDirectory(prefix="mdb-financing-pop-") as directory:
            member = zipfile.ZipFile(path).namelist()
            dbf = Path(directory) / "population.dbf"
            dbf.write_bytes(
                zipfile.ZipFile(path).read(
                    next(name for name in member if name.lower().endswith(".dbf"))
                )
            )
            frame = selected_dbf(dbf, ["COD_MUN", "ANO", "SEXO", "IDADE", "POP"])
        if frame.duplicated(["COD_MUN", "ANO", "SEXO", "IDADE"]).any():
            raise ValueError("Duplicate POPSVS population key")
        if set(frame.ANO) != {str(year)}:
            raise ValueError("Unexpected POPSVS reference year")
        frame["health_region_code"] = frame.COD_MUN.map(mapping)
        if frame.health_region_code.isna().any():
            raise ValueError("Unmapped POPSVS municipality; expected seven-digit IBGE codes")
        frame["population"] = frame.POP.astype("int64")
        frame["municipality"] = frame.COD_MUN.str[:6]
        parts.append(
            frame.groupby(["health_region_code", "municipality"], as_index=False)
            .population.sum()
            .assign(year=year)
        )
    return pd.concat(parts, ignore_index=True)


def build(*, output: Path = OUT, offline: bool = False) -> dict:
    cross = pd.read_parquet(CROSSWALK)
    expected = (
        cross.groupby("health_region_code")
        .agg(
            municipalities_expected=("municipality_code_datasus6", "nunique"),
        )
        .reset_index()
    )
    with SNAPSHOT.open() as stream:
        snap = pd.DataFrame(json.loads(line) for line in stream if line.strip())
    snap["municipality"] = snap.municipality.astype(str).str.zfill(6)
    snap["year"] = snap.year.astype(int)
    snap_ok = snap[snap.status == "ok"].copy()
    region_map = dict(
        zip(
            cross.municipality_code_datasus6.astype(str).str.zfill(6),
            cross.health_region_code,
            strict=True,
        )
    )
    snap_ok["health_region_code"] = snap_ok.municipality.map(region_map)
    annual = snap_ok.groupby(["year", "health_region_code"], as_index=False).agg(
        municipalities_observed=("municipality", "nunique"),
        total_health_expenditure_brl=("group17_total_brl", "sum"),
    )
    out = pd.MultiIndex.from_product(
        [(2022, 2023, 2024), sorted(expected.health_region_code)],
        names=["year", "health_region_code"],
    ).to_frame(index=False)
    out = out.merge(expected, on="health_region_code", how="left").merge(
        annual, on=["year", "health_region_code"], how="left"
    )
    municipal_pop = populations(offline=offline)
    pop = municipal_pop.groupby(["year", "health_region_code"], as_index=False).population.sum()
    pop = pop.rename(columns={"population": "population_expected"})
    out = out.merge(pop, on=["year", "health_region_code"], how="left")
    if len(pop) != 1317 or not out.population_expected.gt(0).all():
        raise ValueError("Incomplete or nonpositive regional population")
    covered = (
        municipal_pop.merge(
            snap_ok[["year", "municipality"]], on=["year", "municipality"], validate="one_to_one"
        )
        .groupby(["year", "health_region_code"], as_index=False)
        .population.sum()
    )
    out = out.merge(
        covered.rename(columns={"population": "population_covered"}),
        on=["year", "health_region_code"],
        how="left",
    )
    # Zero here means no covered municipalities, never zero expenditure.
    out["population_covered"] = out.population_covered.fillna(0).astype("int64")
    out["municipalities_observed"] = out.municipalities_observed.fillna(0).astype(int)
    out["coverage_share"] = out.municipalities_observed / out.municipalities_expected
    out["headline_available"] = out.coverage_share.eq(1) & out.total_health_expenditure_brl.notna()
    out.loc[~out.headline_available, "total_health_expenditure_brl"] = pd.NA
    out["health_expenditure_per_capita_brl"] = (
        out.total_health_expenditure_brl / out.population_expected
    )
    out["quality_flags"] = out.apply(
        lambda row: "" if row.headline_available else "PARTIAL_SIOPS_COVERAGE", axis=1
    )
    out["financing_version"] = "MDB_FINANCING_CONTEXT_1.0"
    out["siops_snapshot_id"] = "MDB_SIOPS_SNAPSHOT_20260831_1"
    out["coverage_population_share"] = out.population_covered / out.population_expected
    out["source_period"] = "2"
    out["source_indicator"] = "grupo=17 Total; Indicator 2.1 validated in stratified sample"
    out = out[
        [
            "financing_version",
            "siops_snapshot_id",
            "year",
            "health_region_code",
            "municipalities_expected",
            "municipalities_observed",
            "population_expected",
            "population_covered",
            "coverage_share",
            "coverage_population_share",
            "total_health_expenditure_brl",
            "health_expenditure_per_capita_brl",
            "headline_available",
            "quality_flags",
            "source_period",
            "source_indicator",
        ]
    ].sort_values(["year", "health_region_code"])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".parquet.tmp")
    out.to_parquet(temporary, index=False)
    temporary.replace(output)
    result = {
        "rows": len(out),
        "full_coverage_rows": int(out.headline_available.sum()),
        "partial_rows": int((~out.headline_available).sum()),
        "output": str(output),
        "sha256": sha256(output),
        "source_snapshot_rows": len(snap),
        "source_snapshot_successes": int((snap.status == "ok").sum()),
        "population_nulls": int(out.population_expected.isna().sum()),
        "available_per_capita_values": int(out.health_expenditure_per_capita_brl.notna().sum()),
        "annual_population": {
            str(y): int(v) for y, v in out.groupby("year").population_expected.sum().items()
        },
        "superseded_output_sha256": (
            "e0268253e318473824312ed3125a01ea73be8d795457ac6e09f568ab9b140985"
        ),
        "missing_not_zero": bool(
            out.loc[~out.headline_available, "total_health_expenditure_brl"].isna().all()
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = build(output=args.output, offline=args.offline)
    if args.output.resolve() == OUT.resolve():
        (ROOT / "audit_results/siops_financing_build.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

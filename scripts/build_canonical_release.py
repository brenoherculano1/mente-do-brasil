"""Build the canonical Mente do Brasil analytical data layer.

This script transforms locked scientific outputs into product-ready canonical
tables. It validates source hashes and joins, but it does not recalculate the
scientific metrics.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

RELEASE_ID = "MDB_ANALYTICAL_2024_1"
CANONICAL_VERSION = "MDB_CANONICAL_1.0"
METHOD_VERSION = "MDB_METHOD_1.0"
GEOGRAPHY_VERSION = "BR_HEALTH_REGIONS_END2024_V1"
BUNDLE_ID = "MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24"

EXPECTED_HEALTH_REGIONS = 439
EXPECTED_MUNICIPALITIES = 5570
EXPECTED_SMALL_SUICIDE_COUNT = 7
EXPECTED_ZERO_REGISTERED_BEDS = 275

RAW_ROOT = Path("data/raw/imported") / BUNDLE_ID / "mdb_import_bundle"
CANONICAL_ROOT = Path("data/canonical") / RELEASE_ID
MANIFEST_PATH = Path("metadata/releases") / f"{RELEASE_ID}_canonical.yaml"

ANALYTICAL = RAW_ROOT / "analytical_release/health_region_analysis_dataset_corrected.csv"
LISA = RAW_ROOT / "analytical_release/LISA_primary_corrected.csv"
SUPPLEMENT = RAW_ROOT / "analytical_release/corrected_Supplement_All_439_Health_Regions.csv"
CROSSWALK = RAW_ROOT / "geography/health_region_crosswalk_LOCKED.csv"
GPKG = RAW_ROOT / "geography/health_regions_LOCKED.gpkg"
GLOBAL_MORAN = RAW_ROOT / "analytical_release/global_moran_primary_corrected.json"
OUTPUT_MANIFEST = Path("metadata/releases") / f"{RELEASE_ID}_outputs.yaml"

HEALTH_REGIONS_OUTPUT = CANONICAL_ROOT / "health_regions.parquet"
CROSSWALK_OUTPUT = CANONICAL_ROOT / "municipality_health_region_crosswalk.parquet"

UF_CODE_TO_UF = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

CANONICAL_COLUMNS = [
    "release_id",
    "method_version",
    "geography_version",
    "health_region_code",
    "health_region_name",
    "uf_code",
    "uf",
    "municipality_count",
    "population",
    "area_km2",
    "population_density",
    "suicide_deaths",
    "suicide_asmr",
    "suicide_percentile",
    "psychiatric_admissions",
    "psychiatric_admission_rate",
    "psychiatric_admission_percentile",
    "caps_count",
    "caps_rate",
    "caps_percentile",
    "mental_health_beds_sus_count",
    "mental_health_beds_sus_rate",
    "beds_percentile",
    "psychiatrist_fte",
    "psychiatrist_fte_rate",
    "psychiatrist_fte_percentile",
    "need_score",
    "capacity_score",
    "mismatch_score",
    "lisa_local_i",
    "lisa_p",
    "lisa_q",
    "lisa_significant",
    "lisa_cluster",
    "data_quality_flags",
]

SOURCE_MAPPING = {
    "health_region_code": "health_region_code",
    "health_region_name": "health_region_name",
    "municipality_count": "municipality_count",
    "population": "population_2024",
    "area_km2": "area_km2",
    "population_density": "population_density_2024",
    "suicide_deaths": "deaths_pooled",
    "suicide_asmr": "ASMR",
    "suicide_percentile": "suicide_percentile",
    "psychiatric_admissions": "admission_n",
    "psychiatric_admission_rate": "admission_rate",
    "psychiatric_admission_percentile": "admissions_percentile",
    "caps_count": "unique_CAPS_n",
    "caps_rate": "CAPS_rate_per_100k",
    "caps_percentile": "CAPS_percentile",
    "mental_health_beds_sus_count": "SUS_mental_health_beds_n",
    "mental_health_beds_sus_rate": "bed_rate_per_100k",
    "beds_percentile": "beds_percentile",
    "psychiatrist_fte": "psychiatrist_FTE",
    "psychiatrist_fte_rate": "FTE_rate_per_100k",
    "psychiatrist_fte_percentile": "FTE_percentile",
    "need_score": "Need_r",
    "capacity_score": "Capacity_r",
    "mismatch_score": "Mismatch_r",
}

LISA_MAPPING = {
    "lisa_local_i": "local_I",
    "lisa_p": "raw_pseudo_p",
    "lisa_q": "BH_adjusted_q",
    "lisa_cluster": "cluster_label",
}

HEALTH_REGION_SCHEMA = pa.schema(
    [
        pa.field("release_id", pa.string(), nullable=False),
        pa.field("method_version", pa.string(), nullable=False),
        pa.field("geography_version", pa.string(), nullable=False),
        pa.field("health_region_code", pa.string(), nullable=False),
        pa.field("health_region_name", pa.string(), nullable=False),
        pa.field("uf_code", pa.string(), nullable=False),
        pa.field("uf", pa.string(), nullable=False),
        pa.field("municipality_count", pa.int64(), nullable=False),
        pa.field("population", pa.int64(), nullable=False),
        pa.field("area_km2", pa.float64(), nullable=False),
        pa.field("population_density", pa.float64(), nullable=False),
        pa.field("suicide_deaths", pa.int64(), nullable=False),
        pa.field("suicide_asmr", pa.float64(), nullable=False),
        pa.field("suicide_percentile", pa.float64(), nullable=False),
        pa.field("psychiatric_admissions", pa.int64(), nullable=False),
        pa.field("psychiatric_admission_rate", pa.float64(), nullable=False),
        pa.field("psychiatric_admission_percentile", pa.float64(), nullable=False),
        pa.field("caps_count", pa.int64(), nullable=False),
        pa.field("caps_rate", pa.float64(), nullable=False),
        pa.field("caps_percentile", pa.float64(), nullable=False),
        pa.field("mental_health_beds_sus_count", pa.int64(), nullable=False),
        pa.field("mental_health_beds_sus_rate", pa.float64(), nullable=False),
        pa.field("beds_percentile", pa.float64(), nullable=False),
        pa.field("psychiatrist_fte", pa.float64(), nullable=False),
        pa.field("psychiatrist_fte_rate", pa.float64(), nullable=False),
        pa.field("psychiatrist_fte_percentile", pa.float64(), nullable=False),
        pa.field("need_score", pa.float64(), nullable=False),
        pa.field("capacity_score", pa.float64(), nullable=False),
        pa.field("mismatch_score", pa.float64(), nullable=False),
        pa.field("lisa_local_i", pa.float64(), nullable=False),
        pa.field("lisa_p", pa.float64(), nullable=False),
        pa.field("lisa_q", pa.float64(), nullable=False),
        pa.field("lisa_significant", pa.bool_(), nullable=False),
        pa.field("lisa_cluster", pa.string(), nullable=False),
        pa.field("data_quality_flags", pa.list_(pa.string()), nullable=False),
    ]
)

CROSSWALK_SCHEMA = pa.schema(
    [
        pa.field("geography_version", pa.string(), nullable=False),
        pa.field("reference_date", pa.string(), nullable=False),
        pa.field("municipality_code_ibge", pa.string(), nullable=False),
        pa.field("municipality_code_datasus6", pa.string(), nullable=False),
        pa.field("municipality_name", pa.string(), nullable=False),
        pa.field("uf", pa.string(), nullable=False),
        pa.field("health_region_code", pa.string(), nullable=False),
        pa.field("health_region_name", pa.string(), nullable=False),
        pa.field("source", pa.string(), nullable=False),
    ]
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_release_output_hashes(root: Path) -> dict[str, str]:
    with (root / OUTPUT_MANIFEST).open(encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    return {entry["path"]: entry["sha256"] for entry in manifest["outputs"]}


def validate_input_hashes(root: Path) -> None:
    expected = read_release_output_hashes(root)
    for rel_path in [ANALYTICAL, LISA, SUPPLEMENT, CROSSWALK, GPKG, GLOBAL_MORAN]:
        full_path = root / rel_path
        if not full_path.exists():
            raise AssertionError(f"Missing locked input: {rel_path}")
        observed = sha256_file(full_path)
        expected_hash = expected.get(str(rel_path))
        if observed != expected_hash:
            raise AssertionError(
                f"Input SHA-256 mismatch for {rel_path}: observed={observed}, "
                f"expected={expected_hash}"
            )


def read_locked_csv(root: Path, rel_path: Path) -> pd.DataFrame:
    return pd.read_csv(root / rel_path, dtype=str, keep_default_na=False)


def normalize_code(series: pd.Series, width: int) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(width)


def to_number(series: pd.Series, field: str) -> pd.Series:
    values = pd.to_numeric(series, errors="raise")
    if values.isna().any():
        raise AssertionError(f"{field} contains null numeric values.")
    return values


def parse_bool(series: pd.Series, field: str) -> pd.Series:
    mapping = {"True": True, "False": False, "true": True, "false": False}
    parsed = series.map(mapping)
    if parsed.isna().any():
        raise AssertionError(f"{field} contains non-boolean values.")
    return parsed.astype(bool)


def validate_keys(analytical: pd.DataFrame, lisa: pd.DataFrame) -> None:
    analytical_codes = set(analytical["health_region_code"])
    lisa_codes = set(lisa["health_region_code"])
    if (
        len(analytical) != EXPECTED_HEALTH_REGIONS
        or len(analytical_codes) != EXPECTED_HEALTH_REGIONS
    ):
        raise AssertionError("Analytical dataset must contain 439 unique health-region codes.")
    if len(lisa) != EXPECTED_HEALTH_REGIONS or len(lisa_codes) != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("LISA dataset must contain 439 unique health-region codes.")
    if analytical["health_region_code"].duplicated().any():
        raise AssertionError("Analytical dataset contains duplicate health_region_code values.")
    if lisa["health_region_code"].duplicated().any():
        raise AssertionError("LISA dataset contains duplicate health_region_code values.")
    missing = sorted(analytical_codes - lisa_codes)
    extra = sorted(lisa_codes - analytical_codes)
    if missing or extra:
        raise AssertionError(
            f"LISA codes do not match analytical codes: missing={missing}, extra={extra}"
        )


def validate_uf_prefix(df: pd.DataFrame) -> None:
    prefixes = df["health_region_code"].str[:2]
    expected_uf = prefixes.map(UF_CODE_TO_UF)
    if expected_uf.isna().any():
        raise AssertionError("Unknown UF code prefix in health_region_code.")
    mismatch = df.loc[expected_uf != df["uf"], ["health_region_code", "uf"]]
    if not mismatch.empty:
        raise AssertionError(f"UF prefix mismatch: {mismatch.head().to_dict(orient='records')}")


def build_quality_flags(source: pd.DataFrame) -> list[list[str]]:
    small = parse_bool(source["small_number_flag"], "small_number_flag")
    beds = to_number(source["SUS_mental_health_beds_n"], "SUS_mental_health_beds_n")
    flags: list[list[str]] = []
    for is_small, bed_count in zip(small, beds, strict=True):
        row_flags: list[str] = []
        if is_small:
            row_flags.append("SMALL_SUICIDE_COUNT")
        if int(bed_count) == 0:
            row_flags.append("ZERO_REGISTERED_BEDS")
        flags.append(row_flags)
    small_count = sum("SMALL_SUICIDE_COUNT" in row for row in flags)
    zero_beds_count = sum("ZERO_REGISTERED_BEDS" in row for row in flags)
    if small_count != EXPECTED_SMALL_SUICIDE_COUNT:
        raise AssertionError(f"SMALL_SUICIDE_COUNT expected 7, got {small_count}.")
    if zero_beds_count != EXPECTED_ZERO_REGISTERED_BEDS:
        raise AssertionError(f"ZERO_REGISTERED_BEDS expected 275, got {zero_beds_count}.")
    return flags


def validate_ranges(df: pd.DataFrame) -> None:
    if df["health_region_code"].isna().any() or (df["health_region_code"] == "").any():
        raise AssertionError("Canonical health_region_code contains null/empty values.")
    if df["health_region_name"].isna().any() or (df["health_region_name"] == "").any():
        raise AssertionError("Canonical health_region_name contains null/empty values.")
    for field in ["population", "municipality_count"]:
        if not (df[field] > 0).all():
            raise AssertionError(f"{field} must be > 0.")
    for field in [
        "suicide_asmr",
        "psychiatric_admission_rate",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
    ]:
        if not (df[field] >= 0).all():
            raise AssertionError(f"{field} must be >= 0.")
    for field in [
        "suicide_percentile",
        "psychiatric_admission_percentile",
        "caps_percentile",
        "beds_percentile",
        "psychiatrist_fte_percentile",
        "need_score",
        "capacity_score",
    ]:
        if not ((df[field] >= 0) & (df[field] <= 1)).all():
            raise AssertionError(f"{field} must be within [0, 1].")
    if not ((df["mismatch_score"] >= -1) & (df["mismatch_score"] <= 1)).all():
        raise AssertionError("mismatch_score must be within [-1, 1].")
    mismatch_delta = (df["mismatch_score"] - (df["need_score"] - df["capacity_score"])).abs().max()
    if mismatch_delta > 1e-12:
        raise AssertionError(f"Mismatch integrity check failed; max delta={mismatch_delta}.")


def canonical_health_regions(root: Path) -> pd.DataFrame:
    analytical = read_locked_csv(root, ANALYTICAL)
    lisa = read_locked_csv(root, LISA)
    analytical["health_region_code"] = normalize_code(analytical["health_region_code"], 5)
    lisa["health_region_code"] = normalize_code(lisa["health_region_code"], 5)
    validate_keys(analytical, lisa)

    joined = analytical.merge(
        lisa[
            [
                "health_region_code",
                "local_I",
                "raw_pseudo_p",
                "BH_adjusted_q",
                "significant_at_q_0.10",
                "cluster_label",
            ]
        ],
        on="health_region_code",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if (joined["_merge"] != "both").sum() != 0 or len(joined) != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("LISA left join did not match 439/439 health regions.")
    joined = (
        joined.drop(columns=["_merge"]).sort_values("health_region_code").reset_index(drop=True)
    )

    output = pd.DataFrame(index=joined.index)
    output["release_id"] = RELEASE_ID
    output["method_version"] = METHOD_VERSION
    output["geography_version"] = GEOGRAPHY_VERSION
    output["health_region_code"] = joined["health_region_code"]
    output["health_region_name"] = joined["health_region_name"]
    output["uf_code"] = joined["health_region_code"].str[:2]
    output["uf"] = joined["UF"]

    integer_fields = {
        "municipality_count",
        "population",
        "suicide_deaths",
        "psychiatric_admissions",
        "caps_count",
        "mental_health_beds_sus_count",
    }
    for target, source in SOURCE_MAPPING.items():
        if target in {"health_region_code", "health_region_name"}:
            continue
        values = to_number(joined[source], source)
        output[target] = (
            values.astype("int64") if target in integer_fields else values.astype("float64")
        )

    for target, source in LISA_MAPPING.items():
        if target == "lisa_cluster":
            output[target] = joined[source]
        else:
            output[target] = to_number(joined[source], source).astype("float64")
    output["lisa_significant"] = parse_bool(
        joined["significant_at_q_0.10"], "significant_at_q_0.10"
    )
    output["data_quality_flags"] = build_quality_flags(joined)
    output = output[CANONICAL_COLUMNS]

    validate_uf_prefix(output)
    validate_ranges(output)
    return output


def canonical_crosswalk(root: Path) -> pd.DataFrame:
    source = read_locked_csv(root, CROSSWALK)
    output = pd.DataFrame(
        {
            "geography_version": GEOGRAPHY_VERSION,
            "reference_date": source["reference_date"],
            "municipality_code_ibge": normalize_code(source["municipality_code_ibge"], 7),
            "municipality_code_datasus6": normalize_code(source["municipality_code_datasus6"], 6),
            "municipality_name": source["municipality_name"],
            "uf": source["UF"],
            "health_region_code": normalize_code(source["health_region_code"], 5),
            "health_region_name": source["health_region_name"],
            "source": source["source"],
        }
    )
    if len(output) != EXPECTED_MUNICIPALITIES:
        raise AssertionError(f"Crosswalk must contain 5570 rows, got {len(output)}.")
    if output["municipality_code_ibge"].nunique() != EXPECTED_MUNICIPALITIES:
        raise AssertionError("Crosswalk municipality_code_ibge must be unique.")
    if output["health_region_code"].isna().any() or (output["health_region_code"] == "").any():
        raise AssertionError("Crosswalk contains municipalities without health regions.")
    if not output["municipality_code_ibge"].str.fullmatch(r"\d{7}").all():
        raise AssertionError("municipality_code_ibge must be a 7-character string.")
    if not output["municipality_code_datasus6"].str.fullmatch(r"\d{6}").all():
        raise AssertionError("municipality_code_datasus6 must be a 6-character string.")
    if not output["health_region_code"].str.fullmatch(r"\d{5}").all():
        raise AssertionError("health_region_code must be a 5-character string.")
    return output.sort_values("municipality_code_ibge").reset_index(drop=True)


def validate_geometry(root: Path, health_region_codes: set[str]) -> dict[str, Any]:
    connection = sqlite3.connect(root / GPKG)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "select table_name from gpkg_contents where data_type = 'features'"
            ).fetchall()
        }
        if "health_regions" not in tables:
            raise AssertionError("GPKG layer 'health_regions' is missing.")
        row_count = connection.execute("select count(*) from health_regions").fetchone()[0]
        unique_codes = connection.execute(
            "select count(distinct health_region_code) from health_regions"
        ).fetchone()[0]
        codes = {
            str(row[0]).zfill(5)
            for row in connection.execute("select health_region_code from health_regions")
        }
        crs_row = connection.execute(
            """
            select s.organization, s.organization_coordsys_id
            from gpkg_geometry_columns g
            join gpkg_spatial_ref_sys s on g.srs_id = s.srs_id
            where g.table_name = 'health_regions'
            """
        ).fetchone()
    finally:
        connection.close()
    if row_count != EXPECTED_HEALTH_REGIONS or unique_codes != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("GPKG health_regions layer must contain 439 unique features.")
    if codes != health_region_codes:
        raise AssertionError("GPKG health_region_code set differs from canonical health_regions.")
    crs = f"{crs_row[0]}:{crs_row[1]}" if crs_row else "unknown"
    if crs != "EPSG:4674":
        raise AssertionError(f"Unexpected CRS for health_regions_LOCKED.gpkg: {crs}")
    return {"layer": "health_regions", "feature_count": row_count, "crs": crs}


def compare_values(left: pd.Series, right: pd.Series, field: str) -> None:
    left_num = pd.to_numeric(left, errors="coerce")
    right_num = pd.to_numeric(right, errors="coerce")
    if left_num.notna().all() and right_num.notna().all():
        delta = (left_num.astype(float) - right_num.astype(float)).abs().max()
        if delta > 1e-12:
            raise AssertionError(f"Supplement cross-check failed for {field}; max delta={delta}.")
    elif not left.astype(str).equals(right.astype(str)):
        raise AssertionError(f"Supplement cross-check failed for {field}.")


def cross_check_supplement(root: Path, canonical: pd.DataFrame) -> None:
    supplement = read_locked_csv(root, SUPPLEMENT)
    supplement["health_region_code"] = normalize_code(supplement["health_region_code"], 5)
    if (
        len(supplement) != EXPECTED_HEALTH_REGIONS
        or supplement["health_region_code"].nunique() != 439
    ):
        raise AssertionError("Supplement must contain 439 unique health-region codes.")
    by_code = supplement.set_index("health_region_code").sort_index()
    canonical_by_code = canonical.set_index("health_region_code").sort_index()
    for target, source in SOURCE_MAPPING.items():
        if target in {"health_region_code"}:
            continue
        if target == "health_region_name":
            compare_values(canonical_by_code[target], by_code[source], target)
        else:
            compare_values(canonical_by_code[target], by_code[source], target)
    for target, source in LISA_MAPPING.items():
        compare_values(canonical_by_code[target], by_code[source], target)


def validate_spatial_locks(root: Path, canonical: pd.DataFrame) -> None:
    with (root / GLOBAL_MORAN).open(encoding="utf-8") as handle:
        moran = json.load(handle)
    if abs(float(moran["I"]) - 0.525494388844) > 1e-12:
        raise AssertionError("Locked Global Moran I changed.")
    if abs(float(moran["I"]) - 0.218740812099) < 1e-12:
        raise AssertionError("Invalid old Global Moran value reappeared.")
    if float(moran["pseudo_p"]) != 0.0001:
        raise AssertionError("Locked Global Moran pseudo-p changed.")
    significant = canonical[canonical["lisa_significant"]]
    counts = {
        "total": len(significant),
        "high-high": int((significant["lisa_cluster"] == "high-high").sum()),
        "low-low": int((significant["lisa_cluster"] == "low-low").sum()),
        "high-low": int((significant["lisa_cluster"] == "high-low").sum()),
        "low-high": int((significant["lisa_cluster"] == "low-high").sum()),
    }
    expected = {"total": 135, "high-high": 60, "low-low": 66, "high-low": 4, "low-high": 5}
    if counts != expected:
        raise AssertionError(f"Locked LISA counts changed: got={counts}, expected={expected}")


def table_from_dataframe(df: pd.DataFrame, schema: pa.Schema) -> pa.Table:
    return pa.Table.from_pydict({name: df[name].tolist() for name in schema.names}, schema=schema)


def write_parquet(table: pa.Table, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table,
        path,
        compression="zstd",
        data_page_version="2.0",
        version="2.6",
        write_statistics=True,
    )


def output_record(
    path: Path, table: pa.Table, schema_reference: str, source_files: list[str]
) -> dict[str, Any]:
    return {
        "path": str(path),
        "row_count": table.num_rows,
        "column_count": table.num_columns,
        "sha256": sha256_file(path),
        "schema_reference": schema_reference,
        "source_files": source_files,
    }


def write_manifest(root: Path, outputs: list[dict[str, Any]], geometry: dict[str, Any]) -> None:
    path = root / MANIFEST_PATH
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    if path.exists():
        existing = yaml.safe_load(path.read_text(encoding="utf-8"))
        existing_stable = {
            key: existing.get(key)
            for key in [
                "canonical_version",
                "release_id",
                "method_version",
                "geography_version",
                "source_release_status",
                "source_quality_status",
                "source_release_gate",
                "outputs",
                "geometry_validation",
            ]
        }
        new_stable = {
            "canonical_version": CANONICAL_VERSION,
            "release_id": RELEASE_ID,
            "method_version": METHOD_VERSION,
            "geography_version": GEOGRAPHY_VERSION,
            "source_release_status": "VALIDATING",
            "source_quality_status": "VALIDATED",
            "source_release_gate": "PASS",
            "outputs": outputs,
            "geometry_validation": geometry,
        }
        if existing_stable == new_stable:
            generated_at = existing["generated_at"]
    manifest = {
        "canonical_version": CANONICAL_VERSION,
        "release_id": RELEASE_ID,
        "method_version": METHOD_VERSION,
        "geography_version": GEOGRAPHY_VERSION,
        "source_release_status": "VALIDATING",
        "source_quality_status": "VALIDATED",
        "source_release_gate": "PASS",
        "generated_at": generated_at,
        "outputs": outputs,
        "geometry_validation": geometry,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest, handle, sort_keys=False, allow_unicode=False)


def build() -> dict[str, Any]:
    root = repo_root()
    validate_input_hashes(root)
    health_regions = canonical_health_regions(root)
    crosswalk = canonical_crosswalk(root)
    cross_check_supplement(root, health_regions)
    validate_spatial_locks(root, health_regions)
    geometry = validate_geometry(root, set(health_regions["health_region_code"]))

    health_table = table_from_dataframe(health_regions, HEALTH_REGION_SCHEMA)
    crosswalk_table = table_from_dataframe(crosswalk, CROSSWALK_SCHEMA)
    write_parquet(health_table, root / HEALTH_REGIONS_OUTPUT)
    write_parquet(crosswalk_table, root / CROSSWALK_OUTPUT)

    outputs = [
        output_record(
            HEALTH_REGIONS_OUTPUT,
            health_table,
            "metadata/canonical/health_regions_v1.yaml",
            [str(ANALYTICAL), str(LISA)],
        ),
        output_record(
            CROSSWALK_OUTPUT,
            crosswalk_table,
            "metadata/canonical/municipality_health_region_crosswalk_v1.yaml",
            [str(CROSSWALK)],
        ),
    ]
    write_manifest(root, outputs, geometry)
    return {"outputs": outputs, "geometry_validation": geometry}


def main() -> int:
    result = build()
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

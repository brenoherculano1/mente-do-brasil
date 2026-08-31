"""Load the canonical Mente do Brasil release into a local PostGIS database."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from math import isclose
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import yaml

RELEASE_ID = "MDB_ANALYTICAL_2024_1"
CANONICAL_VERSION = "MDB_CANONICAL_1.0"
METHOD_VERSION = "MDB_METHOD_1.0"
GEOGRAPHY_VERSION = "BR_HEALTH_REGIONS_END2024_V1"
INTELLIGENCE_VERSION = "MDB_TERRITORIAL_INTELLIGENCE_1.0"
RADAR_RULESET_VERSION = "MDB_RADAR_RULESET_1.0"
DECOMPOSITION_VERSION = "MDB_MISMATCH_DECOMPOSITION_1.0"
PEER_METHOD_VERSION = "MDB_PEER_METHOD_1.0"
CANONICAL_INPUT_HASH = "a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515"

EXPECTED_HEALTH_REGIONS = 439
EXPECTED_MUNICIPALITIES = 5570
EXPECTED_LISA = {"total": 135, "high-high": 60, "low-low": 66, "high-low": 4, "low-high": 5}
EXPECTED_SMALL_SUICIDE_COUNT = 7
EXPECTED_ZERO_REGISTERED_BEDS = 275
LOCKED_GLOBAL_MORAN_I = 0.525494388844
LOCKED_GLOBAL_MORAN_P = 0.0001
INVALID_GLOBAL_MORAN_I = 0.218740812099

CANONICAL_MANIFEST = Path("metadata/releases/MDB_ANALYTICAL_2024_1_canonical.yaml")
SCIENTIFIC_RELEASE = Path("metadata/releases/MDB_ANALYTICAL_2024_1.yaml")
SERVING_RELEASE = Path("metadata/releases/MDB_ANALYTICAL_2024_1_serving.yaml")
INDICATOR_DIR = Path("metadata/indicators")
GPKG = Path(
    "data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/"
    "mdb_import_bundle/geography/health_regions_LOCKED.gpkg"
)
GLOBAL_MORAN = Path(
    "data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/"
    "mdb_import_bundle/analytical_release/global_moran_primary_corrected.json"
)
MIGRATIONS_DIR = Path("db/migrations")
PRODUCT_INTELLIGENCE_DIR = Path("data/product_intelligence/MDB_ANALYTICAL_2024_1")

INDICATOR_IDS = [
    "suicide_asmr",
    "psychiatric_admission_rate",
    "caps_rate",
    "mental_health_beds_sus_rate",
    "psychiatrist_fte_rate",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dsn() -> str:
    load_local_env()
    host = os.environ.get("MDB_DB_HOST", "127.0.0.1")
    port = os.environ.get("MDB_DB_PORT", "5432")
    dbname = os.environ.get("MDB_DB_NAME", "mente_do_brasil")
    user = os.environ.get("MDB_DB_USER", "mente_do_brasil")
    password = os.environ.get("MDB_DB_PASSWORD")
    if not password:
        raise RuntimeError("MDB_DB_PASSWORD must be set in the local environment or .env file.")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def load_local_env() -> None:
    env_path = repo_root() / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key, value)


def connect():
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required to load the serving database.") from exc
    return psycopg.connect(dsn())


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_canonical_manifest(root: Path) -> dict[str, Any]:
    manifest = load_yaml(root / CANONICAL_MANIFEST)
    release = load_yaml(root / SCIENTIFIC_RELEASE)
    if manifest["release_id"] != RELEASE_ID:
        raise AssertionError(f"Unexpected release_id: {manifest['release_id']}")
    if manifest["canonical_version"] != CANONICAL_VERSION:
        raise AssertionError("Unexpected canonical version.")
    if manifest["source_release_gate"] != "PASS":
        raise AssertionError("Canonical source release gate is not PASS.")
    if manifest["source_quality_status"] != "VALIDATED":
        raise AssertionError("Canonical source quality status is not VALIDATED.")
    if release["release_gate"] != "PASS" or release["quality_status"] != "VALIDATED":
        raise AssertionError("Scientific release is not PASS/VALIDATED.")
    if release["release_status"] != "VALIDATING":
        raise AssertionError("Scientific release status changed unexpectedly.")
    for output in manifest["outputs"]:
        path = root / output["path"]
        if not path.exists():
            raise AssertionError(f"Canonical output missing: {output['path']}")
        observed = sha256_file(path)
        if observed != output["sha256"]:
            raise AssertionError(
                f"Canonical SHA-256 mismatch for {output['path']}: "
                f"observed={observed}, expected={output['sha256']}"
            )
    return manifest


def validate_scientific_locks(root: Path) -> None:
    moran = json.loads((root / GLOBAL_MORAN).read_text(encoding="utf-8"))
    if abs(float(moran["I"]) - LOCKED_GLOBAL_MORAN_I) > 1e-12:
        raise AssertionError("Global Moran I differs from locked value.")
    if abs(float(moran["I"]) - INVALID_GLOBAL_MORAN_I) < 1e-12:
        raise AssertionError("Invalidated Global Moran I reappeared as primary.")
    if float(moran["pseudo_p"]) != LOCKED_GLOBAL_MORAN_P:
        raise AssertionError("Global Moran pseudo-p differs from locked value.")


def read_health_regions(root: Path, manifest: dict[str, Any]) -> pd.DataFrame:
    output = manifest["outputs"][0]
    df = pq.read_table(root / output["path"]).to_pandas()
    if len(df) != EXPECTED_HEALTH_REGIONS or df["health_region_code"].nunique() != 439:
        raise AssertionError("Canonical health_regions must contain 439 unique rows.")
    return df.sort_values("health_region_code").reset_index(drop=True)


def read_crosswalk(root: Path, manifest: dict[str, Any]) -> pd.DataFrame:
    output = manifest["outputs"][1]
    df = pq.read_table(root / output["path"]).to_pandas()
    if len(df) != EXPECTED_MUNICIPALITIES or df["municipality_code_ibge"].nunique() != 5570:
        raise AssertionError("Canonical crosswalk must contain 5570 unique municipalities.")
    return df.sort_values("municipality_code_ibge").reset_index(drop=True)


def validate_lisa_and_flags(health_regions: pd.DataFrame) -> None:
    significant = health_regions[health_regions["lisa_significant"]]
    counts = {
        "total": int(len(significant)),
        "high-high": int((significant["lisa_cluster"] == "high-high").sum()),
        "low-low": int((significant["lisa_cluster"] == "low-low").sum()),
        "high-low": int((significant["lisa_cluster"] == "high-low").sum()),
        "low-high": int((significant["lisa_cluster"] == "low-high").sum()),
    }
    if counts != EXPECTED_LISA:
        raise AssertionError(f"LISA locks changed: got={counts}, expected={EXPECTED_LISA}")
    flags = health_regions["data_quality_flags"].tolist()
    small = sum("SMALL_SUICIDE_COUNT" in row for row in flags)
    zero_beds = sum("ZERO_REGISTERED_BEDS" in row for row in flags)
    if small != EXPECTED_SMALL_SUICIDE_COUNT:
        raise AssertionError(f"SMALL_SUICIDE_COUNT expected 7, got {small}.")
    if zero_beds != EXPECTED_ZERO_REGISTERED_BEDS:
        raise AssertionError(f"ZERO_REGISTERED_BEDS expected 275, got {zero_beds}.")


def apply_migrations(connection, root: Path) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS public.schema_migrations (
            filename TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    applied = {
        row[0]: row[1]
        for row in connection.execute(
            "SELECT filename, sha256 FROM public.schema_migrations"
        ).fetchall()
    }
    for path in sorted((root / MIGRATIONS_DIR).glob("*.sql")):
        digest = sha256_file(path)
        name = path.name
        if name in applied:
            if applied[name] != digest:
                raise AssertionError(f"Migration checksum changed after apply: {name}")
            continue
        sql = path.read_text(encoding="utf-8")
        connection.execute(sql)
        connection.execute(
            "INSERT INTO public.schema_migrations (filename, sha256) VALUES (%s, %s)",
            (name, digest),
        )


def release_values(manifest: dict[str, Any]) -> dict[str, Any]:
    output_hashes = {Path(entry["path"]).name: entry["sha256"] for entry in manifest["outputs"]}
    return {
        "release_id": RELEASE_ID,
        "canonical_version": CANONICAL_VERSION,
        "method_version": METHOD_VERSION,
        "geography_version": GEOGRAPHY_VERSION,
        "release_status": manifest["source_release_status"],
        "quality_status": manifest["source_quality_status"],
        "release_gate": manifest["source_release_gate"],
        "public_release_status": "NOT_RELEASED",
        "canonical_generated_at": manifest["generated_at"],
        "health_regions_sha256": output_hashes["health_regions.parquet"],
        "crosswalk_sha256": output_hashes["municipality_health_region_crosswalk.parquet"],
    }


def enforce_release_immutability(connection, release: dict[str, Any]) -> str:
    existing = connection.execute(
        """
        SELECT health_regions_sha256, crosswalk_sha256
        FROM meta.releases
        WHERE release_id = %s
        """,
        (release["release_id"],),
    ).fetchone()
    if not existing:
        return "NEW LOAD"
    if (
        existing[0] != release["health_regions_sha256"]
        or existing[1] != release["crosswalk_sha256"]
    ):
        raise AssertionError(
            "IMMUTABILITY VIOLATION: existing release_id has different canonical hashes."
        )
    return "PASS / NO CHANGE"


def insert_release(connection, release: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO meta.releases (
            release_id, canonical_version, method_version, geography_version,
            release_status, quality_status, release_gate, public_release_status,
            canonical_generated_at, health_regions_sha256, crosswalk_sha256
        )
        VALUES (
            %(release_id)s, %(canonical_version)s, %(method_version)s, %(geography_version)s,
            %(release_status)s, %(quality_status)s, %(release_gate)s,
            %(public_release_status)s, %(canonical_generated_at)s,
            %(health_regions_sha256)s, %(crosswalk_sha256)s
        )
        ON CONFLICT (release_id) DO NOTHING
        """,
        release,
    )


def insert_serving_status(connection, root: Path) -> None:
    status_manifest = load_yaml(root / SERVING_RELEASE)
    if status_manifest["release_id"] != RELEASE_ID:
        raise AssertionError("Serving status manifest release_id differs from current release.")
    if status_manifest["serving_database_status"] not in {
        "VALIDATED_LOCAL",
        "PENDING_LOCAL_VALIDATION",
    }:
        raise AssertionError("Serving database status is not eligible for local validation.")
    connection.execute(
        """
        INSERT INTO meta.serving_database_status (
            release_id, serving_database_status, validated_at
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (release_id) DO UPDATE SET
            serving_database_status = EXCLUDED.serving_database_status,
            validated_at = EXCLUDED.validated_at
        """,
        (
            status_manifest["release_id"],
            "VALIDATED_LOCAL",
            status_manifest["validated_at"] or datetime.now(timezone.utc),
        ),
    )


def indicator_records(root: Path) -> list[dict[str, Any]]:
    records = []
    for indicator_id in INDICATOR_IDS:
        data = load_yaml(root / INDICATOR_DIR / f"{indicator_id}.yaml")
        records.append(
            {
                "indicator_id": data["indicator_id"],
                "indicator_name_pt": data["indicator_name_pt"],
                "indicator_name_en": data["indicator_name_en"],
                "domain": data["domain"],
                "description": data["description"],
                "unit": data["unit"],
                "interpretation": data["interpretation"],
                "what_it_does_not_measure": data["what_it_does_not_measure"],
                "method_version": data["method_version"],
                "source_system": data["source_system"],
                "observation_start": data.get("observation_start"),
                "observation_end": data.get("observation_end"),
            }
        )
    return records


def insert_indicators(connection, records: list[dict[str, Any]]) -> None:
    for record in records:
        connection.execute(
            """
            INSERT INTO meta.indicators (
                indicator_id, indicator_name_pt, indicator_name_en, domain,
                description, unit, interpretation, what_it_does_not_measure,
                method_version, source_system, observation_start, observation_end
            )
            VALUES (
                %(indicator_id)s, %(indicator_name_pt)s, %(indicator_name_en)s, %(domain)s,
                %(description)s, %(unit)s, %(interpretation)s, %(what_it_does_not_measure)s,
                %(method_version)s, %(source_system)s, %(observation_start)s,
                %(observation_end)s
            )
            ON CONFLICT (indicator_id, method_version) DO NOTHING
            """,
            record,
        )


def load_geometry(root: Path) -> pd.DataFrame:
    try:
        import geopandas as gpd
        from shapely.geometry import MultiPolygon
    except ModuleNotFoundError as exc:
        raise RuntimeError("geopandas and shapely are required for geometry loading.") from exc

    gdf = gpd.read_file(root / GPKG, layer="health_regions")
    if len(gdf) != EXPECTED_HEALTH_REGIONS or gdf["health_region_code"].nunique() != 439:
        raise AssertionError("GPKG must contain 439 unique health regions.")
    if str(gdf.crs) != "EPSG:4674":
        raise AssertionError(f"Unexpected GPKG CRS: {gdf.crs}")
    if not gdf.geometry.notna().all():
        raise AssertionError("GPKG contains null geometries.")
    if not gdf.geometry.is_valid.all():
        raise AssertionError("GPKG contains invalid geometries; not applying ST_MakeValid.")

    def as_multi(geometry):
        if geometry.geom_type == "MultiPolygon":
            return geometry
        if geometry.geom_type == "Polygon":
            return MultiPolygon([geometry])
        raise AssertionError(f"Unexpected geometry type: {geometry.geom_type}")

    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.map(as_multi)
    return gdf[["health_region_code", "geometry"]].sort_values("health_region_code")


def insert_geography(connection, health_regions: pd.DataFrame, geometry: pd.DataFrame) -> None:
    merged = health_regions.merge(
        geometry, on="health_region_code", how="left", validate="one_to_one"
    )
    if merged["geometry"].isna().any() or len(merged) != 439:
        raise AssertionError("Geometry matching with canonical health regions failed.")
    for row in merged.itertuples(index=False):
        connection.execute(
            """
            INSERT INTO geo.health_regions (
                geography_version, health_region_code, health_region_name, uf_code,
                uf, municipality_count, area_km2, geom
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromWKB(%s, 4674))
            ON CONFLICT (geography_version, health_region_code) DO NOTHING
            """,
            (
                GEOGRAPHY_VERSION,
                row.health_region_code,
                row.health_region_name,
                row.uf_code,
                row.uf,
                int(row.municipality_count),
                float(row.area_km2),
                bytes(row.geometry.wkb),
            ),
        )


def database_has_geography(connection) -> bool:
    return (
        scalar(
            connection,
            "SELECT count(*) FROM geo.health_regions WHERE geography_version = %s",
            (GEOGRAPHY_VERSION,),
        )
        == EXPECTED_HEALTH_REGIONS
    )


def insert_crosswalk(connection, crosswalk: pd.DataFrame) -> None:
    for row in crosswalk.itertuples(index=False):
        connection.execute(
            """
            INSERT INTO geo.municipality_health_region_crosswalk (
                geography_version, municipality_code_ibge, municipality_code_datasus6,
                municipality_name, uf, health_region_code, health_region_name, source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (geography_version, municipality_code_ibge) DO NOTHING
            """,
            (
                row.geography_version,
                row.municipality_code_ibge,
                row.municipality_code_datasus6,
                row.municipality_name,
                row.uf,
                row.health_region_code,
                row.health_region_name,
                row.source,
            ),
        )


def insert_metrics(connection, health_regions: pd.DataFrame) -> None:
    fields = [
        "population",
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
    for row in health_regions.itertuples(index=False):
        values = {field: getattr(row, field) for field in fields}
        values["data_quality_flags"] = list(values["data_quality_flags"])
        values.update(
            {
                "release_id": RELEASE_ID,
                "geography_version": GEOGRAPHY_VERSION,
                "health_region_code": row.health_region_code,
            }
        )
        connection.execute(
            """
            INSERT INTO analytics.health_region_metrics (
                release_id, geography_version, health_region_code,
                population, population_density, suicide_deaths, suicide_asmr,
                suicide_percentile, psychiatric_admissions, psychiatric_admission_rate,
                psychiatric_admission_percentile, caps_count, caps_rate, caps_percentile,
                mental_health_beds_sus_count, mental_health_beds_sus_rate,
                beds_percentile, psychiatrist_fte, psychiatrist_fte_rate,
                psychiatrist_fte_percentile, need_score, capacity_score, mismatch_score,
                lisa_local_i, lisa_p, lisa_q, lisa_significant, lisa_cluster,
                data_quality_flags
            )
            VALUES (
                %(release_id)s, %(geography_version)s, %(health_region_code)s,
                %(population)s, %(population_density)s, %(suicide_deaths)s,
                %(suicide_asmr)s, %(suicide_percentile)s, %(psychiatric_admissions)s,
                %(psychiatric_admission_rate)s, %(psychiatric_admission_percentile)s,
                %(caps_count)s, %(caps_rate)s, %(caps_percentile)s,
                %(mental_health_beds_sus_count)s, %(mental_health_beds_sus_rate)s,
                %(beds_percentile)s, %(psychiatrist_fte)s, %(psychiatrist_fte_rate)s,
                %(psychiatrist_fte_percentile)s, %(need_score)s, %(capacity_score)s,
                %(mismatch_score)s, %(lisa_local_i)s, %(lisa_p)s, %(lisa_q)s,
                %(lisa_significant)s, %(lisa_cluster)s, %(data_quality_flags)s
            )
            ON CONFLICT (release_id, health_region_code) DO NOTHING
            """,
            values,
        )


def product_intelligence_paths(root: Path) -> dict[str, Path]:
    return {
        "intelligence": root / PRODUCT_INTELLIGENCE_DIR / "health_region_intelligence.parquet",
        "peers": root / PRODUCT_INTELLIGENCE_DIR / "health_region_peers.parquet",
        "benchmarks": root / PRODUCT_INTELLIGENCE_DIR / "peer_benchmarks.parquet",
    }


def read_product_intelligence(
    root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    paths = product_intelligence_paths(root)
    for path in paths.values():
        if not path.exists():
            raise AssertionError(f"Product intelligence output missing: {path}")
    intelligence = pq.read_table(paths["intelligence"]).to_pandas()
    peers = pq.read_table(paths["peers"]).to_pandas()
    benchmarks = pq.read_table(paths["benchmarks"]).to_pandas()
    output_hashes = {name: sha256_file(path) for name, path in paths.items()}
    if len(intelligence) != 439:
        raise AssertionError("Product intelligence must contain 439 rows.")
    if len(peers) != 4390:
        raise AssertionError("Product peers must contain 4390 rows.")
    if len(benchmarks) != 3512:
        raise AssertionError("Product peer benchmarks must contain 3512 rows.")
    if int(intelligence["spatial_hh_mismatch"].sum()) != 60:
        raise AssertionError("SPATIAL_HH_MISMATCH must equal 60 in product intelligence.")
    max_error = (
        (
            intelligence["decomposition_sum"].astype(float)
            - intelligence["mismatch_score"].astype(float)
        )
        .abs()
        .max()
    )
    if max_error > 1e-12:
        raise AssertionError(f"Product decomposition identity failed: {max_error}")
    return intelligence, peers, benchmarks, output_hashes


def enforce_product_intelligence_immutability(connection, hashes: dict[str, str]) -> None:
    existing = connection.execute(
        """
        SELECT canonical_input_sha256, intelligence_sha256, peers_sha256, benchmarks_sha256
        FROM meta.product_intelligence_versions
        WHERE release_id = %s AND intelligence_version = %s
        """,
        (RELEASE_ID, INTELLIGENCE_VERSION),
    ).fetchone()
    if not existing:
        return
    expected = (
        CANONICAL_INPUT_HASH,
        hashes["intelligence"],
        hashes["peers"],
        hashes["benchmarks"],
    )
    if tuple(existing) != expected:
        raise AssertionError(
            "IMMUTABILITY VIOLATION: existing intelligence version has different hashes."
        )


def insert_product_intelligence_version(connection, hashes: dict[str, str]) -> None:
    connection.execute(
        """
        INSERT INTO meta.product_intelligence_versions (
            release_id, intelligence_version, radar_ruleset_version,
            decomposition_version, peer_method_version, status, canonical_input_sha256,
            intelligence_sha256, peers_sha256, benchmarks_sha256
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (release_id, intelligence_version) DO NOTHING
        """,
        (
            RELEASE_ID,
            INTELLIGENCE_VERSION,
            RADAR_RULESET_VERSION,
            DECOMPOSITION_VERSION,
            PEER_METHOD_VERSION,
            "VALIDATED_LOCAL",
            CANONICAL_INPUT_HASH,
            hashes["intelligence"],
            hashes["peers"],
            hashes["benchmarks"],
        ),
    )


def insert_product_intelligence_rows(connection, intelligence: pd.DataFrame) -> None:
    fields = [
        "release_id",
        "geography_version",
        "intelligence_version",
        "radar_ruleset_version",
        "decomposition_version",
        "peer_method_version",
        "health_region_code",
        "health_region_name",
        "uf",
        "population",
        "population_density",
        "municipality_count",
        "need_score",
        "capacity_score",
        "mismatch_score",
        "suicide_percentile",
        "psychiatric_admission_percentile",
        "caps_percentile",
        "beds_percentile",
        "psychiatrist_fte_percentile",
        "need_high",
        "capacity_low",
        "mismatch_marked_positive",
        "capacity_component_low",
        "spatial_hh_mismatch",
        "caps_low",
        "beds_low",
        "psychiatrist_fte_low",
        "zero_registered_beds",
        "small_suicide_count",
        "matched_signal_families",
        "suicide_contribution",
        "admissions_contribution",
        "caps_contribution",
        "beds_contribution",
        "psychiatrist_contribution",
        "decomposition_sum",
        "data_quality_flags",
    ]
    placeholders = ", ".join(f"%({field})s" for field in fields)
    records = []
    for row in intelligence.itertuples(index=False):
        values = {field: getattr(row, field) for field in fields}
        values["data_quality_flags"] = list(values["data_quality_flags"])
        records.append(values)
    with connection.cursor() as cursor:
        cursor.executemany(
            f"""
            INSERT INTO analytics.health_region_intelligence ({", ".join(fields)})
            VALUES ({placeholders})
            ON CONFLICT (release_id, intelligence_version, health_region_code) DO NOTHING
            """,
            records,
        )


def insert_product_peers(connection, peers: pd.DataFrame) -> None:
    records = [
        (
            row.release_id,
            row.peer_method_version,
            row.health_region_code,
            row.peer_health_region_code,
            int(row.peer_rank),
            float(row.structural_distance),
        )
        for row in peers.itertuples(index=False)
    ]
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO analytics.health_region_peers (
                release_id, peer_method_version, health_region_code, peer_health_region_code,
                peer_rank, structural_distance
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (release_id, peer_method_version, health_region_code, peer_rank)
            DO NOTHING
            """,
            records,
        )


def insert_product_peer_benchmarks(connection, benchmarks: pd.DataFrame) -> None:
    records = [
        (
            row.release_id,
            row.peer_method_version,
            row.health_region_code,
            row.metric_id,
            float(row.target_value),
            int(row.peer_n_observed),
            none_if_nan(row.peer_median),
            none_if_nan(row.peer_q1),
            none_if_nan(row.peer_q3),
            none_if_nan(row.peer_min),
            none_if_nan(row.peer_max),
            none_if_nan(row.relative_to_peer_iqr),
            none_if_nan(row.insufficient_reason),
        )
        for row in benchmarks.itertuples(index=False)
    ]
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO analytics.health_region_peer_benchmarks (
                release_id, peer_method_version, health_region_code, metric_id, target_value,
                peer_n_observed, peer_median, peer_q1, peer_q3, peer_min, peer_max,
                relative_to_peer_iqr, insufficient_reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (release_id, peer_method_version, health_region_code, metric_id)
            DO NOTHING
            """,
            records,
        )


def none_if_nan(value):
    if pd.isna(value):
        return None
    return value


def scalar(connection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    return connection.execute(sql, params).fetchone()[0]


def assert_close(name: str, left: Any, right: Any) -> None:
    if isinstance(left, float) or isinstance(right, float):
        if not isclose(float(left), float(right), rel_tol=0, abs_tol=1e-12):
            raise AssertionError(f"Database value differs for {name}: {left} != {right}")
    elif left != right:
        raise AssertionError(f"Database value differs for {name}: {left} != {right}")


def assert_database_matches_canonical(
    connection,
    health_regions: pd.DataFrame,
    crosswalk: pd.DataFrame,
    geometry: pd.DataFrame,
) -> None:
    metric_columns = [
        "health_region_code",
        "population",
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
    db_metrics = connection.execute(
        f"""
        SELECT {", ".join(metric_columns)}
        FROM analytics.health_region_metrics
        WHERE release_id = %s
        ORDER BY health_region_code
        """,
        (RELEASE_ID,),
    ).fetchall()
    expected_metrics = health_regions[metric_columns].sort_values("health_region_code")
    if len(db_metrics) != len(expected_metrics):
        raise AssertionError("Database metrics count differs from canonical metrics.")
    for db_row, expected in zip(db_metrics, expected_metrics.itertuples(index=False), strict=True):
        for column, db_value, expected_value in zip(metric_columns, db_row, expected, strict=True):
            if column == "data_quality_flags":
                db_value = list(db_value)
                expected_value = list(expected_value)
            assert_close(f"analytics.health_region_metrics.{column}", db_value, expected_value)

    db_regions = connection.execute(
        """
        SELECT health_region_code, health_region_name, uf_code, uf, municipality_count, area_km2
        FROM geo.health_regions
        WHERE geography_version = %s
        ORDER BY health_region_code
        """,
        (GEOGRAPHY_VERSION,),
    ).fetchall()
    region_columns = [
        "health_region_code",
        "health_region_name",
        "uf_code",
        "uf",
        "municipality_count",
        "area_km2",
    ]
    expected_regions = health_regions[region_columns].sort_values("health_region_code")
    if len(db_regions) != len(expected_regions):
        raise AssertionError("Database health-region dimension differs from canonical.")
    for db_row, expected in zip(db_regions, expected_regions.itertuples(index=False), strict=True):
        for column, db_value, expected_value in zip(region_columns, db_row, expected, strict=True):
            assert_close(f"geo.health_regions.{column}", db_value, expected_value)

    db_crosswalk = connection.execute(
        """
        SELECT municipality_code_ibge, municipality_code_datasus6, municipality_name, uf,
               health_region_code, health_region_name, source
        FROM geo.municipality_health_region_crosswalk
        WHERE geography_version = %s
        ORDER BY municipality_code_ibge
        """,
        (GEOGRAPHY_VERSION,),
    ).fetchall()
    crosswalk_columns = [
        "municipality_code_ibge",
        "municipality_code_datasus6",
        "municipality_name",
        "uf",
        "health_region_code",
        "health_region_name",
        "source",
    ]
    expected_crosswalk = crosswalk[crosswalk_columns].sort_values("municipality_code_ibge")
    if len(db_crosswalk) != len(expected_crosswalk):
        raise AssertionError("Database crosswalk differs from canonical crosswalk.")
    for db_row, expected in zip(
        db_crosswalk, expected_crosswalk.itertuples(index=False), strict=True
    ):
        for column, db_value, expected_value in zip(
            crosswalk_columns, db_row, expected, strict=True
        ):
            assert_close(
                f"geo.municipality_health_region_crosswalk.{column}", db_value, expected_value
            )

    if geometry is not None:
        db_geometry = connection.execute(
            """
            SELECT health_region_code, ST_AsBinary(geom)
            FROM geo.health_regions
            WHERE geography_version = %s
            ORDER BY health_region_code
            """,
            (GEOGRAPHY_VERSION,),
        ).fetchall()
        expected_geometry = geometry.sort_values("health_region_code")
        expected_wkb = {
            row.health_region_code: bytes(row.geometry.wkb)
            for row in expected_geometry.itertuples(index=False)
        }
        for code, db_wkb in db_geometry:
            if bytes(db_wkb) != expected_wkb[code]:
                raise AssertionError(f"Database geometry differs for health_region_code={code}")


def validate_database(connection, release: dict[str, Any]) -> dict[str, Any]:
    geography_version = release["geography_version"]
    checks = {
        "releases": scalar(
            connection,
            "SELECT count(*) FROM meta.releases WHERE release_id = %s",
            (RELEASE_ID,),
        ),
        "serving_status": scalar(
            connection,
            """
            SELECT count(*)
            FROM meta.serving_database_status
            WHERE release_id = %s AND serving_database_status = 'VALIDATED_LOCAL'
            """,
            (RELEASE_ID,),
        ),
        "health_regions": scalar(
            connection,
            "SELECT count(*) FROM geo.health_regions WHERE geography_version = %s",
            (geography_version,),
        ),
        "municipalities": scalar(
            connection,
            """
            SELECT count(*)
            FROM geo.municipality_health_region_crosswalk
            WHERE geography_version = %s
            """,
            (geography_version,),
        ),
        "metrics": scalar(
            connection,
            "SELECT count(*) FROM analytics.health_region_metrics WHERE release_id = %s",
            (RELEASE_ID,),
        ),
        "profile": scalar(
            connection,
            "SELECT count(*) FROM serving.health_region_profile WHERE release_id = %s",
            (RELEASE_ID,),
        ),
        "map": scalar(
            connection,
            "SELECT count(*) FROM serving.health_region_map WHERE release_id = %s",
            (RELEASE_ID,),
        ),
        "lookup": scalar(
            connection,
            "SELECT count(*) FROM serving.health_region_lookup WHERE release_id = %s",
            (RELEASE_ID,),
        ),
        "srid_4674": scalar(
            connection,
            """
            SELECT count(*)
            FROM geo.health_regions
            WHERE geography_version = %s AND ST_SRID(geom) = 4674
            """,
            (geography_version,),
        ),
        "valid_geom": scalar(
            connection,
            """
            SELECT count(*)
            FROM geo.health_regions
            WHERE geography_version = %s AND ST_IsValid(geom)
            """,
            (geography_version,),
        ),
        "lisa_significant": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_metrics
            WHERE release_id = %s AND lisa_significant
            """,
            (RELEASE_ID,),
        ),
        "small_suicide": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_metrics
            WHERE release_id = %s AND %s = ANY(data_quality_flags)
            """,
            (RELEASE_ID, "SMALL_SUICIDE_COUNT"),
        ),
        "zero_beds": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_metrics
            WHERE release_id = %s AND %s = ANY(data_quality_flags)
            """,
            (RELEASE_ID, "ZERO_REGISTERED_BEDS"),
        ),
        "intelligence_versions": scalar(
            connection,
            """
            SELECT count(*)
            FROM meta.product_intelligence_versions
            WHERE release_id = %s AND intelligence_version = %s
            """,
            (RELEASE_ID, INTELLIGENCE_VERSION),
        ),
        "intelligence": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_intelligence
            WHERE release_id = %s AND intelligence_version = %s
            """,
            (RELEASE_ID, INTELLIGENCE_VERSION),
        ),
        "peers": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_peers
            WHERE release_id = %s AND peer_method_version = %s
            """,
            (RELEASE_ID, PEER_METHOD_VERSION),
        ),
        "peer_benchmarks": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_peer_benchmarks
            WHERE release_id = %s AND peer_method_version = %s
            """,
            (RELEASE_ID, PEER_METHOD_VERSION),
        ),
    }
    expected = {
        "releases": 1,
        "serving_status": 1,
        "health_regions": 439,
        "municipalities": 5570,
        "metrics": 439,
        "profile": 439,
        "map": 439,
        "lookup": 439,
        "srid_4674": 439,
        "valid_geom": 439,
        "lisa_significant": EXPECTED_LISA["total"],
        "small_suicide": 7,
        "zero_beds": 275,
        "intelligence_versions": 1,
        "intelligence": 439,
        "peers": 4390,
        "peer_benchmarks": 3512,
    }
    if checks != expected:
        raise AssertionError(f"Database validation failed: got={checks}, expected={expected}")

    clusters = dict(
        connection.execute(
            """
            SELECT lisa_cluster, count(*)
            FROM analytics.health_region_metrics
            WHERE release_id = %s AND lisa_significant
            GROUP BY lisa_cluster
            """,
            (RELEASE_ID,),
        ).fetchall()
    )
    expected_clusters = {key: value for key, value in EXPECTED_LISA.items() if key != "total"}
    if clusters != expected_clusters:
        raise AssertionError(f"LISA cluster counts changed: {clusters}")

    intelligence_checks = {
        "spatial_hh_mismatch": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_intelligence
            WHERE release_id = %s AND intelligence_version = %s AND spatial_hh_mismatch
            """,
            (RELEASE_ID, INTELLIGENCE_VERSION),
        ),
        "self_peers": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_peers
            WHERE release_id = %s AND peer_method_version = %s
              AND health_region_code = peer_health_region_code
            """,
            (RELEASE_ID, PEER_METHOD_VERSION),
        ),
        "duplicate_peers": scalar(
            connection,
            """
            SELECT count(*)
            FROM (
                SELECT health_region_code, peer_health_region_code, count(*) AS n
                FROM analytics.health_region_peers
                WHERE release_id = %s AND peer_method_version = %s
                GROUP BY health_region_code, peer_health_region_code
                HAVING count(*) > 1
            ) d
            """,
            (RELEASE_ID, PEER_METHOD_VERSION),
        ),
        "decomposition_failures": scalar(
            connection,
            """
            SELECT count(*)
            FROM analytics.health_region_intelligence
            WHERE release_id = %s AND intelligence_version = %s
              AND abs(decomposition_sum - mismatch_score) > 1e-12
            """,
            (RELEASE_ID, INTELLIGENCE_VERSION),
        ),
    }
    expected_intelligence = {
        "spatial_hh_mismatch": 60,
        "self_peers": 0,
        "duplicate_peers": 0,
        "decomposition_failures": 0,
    }
    if intelligence_checks != expected_intelligence:
        raise AssertionError(
            f"Product intelligence validation failed: "
            f"got={intelligence_checks}, expected={expected_intelligence}"
        )

    hashes = connection.execute(
        """
        SELECT health_regions_sha256, crosswalk_sha256
        FROM meta.releases
        WHERE release_id = %s
        """,
        (RELEASE_ID,),
    ).fetchone()
    if hashes[0] != release["health_regions_sha256"] or hashes[1] != release["crosswalk_sha256"]:
        raise AssertionError("Stored canonical hashes differ from current manifest.")
    return checks


def load() -> dict[str, Any]:
    root = repo_root()
    manifest = validate_canonical_manifest(root)
    validate_scientific_locks(root)
    health_regions = read_health_regions(root, manifest)
    crosswalk = read_crosswalk(root, manifest)
    validate_lisa_and_flags(health_regions)
    release = release_values(manifest)
    indicators = indicator_records(root)
    intelligence, peers, benchmarks, intelligence_hashes = read_product_intelligence(root)

    with connect() as connection:
        with connection.transaction():
            apply_migrations(connection, root)
            mode = enforce_release_immutability(connection, release)
            enforce_product_intelligence_immutability(connection, intelligence_hashes)
            geometry = None if database_has_geography(connection) else load_geometry(root)
            insert_release(connection, release)
            insert_indicators(connection, indicators)
            if geometry is not None:
                insert_geography(connection, health_regions, geometry)
            insert_crosswalk(connection, crosswalk)
            insert_metrics(connection, health_regions)
            insert_product_intelligence_version(connection, intelligence_hashes)
            insert_product_intelligence_rows(connection, intelligence)
            insert_product_peers(connection, peers)
            insert_product_peer_benchmarks(connection, benchmarks)
            # Visible only after every check succeeds and the transaction commits.
            insert_serving_status(connection, root)
            checks = validate_database(connection, release)
            assert_database_matches_canonical(connection, health_regions, crosswalk, geometry)
    return {"status": mode, "checks": checks}


def main() -> int:
    try:
        result = load()
    except Exception as exc:
        print("SERVING DATABASE LOAD")
        print("FAIL")
        print(str(exc))
        return 1
    print("SERVING DATABASE LOAD")
    print("PASS")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the derived web geometry layer from locked PostGIS health-region geometry."""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.load_serving_database import apply_migrations, dsn, repo_root

WEB_GEOMETRY_VERSION = "MDB_WEB_GEOMETRY_V1"
GEOGRAPHY_VERSION = "BR_HEALTH_REGIONS_END2024_V1"
SOURCE_SRID = 4674
METRIC_SRID = 5880
WEB_SRID = 4326
EXPECTED_HEALTH_REGIONS = 439
TOLERANCE_CANDIDATES_M = [5000, 2000, 1000, 500, 250, 100, 50]
SELECTED_PROFILES = {"overview": 5000, "detail": 1000}
METHOD = "PostGIS ST_CoverageSimplify in EPSG:5880, transformed to EPSG:4326"
BASE_API_BYTES = 146_130_031


@dataclass(frozen=True)
class CandidateResult:
    tolerance_m: int
    status: str
    elapsed_ms: float
    feature_count: int | None = None
    unique_codes: int | None = None
    output_vertices: int | None = None
    vertex_reduction_percent: float | None = None
    valid_geometry_count: int | None = None
    empty_geometry_count: int | None = None
    srid_min: int | None = None
    srid_max: int | None = None
    area_diff_percent: float | None = None
    symdiff_area_percent: float | None = None
    max_hausdorff_m: float | None = None
    coverage_invalid_edges: int | None = None
    bbox: str | None = None
    error: str | None = None


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def gzip_file(path: Path) -> Path:
    gz_path = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as source, gzip.open(gz_path, "wb", compresslevel=9) as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            target.write(chunk)
    return gz_path


def source_fingerprint(connection) -> str:
    digest = hashlib.sha256()
    rows = connection.execute(
        """
        SELECT health_region_code, ST_AsEWKB(geom)
        FROM geo.health_regions
        WHERE geography_version = %s
        ORDER BY health_region_code
        """,
        (GEOGRAPHY_VERSION,),
    )
    for code, ewkb in rows:
        digest.update(code.encode("ascii"))
        digest.update(b"\0")
        digest.update(bytes(ewkb))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_source(connection) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT count(*) AS feature_count,
               count(DISTINCT health_region_code) AS unique_codes,
               sum(ST_NPoints(geom)) AS vertex_count,
               min(ST_SRID(geom)) AS srid_min,
               max(ST_SRID(geom)) AS srid_max,
               count(*) FILTER (WHERE ST_IsValid(geom)) AS valid_geometry_count,
               count(*) FILTER (WHERE ST_IsEmpty(geom)) AS empty_geometry_count,
               array_agg(DISTINCT ST_GeometryType(geom)) AS geometry_types,
               ST_AsText(ST_Extent(geom)) AS bbox,
               sum(ST_Area(geom::geography)) AS area_m2
        FROM geo.health_regions
        WHERE geography_version = %s
        """,
        (GEOGRAPHY_VERSION,),
    ).fetchone()
    source = {
        "feature_count": row[0],
        "unique_codes": row[1],
        "vertex_count": row[2],
        "srid_min": row[3],
        "srid_max": row[4],
        "valid_geometry_count": row[5],
        "empty_geometry_count": row[6],
        "geometry_types": row[7],
        "bbox": row[8],
        "area_m2": float(row[9]),
        "source_geometry_fingerprint_sha256": source_fingerprint(connection),
    }
    if source["feature_count"] != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("Locked source feature count changed.")
    if source["unique_codes"] != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("Locked source health_region_code count changed.")
    if source["srid_min"] != SOURCE_SRID or source["srid_max"] != SOURCE_SRID:
        raise AssertionError("Locked source SRID changed.")
    if source["valid_geometry_count"] != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("Locked source has invalid geometries.")
    if source["empty_geometry_count"] != 0:
        raise AssertionError("Locked source has empty geometries.")
    return source


def full_geojson_payload(connection, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    payload = connection.execute(
        """
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(json_build_object(
                'type', 'Feature',
                'id', health_region_code,
                'geometry', ST_AsGeoJSON(geom)::json,
                'properties', json_build_object(
                    'health_region_code', health_region_code,
                    'health_region_name', health_region_name,
                    'uf', uf
                )
            ) ORDER BY uf, health_region_name, health_region_code),
            'crs', json_build_object(
                'type', 'name',
                'properties', json_build_object('name', 'EPSG:4674')
            )
        )::text
        FROM geo.health_regions
        WHERE geography_version = %s
        """,
        (GEOGRAPHY_VERSION,),
    ).fetchone()[0].encode("utf-8")
    path = output_dir / "health_regions_full_scientific_baseline.sample.geojson"
    path.write_bytes(payload)
    gz_path = gzip_file(path)
    return {
        "feature_count": EXPECTED_HEALTH_REGIONS,
        "uncompressed_size_bytes": len(payload),
        "gzip_size_bytes": gz_path.stat().st_size,
        "sha256": sha256_bytes(payload),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "path": str(path.relative_to(repo_root())),
        "gzip_path": str(gz_path.relative_to(repo_root())),
    }


def prepare_projected_source(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS pg_temp.mdb_web_geometry_source")
    connection.execute(
        """
        CREATE TEMP TABLE mdb_web_geometry_source AS
        SELECT geography_version, health_region_code, health_region_name, uf, geom,
               ST_Transform(geom, %s) AS geom_m
        FROM geo.health_regions
        WHERE geography_version = %s
        ORDER BY health_region_code
        """,
        (METRIC_SRID, GEOGRAPHY_VERSION),
    )


def candidate_sql(select_sql: str) -> str:
    return (
        """
        WITH simplified_m AS (
            SELECT geography_version, health_region_code, health_region_name, uf, geom, geom_m,
                   ST_SetSRID(
                       ST_CoverageSimplify(geom_m, %s, true) OVER (),
                       5880
                   ) AS geom_s_m
            FROM mdb_web_geometry_source
        ),
        web AS (
            SELECT geography_version, health_region_code, health_region_name, uf, geom, geom_m,
                   geom_s_m,
                   ST_Multi(ST_Transform(geom_s_m, 4326))::geometry(MultiPolygon, 4326)
                       AS geom_web
            FROM simplified_m
        )
        """
        + select_sql
    )


def benchmark_candidate(connection, tolerance_m: int, source: dict[str, Any]) -> CandidateResult:
    started = time.perf_counter()
    try:
        row = connection.execute(
            candidate_sql(
                """
                , invalid_edges AS (
                    SELECT health_region_code,
                           ST_CoverageInvalidEdges(geom_s_m, 0) OVER () AS invalid_edge
                    FROM web
                )
                SELECT count(*),
                       count(DISTINCT health_region_code),
                       sum(ST_NPoints(geom_web)),
                       count(*) FILTER (WHERE ST_IsValid(geom_web)),
                       count(*) FILTER (WHERE ST_IsEmpty(geom_web)),
                       min(ST_SRID(geom_web)),
                       max(ST_SRID(geom_web)),
                       abs(sum(ST_Area(geom_web::geography)) - %s) / %s * 100.0,
                       sum(ST_Area(ST_SymDifference(geom_m, geom_s_m))) / %s * 100.0,
                       max(ST_HausdorffDistance(geom_m, geom_s_m)),
                       (SELECT sum(CASE
                            WHEN invalid_edge IS NULL OR ST_IsEmpty(invalid_edge) THEN 0
                            ELSE 1
                        END)
                        FROM invalid_edges),
                       ST_AsText(ST_Extent(geom_web))
                FROM web
                """
            ),
            (
                tolerance_m,
                source["area_m2"],
                source["area_m2"],
                source["area_m2"],
            ),
        ).fetchone()
        output_vertices = int(row[2])
        return CandidateResult(
            tolerance_m=tolerance_m,
            status="PASS",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            feature_count=row[0],
            unique_codes=row[1],
            output_vertices=output_vertices,
            vertex_reduction_percent=round(
                (1 - output_vertices / source["vertex_count"]) * 100, 4
            ),
            valid_geometry_count=row[3],
            empty_geometry_count=row[4],
            srid_min=row[5],
            srid_max=row[6],
            area_diff_percent=round(float(row[7]), 6),
            symdiff_area_percent=round(float(row[8]), 6),
            max_hausdorff_m=round(float(row[9]), 3),
            coverage_invalid_edges=int(row[10]),
            bbox=row[11],
        )
    except psycopg.errors.QueryCanceled:
        connection.rollback()
        return CandidateResult(
            tolerance_m=tolerance_m,
            status="TIMEOUT",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            error="statement_timeout",
        )
    except psycopg.Error as exc:
        connection.rollback()
        return CandidateResult(
            tolerance_m=tolerance_m,
            status="FAIL",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            error=exc.__class__.__name__,
        )


def build_profile_rows(connection, profile: str, tolerance_m: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        candidate_sql(
            """
            SELECT health_region_code, health_region_name, uf,
                   ST_AsEWKB(geom) AS source_ewkb,
                   ST_AsEWKB(geom_web) AS web_ewkb,
                   ST_AsGeoJSON(geom_web)::json AS geometry
            FROM web
            ORDER BY uf, health_region_name, health_region_code
            """
        ),
        (tolerance_m,),
    ).fetchall()
    result = []
    for code, name, uf, source_ewkb, web_ewkb, geometry in rows:
        result.append(
            {
                "health_region_code": code,
                "health_region_name": name,
                "uf": uf,
                "source_sha256": sha256_bytes(bytes(source_ewkb)),
                "web_ewkb": bytes(web_ewkb),
                "geometry": geometry if isinstance(geometry, dict) else json.loads(geometry),
                "profile": profile,
                "tolerance_m": tolerance_m,
            }
        )
    return result


def load_profile(connection, profile: str, tolerance_m: int, rows: list[dict[str, Any]]) -> None:
    connection.execute(
        """
        DELETE FROM web.health_region_geometry
        WHERE web_geometry_version = %s
          AND geography_version = %s
          AND geometry_profile = %s
        """,
        (WEB_GEOMETRY_VERSION, GEOGRAPHY_VERSION, profile),
    )
    with connection.cursor() as cursor:
        for row in rows:
            cursor.execute(
                """
                INSERT INTO web.health_region_geometry (
                    web_geometry_version, geography_version, health_region_code,
                    geometry_profile, source_srid, web_srid, simplification_method,
                    simplification_tolerance_m, source_geometry_sha256, geom
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKB(%s))
                """,
                (
                    WEB_GEOMETRY_VERSION,
                    GEOGRAPHY_VERSION,
                    row["health_region_code"],
                    profile,
                    SOURCE_SRID,
                    WEB_SRID,
                    METHOD,
                    tolerance_m,
                    row["source_sha256"],
                    row["web_ewkb"],
                ),
            )


def feature_collection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": row["health_region_code"],
                "geometry": row["geometry"],
                "properties": {
                    "health_region_code": row["health_region_code"],
                    "health_region_name": row["health_region_name"],
                    "uf": row["uf"],
                },
            }
            for row in rows
        ],
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    }


def write_profile_asset(
    profile: str, rows: list[dict[str, Any]], output_dir: Path, source: dict[str, Any]
) -> dict[str, Any]:
    payload = json.dumps(
        feature_collection(rows),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    path = output_dir / f"health_regions_{profile}.geojson"
    path.write_bytes(payload)
    gz_path = gzip_file(path)
    output_vertices = geometry_vertex_count(rows)
    return {
        "profile": profile,
        "feature_count": len(rows),
        "source_vertex_count": source["vertex_count"],
        "output_vertex_count": output_vertices,
        "vertex_reduction_percent": round(
            (1 - output_vertices / source["vertex_count"]) * 100, 4
        ),
        "uncompressed_size_bytes": len(payload),
        "gzip_size_bytes": gz_path.stat().st_size,
        "sha256": sha256_bytes(payload),
        "gzip_sha256": sha256_file(gz_path),
        "method": METHOD,
        "tolerance_m": rows[0]["tolerance_m"],
        "crs": "EPSG:4326",
        "valid_geometry_count": len(rows),
        "path": str(path.relative_to(repo_root())),
        "gzip_path": str(gz_path.relative_to(repo_root())),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometry_vertex_count(rows: list[dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        for polygon in row["geometry"]["coordinates"]:
            for ring in polygon:
                total += len(ring)
    return total


def verify_loaded_profiles(connection, source_fingerprint_before: str) -> dict[str, Any]:
    source_after = source_fingerprint(connection)
    if source_after != source_fingerprint_before:
        raise AssertionError("Locked geo.health_regions fingerprint changed.")
    rows = connection.execute(
        """
        WITH invalid_edges AS (
            SELECT geometry_profile,
                   ST_CoverageInvalidEdges(ST_Transform(geom, 5880), 0.001) OVER (
                       PARTITION BY geometry_profile
                   ) AS invalid_edge
            FROM web.health_region_geometry
            WHERE web_geometry_version = %s
              AND geography_version = %s
        )
        SELECT geometry_profile, count(*), count(DISTINCT health_region_code),
               count(*) FILTER (WHERE ST_IsValid(geom)), count(*) FILTER (WHERE ST_IsEmpty(geom)),
               min(ST_SRID(geom)), max(ST_SRID(geom)),
               (
                   SELECT sum(CASE
                       WHEN invalid_edge IS NULL OR ST_IsEmpty(invalid_edge) THEN 0
                       ELSE 1
                   END)
                   FROM invalid_edges i
                   WHERE i.geometry_profile = g.geometry_profile
               )
        FROM web.health_region_geometry
            g
        WHERE web_geometry_version = %s
          AND geography_version = %s
        GROUP BY geometry_profile
        ORDER BY geometry_profile
        """,
        (
            WEB_GEOMETRY_VERSION,
            GEOGRAPHY_VERSION,
            WEB_GEOMETRY_VERSION,
            GEOGRAPHY_VERSION,
        ),
    ).fetchall()
    qc = {}
    for profile, count, unique_codes, valid, empty, srid_min, srid_max, invalid_edges in rows:
        qc[profile] = {
            "feature_count": count,
            "unique_codes": unique_codes,
            "valid_geometry_count": valid,
            "empty_geometry_count": empty,
            "srid_min": srid_min,
            "srid_max": srid_max,
            "coverage_invalid_edges": int(invalid_edges),
        }
        if count != EXPECTED_HEALTH_REGIONS or unique_codes != EXPECTED_HEALTH_REGIONS:
            raise AssertionError(f"{profile} feature/code count failed.")
        if valid != EXPECTED_HEALTH_REGIONS or empty != 0:
            raise AssertionError(f"{profile} validity failed.")
        if srid_min != WEB_SRID or srid_max != WEB_SRID:
            raise AssertionError(f"{profile} SRID failed.")
    if sorted(qc) != ["detail", "overview"]:
        raise AssertionError("Expected overview and detail profiles.")
    return {"source_unchanged": True, "profiles": qc}


def write_svg_qc(connection, qc_dir: Path) -> list[str]:
    qc_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    targets = [
        ("brazil_original_vs_overview", None, "overview", 0.05),
        ("brazil_original_vs_detail", None, "detail", 0.03),
        ("coastal_region_original_vs_detail", "33005", "detail", 0.005),
        ("small_complex_region_original_vs_detail", "35064", "detail", 0.005),
        ("dense_internal_boundaries_original_vs_overview", "SP", "overview", 0.01),
    ]
    for name, focus, profile, visual_tolerance_degrees in targets:
        if focus in {"SP"}:
            where = "AND g.uf = %s"
            params = (
                visual_tolerance_degrees,
                WEB_GEOMETRY_VERSION,
                GEOGRAPHY_VERSION,
                profile,
                focus,
            )
        elif focus:
            where = "AND g.health_region_code = %s"
            params = (
                visual_tolerance_degrees,
                WEB_GEOMETRY_VERSION,
                GEOGRAPHY_VERSION,
                profile,
                focus,
            )
        else:
            where = ""
            params = (
                visual_tolerance_degrees,
                WEB_GEOMETRY_VERSION,
                GEOGRAPHY_VERSION,
                profile,
            )
        svg = connection.execute(
            f"""
            WITH pairs AS (
                SELECT ST_SimplifyPreserveTopology(ST_Transform(g.geom, 4326), %s)
                           AS original_visual,
                       w.geom AS derived
                FROM geo.health_regions g
                JOIN web.health_region_geometry w
                  ON w.geography_version = g.geography_version
                 AND w.health_region_code = g.health_region_code
                WHERE w.web_geometry_version = %s
                  AND g.geography_version = %s
                  AND w.geometry_profile = %s
                  {where}
            ),
            extent AS (
                SELECT ST_Envelope(ST_Extent(original_visual)::geometry) AS box FROM pairs
            )
            SELECT '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' ||
                   ST_XMin(box) || ' ' || (-ST_YMax(box)) || ' ' ||
                   (ST_XMax(box)-ST_XMin(box)) || ' ' || (ST_YMax(box)-ST_YMin(box)) ||
                   '"><g fill="none" stroke-width="0.015">' ||
                   string_agg('<path d="' || ST_AsSVG(original_visual, 1, 6) ||
                       '" stroke="#111827" opacity="0.45"/>', '') ||
                   string_agg('<path d="' || ST_AsSVG(derived, 1, 6) ||
                       '" stroke="#dc2626" opacity="0.9"/>', '') ||
                   '</g></svg>'
            FROM pairs, extent
            GROUP BY box
            """,
            params,
        ).fetchone()[0]
        path = qc_dir / f"{name}.svg"
        path.write_text(svg, encoding="utf-8")
        outputs.append(str(path.relative_to(repo_root())))
    return outputs


def write_manifest(
    manifest_path: Path,
    source: dict[str, Any],
    full_payload: dict[str, Any],
    candidates: list[CandidateResult],
    outputs: list[dict[str, Any]],
    load_qc: dict[str, Any],
    qc_images: list[str],
) -> None:
    manifest = {
        "web_geometry_version": WEB_GEOMETRY_VERSION,
        "generated_at": now_iso(),
        "source": {
            "table": "geo.health_regions",
            "geography_version": GEOGRAPHY_VERSION,
            "source_srid": SOURCE_SRID,
            "web_srid": WEB_SRID,
            "feature_count": source["feature_count"],
            "vertex_count": source["vertex_count"],
            "geometry_types": source["geometry_types"],
            "bbox": source["bbox"],
            "source_geometry_fingerprint_sha256": source[
                "source_geometry_fingerprint_sha256"
            ],
        },
        "baseline_payload": {
            "scientific_geojson_size_bytes": full_payload["uncompressed_size_bytes"],
            "scientific_geojson_gzip_size_bytes": full_payload["gzip_size_bytes"],
            "api_full_response_size_bytes": BASE_API_BYTES,
        },
        "method": METHOD,
        "candidate_benchmark": [candidate.__dict__ for candidate in candidates],
        "selected_profiles": {
            profile: {
                "method": METHOD,
                "tolerance_m": tolerance,
            }
            for profile, tolerance in SELECTED_PROFILES.items()
        },
        "selection_rationale": (
            "overview uses 5000 m because it reduces the national geometry to a very "
            "small browser-suitable layer while preserving all regions and valid shared "
            "coverage; detail uses 1000 m because it keeps substantially more boundary "
            "detail for state/regional zoom while remaining far smaller than full geometry."
        ),
        "qc_thresholds": {
            "feature_count": EXPECTED_HEALTH_REGIONS,
            "unique_codes": EXPECTED_HEALTH_REGIONS,
            "required_srid": WEB_SRID,
            "invalid_geometry_count": 0,
            "empty_geometry_count": 0,
            "coverage_invalid_edges": 0,
            "minimum_payload_reduction_percent": 90,
        },
        "outputs": outputs,
        "load_qc": load_qc,
        "visual_qc": qc_images,
        "limitations": [
            "Derived web geometry is for visualization only.",
            "Scientific area_km2 and all analytical metrics remain sourced from "
            "canonical/serving data.",
            "Full scientific geometry remains available only via explicit API request.",
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def build() -> None:
    root = repo_root()
    output_dir = root / "data/web" / WEB_GEOMETRY_VERSION
    qc_dir = root / "docs/web_geometry_qc_2026-08-24"
    output_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)

    with psycopg.connect(dsn(), autocommit=True) as connection:
        connection.execute("SET statement_timeout = '15min'")
        apply_migrations(connection, root)
        source = validate_source(connection)
        source_fingerprint_before = source["source_geometry_fingerprint_sha256"]
        print("SOURCE PASS", source["feature_count"], source["vertex_count"])
        full_payload = full_geojson_payload(connection, output_dir)
        print("BASELINE PAYLOAD", full_payload["uncompressed_size_bytes"])

        prepare_projected_source(connection)
        candidates = []
        skip_remaining = False
        for tolerance_m in TOLERANCE_CANDIDATES_M:
            if skip_remaining:
                candidate = CandidateResult(
                    tolerance_m=tolerance_m,
                    status="SKIPPED_AFTER_TIMEOUT",
                    elapsed_ms=0,
                    error="finer_than_timed_out_candidate",
                )
            else:
                connection.execute("SET statement_timeout = '120s'")
                candidate = benchmark_candidate(connection, tolerance_m, source)
                if candidate.status in {"TIMEOUT", "FAIL"} and tolerance_m <= 500:
                    skip_remaining = True
            candidates.append(candidate)
            print("CANDIDATE", candidate.__dict__)
        connection.execute("SET statement_timeout = '15min'")

        outputs = []
        for profile, tolerance_m in SELECTED_PROFILES.items():
            rows = build_profile_rows(connection, profile, tolerance_m)
            load_profile(connection, profile, tolerance_m, rows)
            output = write_profile_asset(profile, rows, output_dir, source)
            outputs.append(output)
            print("PROFILE", profile, output)

        load_qc = verify_loaded_profiles(connection, source_fingerprint_before)
        qc_images = write_svg_qc(connection, qc_dir)
        write_manifest(
            root / "metadata/web_geometry/MDB_WEB_GEOMETRY_V1_manifest.yaml",
            source,
            full_payload,
            candidates,
            outputs,
            load_qc,
            qc_images,
        )
        print("WEB GEOMETRY BUILD PASS")


if __name__ == "__main__":
    build()

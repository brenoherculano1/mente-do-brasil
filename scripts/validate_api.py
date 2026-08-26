"""Validate the local read-only Mente do Brasil API against the serving database."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.config import get_settings

RELEASE_ID = "MDB_ANALYTICAL_2024_1"
EXPECTED_HEALTH_REGIONS = 439
EXPECTED_MUNICIPALITIES = 5570
EXPECTED_LISA = {"high-high": 60, "low-low": 66, "high-low": 4, "low-high": 5}
EXPECTED_FLAGS = {"SMALL_SUICIDE_COUNT": 7, "ZERO_REGISTERED_BEDS": 275}
WEB_GEOMETRY_VERSION = "MDB_WEB_GEOMETRY_V1"


@dataclass
class Response:
    status: int
    body: Any
    elapsed_ms: float
    size_bytes: int


def request(path: str, expected_status: int = 200) -> Response:
    settings = get_settings()
    base = f"http://{settings.api_host}:{settings.api_port}"
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(base + path, timeout=60) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read()
        status = error.code
    elapsed_ms = (time.perf_counter() - started) * 1000
    if status != expected_status:
        raise AssertionError(f"{path} returned {status}, expected {expected_status}: {raw[:300]!r}")
    return Response(status, json.loads(raw.decode("utf-8")), elapsed_ms, len(raw))


def gzip_size(path: str) -> tuple[int, int, str | None]:
    settings = get_settings()
    base = f"http://{settings.api_host}:{settings.api_port}"
    request_obj = urllib.request.Request(base + path, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(request_obj, timeout=60) as response:
        raw = response.read()
        encoding = response.headers.get("Content-Encoding")
    return len(raw), response.status, encoding


def db_scalar(sql: str, params: tuple = ()) -> Any:
    settings = get_settings()
    with psycopg.connect(settings.dsn, autocommit=True) as connection:
        return connection.execute(sql, params).fetchone()[0]


def db_row(sql: str, params: tuple = ()) -> tuple:
    settings = get_settings()
    with psycopg.connect(settings.dsn, autocommit=True) as connection:
        return connection.execute(sql, params).fetchone()


def assert_read_only_role() -> None:
    settings = get_settings()
    with psycopg.connect(settings.dsn, autocommit=True) as connection:
        read_only = connection.execute("SHOW default_transaction_read_only").fetchone()[0]
        if read_only != "on":
            raise AssertionError("API DB role default_transaction_read_only is not on.")
        write_attempts = [
            "INSERT INTO meta.indicators (indicator_id, indicator_name_pt, indicator_name_en, "
            "domain, description, unit, interpretation, method_version, source_system) "
            "VALUES ('x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x')",
            "UPDATE meta.releases SET release_status = release_status WHERE release_id = "
            f"'{RELEASE_ID}'",
            "DELETE FROM meta.indicators WHERE indicator_id = '__never__'",
            "CREATE TABLE public.__mdb_api_write_probe (id integer)",
        ]
        for statement in write_attempts:
            try:
                connection.execute(statement)
            except psycopg.Error:
                continue
            raise AssertionError(f"API DB role unexpectedly allowed write: {statement[:40]}")


def validate() -> None:
    print("MENTE DO BRASIL API VALIDATION")
    health = request("/health")
    if health.body != {"status": "ok"}:
        raise AssertionError("/health contract changed.")
    print("health PASS")

    ready = request("/ready")
    if ready.body != {"status": "ready", "database": "ok", "release_id": RELEASE_ID}:
        raise AssertionError("/ready contract changed.")
    print("ready PASS")

    releases = request("/api/v1/releases")
    if len(releases.body) != 1 or releases.body[0]["release_id"] != RELEASE_ID:
        raise AssertionError("Release list does not expose the locked release exactly once.")
    request(f"/api/v1/releases/{RELEASE_ID}")
    print("releases PASS")

    indicators = request("/api/v1/indicators")
    indicator_ids = {indicator["indicator_id"] for indicator in indicators.body}
    if indicator_ids != {
        "suicide_asmr",
        "psychiatric_admission_rate",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
    }:
        raise AssertionError(f"Unexpected indicators: {sorted(indicator_ids)}")
    print("indicators PASS")

    regions = request("/api/v1/health-regions?limit=100")
    if regions.body["pagination"]["total"] != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("Health region total changed.")
    print("health regions PASS")

    state_ac = request("/api/v1/states/AC")
    if state_ac.body["state"]["health_region_count"] != 3 or len(state_ac.body["regions"]) != 3:
        raise AssertionError("AC state contract did not return 3 Health Regions.")
    if any(
        field in state_ac.body["state"]
        for field in ["state_need_score", "state_capacity_score", "state_mismatch_score", "ranking"]
    ):
        raise AssertionError("State contract exposed a state score or ranking field.")
    if state_ac.body["state"]["population"] != sum(
        region["population"] for region in state_ac.body["regions"]
    ):
        raise AssertionError("State population aggregation mismatch.")
    state_sp = request("/api/v1/states/SP")
    if state_sp.body["state"]["health_region_count"] != len(state_sp.body["regions"]):
        raise AssertionError("Large-state count mismatch.")
    state_df = request("/api/v1/states/DF")
    if state_df.body["state"]["uf"] != "DF" or not state_df.body["regions"]:
        raise AssertionError("DF state contract failed.")
    request("/api/v1/states/ac")
    request("/api/v1/states/XX", 404)
    injection_state = urllib.parse.quote("AC' OR '1'='1", safe="")
    request(f"/api/v1/states/{injection_state}", 422)
    print("state profiles PASS")

    profile = request("/api/v1/health-regions/12001")
    db_profile = db_row(
        """
        SELECT health_region_name, uf, population, need_score, capacity_score,
               mismatch_score, psychiatrist_fte_rate
        FROM serving.health_region_profile
        WHERE release_id = %s AND health_region_code = '12001'
        """,
        (RELEASE_ID,),
    )
    api_profile = profile.body
    if (
        api_profile["territory"]["health_region_name"],
        api_profile["territory"]["uf"],
        api_profile["territory"]["population"],
        api_profile["need"]["score"],
        api_profile["capacity"]["score"],
        api_profile["mismatch"]["score"],
        api_profile["capacity"]["psychiatrist_fte"]["rate"],
    ) != db_profile:
        raise AssertionError("API profile differs from serving view for 12001.")
    print("profile PASS")

    municipality = request("/api/v1/municipalities/1100015/health-region")
    if municipality.body["health_region_code"] != "11005":
        raise AssertionError("Municipality lookup mismatch for 1100015.")
    municipalities = db_scalar(
        """
        SELECT count(*)
        FROM geo.municipality_health_region_crosswalk
        WHERE geography_version = 'BR_HEALTH_REGIONS_END2024_V1'
        """
    )
    if municipalities != EXPECTED_MUNICIPALITIES:
        raise AssertionError("Municipality count changed.")
    print("municipality lookup PASS")

    web_geometry = db_row(
        """
        SELECT count(*) FILTER (WHERE geometry_profile = 'overview'),
               count(*) FILTER (WHERE geometry_profile = 'detail'),
               min(ST_SRID(geom)), max(ST_SRID(geom)),
               count(*) FILTER (WHERE NOT ST_IsValid(geom))
        FROM web.health_region_geometry
        WHERE web_geometry_version = %s
          AND geography_version = 'BR_HEALTH_REGIONS_END2024_V1'
        """,
        (WEB_GEOMETRY_VERSION,),
    )
    if web_geometry != (439, 439, 4326, 4326, 0):
        raise AssertionError(f"Web geometry table failed: {web_geometry}")

    map_rows = request("/api/v1/map/health-regions?include_geometry=false&metric=mismatch_score")
    if len(map_rows.body) != EXPECTED_HEALTH_REGIONS:
        raise AssertionError("Map metadata endpoint did not return 439 regions.")
    print("map metadata PASS")

    map_geo = request("/api/v1/map/health-regions?include_geometry=true&metric=mismatch_score")
    if map_geo.body["type"] != "FeatureCollection" or len(map_geo.body["features"]) != 439:
        raise AssertionError("GeoJSON endpoint did not return 439 features.")
    if map_geo.body["geometry_metadata"] != {
        "profile": "overview",
        "version": WEB_GEOMETRY_VERSION,
        "crs": "EPSG:4326",
    }:
        raise AssertionError("Default geometry profile is not overview.")
    overview = request(
        "/api/v1/map/health-regions?include_geometry=true&metric=mismatch_score"
        "&geometry_profile=overview"
    )
    detail = request(
        "/api/v1/map/health-regions?include_geometry=true&metric=mismatch_score"
        "&geometry_profile=detail"
    )
    full = request(
        "/api/v1/map/health-regions?include_geometry=true&metric=mismatch_score"
        "&geometry_profile=full",
        403,
    )
    if len(overview.body["features"]) != 439 or len(detail.body["features"]) != 439:
        raise AssertionError("Web geometry profile feature count changed.")
    if full.body != {
        "error": {
            "code": "FULL_GEOMETRY_RESTRICTED",
            "message": "Full geometry is not available on the operational API.",
        }
    }:
        raise AssertionError("Full geometry restriction error contract changed.")
    if full.size_bytes >= 512 or full.elapsed_ms >= 500:
        raise AssertionError(
            "Full geometry restriction should return a small response before heavy work: "
            f"{full.size_bytes} bytes, {full.elapsed_ms:.2f} ms"
        )
    if not (overview.size_bytes < detail.size_bytes):
        raise AssertionError("Geometry payload size ordering failed.")
    gz_bytes, gz_status, gz_encoding = gzip_size(
        "/api/v1/map/health-regions?include_geometry=true&metric=mismatch_score"
        "&geometry_profile=overview"
    )
    if gz_status != 200 or gz_encoding != "gzip" or gz_bytes >= overview.size_bytes:
        raise AssertionError("HTTP gzip validation failed.")
    print(
        "map geometry PASS",
        {
            "overview_bytes": overview.size_bytes,
            "detail_bytes": detail.size_bytes,
            "full_blocked_status": full.status,
            "full_blocked_bytes": full.size_bytes,
            "full_blocked_elapsed_ms": round(full.elapsed_ms, 2),
            "overview_gzip_bytes": gz_bytes,
        },
    )

    lisa_counts = {}
    for row in map_rows.body:
        if row["lisa_significant"]:
            lisa_counts[row["lisa_cluster"]] = lisa_counts.get(row["lisa_cluster"], 0) + 1
    if lisa_counts != EXPECTED_LISA:
        raise AssertionError(f"LISA counts changed: {lisa_counts}")
    print("scientific regression PASS")

    flag_counts = {}
    for row in map_rows.body:
        for flag in row["data_quality_flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    if flag_counts != EXPECTED_FLAGS:
        raise AssertionError(f"Flag counts changed: {flag_counts}")
    print("flags PASS")

    request("/api/v1/health-regions/99999", 404)
    request("/api/v1/municipalities/9999999/health-region", 404)
    request("/api/v1/map/health-regions?metric=not_a_metric", 422)
    request("/api/v1/map/health-regions?geometry_profile=unknown", 422)
    request("/api/v1/health-regions?uf=ABCDE", 422)
    request("/api/v1/states/AC?release_id=NOT_A_RELEASE", 404)
    injection = urllib.parse.quote("12001' OR '1'='1", safe="")
    request(f"/api/v1/health-regions?q={injection}&limit=10")
    print("errors PASS")

    assert_read_only_role()
    print("read-only PASS")

    print(
        "latency_ms",
        {
            "health": round(health.elapsed_ms, 2),
            "ready": round(ready.elapsed_ms, 2),
            "map_geometry_overview": round(map_geo.elapsed_ms, 2),
            "map_geometry_detail": round(detail.elapsed_ms, 2),
            "map_geometry_full_blocked": round(full.elapsed_ms, 2),
        },
    )
    print("PASS")


if __name__ == "__main__":
    validate()

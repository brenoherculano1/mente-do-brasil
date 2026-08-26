from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

import psycopg
import pytest
import yaml

from api.config import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_GEOMETRY_VERSION = "MDB_WEB_GEOMETRY_V1"
GEOGRAPHY_VERSION = "BR_HEALTH_REGIONS_END2024_V1"


def db_fetchone(sql: str, params: tuple = ()) -> tuple:
    settings = get_settings()
    try:
        with psycopg.connect(settings.dsn, autocommit=True) as connection:
            return connection.execute(sql, params).fetchone()
    except psycopg.OperationalError as error:
        pytest.skip(f"Local serving database is not available: {error}")


def api_status(path: str) -> int:
    settings = get_settings()
    base = f"http://{settings.api_host}:{settings.api_port}"
    try:
        with urllib.request.urlopen(base + path, timeout=60) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except OSError as error:
        pytest.skip(f"Local API is not running: {error}")


def test_web_geometry_manifest_contract():
    config = yaml.safe_load(
        (REPO_ROOT / "metadata/web_geometry/MDB_WEB_GEOMETRY_V1.yaml").read_text()
    )
    manifest = yaml.safe_load(
        (REPO_ROOT / "metadata/web_geometry/MDB_WEB_GEOMETRY_V1_manifest.yaml").read_text()
    )
    assert config["web_geometry_version"] == WEB_GEOMETRY_VERSION
    assert manifest["web_geometry_version"] == WEB_GEOMETRY_VERSION
    assert manifest["source"]["feature_count"] == 439
    assert manifest["source"]["vertex_count"] == 5796847
    assert manifest["selected_profiles"]["overview"]["tolerance_m"] == 5000
    assert manifest["selected_profiles"]["detail"]["tolerance_m"] == 1000
    assert {output["profile"] for output in manifest["outputs"]} == {"overview", "detail"}


def test_web_geometry_database_qc_and_source_unchanged():
    source = db_fetchone(
        """
        SELECT count(*), count(DISTINCT health_region_code), min(ST_SRID(geom)),
               max(ST_SRID(geom)), count(*) FILTER (WHERE ST_IsValid(geom))
        FROM geo.health_regions
        WHERE geography_version = %s
        """,
        (GEOGRAPHY_VERSION,),
    )
    assert source == (439, 439, 4674, 4674, 439)

    web = db_fetchone(
        """
        SELECT count(*) FILTER (WHERE geometry_profile = 'overview'),
               count(*) FILTER (WHERE geometry_profile = 'detail'),
               count(DISTINCT health_region_code),
               min(ST_SRID(geom)), max(ST_SRID(geom)),
               count(*) FILTER (WHERE ST_IsValid(geom)),
               count(*) FILTER (WHERE ST_IsEmpty(geom))
        FROM web.health_region_geometry
        WHERE web_geometry_version = %s
          AND geography_version = %s
        """,
        (WEB_GEOMETRY_VERSION, GEOGRAPHY_VERSION),
    )
    assert web == (439, 439, 439, 4326, 4326, 878, 0)


def test_web_geometry_api_profiles_are_reachable_with_full_restricted_by_default():
    assert api_status("/api/v1/map/health-regions?include_geometry=true") == 200
    assert (
        api_status("/api/v1/map/health-regions?include_geometry=true&geometry_profile=overview")
        == 200
    )
    assert (
        api_status("/api/v1/map/health-regions?include_geometry=true&geometry_profile=detail")
        == 200
    )
    assert (
        api_status("/api/v1/map/health-regions?include_geometry=true&geometry_profile=full")
        == 403
    )
    assert (
        api_status("/api/v1/map/health-regions?include_geometry=true&geometry_profile=unknown")
        == 422
    )

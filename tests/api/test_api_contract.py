from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

import psycopg
import pytest

from api.config import get_settings

RELEASE_ID = "MDB_ANALYTICAL_2024_1"


def api_get(path: str) -> tuple[int, object]:
    settings = get_settings()
    base = f"http://{settings.api_host}:{settings.api_port}"
    try:
        with urllib.request.urlopen(base + path, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))
    except OSError as error:
        pytest.skip(f"Local API is not running: {error}")


def db_fetchone(sql: str, params: tuple = ()) -> tuple:
    settings = get_settings()
    try:
        with psycopg.connect(settings.dsn, autocommit=True) as connection:
            return connection.execute(sql, params).fetchone()
    except psycopg.OperationalError as error:
        pytest.skip(f"Local serving database is not available: {error}")


def test_health_and_ready_contracts():
    assert api_get("/health") == (200, {"status": "ok"})
    assert api_get("/ready") == (
        200,
        {"status": "ready", "database": "ok", "release_id": RELEASE_ID},
    )


def test_release_and_indicator_contracts():
    status, releases = api_get("/api/v1/releases")
    assert status == 200
    assert len(releases) == 1
    assert releases[0]["release_id"] == RELEASE_ID
    assert releases[0]["release_status"] == "VALIDATING"
    assert releases[0]["quality_status"] == "VALIDATED"
    assert releases[0]["release_gate"] == "PASS"
    assert releases[0]["public_release_status"] == "NOT_RELEASED"

    status, release = api_get(f"/api/v1/releases/{RELEASE_ID}")
    assert status == 200
    assert release == releases[0]

    status, indicators = api_get("/api/v1/indicators")
    assert status == 200
    assert {indicator["indicator_id"] for indicator in indicators} == {
        "suicide_asmr",
        "psychiatric_admission_rate",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
    }


def test_health_region_list_profile_and_map_match_locked_counts():
    status, regions = api_get("/api/v1/health-regions?limit=100")
    assert status == 200
    assert regions["pagination"] == {"limit": 100, "offset": 0, "count": 100, "total": 439}

    status, ac_regions = api_get("/api/v1/health-regions?uf=AC")
    assert status == 200
    assert ac_regions["pagination"]["total"] == 3

    status, profile = api_get("/api/v1/health-regions/12001")
    assert status == 200
    db_row = db_fetchone(
        """
        SELECT health_region_name, uf, population, need_score, capacity_score,
               mismatch_score, psychiatrist_fte_rate
        FROM serving.health_region_profile
        WHERE release_id = %s AND health_region_code = '12001'
        """,
        (RELEASE_ID,),
    )
    assert (
        profile["territory"]["health_region_name"],
        profile["territory"]["uf"],
        profile["territory"]["population"],
        profile["need"]["score"],
        profile["capacity"]["score"],
        profile["mismatch"]["score"],
        profile["capacity"]["psychiatrist_fte"]["rate"],
    ) == db_row

    status, map_rows = api_get("/api/v1/map/health-regions?include_geometry=false")
    assert status == 200
    assert len(map_rows) == 439
    assert "geometry" not in map_rows[0]

    status, geojson = api_get("/api/v1/map/health-regions?include_geometry=true")
    assert status == 200
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 439
    assert geojson["crs"]["properties"]["name"] == "EPSG:4674"


def test_municipality_and_uf_lookup_contracts():
    status, lookup = api_get("/api/v1/municipalities/1100015/health-region")
    assert status == 200
    assert lookup["municipality_name"] == "Alta Floresta D'Oeste"
    assert lookup["health_region_code"] == "11005"
    assert lookup["health_region_name"] == "Zona da Mata"

    status, ufs = api_get("/api/v1/ufs")
    assert status == 200
    assert len(ufs) == 27
    assert sum(row["health_region_count"] for row in ufs) == 439


def test_error_contracts_and_parameter_guards():
    assert api_get("/api/v1/health-regions/99999")[0] == 404
    assert api_get("/api/v1/municipalities/9999999/health-region")[0] == 404
    invalid_metric_status, invalid_metric = api_get(
        "/api/v1/map/health-regions?metric=not_a_metric"
    )
    assert invalid_metric_status == 422
    assert invalid_metric["error"]["code"] == "INVALID_METRIC"
    assert api_get("/api/v1/health-regions?uf=ABCDE")[0] == 422
    assert api_get("/api/v1/health-regions?limit=101")[0] == 422
    assert api_get("/api/v1/health-regions?offset=-1")[0] == 422
    assert api_get("/api/v1/releases/NOT_A_RELEASE")[0] == 404
    assert api_get("/api/v1/health-regions?release_id=NOT_A_RELEASE")[0] == 404
    assert api_get("/api/v1/map/health-regions?release_id=NOT_A_RELEASE")[0] == 404

    injected = urllib.parse.quote("12001' OR '1'='1", safe="")
    status, payload = api_get(f"/api/v1/health-regions?q={injected}&limit=10")
    assert status == 200
    assert payload["pagination"]["total"] == 0


def test_no_unrequested_product_surfaces_exist():
    assert api_get("/api/v1/rankings")[0] == 404
    assert api_get("/api/v1/dashboard")[0] == 404
    assert api_get("/api/v1/chat")[0] == 404


def test_api_role_is_read_only():
    settings = get_settings()
    with psycopg.connect(settings.dsn, autocommit=True) as connection:
        read_only = connection.execute("SHOW default_transaction_read_only").fetchone()[0]
        assert read_only == "on"
        for statement in [
            "UPDATE meta.releases SET release_status = release_status "
            f"WHERE release_id = '{RELEASE_ID}'",
            "DELETE FROM meta.indicators WHERE indicator_id = '__never__'",
            "CREATE TABLE public.__mdb_api_write_probe (id integer)",
        ]:
            with pytest.raises(psycopg.Error):
                connection.execute(statement)

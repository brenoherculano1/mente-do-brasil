from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from types import SimpleNamespace

import psycopg
import pytest
from fastapi import HTTPException

from api.config import get_settings
from api.routers import health_regions as health_regions_router
from api.schemas.common import GeometryProfile, Metric

RELEASE_ID = "MDB_ANALYTICAL_2024_1"
WEB_GEOMETRY_VERSION = "MDB_WEB_GEOMETRY_V1"


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


def api_get_raw(path: str, headers: dict[str, str] | None = None) -> tuple[int, bytes, str | None]:
    settings = get_settings()
    base = f"http://{settings.api_host}:{settings.api_port}"
    request = urllib.request.Request(base + path, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read(), response.headers.get("Content-Encoding")
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers.get("Content-Encoding")
    except OSError as error:
        pytest.skip(f"Local API is not running: {error}")


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
    assert geojson["crs"]["properties"]["name"] == "EPSG:4326"
    assert geojson["geometry_metadata"] == {
        "profile": "overview",
        "version": WEB_GEOMETRY_VERSION,
        "crs": "EPSG:4326",
    }


def test_web_geometry_profiles_and_full_geometry_policy():
    db_row = db_fetchone(
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
    assert db_row == (439, 439, 4326, 4326, 0)

    paths = {
        "overview": "/api/v1/map/health-regions?include_geometry=true"
        "&geometry_profile=overview",
        "detail": "/api/v1/map/health-regions?include_geometry=true&geometry_profile=detail",
    }
    payloads = {}
    for profile, path in paths.items():
        status, raw, encoding = api_get_raw(path)
        assert status == 200
        assert encoding is None
        payload = json.loads(raw.decode("utf-8"))
        assert len(payload["features"]) == 439
        assert payload["geometry_metadata"]["profile"] == profile
        payloads[profile] = raw

    assert len(payloads["overview"]) < len(payloads["detail"])

    status, raw, encoding = api_get_raw(
        "/api/v1/map/health-regions?include_geometry=true&geometry_profile=full"
    )
    assert status == 403
    assert encoding is None
    assert len(raw) < 512
    assert json.loads(raw.decode("utf-8")) == {
        "error": {
            "code": "FULL_GEOMETRY_RESTRICTED",
            "message": "Full geometry is not available on the operational API.",
        }
    }


def test_full_geometry_policy_is_server_side_and_fail_closed(monkeypatch):
    monkeypatch.delenv("MDB_API_ALLOW_FULL_GEOMETRY", raising=False)
    assert get_settings().allow_full_geometry is False

    monkeypatch.setenv("MDB_API_ALLOW_FULL_GEOMETRY", "false")
    assert get_settings().allow_full_geometry is False

    monkeypatch.setenv("MDB_API_ALLOW_FULL_GEOMETRY", "0")
    assert get_settings().allow_full_geometry is False

    monkeypatch.setenv("MDB_API_ALLOW_FULL_GEOMETRY", "not-valid")
    assert get_settings().allow_full_geometry is False

    monkeypatch.setenv("MDB_API_ALLOW_FULL_GEOMETRY", "true")
    assert get_settings().allow_full_geometry is True


def test_fastapi_docs_policy_is_server_side_and_fail_closed(monkeypatch):
    monkeypatch.delenv("MDB_API_ENABLE_DOCS", raising=False)
    assert get_settings().enable_docs is False

    monkeypatch.setenv("MDB_API_ENABLE_DOCS", "false")
    assert get_settings().enable_docs is False

    monkeypatch.setenv("MDB_API_ENABLE_DOCS", "0")
    assert get_settings().enable_docs is False

    monkeypatch.setenv("MDB_API_ENABLE_DOCS", "not-valid")
    assert get_settings().enable_docs is False

    monkeypatch.setenv("MDB_API_ENABLE_DOCS", "true")
    assert get_settings().enable_docs is True


def test_programmatic_openapi_remains_available_when_docs_http_is_disabled():
    from api.main import app

    schema = app.openapi()
    assert "/api/v1/states/{uf}" in schema["paths"]
    assert "/api/v1/map/health-regions" in schema["paths"]


def test_full_geometry_block_short_circuits_before_heavy_query(monkeypatch):
    calls = []

    def fail_if_called(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Full geometry query path should not be called when blocked.")

    monkeypatch.setattr(health_regions_router, "list_map_data", fail_if_called)
    settings = SimpleNamespace(default_release_id=RELEASE_ID, allow_full_geometry=False)
    with pytest.raises(HTTPException) as error:
        health_regions_router.health_region_map(
            db=object(),
            settings=settings,
            metric=Metric.mismatch_score,
            include_geometry=True,
            geometry_profile=GeometryProfile.full,
        )

    assert error.value.status_code == 403
    assert calls == []


def test_full_geometry_policy_allows_internal_opt_in_without_fetching_payload(monkeypatch):
    calls = []

    def fake_list_map_data(*args):
        calls.append(args)
        return []

    monkeypatch.setattr(health_regions_router, "list_map_data", fake_list_map_data)
    settings = SimpleNamespace(default_release_id=RELEASE_ID, allow_full_geometry=True)

    result = health_regions_router.health_region_map(
        db=object(),
        settings=settings,
        metric=Metric.mismatch_score,
        include_geometry=True,
        geometry_profile=GeometryProfile.full,
    )

    assert result == []
    assert len(calls) == 1
    assert calls[0][-1] == GeometryProfile.full


def test_http_gzip_for_geometry_payloads():
    status, compressed, encoding = api_get_raw(
        "/api/v1/map/health-regions?include_geometry=true&geometry_profile=overview",
        headers={"Accept-Encoding": "gzip"},
    )
    assert status == 200
    assert encoding == "gzip"
    status_plain, plain, _ = api_get_raw(
        "/api/v1/map/health-regions?include_geometry=true&geometry_profile=overview"
    )
    assert status_plain == 200
    assert len(compressed) < len(plain)


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


def test_state_profile_contract_has_no_state_score_or_ranking():
    status, ac = api_get("/api/v1/states/AC")
    assert status == 200
    assert ac["release"]["release_id"] == RELEASE_ID
    assert ac["release"]["public_release_status"] == "NOT_RELEASED"
    assert ac["state"]["uf"] == "AC"
    assert ac["state"]["state_name"] == "Acre"
    assert ac["state"]["health_region_count"] == 3
    assert len(ac["regions"]) == 3
    assert [region["health_region_name"] for region in ac["regions"]] == sorted(
        region["health_region_name"] for region in ac["regions"]
    )
    assert ac["state"]["population"] == sum(region["population"] for region in ac["regions"])
    assert ac["state"]["municipality_count"] == sum(
        region["municipality_count"] for region in ac["regions"]
    )
    forbidden_state_fields = {
        "state_need_score",
        "state_capacity_score",
        "state_mismatch_score",
        "state_rank",
        "state_index",
        "state_grade",
        "ranking",
    }
    assert forbidden_state_fields.isdisjoint(ac["state"])
    assert all(forbidden_state_fields.isdisjoint(region) for region in ac["regions"])
    expected_region_fields = {
        "health_region_code",
        "health_region_name",
        "uf",
        "population",
        "municipality_count",
        "suicide_percentile",
        "psychiatric_admission_percentile",
        "need_score",
        "caps_percentile",
        "beds_percentile",
        "psychiatrist_fte_percentile",
        "capacity_score",
        "mismatch_score",
        "lisa_significant",
        "lisa_cluster",
        "data_quality_flags",
    }
    assert set(ac["regions"][0]) == expected_region_fields

    status, ac_lowercase = api_get("/api/v1/states/ac")
    assert status == 200
    assert ac_lowercase == ac

    status, ac_map = api_get(
        "/api/v1/map/health-regions?uf=AC&include_geometry=true&geometry_profile=overview"
    )
    assert status == 200
    assert len(ac_map["features"]) == ac["state"]["health_region_count"]
    assert ac_map["geometry_metadata"] == {
        "profile": "overview",
        "version": WEB_GEOMETRY_VERSION,
        "crs": "EPSG:4326",
    }


def test_state_profile_handles_df_large_state_and_invalid_inputs():
    status, sp = api_get("/api/v1/states/SP")
    assert status == 200
    assert sp["state"]["uf"] == "SP"
    assert sp["state"]["state_name"] == "São Paulo"
    assert sp["state"]["health_region_count"] == len(sp["regions"])
    assert sp["state"]["health_region_count"] > 3

    status, df = api_get("/api/v1/states/DF")
    assert status == 200
    assert df["state"]["uf"] == "DF"
    assert df["state"]["state_name"] == "Distrito Federal"
    assert df["state"]["health_region_count"] == len(df["regions"])

    assert api_get("/api/v1/states/XX")[0] == 404
    injection = urllib.parse.quote("AC' OR '1'='1", safe="")
    assert api_get(f"/api/v1/states/{injection}")[0] == 422


def test_error_contracts_and_parameter_guards():
    assert api_get("/api/v1/health-regions/99999")[0] == 404
    assert api_get("/api/v1/municipalities/9999999/health-region")[0] == 404
    invalid_metric_status, invalid_metric = api_get(
        "/api/v1/map/health-regions?metric=not_a_metric"
    )
    assert invalid_metric_status == 422
    assert invalid_metric["error"]["code"] == "INVALID_METRIC"
    assert api_get("/api/v1/map/health-regions?geometry_profile=unknown")[0] == 422
    assert api_get("/api/v1/health-regions?uf=ABCDE")[0] == 422
    assert api_get("/api/v1/health-regions?limit=101")[0] == 422
    assert api_get("/api/v1/health-regions?offset=-1")[0] == 422
    assert api_get("/api/v1/releases/NOT_A_RELEASE")[0] == 404
    assert api_get("/api/v1/health-regions?release_id=NOT_A_RELEASE")[0] == 404
    assert api_get("/api/v1/map/health-regions?release_id=NOT_A_RELEASE")[0] == 404
    assert api_get("/api/v1/states/AC?release_id=NOT_A_RELEASE")[0] == 404

    injected = urllib.parse.quote("12001' OR '1'='1", safe="")
    status, payload = api_get(f"/api/v1/health-regions?q={injected}&limit=10")
    assert status == 200
    assert payload["pagination"]["total"] == 0


def test_territorial_intelligence_radar_contract():
    status, radar = api_get("/api/v1/radar/health-regions")
    assert status == 200
    assert radar["release"]["intelligence_version"] == "MDB_TERRITORIAL_INTELLIGENCE_1.0"
    assert radar["filters"]["min_signal_families"] == 2
    assert radar["total_matching"] == 113
    assert radar["geometry"] is None
    assert {region["signals"]["matched_signal_families"] for region in radar["regions"]} <= {
        2,
        3,
        4,
        5,
    }

    status, geojson = api_get(
        "/api/v1/radar/health-regions?min_signal_families=0&include_geometry=true"
    )
    assert status == 200
    assert geojson["total_matching"] == 439
    assert len(geojson["regions"]) == 439
    assert len(geojson["geometry"]["features"]) == 439
    assert geojson["geometry"]["geometry_metadata"] == {
        "profile": "overview",
        "version": WEB_GEOMETRY_VERSION,
        "crs": "EPSG:4326",
    }

    status, ac = api_get("/api/v1/radar/health-regions?uf=AC&min_signal_families=0")
    assert status == 200
    assert {region["uf"] for region in ac["regions"]} == {"AC"}
    assert ac["total_matching"] == 3

    status, signal = api_get(
        "/api/v1/radar/health-regions?signal=SPATIAL_HH_MISMATCH&min_signal_families=0"
    )
    assert status == 200
    assert signal["total_matching"] == 60
    assert all(region["signals"]["spatial_hh_mismatch"] for region in signal["regions"])

    assert api_get("/api/v1/radar/health-regions?signal=UNKNOWN")[0] == 422
    assert api_get("/api/v1/radar/health-regions?min_signal_families=6")[0] == 422
    assert api_get("/api/v1/radar/health-regions?uf=XX")[0] == 404


def test_territorial_intelligence_explanation_and_peers_contract():
    status, explanation = api_get("/api/v1/health-regions/12001/explanation")
    assert status == 200
    assert explanation["health_region_code"] == "12001"
    assert len(explanation["decomposition"]) == 5
    decomposition_sum = sum(item["contribution"] for item in explanation["decomposition"])
    assert abs(decomposition_sum - explanation["mismatch_score"]) <= 1e-12
    assert abs(explanation["decomposition_sum"] - explanation["mismatch_score"]) <= 1e-12

    status, peers = api_get("/api/v1/health-regions/12001/peers")
    assert status == 200
    assert peers["release"]["peer_method_version"] == "MDB_PEER_METHOD_1.0"
    assert len(peers["peers"]) == 10
    assert "12001" not in {peer["health_region_code"] for peer in peers["peers"]}
    assert len(peers["benchmarks"]) == 8
    assert {benchmark["peer_n_observed"] for benchmark in peers["benchmarks"]} == {10}
    assert peers["method"]["outcome_variables_used_for_selection"] is False

    status, methods = api_get("/api/v1/intelligence/methods")
    assert status == 200
    assert methods["release"]["radar_ruleset_version"] == "MDB_RADAR_RULESET_1.0"


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

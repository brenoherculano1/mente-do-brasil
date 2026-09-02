from tests.api.test_api_contract import api_get


def test_public_release_and_openapi_contracts():
    status, body = api_get("/api/public/v1/releases")
    assert status == 200
    assert body["meta"] == {
        "api_version": "MDB_PUBLIC_API_V1",
        "open_data_release": "MDB_OPEN_DATA_2024_1",
        "analytical_release": "MDB_ANALYTICAL_2024_2",
    }
    assert body["data"][0]["public_release_status"] == "NOT_RELEASED"
    status, spec = api_get("/api/public/v1/openapi.json")
    assert status == 200
    assert spec["openapi"] == "3.1.0"
    assert "/health-regions" in spec["paths"]
    for path, item in spec["paths"].items():
        declared = {parameter["name"] for parameter in item["get"]["parameters"]}
        expected = {part[1:-1] for part in path.split("/") if part.startswith("{")}
        assert declared == expected


def test_public_health_region_pagination_and_detail():
    status, page = api_get("/api/public/v1/health-regions?uf=AC&limit=2")
    assert status == 200
    assert len(page["data"]) == 2
    assert page["meta"]["pagination"]["next_cursor"]
    assert {row["uf"] for row in page["data"]} == {"AC"}
    status, detail = api_get("/api/public/v1/health-regions/12001")
    assert status == 200
    assert detail["data"]["health_region_name"] == "Alto Acre"
    assert "suicide_deaths" not in detail["data"]


def test_public_temporal_change_financing_and_comparator_contracts():
    assert api_get("/api/public/v1/health-regions/12001/timeline")[0] == 200
    assert api_get("/api/public/v1/changes?from_year=2022&to_year=2024&uf=AC")[0] == 200
    assert api_get("/api/public/v1/financing?year=2024&uf=AC")[0] == 200
    assert api_get("/api/public/v1/health-regions/12001/financing")[0] == 200
    assert len(api_get("/api/public/v1/health-regions/12001/peers")[1]["data"]) == 10
    status, municipality = api_get("/api/public/v1/municipalities/1200013/health-region")
    assert status == 200
    assert municipality["data"]["health_region_code"] == "12002"


def test_public_flow_boundary_and_safe_errors():
    status, flows = api_get("/api/public/v1/health-regions/12001/flows?perspective=origin")
    assert status == 200
    assert all(row["admissions"] >= 5 for row in flows["data"])
    assert all("suppressed" not in row for row in flows["data"])
    assert api_get("/api/public/v1/health-regions?limit=501")[0] == 422
    assert api_get("/api/public/v1/health-regions?cursor=not-a-cursor")[0] == 400
    assert api_get("/api/public/v1/changes?from_year=2022&to_year=2022")[0] == 422
    assert api_get("/api/public/v1/health-regions/99999")[0] == 404

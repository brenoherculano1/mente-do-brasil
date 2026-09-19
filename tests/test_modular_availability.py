import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException

from api.dependencies import settings_dependency
from api.routers.availability import require_preview, router
from api.services.availability import availability_2025, unavailable_observations_2025


def test_metadata_is_unique_and_never_claims_a_release():
    rows = availability_2025()
    assert len({r.indicator_id for r in rows}) == len(rows)
    assert all(r.reference_year == 2025 and r.release_id is None for r in rows)
    assert all(not r.available_publicly and r.reason_unavailable for r in rows)


def test_null_is_not_zero_and_has_no_historical_fallback():
    assert all(r["value"] is None for r in unavailable_observations_2025())


def test_exported_metadata_matches_api():
    root = Path(__file__).resolve().parents[1]
    exported = json.loads((root / "metadata/annual_updates/2025/availability.json").read_text())
    assert exported["indicators"] == [r.model_dump() for r in availability_2025()]
    assert exported["observed_release_created"] is False


def test_historical_reproduction_did_not_change_science():
    root = Path(__file__).resolve().parents[1]
    result = json.loads(
        (root / "audit_results/modular_2025/reproduction_2024_historical_runtime.json").read_text()
    )
    assert result["byte_identical"] is True
    assert result["protected_changed"] == []
    assert all(result["column_exact_match"].values())


def test_capacity_does_not_depend_on_sim_or_spatial_reproduction():
    rows = {r.indicator_id: r for r in availability_2025()}
    assert rows["capacity_score"].dependencies == [
        "caps_rate",
        "beds_sus_rate",
        "psychiatrist_fte_rate",
    ]
    assert rows["radar_capacity_signals"].status == "UNDER_VALIDATION"
    for identifier in ["suicide_asmr", "need_score", "mismatch_score", "moran", "lisa", "radar"]:
        assert rows[identifier].status == "UNAVAILABLE"
    assert rows["suicide_asmr"].source_status == "PROVISIONAL_NOT_PUBLIC"


def test_api_unavailable_and_year_isolation(monkeypatch):
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[settings_dependency] = lambda: SimpleNamespace(production_mode=False)

    async def request(path, year):
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "root_path": "",
                "query_string": f"year={year}".encode(),
                "headers": [],
                "server": ("test", 80),
                "client": ("test", 1),
            },
            receive,
            send,
        )
        status = next(m["status"] for m in messages if m["type"] == "http.response.start")
        body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
        return status, json.loads(body)

    status, body = asyncio.run(request("/api/v1/observations/unavailable", 2025))
    assert status == 200
    assert all(r["value"] is None for r in body["indicators"])
    for year in [2024, 2026]:
        assert asyncio.run(request("/api/v1/observations/availability", year))[0] == 422


@pytest.mark.parametrize(
    "environment,production,allowed",
    [("production", False, False), ("preview", True, True), ("", True, False), ("", False, True)],
)
def test_production_guard(monkeypatch, environment, production, allowed):
    monkeypatch.setenv("VERCEL_ENV", environment)
    if allowed:
        require_preview(production)
    else:
        with pytest.raises(HTTPException):
            require_preview(production)

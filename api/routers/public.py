# ruff: noqa: E501
"""Private upstream for the versioned public API boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request
from fastapi import Path as ApiPath
from fastapi.responses import JSONResponse

from api.dependencies import DatabaseDep
from api.release_metadata import RELEASE_JSON
from api.services.public_api import (
    ANALYTICAL_RELEASE,
    API_VERSION,
    OPEN_DATA_RELEASE,
    decode_cursor,
    envelope,
    page,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = ROOT / "metadata/open_platform/public_field_registry_v1.yaml"
router = APIRouter(prefix="/api/public/v1", tags=["public open data"])


def problem(request: Request, status: int, title: str, detail: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://mentedobrasil.com.br/problems/{code.lower()}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
            "code": code,
        },
    )


def cursor_offset(cursor: str | None, request: Request) -> int | JSONResponse:
    try:
        return decode_cursor(cursor)
    except ValueError as exc:
        return problem(request, 400, "Invalid cursor", str(exc), "INVALID_CURSOR")


@router.get("/releases")
def releases() -> dict:
    return envelope([json.loads(RELEASE_JSON)])


@router.get("/releases/{release_id}")
def release(release_id: str, request: Request):
    if release_id != OPEN_DATA_RELEASE:
        return problem(request, 404, "Release not found", "Unknown public release.", "NOT_FOUND")
    return envelope(json.loads(RELEASE_JSON))


@router.get("/health-regions")
def health_regions(
    request: Request,
    db: DatabaseDep,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    offset = cursor_offset(cursor, request)
    if isinstance(offset, JSONResponse):
        return offset
    where = "WHERE release_id = %s"
    params: tuple = (ANALYTICAL_RELEASE,)
    if uf:
        where += " AND uf = %s"
        params += (uf.upper(),)
    return page(
        db,
        "SELECT release_id, method_version, geography_version, health_region_code, "
        "health_region_name, uf, municipality_count, population, area_km2, "
        "population_density, suicide_asmr, suicide_percentile, psychiatric_admission_rate, "
        "psychiatric_admission_percentile, caps_count, caps_rate, caps_percentile, "
        "mental_health_beds_sus_count, mental_health_beds_sus_rate, beds_percentile, "
        "psychiatrist_fte, psychiatrist_fte_rate, psychiatrist_fte_percentile, need_score, "
        "capacity_score, mismatch_score, lisa_local_i, lisa_p, lisa_q, lisa_significant, "
        f"lisa_cluster, data_quality_flags FROM serving.v_public_health_regions_current {where} "
        "ORDER BY uf, health_region_code",
        params,
        limit,
        offset,
    )


@router.get("/health-regions/{code}")
def health_region(
    code: Annotated[str, ApiPath(pattern=r"^\d{5}$")], request: Request, db: DatabaseDep
):
    row = db.row(
        "SELECT release_id, method_version, geography_version, health_region_code, "
        "health_region_name, uf, municipality_count, population, area_km2, "
        "population_density, suicide_asmr, suicide_percentile, psychiatric_admission_rate, "
        "psychiatric_admission_percentile, caps_count, caps_rate, caps_percentile, "
        "mental_health_beds_sus_count, mental_health_beds_sus_rate, beds_percentile, "
        "psychiatrist_fte, psychiatrist_fte_rate, psychiatrist_fte_percentile, need_score, "
        "capacity_score, mismatch_score, lisa_local_i, lisa_p, lisa_q, lisa_significant, "
        "lisa_cluster, data_quality_flags FROM serving.v_public_health_regions_current "
        "WHERE release_id = %s AND health_region_code = %s",
        (ANALYTICAL_RELEASE, code),
    )
    return (
        envelope(row)
        if row
        else problem(
            request, 404, "Health region not found", "Unknown health-region code.", "NOT_FOUND"
        )
    )


@router.get("/health-regions/{code}/timeline")
def timeline(code: Annotated[str, ApiPath(pattern=r"^\d{5}$")], request: Request, db: DatabaseDep):
    rows = db.rows(
        "SELECT health_region_code, health_region_name, uf, geography_version, population, "
        "person_years, suicide_asmr, psychiatric_admissions, psychiatric_admission_rate, "
        "caps_count, mental_health_beds_sus_count, psychiatrist_fte, caps_rate, "
        "mental_health_beds_sus_rate, psychiatrist_fte_rate, suicide_percentile, "
        "psychiatric_admission_percentile, caps_percentile, beds_percentile, "
        "psychiatrist_fte_percentile, need_score, capacity_score, mismatch_score, year, "
        "need_window_start, need_window_end, capacity_competence, temporal_version, release_id, "
        "quality_flags FROM serving.v_public_temporal WHERE health_region_code = %s ORDER BY year",
        (code,),
    )
    return (
        envelope(rows)
        if rows
        else problem(request, 404, "Timeline not found", "Unknown health-region code.", "NOT_FOUND")
    )


@router.get("/changes")
def changes(
    request: Request,
    db: DatabaseDep,
    from_year: Annotated[int | None, Query(ge=2022, le=2023)] = None,
    to_year: Annotated[int | None, Query(ge=2023, le=2024)] = None,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    family: Literal["need", "capacity", "mismatch", "need_component", "capacity_component"]
    | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    offset = cursor_offset(cursor, request)
    if isinstance(offset, JSONResponse):
        return offset
    if (from_year, to_year) not in {(None, None), (2022, 2023), (2023, 2024), (2022, 2024)}:
        return problem(
            request,
            400,
            "Invalid year pair",
            "Supported pairs are 2022-2023, 2023-2024, and 2022-2024.",
            "INVALID_YEAR_PAIR",
        )
    filters, params = [], []
    if from_year is not None:
        filters += ["from_year = %s", "to_year = %s"]
        params += [from_year, to_year]
    if uf:
        filters.append("uf = %s")
        params.append(uf.upper())
    family_column = {
        "need": '"NEED_POSITION_UP"',
        "capacity": '"CAPACITY_POSITION_DOWN"',
        "mismatch": '"MISMATCH_POSITION_UP"',
        "need_component": '"NEED_COMPONENT_POSITION_UP"',
        "capacity_component": '"CAPACITY_COMPONENT_POSITION_DOWN"',
    }
    if family:
        filters.append(f"{family_column[family]} = true")
    where = " WHERE " + " AND ".join(filters) if filters else ""
    columns = 'health_region_code, delta_need_score, delta_capacity_score, delta_mismatch_score, delta_suicide_percentile, delta_psychiatric_admission_percentile, delta_caps_percentile, delta_beds_percentile, delta_psychiatrist_fte_percentile, "NEED_POSITION_UP", "CAPACITY_POSITION_DOWN", "MISMATCH_POSITION_UP", "NEED_COMPONENT_POSITION_UP", "CAPACITY_COMPONENT_POSITION_DOWN", matched_change_families, from_year, to_year, change_version'
    return page(
        db,
        f"SELECT {columns} FROM serving.v_public_changes{where} ORDER BY from_year, to_year, health_region_code",
        tuple(params),
        limit,
        offset,
    )


@router.get("/financing")
def financing(
    request: Request,
    db: DatabaseDep,
    year: Annotated[int | None, Query(ge=2022, le=2024)] = None,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    coverage: Literal["complete", "partial"] | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    offset = cursor_offset(cursor, request)
    if isinstance(offset, JSONResponse):
        return offset
    filters, params = [], []
    if year:
        filters.append("year = %s")
        params.append(year)
    if uf:
        filters.append("uf = %s")
        params.append(uf.upper())
    if coverage:
        filters.append("headline_available = %s")
        params.append(coverage == "complete")
    where = " WHERE " + " AND ".join(filters) if filters else ""
    columns = "financing_version, siops_snapshot_id, year, health_region_code, municipalities_expected, municipalities_observed, population_expected, population_covered, coverage_share, coverage_population_share, total_health_expenditure_brl, health_expenditure_per_capita_brl, headline_available, quality_flags, source_period, source_indicator"
    return page(
        db,
        f"SELECT {columns} FROM serving.v_public_financing{where} ORDER BY year, health_region_code",
        tuple(params),
        limit,
        offset,
    )


@router.get("/health-regions/{code}/financing")
def region_financing(
    code: Annotated[str, ApiPath(pattern=r"^\d{5}$")], request: Request, db: DatabaseDep
):
    rows = db.rows(
        "SELECT financing_version, siops_snapshot_id, year, health_region_code, municipalities_expected, municipalities_observed, population_expected, population_covered, coverage_share, coverage_population_share, total_health_expenditure_brl, health_expenditure_per_capita_brl, headline_available, quality_flags, source_period, source_indicator FROM serving.v_public_financing WHERE health_region_code = %s ORDER BY year",
        (code,),
    )
    return (
        envelope(rows)
        if rows
        else problem(
            request, 404, "Financing context not found", "Unknown health-region code.", "NOT_FOUND"
        )
    )


@router.get("/health-regions/{code}/flows")
def flows(
    code: Annotated[str, ApiPath(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    perspective: Literal["origin", "destination"] = "origin",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    field = "origin_region" if perspective == "origin" else "destination_region"
    rows = db.rows(
        f"SELECT flow_version, contribution_id, origin_region, destination_region, admissions FROM serving.v_public_flow_edges WHERE {field} = %s ORDER BY admissions DESC, contribution_id LIMIT %s",
        (code, limit),
    )
    return envelope(rows, perspective=perspective)


@router.get("/health-regions/{code}/peers")
def peers(code: Annotated[str, ApiPath(pattern=r"^\d{5}$")], db: DatabaseDep):
    rows = db.rows(
        "SELECT release_id, peer_method_version, health_region_code, peer_health_region_code, peer_rank, structural_distance FROM serving.v_public_peers WHERE release_id = %s AND health_region_code = %s ORDER BY peer_rank",
        (ANALYTICAL_RELEASE, code),
    )
    return envelope(rows)


@router.get("/municipalities/{ibge_code}/health-region")
def municipality(
    ibge_code: Annotated[str, ApiPath(pattern=r"^\d{7}$")], request: Request, db: DatabaseDep
):
    row = db.row(
        "SELECT municipality_code_ibge, municipality_name, uf, health_region_code, health_region_name, geography_version FROM serving.v_public_municipality_crosswalk WHERE municipality_code_ibge = %s",
        (ibge_code,),
    )
    return (
        envelope(row)
        if row
        else problem(
            request, 404, "Municipality not found", "Unknown IBGE municipality code.", "NOT_FOUND"
        )
    )


@router.get("/metadata/indicators")
def indicators(db: DatabaseDep):
    rows = db.rows(
        "SELECT indicator_id, indicator_name_pt, indicator_name_en, domain, description, unit, interpretation, what_it_does_not_measure, source_system, observation_start, observation_end, method_version FROM meta.indicators ORDER BY domain, indicator_id, method_version"
    )
    return envelope(rows)


@router.get("/metadata/methodology")
def methodology():
    return envelope(
        {
            "method_version": "MDB_METHOD_1.1",
            "geography_version": "BR_HEALTH_REGIONS_END2024_V1",
            "unit_of_analysis": "Brazilian Health Region",
            "reference_year": 2024,
            "responsible_use": [
                "territorial intelligence",
                "not prevalence",
                "not individual risk",
                "not direct access or quality measurement",
                "not an automatic policy recommendation",
            ],
        }
    )


@router.get("/openapi.json")
def public_openapi():
    route_parameters = {
        "/releases": [],
        "/releases/{release_id}": ["release_id"],
        "/health-regions": [],
        "/health-regions/{code}": ["code"],
        "/health-regions/{code}/timeline": ["code"],
        "/changes": [],
        "/financing": [],
        "/health-regions/{code}/financing": ["code"],
        "/health-regions/{code}/flows": ["code"],
        "/health-regions/{code}/peers": ["code"],
        "/municipalities/{ibge_code}/health-region": ["ibge_code"],
        "/metadata/indicators": [],
        "/metadata/methodology": [],
    }
    paths = {}
    for path, parameter_names in route_parameters.items():
        parameters = [
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for name in parameter_names
        ]
        paths[path] = {
            "get": {
                "parameters": parameters,
                "responses": {
                    "200": {
                        "description": "Successful public read",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "4XX": {
                        "description": "Problem Details error",
                        "content": {"application/problem+json": {"schema": {"type": "object"}}},
                    },
                },
            }
        }
    return {
        "openapi": "3.1.0",
        "info": {"title": "Mente do Brasil Public API", "version": API_VERSION},
        "servers": [{"url": "/api/public/v1"}],
        "paths": paths,
    }

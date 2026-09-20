from typing import Annotated, Literal

from fastapi import APIRouter, Path, Query

from api.dependencies import DatabaseDep
from api.services.advanced import flows, historical_regions, list_changes, timeline

router = APIRouter(prefix="/api/v1", tags=["advanced territorial"])
Code = Annotated[str, Path(pattern=r"^\d{5}$")]
Year = Annotated[int, Query(ge=2022, le=2024)]


@router.get("/historical/health-regions")
def historical_anchor(
    db: DatabaseDep,
    year: Year = 2024,
    metric: Literal[
        "mismatch_score",
        "need_score",
        "capacity_score",
        "suicide_asmr",
        "psychiatric_admission_rate",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
    ] = "mismatch_score",
    include_geometry: bool = False,
):
    return historical_regions(db, year, metric, include_geometry)


@router.get("/health-regions/{code}/timeline")
def region_timeline(code: Code, db: DatabaseDep):
    return timeline(db, code)


@router.get("/changes/health-regions")
def change_regions(
    db: DatabaseDep,
    from_year: Year = 2022,
    to_year: Year = 2024,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    signal: Annotated[str | None, Query(max_length=60)] = None,
    min_change_families: Annotated[int, Query(ge=0, le=5)] = 1,
    q: Annotated[str | None, Query(max_length=100)] = None,
    sort: Literal["families", "mismatch", "name"] = "families",
    include_geometry: bool = False,
):
    return list_changes(
        db, from_year, to_year, uf, signal, min_change_families, q, sort, include_geometry
    )


@router.get("/health-regions/{code}/flows")
def region_flows(
    code: Code,
    db: DatabaseDep,
    perspective: Literal["origin", "destination"] = "origin",
    limit: Annotated[int, Query(ge=1, le=8)] = 8,
):
    return flows(db, code, perspective, limit)

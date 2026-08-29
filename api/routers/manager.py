from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi.responses import Response

from api.dependencies import DatabaseDep, SettingsDep
from api.schemas.manager import ManagerBrief, ManagerCompareResponse
from api.services.manager import (
    compare_manager_regions,
    get_manager_brief,
    manager_methods_payload,
    report_response,
)

router = APIRouter(prefix="/api/v1", tags=["manager workbench"])


@router.get("/manager/health-regions/{health_region_code}", response_model=ManagerBrief)
def manager_health_region(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> ManagerBrief:
    return get_manager_brief(db, release_id or settings.default_release_id, health_region_code)


@router.get("/manager/compare", response_model=ManagerCompareResponse)
def manager_compare(
    db: DatabaseDep,
    settings: SettingsDep,
    codes: Annotated[str, Query(min_length=11, max_length=23)],
    release_id: str | None = None,
) -> ManagerCompareResponse:
    return compare_manager_regions(
        db,
        release_id or settings.default_release_id,
        codes.split(","),
    )


@router.get("/manager/methods")
def manager_methods(
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> dict:
    get_manager_brief(db, release_id or settings.default_release_id, "12001")
    return manager_methods_payload()


@router.get("/health-regions/{health_region_code}/report.pdf", response_class=Response)
def health_region_report_pdf(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> Response:
    brief = get_manager_brief(db, release_id or settings.default_release_id, health_region_code)
    return report_response(brief)

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query

from api.dependencies import DatabaseDep
from api.schemas.financing import FinancingResponse
from api.services.financing import get_financing

router = APIRouter(prefix="/api/v1", tags=["financing"])


@router.get("/financing/health-regions", response_model=FinancingResponse)
def financing_health_regions(
    db: DatabaseDep,
    year: Annotated[int | None, Query(ge=2022, le=2024)] = None,
) -> FinancingResponse:
    return get_financing(db, year=year)


@router.get("/health-regions/{health_region_code}/financing", response_model=FinancingResponse)
def health_region_financing(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    year: Annotated[int | None, Query(ge=2022, le=2024)] = None,
) -> FinancingResponse:
    return get_financing(db, code=health_region_code, year=year)

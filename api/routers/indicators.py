from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import DatabaseDep
from api.schemas.indicators import IndicatorPublic
from api.services.health_regions import get_indicator, list_indicators

router = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router.get("", response_model=list[IndicatorPublic])
def indicators(db: DatabaseDep) -> list[IndicatorPublic]:
    return list_indicators(db)


@router.get("/{indicator_id}", response_model=IndicatorPublic)
def indicator_detail(indicator_id: str, db: DatabaseDep) -> IndicatorPublic:
    return get_indicator(db, indicator_id)

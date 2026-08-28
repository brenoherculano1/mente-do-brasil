from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Path, Query

from api.dependencies import DatabaseDep, SettingsDep
from api.schemas.common import Metric
from api.schemas.intelligence import (
    ExplanationResponse,
    IntelligenceMethodsResponse,
    PeersResponse,
    RadarResponse,
    RadarSignal,
)
from api.services.intelligence import get_explanation, get_peers, list_radar_regions, methods

router = APIRouter(prefix="/api/v1", tags=["territorial intelligence"])


@router.get("/radar/health-regions", response_model=RadarResponse)
def radar_health_regions(
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    signal: RadarSignal | None = None,
    min_signal_families: Annotated[int, Query(ge=0, le=5)] = 2,
    q: Annotated[str | None, Query(max_length=100)] = None,
    sort: Literal["signals", "mismatch", "name"] = "signals",
    include_geometry: bool = False,
) -> RadarResponse:
    return list_radar_regions(
        db=db,
        release_id=release_id or settings.default_release_id,
        uf=uf.upper() if uf else None,
        signal=signal,
        min_signal_families=min_signal_families,
        q=q,
        sort=sort,
        include_geometry=include_geometry,
    )


@router.get("/health-regions/{health_region_code}/explanation", response_model=ExplanationResponse)
def health_region_explanation(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> ExplanationResponse:
    return get_explanation(db, release_id or settings.default_release_id, health_region_code)


@router.get("/health-regions/{health_region_code}/peers", response_model=PeersResponse)
def health_region_peers(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
    metric: Metric = Metric.mismatch_score,
) -> PeersResponse:
    return get_peers(db, release_id or settings.default_release_id, health_region_code, metric)


@router.get("/intelligence/methods", response_model=IntelligenceMethodsResponse)
def intelligence_methods(
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> IntelligenceMethodsResponse:
    return methods(db, release_id or settings.default_release_id)

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query

from api.dependencies import DatabaseDep, SettingsDep
from api.errors import api_error
from api.schemas.common import GeometryProfile, Metric, PaginatedResponse, Pagination
from api.schemas.health_regions import (
    GeoJsonFeatureCollection,
    HealthRegionLookup,
    HealthRegionMapItem,
    HealthRegionMunicipalities,
    HealthRegionProfile,
    MunicipalityHealthRegion,
    StateProfile,
    UfOption,
)
from api.services.health_regions import (
    get_health_region_profile,
    get_state_profile,
    health_region_municipalities,
    list_health_regions,
    list_map_data,
    municipality_health_region,
    search_municipalities,
    uf_options,
)

router = APIRouter(prefix="/api/v1", tags=["health regions"])


@router.get("/health-regions", response_model=PaginatedResponse[HealthRegionLookup])
def health_regions(
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[HealthRegionLookup]:
    active_release = release_id or settings.default_release_id
    items, total = list_health_regions(
        db, active_release, uf.upper() if uf else None, q, limit, offset
    )
    return PaginatedResponse(
        items=items,
        pagination=Pagination(limit=limit, offset=offset, count=len(items), total=total),
    )


@router.get(
    "/health-regions/{health_region_code}/municipalities",
    response_model=HealthRegionMunicipalities,
)
def region_municipalities(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> HealthRegionMunicipalities:
    return health_region_municipalities(
        db, health_region_code, release_id or settings.default_release_id
    )


@router.get("/health-regions/{health_region_code}", response_model=HealthRegionProfile)
def health_region_profile(
    health_region_code: Annotated[str, Path(pattern=r"^\d{5}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> HealthRegionProfile:
    return get_health_region_profile(
        db, release_id or settings.default_release_id, health_region_code
    )


@router.get("/states/{uf}", response_model=StateProfile)
def state_profile(
    uf: Annotated[str, Path(pattern=r"^[A-Za-z]{2}$")],
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> StateProfile:
    return get_state_profile(db, release_id or settings.default_release_id, uf.upper())


@router.get(
    "/map/health-regions",
    response_model=list[HealthRegionMapItem] | GeoJsonFeatureCollection,
)
def health_region_map(
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
    metric: Metric = Metric.mismatch_score,
    uf: Annotated[str | None, Query(pattern=r"^[A-Za-z]{2}$")] = None,
    include_geometry: bool = False,
    geometry_profile: Annotated[
        GeometryProfile | None,
        Query(
            description="Geometry profile. full is restricted on the operational API by default."
        ),
    ] = None,
) -> list[HealthRegionMapItem] | GeoJsonFeatureCollection:
    profile = geometry_profile or GeometryProfile.overview
    if include_geometry and profile == GeometryProfile.full and not settings.allow_full_geometry:
        raise api_error(
            403,
            "FULL_GEOMETRY_RESTRICTED",
            "Full geometry is not available on the operational API.",
        )
    return list_map_data(
        db,
        release_id or settings.default_release_id,
        metric,
        uf.upper() if uf else None,
        include_geometry,
        profile,
    )


@router.get(
    "/municipalities/{municipality_code_ibge}/health-region",
    response_model=MunicipalityHealthRegion,
)
def municipality_lookup(
    municipality_code_ibge: Annotated[str, Path(pattern=r"^\d{7}$")],
    db: DatabaseDep,
    settings: SettingsDep,
) -> MunicipalityHealthRegion:
    return municipality_health_region(db, municipality_code_ibge, settings.default_release_id)


@router.get("/municipalities", response_model=list[MunicipalityHealthRegion])
def municipality_search(
    db: DatabaseDep,
    settings: SettingsDep,
    q: Annotated[str, Query(min_length=2, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> list[MunicipalityHealthRegion]:
    return search_municipalities(db, q, settings.default_release_id, limit)


@router.get("/ufs", response_model=list[UfOption])
def ufs(
    db: DatabaseDep,
    settings: SettingsDep,
    release_id: str | None = None,
) -> list[UfOption]:
    return uf_options(db, release_id or settings.default_release_id)

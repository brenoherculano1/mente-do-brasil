from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import DatabaseDep
from api.schemas.releases import ReleasePublic
from api.services.health_regions import get_release, list_releases

router = APIRouter(prefix="/api/v1/releases", tags=["releases"])


@router.get("", response_model=list[ReleasePublic])
def releases(db: DatabaseDep) -> list[ReleasePublic]:
    return list_releases(db)


@router.get("/{release_id}", response_model=ReleasePublic)
def release_detail(release_id: str, db: DatabaseDep) -> ReleasePublic:
    return get_release(db, release_id)

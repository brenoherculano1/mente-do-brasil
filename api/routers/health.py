from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import DatabaseDep, SettingsDep
from api.services.health_regions import ready_check

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(db: DatabaseDep, settings: SettingsDep) -> dict[str, str]:
    return ready_check(db, settings.default_release_id)

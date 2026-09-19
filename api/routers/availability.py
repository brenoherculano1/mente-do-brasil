"""Preview-only 2025 contract; existing historical endpoints stay unchanged."""

import os
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import SettingsDep
from api.services.availability import availability_2025, unavailable_observations_2025

router = APIRouter(prefix="/api/v1/observations", tags=["availability"])


def require_preview(production_mode: bool):
    environment = os.environ.get("VERCEL_ENV")
    if environment == "production" or (production_mode and environment != "preview"):
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/availability")
def availability(settings: SettingsDep, year: Annotated[int, Query(ge=2025, le=2025)] = 2025):
    require_preview(settings.production_mode)
    return {
        "reference_year": year,
        "public_release_status": "NOT_RELEASED",
        "geography_validated": False,
        "indicators": availability_2025(),
    }


@router.get("/unavailable")
def unavailable(settings: SettingsDep, year: Annotated[int, Query(ge=2025, le=2025)] = 2025):
    require_preview(settings.production_mode)
    return {
        "reference_year": year,
        "geography_validated": False,
        "territory_scope": "Regional values blocked pending dated territorial linkage",
        "indicators": unavailable_observations_2025(),
    }

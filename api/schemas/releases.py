from __future__ import annotations

from pydantic import BaseModel


class ReleasePublic(BaseModel):
    release_id: str
    canonical_version: str
    method_version: str
    geography_version: str
    release_status: str
    quality_status: str
    release_gate: str
    public_release_status: str

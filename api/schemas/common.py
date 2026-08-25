from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class Metric(StrEnum):
    need_score = "need_score"
    capacity_score = "capacity_score"
    mismatch_score = "mismatch_score"
    suicide_asmr = "suicide_asmr"
    psychiatric_admission_rate = "psychiatric_admission_rate"
    caps_rate = "caps_rate"
    mental_health_beds_sus_rate = "mental_health_beds_sus_rate"
    psychiatrist_fte_rate = "psychiatrist_fte_rate"


class GeometryProfile(StrEnum):
    overview = "overview"
    detail = "detail"
    full = "full"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Pagination(BaseModel):
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    count: int = Field(ge=0)
    total: int = Field(ge=0)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: Pagination

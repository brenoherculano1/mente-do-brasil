from __future__ import annotations

from pydantic import BaseModel


class FinancingRecord(BaseModel):
    financing_version: str
    siops_snapshot_id: str
    year: int
    health_region_code: str
    municipalities_expected: int
    municipalities_observed: int
    population_expected: int
    population_covered: int | None
    coverage_share: float
    coverage_population_share: float | None
    total_health_expenditure_brl: float | None
    health_expenditure_per_capita_brl: float | None
    headline_available: bool
    quality_flags: list[str]
    source_period: str
    source_indicator: str
    scope: str = "GENERAL_HEALTH_FINANCING_CONTEXT"


class FinancingResponse(BaseModel):
    records: list[FinancingRecord]
    disclaimer: str

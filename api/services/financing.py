from __future__ import annotations

from api.db import Database
from api.errors import api_error
from api.schemas.financing import FinancingRecord, FinancingResponse

DISCLAIMER = (
    "Esta camada descreve o contexto geral de financiamento da saúde e não mede "
    "gasto específico em saúde mental."
)


def get_financing(
    db: Database, code: str | None = None, year: int | None = None
) -> FinancingResponse:
    filters = ["financing_version = 'MDB_FINANCING_CONTEXT_1.0'"]
    params: list[object] = []
    if code:
        filters.append("health_region_code = %s")
        params.append(code)
    if year:
        filters.append("year = %s")
        params.append(year)
    rows = db.rows(
        "SELECT financing_version, siops_snapshot_id, year, health_region_code, "
        "municipalities_expected, municipalities_observed, population_expected, "
        "population_covered, coverage_share, coverage_population_share, "
        "total_health_expenditure_brl::float8 AS total_health_expenditure_brl, "
        "health_expenditure_per_capita_brl::float8 AS health_expenditure_per_capita_brl, "
        "headline_available, quality_flags, source_period, source_indicator "
        f"FROM analytics.health_region_financing WHERE {' AND '.join(filters)} "
        "ORDER BY year, health_region_code",
        tuple(params),
    )
    if not rows:
        raise api_error(404, "FINANCING_NOT_FOUND", "Financing context not found.")
    return FinancingResponse(
        records=[FinancingRecord(**row) for row in rows], disclaimer=DISCLAIMER
    )

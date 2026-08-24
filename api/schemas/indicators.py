from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class IndicatorPublic(BaseModel):
    indicator_id: str
    indicator_name_pt: str
    indicator_name_en: str
    domain: str
    description: str
    unit: str
    interpretation: str
    what_it_does_not_measure: list[str]
    source_system: str
    observation_start: date | None
    observation_end: date | None
    method_version: str

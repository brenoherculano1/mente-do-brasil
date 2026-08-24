from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from .common import Metric
from .releases import ReleasePublic


class HealthRegionLookup(BaseModel):
    health_region_code: str
    health_region_name: str
    uf: str
    geography_version: str
    release_id: str


class TerritoryProfile(BaseModel):
    health_region_code: str
    health_region_name: str
    uf: str
    uf_code: str
    municipality_count: int
    population: int
    area_km2: float
    population_density: float


class SuicideNeed(BaseModel):
    deaths: int
    asmr: float
    percentile: float


class PsychiatricAdmissionsNeed(BaseModel):
    count: int
    rate: float
    percentile: float


class NeedProfile(BaseModel):
    suicide: SuicideNeed
    psychiatric_admissions: PsychiatricAdmissionsNeed
    score: float


class CapsCapacity(BaseModel):
    count: int
    rate: float
    percentile: float


class BedsCapacity(BaseModel):
    count: int
    rate: float
    percentile: float


class PsychiatristFteCapacity(BaseModel):
    fte: float
    rate: float
    percentile: float


class CapacityProfile(BaseModel):
    caps: CapsCapacity
    mental_health_beds_sus: BedsCapacity
    psychiatrist_fte: PsychiatristFteCapacity
    score: float


class MismatchProfile(BaseModel):
    score: float


class SpatialProfile(BaseModel):
    lisa_local_i: float | None
    lisa_p: float | None
    lisa_q: float | None
    lisa_significant: bool
    lisa_cluster: str | None


class HealthRegionProfile(BaseModel):
    release: ReleasePublic
    territory: TerritoryProfile
    need: NeedProfile
    capacity: CapacityProfile
    mismatch: MismatchProfile
    spatial: SpatialProfile
    data_quality_flags: list[str]


class HealthRegionMapItem(BaseModel):
    health_region_code: str
    health_region_name: str
    uf: str
    population: int
    metric: Metric
    value: float
    data_quality_flags: list[str]
    lisa_significant: bool
    lisa_cluster: str | None


class GeoJsonFeature(BaseModel):
    type: Literal["Feature"]
    id: str
    geometry: dict[str, Any]
    properties: HealthRegionMapItem


class GeoJsonFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[GeoJsonFeature]
    crs: dict[str, Any]


class MunicipalityHealthRegion(BaseModel):
    municipality_code_ibge: str
    municipality_name: str
    uf: str
    health_region_code: str
    health_region_name: str
    geography_version: str


class UfOption(BaseModel):
    uf: str
    health_region_count: int

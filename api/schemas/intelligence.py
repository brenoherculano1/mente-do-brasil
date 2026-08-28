from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .common import Metric
from .health_regions import GeometryMetadata

INTELLIGENCE_VERSION = "MDB_TERRITORIAL_INTELLIGENCE_1.0"
RADAR_RULESET_VERSION = "MDB_RADAR_RULESET_1.0"
DECOMPOSITION_VERSION = "MDB_MISMATCH_DECOMPOSITION_1.0"
PEER_METHOD_VERSION = "MDB_PEER_METHOD_1.0"

RadarSignal = Literal[
    "NEED_HIGH",
    "CAPACITY_LOW",
    "MISMATCH_MARKED_POSITIVE",
    "CAPACITY_COMPONENT_LOW",
    "SPATIAL_HH_MISMATCH",
]

PeerPosition = Literal["BELOW_PEER_IQR", "WITHIN_PEER_IQR", "ABOVE_PEER_IQR"]


class SignalDefinitions(BaseModel):
    NEED_HIGH: str
    CAPACITY_LOW: str
    MISMATCH_MARKED_POSITIVE: str
    CAPACITY_COMPONENT_LOW: str
    SPATIAL_HH_MISMATCH: str


class IntelligenceRelease(BaseModel):
    release_id: str
    intelligence_version: str
    radar_ruleset_version: str
    decomposition_version: str
    peer_method_version: str


class RadarSignals(BaseModel):
    need_high: bool
    capacity_low: bool
    mismatch_marked_positive: bool
    capacity_component_low: bool
    spatial_hh_mismatch: bool
    caps_low: bool
    beds_low: bool
    psychiatrist_fte_low: bool
    zero_registered_beds: bool
    matched_signal_families: int = Field(ge=0, le=5)


class RadarRegion(BaseModel):
    health_region_code: str
    health_region_name: str
    uf: str
    population: int
    municipality_count: int
    need_score: float
    capacity_score: float
    mismatch_score: float
    matched_signal_families: int = Field(ge=0, le=5)
    signals: RadarSignals
    data_quality_flags: list[str]


class RadarFeature(BaseModel):
    type: Literal["Feature"]
    id: str
    geometry: dict[str, Any]
    properties: RadarRegion


class RadarFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[RadarFeature]
    crs: dict[str, Any]
    geometry_metadata: GeometryMetadata


class RadarResponse(BaseModel):
    release: IntelligenceRelease
    filters: dict[str, Any]
    signal_definitions: SignalDefinitions
    total_matching: int
    regions: list[RadarRegion]
    geometry: RadarFeatureCollection | None = None


class DecompositionItem(BaseModel):
    component: str
    label: str
    source_percentile: float
    contribution: float
    caution: str | None = None


class ExplanationResponse(BaseModel):
    release: IntelligenceRelease
    health_region_code: str
    health_region_name: str
    uf: str
    matched_signal_families: int
    triggers: list[str]
    subsignals: list[str]
    quality_cautions: list[str]
    decomposition: list[DecompositionItem]
    decomposition_sum: float
    mismatch_score: float
    interpretation: str


class PeerRegion(BaseModel):
    health_region_code: str
    health_region_name: str
    uf: str
    population: int
    population_density: float
    municipality_count: int
    metric_value: float | None = None


class PeerBenchmark(BaseModel):
    metric_id: Metric
    target_value: float
    peer_n_observed: int
    peer_median: float | None
    peer_q1: float | None
    peer_q3: float | None
    peer_min: float | None
    peer_max: float | None
    relative_to_peer_iqr: PeerPosition | None
    insufficient_reason: str | None


class PeersResponse(BaseModel):
    release: IntelligenceRelease
    health_region_code: str
    health_region_name: str
    uf: str
    method: dict[str, Any]
    selected_metric: Metric
    peers: list[PeerRegion]
    benchmarks: list[PeerBenchmark]


class IntelligenceMethodsResponse(BaseModel):
    release: IntelligenceRelease
    radar: dict[str, Any]
    decomposition: dict[str, Any]
    peers: dict[str, Any]

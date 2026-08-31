from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .common import Metric
from .intelligence import DecompositionItem, PeerBenchmark, RadarSignals
from .releases import ReleasePublic

MANAGER_MODE_VERSION = "MDB_MANAGER_MODE_1.0"
TERRITORIAL_REPORT_VERSION = "MDB_TERRITORIAL_REPORT_1.0"
INVESTIGATION_GUIDE_VERSION = "MDB_INVESTIGATION_GUIDE_1.0"
MANAGER_BRIEF_VERSION = "MDB_MANAGER_BRIEF_1.0"
REPORT_GENERATOR_VERSION = "MDB_REPORTLAB_GENERATOR_1.1"


class ManagerVersions(BaseModel):
    intelligence_version: str
    radar_ruleset_version: str
    decomposition_version: str
    peer_method_version: str
    manager_mode_version: str = MANAGER_MODE_VERSION
    report_version: str = TERRITORIAL_REPORT_VERSION
    investigation_guide_version: str = INVESTIGATION_GUIDE_VERSION
    manager_brief_version: str = MANAGER_BRIEF_VERSION


class ManagerRegionIdentity(BaseModel):
    health_region_code: str
    health_region_name: str
    uf: str
    population: int
    municipality_count: int


class ManagerMetricValue(BaseModel):
    metric_id: Metric
    label: str
    value: float | int | None
    percentile: float | None = None
    unit: str


class ManagerSpatialContext(BaseModel):
    lisa_significant: bool
    lisa_cluster: str | None
    lisa_local_i: float | None
    lisa_p: float | None
    description: str


class InvestigationQuestion(BaseModel):
    rule_id: str
    version: str = INVESTIGATION_GUIDE_VERSION
    category: Literal[
        "Base", "Radar", "Capacity", "Spatial", "Quality", "Change", "Financing", "Flow"
    ]
    question: str
    rationale: str
    priority: int
    claim_limit: str


class ManagerPeerSummary(BaseModel):
    method_version: str
    peer_count: int
    default_metric: Metric
    selected_benchmarks: list[PeerBenchmark]


class ManagerBrief(BaseModel):
    release: ReleasePublic
    versions: ManagerVersions
    region: ManagerRegionIdentity
    need_score: float
    capacity_score: float
    mismatch_score: float
    radar_signals: RadarSignals
    matched_signal_families: int = Field(ge=0, le=5)
    radar_triggers: list[str]
    radar_subsignals: list[str]
    deterministic_summary: str
    decomposition: list[DecompositionItem]
    peer_summary: ManagerPeerSummary
    spatial_context: ManagerSpatialContext
    quality_cautions: list[str]
    indicators: list[ManagerMetricValue]
    investigation_questions: list[InvestigationQuestion]
    method_references: list[str]
    report_content_sha256: str
    temporal_summary: dict | None = None
    change_summary: dict | None = None
    financing_context: dict | None = None
    hospital_flow_summary: dict | None = None


class CompareRegion(BaseModel):
    identity: ManagerRegionIdentity
    need_score: float
    capacity_score: float
    mismatch_score: float
    indicators: list[ManagerMetricValue]
    radar_signals: RadarSignals
    matched_signal_families: int = Field(ge=0, le=5)
    quality_cautions: list[str]
    lisa_context: ManagerSpatialContext


class ManagerCompareResponse(BaseModel):
    release: ReleasePublic
    versions: ManagerVersions
    requested_codes: list[str]
    metric_options: list[Metric]
    regions: list[CompareRegion]
    ranking_introduced: bool = False

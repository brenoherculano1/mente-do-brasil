"""Read-only queries for the Territorial Intelligence product layer."""

from __future__ import annotations

import json
from typing import Any

from api.db import Database
from api.errors import api_error
from api.schemas.common import GeometryProfile, Metric
from api.schemas.health_regions import GeometryMetadata
from api.schemas.intelligence import (
    DECOMPOSITION_VERSION,
    INTELLIGENCE_VERSION,
    PEER_METHOD_VERSION,
    RADAR_RULESET_VERSION,
    DecompositionItem,
    ExplanationResponse,
    IntelligenceMethodsResponse,
    IntelligenceRelease,
    PeerBenchmark,
    PeerRegion,
    PeersResponse,
    RadarFeature,
    RadarFeatureCollection,
    RadarRegion,
    RadarResponse,
    RadarSignal,
    RadarSignals,
    SignalDefinitions,
)
from api.services.health_regions import STATE_NAMES, WEB_GEOMETRY_VERSION, ensure_release_exists

SIGNAL_DEFINITIONS = SignalDefinitions(
    NEED_HIGH="need_score >= 0.75",
    CAPACITY_LOW="capacity_score <= 0.25",
    MISMATCH_MARKED_POSITIVE="mismatch_score >= 0.25",
    CAPACITY_COMPONENT_LOW=(
        "caps_percentile <= 0.25 OR beds_percentile <= 0.25 OR psychiatrist_fte_percentile <= 0.25"
    ),
    SPATIAL_HH_MISMATCH="lisa_significant = true AND lisa_cluster = high-high",
)

SIGNAL_TO_COLUMN = {
    "NEED_HIGH": "need_high",
    "CAPACITY_LOW": "capacity_low",
    "MISMATCH_MARKED_POSITIVE": "mismatch_marked_positive",
    "CAPACITY_COMPONENT_LOW": "capacity_component_low",
    "SPATIAL_HH_MISMATCH": "spatial_hh_mismatch",
}

TRIGGER_TEXT = {
    "need_high": "Need Score em faixa relativamente alta.",
    "capacity_low": "Capacity Score em faixa relativamente baixa.",
    "mismatch_marked_positive": (
        "Mismatch com diferença de pelo menos 25 pontos na escala percentual relativa."
    ),
    "capacity_component_low": (
        "Ao menos um componente de Capacity está em faixa relativamente baixa."
    ),
    "spatial_hh_mismatch": (
        "Mismatch relativamente alto em um contexto local de valores também altos."
    ),
}

SUBSIGNAL_TEXT = {
    "caps_low": "CAPS em faixa relativamente baixa.",
    "beds_low": "Leitos SUS em faixa relativamente baixa.",
    "psychiatrist_fte_low": "Psiquiatras FTE no SUS em faixa relativamente baixa.",
    "zero_registered_beds": "Zero leitos de saúde mental SUS registrados neste release.",
}

DECOMPOSITION_FIELDS = [
    ("suicide_contribution", "Suicídio", "suicide_percentile"),
    ("admissions_contribution", "Internações psiquiátricas", "psychiatric_admission_percentile"),
    ("caps_contribution", "CAPS", "caps_percentile"),
    ("beds_contribution", "Leitos SUS", "beds_percentile"),
    ("psychiatrist_contribution", "Psiquiatras FTE", "psychiatrist_fte_percentile"),
]


def intelligence_version(release_id: str) -> str:
    return (
        "MDB_TERRITORIAL_INTELLIGENCE_1.1"
        if release_id == "MDB_ANALYTICAL_2024_2"
        else INTELLIGENCE_VERSION
    )


def intelligence_release(row: dict | None = None) -> IntelligenceRelease:
    release_id = (row or {}).get("release_id", "MDB_ANALYTICAL_2024_1")
    return IntelligenceRelease(
        release_id=release_id,
        intelligence_version=(row or {}).get(
            "intelligence_version", intelligence_version(release_id)
        ),
        radar_ruleset_version=(row or {}).get("radar_ruleset_version", RADAR_RULESET_VERSION),
        decomposition_version=(row or {}).get("decomposition_version", DECOMPOSITION_VERSION),
        peer_method_version=(row or {}).get("peer_method_version", PEER_METHOD_VERSION),
    )


def radar_region_from_row(row: dict) -> RadarRegion:
    return RadarRegion(
        health_region_code=row["health_region_code"],
        health_region_name=row["health_region_name"],
        uf=row["uf"],
        population=row["population"],
        municipality_count=row["municipality_count"],
        need_score=row["need_score"],
        capacity_score=row["capacity_score"],
        mismatch_score=row["mismatch_score"],
        matched_signal_families=row["matched_signal_families"],
        signals=RadarSignals(
            need_high=row["need_high"],
            capacity_low=row["capacity_low"],
            mismatch_marked_positive=row["mismatch_marked_positive"],
            capacity_component_low=row["capacity_component_low"],
            spatial_hh_mismatch=row["spatial_hh_mismatch"],
            caps_low=row["caps_low"],
            beds_low=row["beds_low"],
            psychiatrist_fte_low=row["psychiatrist_fte_low"],
            zero_registered_beds=row["zero_registered_beds"],
            matched_signal_families=row["matched_signal_families"],
        ),
        data_quality_flags=list(row["data_quality_flags"]),
    )


def list_radar_regions(
    db: Database,
    release_id: str,
    uf: str | None,
    signal: RadarSignal | None,
    min_signal_families: int,
    q: str | None,
    sort: str,
    include_geometry: bool,
) -> RadarResponse:
    ensure_release_exists(db, release_id)
    filters = [
        "i.release_id = %s",
        "i.intelligence_version = %s",
        "i.matched_signal_families >= %s",
    ]
    params: list[Any] = [release_id, intelligence_version(release_id), min_signal_families]
    if uf:
        normalized = uf.upper()
        if normalized not in STATE_NAMES:
            raise api_error(404, "STATE_NOT_FOUND", "State not found for the requested release.")
        filters.append("i.uf = %s")
        params.append(normalized)
    if signal:
        filters.append(f"i.{SIGNAL_TO_COLUMN[signal]} = true")
    if q:
        filters.append("(i.health_region_name ILIKE %s OR i.health_region_code ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    order = {
        "signals": "i.matched_signal_families DESC, i.health_region_code ASC",
        "mismatch": "i.mismatch_score DESC, i.health_region_code ASC",
        "name": "i.health_region_name ASC, i.health_region_code ASC",
    }[sort]
    geometry_join = ""
    geometry_select = ""
    query_params = params.copy()
    if include_geometry:
        geometry_join = """
        JOIN web.health_region_geometry w
          ON w.geography_version = i.geography_version
         AND w.health_region_code = i.health_region_code
         AND w.web_geometry_version = %s
         AND w.geometry_profile = 'overview'
        """
        geometry_select = ", ST_AsGeoJSON(w.geom)::json AS geometry"
        query_params = [WEB_GEOMETRY_VERSION, *params]
    rows = db.rows(
        f"""
        SELECT i.*{geometry_select}
        FROM analytics.health_region_intelligence i
        {geometry_join}
        WHERE {" AND ".join(filters)}
        ORDER BY {order}
        """,
        tuple(query_params),
    )
    regions = [radar_region_from_row(row) for row in rows]
    geometry = None
    if include_geometry:
        geometry = RadarFeatureCollection(
            type="FeatureCollection",
            features=[
                RadarFeature(
                    type="Feature",
                    id=row["health_region_code"],
                    geometry=parse_geometry(row["geometry"]),
                    properties=radar_region_from_row(row),
                )
                for row in rows
            ],
            crs={"type": "name", "properties": {"name": "EPSG:4326"}},
            geometry_metadata=GeometryMetadata(
                profile=GeometryProfile.overview,
                version=WEB_GEOMETRY_VERSION,
                crs="EPSG:4326",
            ),
        )
    return RadarResponse(
        release=intelligence_release(rows[0] if rows else {"release_id": release_id}),
        filters={
            "uf": uf.upper() if uf else None,
            "signal": signal,
            "min_signal_families": min_signal_families,
            "q": q,
            "sort": sort,
            "include_geometry": include_geometry,
        },
        signal_definitions=SIGNAL_DEFINITIONS,
        total_matching=len(regions),
        regions=regions,
        geometry=geometry,
    )


def get_explanation(db: Database, release_id: str, code: str) -> ExplanationResponse:
    ensure_release_exists(db, release_id)
    row = db.row(
        """
        SELECT *
        FROM analytics.health_region_intelligence
        WHERE release_id = %s AND intelligence_version = %s AND health_region_code = %s
        """,
        (release_id, intelligence_version(release_id), code),
    )
    if not row:
        raise api_error(404, "HEALTH_REGION_NOT_FOUND", "Health Region not found.")
    triggers = [text for key, text in TRIGGER_TEXT.items() if row[key]]
    subsignals = [text for key, text in SUBSIGNAL_TEXT.items() if row[key]]
    flags = list(row["data_quality_flags"])
    cautions = []
    if "SMALL_SUICIDE_COUNT" in flags:
        cautions.append(
            "Pouco número de óbitos no período agregado; "
            "interprete o componente de suicídio com cautela."
        )
    if row["zero_registered_beds"]:
        cautions.append(
            "Zero leitos de saúde mental SUS registrados não significa "
            "ausência de toda possibilidade de acesso."
        )
    decomposition = []
    for contribution_field, label, percentile_field in DECOMPOSITION_FIELDS:
        caution = None
        if contribution_field == "suicide_contribution" and "SMALL_SUICIDE_COUNT" in flags:
            caution = "Pouco número de óbitos no período agregado; interprete com cautela."
        decomposition.append(
            DecompositionItem(
                component=contribution_field.replace("_contribution", ""),
                label=label,
                source_percentile=row[percentile_field],
                contribution=row[contribution_field],
                caution=caution,
            )
        )
    interpretation = deterministic_interpretation(row["mismatch_score"], decomposition)
    return ExplanationResponse(
        release=intelligence_release(row),
        health_region_code=row["health_region_code"],
        health_region_name=row["health_region_name"],
        uf=row["uf"],
        matched_signal_families=row["matched_signal_families"],
        triggers=triggers,
        subsignals=subsignals,
        quality_cautions=cautions,
        decomposition=decomposition,
        decomposition_sum=row["decomposition_sum"],
        mismatch_score=row["mismatch_score"],
        interpretation=interpretation,
    )


def deterministic_interpretation(
    mismatch_score: float, decomposition: list[DecompositionItem]
) -> str:
    positives = sorted(
        [item for item in decomposition if item.contribution > 0],
        key=lambda item: abs(item.contribution),
        reverse=True,
    )
    negatives = sorted(
        [item for item in decomposition if item.contribution < 0],
        key=lambda item: abs(item.contribution),
        reverse=True,
    )
    direction = (
        "positivo"
        if mismatch_score > 0
        else "negativo"
        if mismatch_score < 0
        else "próximo de zero"
    )
    up = " e ".join(item.label for item in positives[:2]) if positives else "nenhum componente"
    down = " e ".join(item.label for item in negatives[:2]) if negatives else "nenhum componente"
    return (
        f"O Mismatch desta região é {direction}. Entre as maiores contribuições "
        f"algébricas para cima estão {up}. No sentido oposto aparecem {down}."
    )


def get_peers(db: Database, release_id: str, code: str, metric: Metric) -> PeersResponse:
    ensure_release_exists(db, release_id)
    target = db.row(
        """
        SELECT health_region_code, health_region_name, uf
        FROM analytics.health_region_intelligence
        WHERE release_id = %s AND intelligence_version = %s AND health_region_code = %s
        """,
        (release_id, intelligence_version(release_id), code),
    )
    if not target:
        raise api_error(404, "HEALTH_REGION_NOT_FOUND", "Health Region not found.")
    peer_rows = db.rows(
        f"""
        SELECT p.peer_rank, g.health_region_code, g.health_region_name, g.uf,
               m.population, m.population_density, g.municipality_count,
               m.{metric.value} AS metric_value
        FROM analytics.health_region_peers p
        JOIN serving.health_region_profile g
          ON g.release_id = p.release_id
         AND g.health_region_code = p.peer_health_region_code
        JOIN analytics.health_region_metrics m
          ON m.release_id = p.release_id
         AND m.health_region_code = p.peer_health_region_code
        WHERE p.release_id = %s
          AND p.peer_method_version = %s
          AND p.health_region_code = %s
        ORDER BY p.peer_rank
        """,
        (release_id, PEER_METHOD_VERSION, code),
    )
    benchmark_rows = db.rows(
        """
        SELECT metric_id, target_value, peer_n_observed, peer_median, peer_q1, peer_q3,
               peer_min, peer_max, relative_to_peer_iqr, insufficient_reason
        FROM analytics.health_region_peer_benchmarks
        WHERE release_id = %s AND peer_method_version = %s AND health_region_code = %s
        ORDER BY metric_id
        """,
        (release_id, PEER_METHOD_VERSION, code),
    )
    return PeersResponse(
        release=intelligence_release({"release_id": release_id}),
        health_region_code=target["health_region_code"],
        health_region_name=target["health_region_name"],
        uf=target["uf"],
        selected_metric=metric,
        method=peer_method_payload(),
        peers=[PeerRegion(**row) for row in peer_rows],
        benchmarks=[PeerBenchmark(**row) for row in benchmark_rows],
    )


def methods(db: Database, release_id: str) -> IntelligenceMethodsResponse:
    ensure_release_exists(db, release_id)
    return IntelligenceMethodsResponse(
        release=intelligence_release({"release_id": release_id}),
        radar={
            "version": RADAR_RULESET_VERSION,
            "families": SIGNAL_DEFINITIONS.model_dump(),
            "matched_signal_families": "Contagem sem pesos das cinco famílias transparentes.",
            "not_ordered_priority_list": True,
            "data_quality_flags_count": False,
        },
        decomposition={
            "version": DECOMPOSITION_VERSION,
            "reference": "P50 como referência relativa neutra nacional.",
            "identity": "sum(contributions) == mismatch_score",
            "interpretation": "contribuição algébrica, sem leitura etiológica.",
        },
        peers=peer_method_payload(),
    )


def peer_method_payload() -> dict[str, Any]:
    return {
        "version": PEER_METHOD_VERSION,
        "structural_variables": ["population", "population_density", "municipality_count"],
        "transform": "log1p, depois z-score nacional com std populacional ddof=0",
        "distance": "Euclidean distance com pesos iguais nas três dimensões.",
        "selection": "10 regiões mais próximas; self excluído; desempate por health_region_code.",
        "outcome_variables_used_for_selection": False,
        "limitations": [
            "Peers V1 não incorpora renda, urbanização formal, perfil etário, "
            "vulnerabilidade social ou financiamento.",
            "Semelhante significa semelhante apenas nas três dimensões explicitadas.",
        ],
    }


def parse_geometry(geometry: dict | str) -> dict:
    if isinstance(geometry, dict):
        return geometry
    return json.loads(geometry)

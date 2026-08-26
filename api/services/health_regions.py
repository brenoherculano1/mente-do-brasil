"""Read-only queries for health-region serving views."""

from __future__ import annotations

import json

from api.db import Database
from api.errors import api_error
from api.schemas.common import GeometryProfile, Metric
from api.schemas.health_regions import (
    BedsCapacity,
    CapacityProfile,
    CapsCapacity,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
    GeometryMetadata,
    HealthRegionLookup,
    HealthRegionMapItem,
    HealthRegionProfile,
    MismatchProfile,
    MunicipalityHealthRegion,
    NeedProfile,
    PsychiatricAdmissionsNeed,
    PsychiatristFteCapacity,
    SpatialProfile,
    StateProfile,
    StateRegion,
    StateSummary,
    SuicideNeed,
    TerritoryProfile,
    UfOption,
)
from api.schemas.indicators import IndicatorPublic
from api.schemas.releases import ReleasePublic

WEB_GEOMETRY_VERSION = "MDB_WEB_GEOMETRY_V1"

STATE_NAMES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

RELEASE_COLUMNS = """
release_id, canonical_version, method_version, geography_version, release_status,
quality_status, release_gate, public_release_status
"""

PROFILE_COLUMNS = """
release_id, canonical_version, method_version, geography_version, release_status,
quality_status, release_gate, public_release_status, health_region_code,
health_region_name, uf_code, uf, municipality_count, area_km2, population,
population_density, suicide_deaths, suicide_asmr, suicide_percentile,
psychiatric_admissions, psychiatric_admission_rate, psychiatric_admission_percentile,
caps_count, caps_rate, caps_percentile, mental_health_beds_sus_count,
mental_health_beds_sus_rate, beds_percentile, psychiatrist_fte, psychiatrist_fte_rate,
psychiatrist_fte_percentile, need_score, capacity_score, mismatch_score,
lisa_local_i, lisa_p, lisa_q, lisa_significant, lisa_cluster, data_quality_flags
"""


def release_from_row(row: dict) -> ReleasePublic:
    return ReleasePublic(**{field: row[field] for field in ReleasePublic.model_fields})


def list_releases(db: Database) -> list[ReleasePublic]:
    rows = db.rows(
        f"""
        SELECT {RELEASE_COLUMNS}
        FROM meta.releases
        ORDER BY release_id
        """
    )
    return [ReleasePublic(**row) for row in rows]


def get_release(db: Database, release_id: str) -> ReleasePublic:
    row = db.row(
        f"""
        SELECT {RELEASE_COLUMNS}
        FROM meta.releases
        WHERE release_id = %s
        """,
        (release_id,),
    )
    if not row:
        raise api_error(404, "RELEASE_NOT_FOUND", "Release not found.")
    return ReleasePublic(**row)


def ensure_release_exists(db: Database, release_id: str) -> None:
    row = db.row("SELECT 1 AS exists FROM meta.releases WHERE release_id = %s", (release_id,))
    if not row:
        raise api_error(404, "RELEASE_NOT_FOUND", "Release not found.")


def ready_check(db: Database, release_id: str) -> dict:
    row = db.row(
        """
        SELECT r.release_id, s.serving_database_status
        FROM meta.releases r
        JOIN meta.serving_database_status s ON s.release_id = r.release_id
        WHERE r.release_id = %s
          AND s.serving_database_status IN ('VALIDATED_LOCAL')
        """,
        (release_id,),
    )
    if not row:
        raise api_error(503, "DATABASE_UNAVAILABLE", "Default release is not ready.")
    return {"status": "ready", "database": "ok", "release_id": row["release_id"]}


def list_indicators(db: Database) -> list[IndicatorPublic]:
    rows = db.rows(
        """
        SELECT indicator_id, indicator_name_pt, indicator_name_en, domain, description,
               unit, interpretation, what_it_does_not_measure, source_system,
               observation_start, observation_end, method_version
        FROM meta.indicators
        ORDER BY domain, indicator_id, method_version
        """
    )
    return [IndicatorPublic(**row) for row in rows]


def get_indicator(db: Database, indicator_id: str) -> IndicatorPublic:
    row = db.row(
        """
        SELECT indicator_id, indicator_name_pt, indicator_name_en, domain, description,
               unit, interpretation, what_it_does_not_measure, source_system,
               observation_start, observation_end, method_version
        FROM meta.indicators
        WHERE indicator_id = %s
        ORDER BY method_version
        LIMIT 1
        """,
        (indicator_id,),
    )
    if not row:
        raise api_error(404, "INDICATOR_NOT_FOUND", "Indicator not found.")
    return IndicatorPublic(**row)


def list_health_regions(
    db: Database,
    release_id: str,
    uf: str | None,
    q: str | None,
    limit: int,
    offset: int,
) -> tuple[list[HealthRegionLookup], int]:
    ensure_release_exists(db, release_id)
    filters = ["release_id = %s"]
    params: list = [release_id]
    if uf:
        filters.append("uf = %s")
        params.append(uf.upper())
    if q:
        filters.append("(health_region_name ILIKE %s OR health_region_code ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    where_clause = " AND ".join(filters)
    total = db.row(
        f"SELECT count(*) AS total FROM serving.health_region_lookup WHERE {where_clause}",
        tuple(params),
    )["total"]
    rows = db.rows(
        f"""
        SELECT health_region_code, health_region_name, uf, geography_version, release_id
        FROM serving.health_region_lookup
        WHERE {where_clause}
        ORDER BY uf, health_region_name, health_region_code
        LIMIT %s OFFSET %s
        """,
        (*params, limit, offset),
    )
    return [HealthRegionLookup(**row) for row in rows], total


def get_health_region_profile(db: Database, release_id: str, code: str) -> HealthRegionProfile:
    ensure_release_exists(db, release_id)
    row = db.row(
        f"""
        SELECT {PROFILE_COLUMNS}
        FROM serving.health_region_profile
        WHERE release_id = %s AND health_region_code = %s
        """,
        (release_id, code),
    )
    if not row:
        raise api_error(
            404,
            "HEALTH_REGION_NOT_FOUND",
            "Health Region not found for the requested release.",
        )
    return HealthRegionProfile(
        release=release_from_row(row),
        territory=TerritoryProfile(
            health_region_code=row["health_region_code"],
            health_region_name=row["health_region_name"],
            uf=row["uf"],
            uf_code=row["uf_code"],
            municipality_count=row["municipality_count"],
            population=row["population"],
            area_km2=row["area_km2"],
            population_density=row["population_density"],
        ),
        need=NeedProfile(
            suicide=SuicideNeed(
                deaths=row["suicide_deaths"],
                asmr=row["suicide_asmr"],
                percentile=row["suicide_percentile"],
            ),
            psychiatric_admissions=PsychiatricAdmissionsNeed(
                count=row["psychiatric_admissions"],
                rate=row["psychiatric_admission_rate"],
                percentile=row["psychiatric_admission_percentile"],
            ),
            score=row["need_score"],
        ),
        capacity=CapacityProfile(
            caps=CapsCapacity(
                count=row["caps_count"],
                rate=row["caps_rate"],
                percentile=row["caps_percentile"],
            ),
            mental_health_beds_sus=BedsCapacity(
                count=row["mental_health_beds_sus_count"],
                rate=row["mental_health_beds_sus_rate"],
                percentile=row["beds_percentile"],
            ),
            psychiatrist_fte=PsychiatristFteCapacity(
                fte=row["psychiatrist_fte"],
                rate=row["psychiatrist_fte_rate"],
                percentile=row["psychiatrist_fte_percentile"],
            ),
            score=row["capacity_score"],
        ),
        mismatch=MismatchProfile(score=row["mismatch_score"]),
        spatial=SpatialProfile(
            lisa_local_i=row["lisa_local_i"],
            lisa_p=row["lisa_p"],
            lisa_q=row["lisa_q"],
            lisa_significant=row["lisa_significant"],
            lisa_cluster=row["lisa_cluster"],
        ),
        data_quality_flags=list(row["data_quality_flags"]),
    )


def get_state_profile(db: Database, release_id: str, uf: str) -> StateProfile:
    ensure_release_exists(db, release_id)
    normalized_uf = uf.upper()
    if normalized_uf not in STATE_NAMES:
        raise api_error(404, "STATE_NOT_FOUND", "State not found for the requested release.")
    rows = db.rows(
        f"""
        SELECT {PROFILE_COLUMNS}
        FROM serving.health_region_profile
        WHERE release_id = %s AND uf = %s
        ORDER BY health_region_name, health_region_code
        """,
        (release_id, normalized_uf),
    )
    if not rows:
        raise api_error(404, "STATE_NOT_FOUND", "State not found for the requested release.")
    release = release_from_row(rows[0])
    regions = [
        StateRegion(
            health_region_code=row["health_region_code"],
            health_region_name=row["health_region_name"],
            uf=row["uf"],
            population=row["population"],
            municipality_count=row["municipality_count"],
            suicide_percentile=row["suicide_percentile"],
            psychiatric_admission_percentile=row["psychiatric_admission_percentile"],
            need_score=row["need_score"],
            caps_percentile=row["caps_percentile"],
            beds_percentile=row["beds_percentile"],
            psychiatrist_fte_percentile=row["psychiatrist_fte_percentile"],
            capacity_score=row["capacity_score"],
            mismatch_score=row["mismatch_score"],
            lisa_significant=row["lisa_significant"],
            lisa_cluster=row["lisa_cluster"],
            data_quality_flags=list(row["data_quality_flags"]),
        )
        for row in rows
    ]
    lisa_cluster_counts: dict[str, int] = {}
    quality_flag_counts: dict[str, int] = {}
    for region in regions:
        if region.lisa_significant and region.lisa_cluster:
            lisa_cluster_counts[region.lisa_cluster] = (
                lisa_cluster_counts.get(region.lisa_cluster, 0) + 1
            )
        for flag in region.data_quality_flags:
            quality_flag_counts[flag] = quality_flag_counts.get(flag, 0) + 1
    return StateProfile(
        release=release,
        state=StateSummary(
            uf=normalized_uf,
            state_name=STATE_NAMES[normalized_uf],
            health_region_count=len(regions),
            population=sum(region.population for region in regions),
            municipality_count=sum(region.municipality_count for region in regions),
            lisa_significant_count=sum(1 for region in regions if region.lisa_significant),
            lisa_cluster_counts=lisa_cluster_counts,
            quality_flag_counts=quality_flag_counts,
        ),
        regions=regions,
    )


def list_map_data(
    db: Database,
    release_id: str,
    metric: Metric,
    uf: str | None,
    include_geometry: bool,
    geometry_profile: GeometryProfile | None,
) -> list[HealthRegionMapItem] | GeoJsonFeatureCollection:
    ensure_release_exists(db, release_id)
    metric_column = metric.value
    filters = ["m.release_id = %s"]
    filter_params: list = [release_id]
    if uf:
        filters.append("m.uf = %s")
        filter_params.append(uf.upper())
    where_clause = " AND ".join(filters)
    profile = geometry_profile or GeometryProfile.overview
    join_params: list = []
    if include_geometry and profile == GeometryProfile.full:
        geometry_join = ""
        geometry_select = ", ST_AsGeoJSON(m.geom)::json AS geometry"
        geometry_metadata = GeometryMetadata(
            profile=GeometryProfile.full,
            version="BR_HEALTH_REGIONS_END2024_V1",
            crs="EPSG:4674",
        )
    elif include_geometry:
        geometry_join = """
        JOIN web.health_region_geometry w
          ON w.geography_version = m.geography_version
         AND w.health_region_code = m.health_region_code
         AND w.web_geometry_version = %s
         AND w.geometry_profile = %s
        """
        join_params.extend([WEB_GEOMETRY_VERSION, profile.value])
        geometry_select = ", ST_AsGeoJSON(w.geom)::json AS geometry"
        geometry_metadata = GeometryMetadata(
            profile=profile,
            version=WEB_GEOMETRY_VERSION,
            crs="EPSG:4326",
        )
    else:
        geometry_join = ""
        geometry_select = ""
        geometry_metadata = None
    rows = db.rows(
        f"""
        SELECT m.health_region_code, m.health_region_name, m.uf, m.population,
               m.{metric_column} AS value, m.data_quality_flags, m.lisa_significant,
               m.lisa_cluster{geometry_select}
        FROM serving.health_region_map m
        {geometry_join}
        WHERE {where_clause}
        ORDER BY m.uf, m.health_region_name, m.health_region_code
        """,
        tuple(join_params + filter_params),
    )
    items = [
        HealthRegionMapItem(
            health_region_code=row["health_region_code"],
            health_region_name=row["health_region_name"],
            uf=row["uf"],
            population=row["population"],
            metric=metric.value,
            value=row["value"],
            data_quality_flags=list(row["data_quality_flags"]),
            lisa_significant=row["lisa_significant"],
            lisa_cluster=row["lisa_cluster"],
        )
        for row in rows
    ]
    if not include_geometry:
        return items
    if len(items) != len(rows):
        raise api_error(503, "DATABASE_UNAVAILABLE", "Geometry layer is not ready.")
    features = [
        GeoJsonFeature(
            type="Feature",
            id=item.health_region_code,
            geometry=parse_geometry(row["geometry"]),
            properties=item,
        )
        for item, row in zip(items, rows, strict=True)
    ]
    return GeoJsonFeatureCollection(
        type="FeatureCollection",
        features=features,
        crs={"type": "name", "properties": {"name": geometry_metadata.crs}},
        geometry_metadata=geometry_metadata,
    )


def parse_geometry(geometry: dict | str) -> dict:
    if isinstance(geometry, dict):
        return geometry
    return json.loads(geometry)


def municipality_health_region(
    db: Database, code: str, release_id: str
) -> MunicipalityHealthRegion:
    row = db.row(
        """
        SELECT municipality_code_ibge, municipality_name, uf, health_region_code,
               health_region_name, geography_version
        FROM geo.municipality_health_region_crosswalk
        WHERE municipality_code_ibge = %s
          AND geography_version = (
              SELECT geography_version
              FROM meta.releases
              WHERE release_id = %s
          )
        """,
        (code, release_id),
    )
    if not row:
        raise api_error(404, "MUNICIPALITY_NOT_FOUND", "Municipality not found.")
    return MunicipalityHealthRegion(**row)


def uf_options(db: Database, release_id: str) -> list[UfOption]:
    ensure_release_exists(db, release_id)
    rows = db.rows(
        """
        SELECT uf, count(*) AS health_region_count
        FROM serving.health_region_lookup
        WHERE release_id = %s
        GROUP BY uf
        ORDER BY uf
        """,
        (release_id,),
    )
    return [UfOption(**row) for row in rows]

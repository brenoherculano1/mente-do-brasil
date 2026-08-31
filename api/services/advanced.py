"""Read-only access to frozen advanced products; no runtime scientific computation."""

from api.db import Database
from api.errors import api_error
from api.services.health_regions import STATE_NAMES, WEB_GEOMETRY_VERSION

CURRENT = "MDB_ANALYTICAL_2024_2"
TEMPORAL = "MDB_TEMPORAL_2022_2024_1"
CHANGES = "MDB_CHANGE_RADAR_RULESET_1.0"
FLOW = "MDB_HOSPITAL_FLOW_METHOD_1.0"
FAMILIES = (
    "NEED_POSITION_UP",
    "CAPACITY_POSITION_DOWN",
    "MISMATCH_POSITION_UP",
    "NEED_COMPONENT_POSITION_UP",
    "CAPACITY_COMPONENT_POSITION_DOWN",
)


def timeline(db: Database, code: str):
    rows = db.rows(
        'SELECT "values" FROM analytics.health_region_temporal '
        "WHERE temporal_version=%s AND health_region_code=%s ORDER BY year",
        (TEMPORAL, code),
    )
    if not rows:
        raise api_error(404, "TIMELINE_NOT_FOUND", "Timeline not found.")
    return {
        "release_id": CURRENT,
        "temporal_version": TEMPORAL,
        "anchors": [row["values"] for row in rows],
        "anchor_definition": "Need: janela de tres anos; Capacity: dezembro do ano-ancora.",
    }


def list_changes(
    db: Database,
    start: int,
    end: int,
    uf: str | None,
    signal: str | None,
    minimum: int,
    query: str | None,
    sort: str,
    geometry: bool,
):
    if (start, end) not in {(2022, 2023), (2023, 2024), (2022, 2024)}:
        raise api_error(422, "UNSUPPORTED_PERIOD", "Unsupported anchor comparison.")
    if uf and uf.upper() not in STATE_NAMES:
        raise api_error(404, "STATE_NOT_FOUND", "State not found.")
    filters = [
        "c.change_version=%s",
        "c.from_year=%s",
        "c.to_year=%s",
        "c.matched_change_families >= %s",
    ]
    params = [CHANGES, start, end, minimum]
    if uf:
        filters.append("g.uf=%s")
        params.append(uf.upper())
    if signal:
        if signal not in FAMILIES:
            raise api_error(422, "INVALID_CHANGE_FAMILY", "Unknown change family.")
        filters.append('(c."values"->>%s)::boolean')
        params.append(signal)
    if query:
        filters.append("(g.health_region_name ILIKE %s OR g.health_region_code ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])
    order = {
        "families": "c.matched_change_families DESC",
        "mismatch": "(c.\"values\"->>'delta_mismatch_score')::float8 DESC",
        "name": "g.health_region_name",
    }[sort]
    select, join = "", ""
    if geometry:
        select = ", ST_AsGeoJSON(w.geom)::json AS geometry"
        join = "JOIN web.health_region_geometry w ON w.geography_version=c.geography_version AND w.health_region_code=c.health_region_code AND w.web_geometry_version=%s AND w.geometry_profile='overview'"
        params.insert(0, WEB_GEOMETRY_VERSION)
    rows = db.rows(
        f'SELECT c."values", g.health_region_name, g.uf{select} '
        "FROM analytics.health_region_changes c JOIN geo.health_regions g "
        "ON g.health_region_code=c.health_region_code AND g.geography_version=c.geography_version "
        f"{join} WHERE {' AND '.join(filters)} ORDER BY {order}, c.health_region_code",
        tuple(params),
    )
    records = [
        {**r["values"], "health_region_name": r["health_region_name"], "uf": r["uf"]} for r in rows
    ]
    return {
        "release_id": CURRENT,
        "change_version": CHANGES,
        "records": records,
        "total_matching": len(records),
        "from_year": start,
        "to_year": end,
        "geometry": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": record["health_region_code"],
                    "properties": record,
                    "geometry": row["geometry"],
                }
                for record, row in zip(records, rows, strict=True)
            ],
        }
        if geometry
        else None,
    }


def flows(db: Database, code: str, perspective: str, limit: int):
    summary = db.row(
        'SELECT "values" FROM analytics.health_region_flow_summary '
        "WHERE flow_version=%s AND health_region_code=%s",
        (FLOW, code),
    )
    if not summary:
        raise api_error(404, "FLOW_NOT_FOUND", "Flow region not found.")
    focus, other = (
        ("origin_region", "destination_region")
        if perspective == "origin"
        else ("destination_region", "origin_region")
    )
    rows = db.rows(
        f"SELECT f.{other} AS health_region_code, g.health_region_name, g.uf, "
        "CASE WHEN bool_or(f.suppressed) THEN NULL ELSE sum(f.admissions) END AS admissions, "
        "bool_or(f.suppressed) AS partial, "
        "ST_X(ST_Transform(ST_PointOnSurface(g.geom),4326)) AS longitude, "
        "ST_Y(ST_Transform(ST_PointOnSurface(g.geom),4326)) AS latitude "
        "FROM analytics.hospitalization_flows f JOIN geo.health_regions g "
        f"ON g.geography_version=f.geography_version AND g.health_region_code=f.{other} "
        f"WHERE f.flow_version=%s AND f.{focus}=%s "
        f"GROUP BY f.{other},g.health_region_name,g.uf,g.geom "
        "ORDER BY admissions DESC NULLS LAST,health_region_code LIMIT %s",
        (FLOW, code, limit),
    )
    center = db.row(
        "SELECT health_region_name,uf,ST_X(ST_Transform(ST_PointOnSurface(geom),4326)) AS longitude, "
        "ST_Y(ST_Transform(ST_PointOnSurface(geom),4326)) AS latitude FROM geo.health_regions "
        "WHERE geography_version=%s AND health_region_code=%s",
        ("BR_HEALTH_REGIONS_END2024_V1", code),
    )
    return {
        "release_id": CURRENT,
        "flow_version": FLOW,
        "perspective": perspective,
        "health_region_code": code,
        "region": center,
        "summary": summary["values"],
        "connections": rows,
        "unit": "AIHs/admissions; not unique patients",
        "suppression": "Counts below five suppressed. Regional pairs containing suppressed contributions are unavailable.",
    }

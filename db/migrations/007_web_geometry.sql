CREATE SCHEMA IF NOT EXISTS web;

CREATE TABLE IF NOT EXISTS web.health_region_geometry (
    web_geometry_version TEXT NOT NULL,
    geography_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    geometry_profile TEXT NOT NULL,
    source_srid INTEGER NOT NULL,
    web_srid INTEGER NOT NULL,
    simplification_method TEXT NOT NULL,
    simplification_tolerance_m DOUBLE PRECISION,
    source_geometry_sha256 TEXT,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (
        web_geometry_version,
        geography_version,
        health_region_code,
        geometry_profile
    ),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions (geography_version, health_region_code),
    CHECK (geometry_profile IN ('overview', 'detail')),
    CHECK (source_srid = 4674),
    CHECK (web_srid = 4326),
    CHECK (simplification_tolerance_m IS NULL OR simplification_tolerance_m > 0),
    CHECK (ST_SRID(geom) = 4326),
    CHECK (ST_IsValid(geom)),
    CHECK (NOT ST_IsEmpty(geom))
);

CREATE INDEX IF NOT EXISTS web_health_region_geometry_geom_gix
    ON web.health_region_geometry USING gist (geom);

CREATE INDEX IF NOT EXISTS web_health_region_geometry_profile_idx
    ON web.health_region_geometry (
        web_geometry_version,
        geography_version,
        geometry_profile
    );

CREATE TABLE IF NOT EXISTS meta.releases (
    release_id TEXT PRIMARY KEY,
    canonical_version TEXT NOT NULL,
    method_version TEXT NOT NULL,
    geography_version TEXT NOT NULL,
    release_status TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    release_gate TEXT NOT NULL,
    public_release_status TEXT NOT NULL,
    canonical_generated_at TIMESTAMPTZ,
    health_regions_sha256 TEXT NOT NULL,
    crosswalk_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (release_id, geography_version)
);

CREATE TABLE IF NOT EXISTS meta.indicators (
    indicator_id TEXT NOT NULL,
    indicator_name_pt TEXT NOT NULL,
    indicator_name_en TEXT NOT NULL,
    domain TEXT NOT NULL,
    description TEXT NOT NULL,
    unit TEXT NOT NULL,
    interpretation TEXT NOT NULL,
    what_it_does_not_measure TEXT[] NOT NULL DEFAULT '{}',
    method_version TEXT NOT NULL,
    source_system TEXT NOT NULL,
    observation_start DATE,
    observation_end DATE,
    PRIMARY KEY (indicator_id, method_version)
);

CREATE TABLE IF NOT EXISTS geo.health_regions (
    geography_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    health_region_name TEXT NOT NULL,
    uf_code VARCHAR(2) NOT NULL,
    uf CHAR(2) NOT NULL,
    municipality_count INTEGER NOT NULL,
    area_km2 DOUBLE PRECISION NOT NULL,
    geom geometry(MultiPolygon, 4674) NOT NULL,
    PRIMARY KEY (geography_version, health_region_code)
);

CREATE TABLE IF NOT EXISTS geo.municipality_health_region_crosswalk (
    geography_version TEXT NOT NULL,
    municipality_code_ibge VARCHAR(7) NOT NULL,
    municipality_code_datasus6 VARCHAR(6) NOT NULL,
    municipality_name TEXT NOT NULL,
    uf CHAR(2) NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    health_region_name TEXT NOT NULL,
    source TEXT,
    PRIMARY KEY (geography_version, municipality_code_ibge),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions (geography_version, health_region_code)
);

CREATE TABLE IF NOT EXISTS analytics.health_region_metrics (
    release_id TEXT NOT NULL,
    geography_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    population BIGINT NOT NULL,
    population_density DOUBLE PRECISION NOT NULL,
    suicide_deaths INTEGER NOT NULL,
    suicide_asmr DOUBLE PRECISION NOT NULL,
    suicide_percentile DOUBLE PRECISION NOT NULL,
    psychiatric_admissions BIGINT NOT NULL,
    psychiatric_admission_rate DOUBLE PRECISION NOT NULL,
    psychiatric_admission_percentile DOUBLE PRECISION NOT NULL,
    caps_count INTEGER NOT NULL,
    caps_rate DOUBLE PRECISION NOT NULL,
    caps_percentile DOUBLE PRECISION NOT NULL,
    mental_health_beds_sus_count INTEGER NOT NULL,
    mental_health_beds_sus_rate DOUBLE PRECISION NOT NULL,
    beds_percentile DOUBLE PRECISION NOT NULL,
    psychiatrist_fte DOUBLE PRECISION NOT NULL,
    psychiatrist_fte_rate DOUBLE PRECISION NOT NULL,
    psychiatrist_fte_percentile DOUBLE PRECISION NOT NULL,
    need_score DOUBLE PRECISION NOT NULL,
    capacity_score DOUBLE PRECISION NOT NULL,
    mismatch_score DOUBLE PRECISION NOT NULL,
    lisa_local_i DOUBLE PRECISION,
    lisa_p DOUBLE PRECISION,
    lisa_q DOUBLE PRECISION,
    lisa_significant BOOLEAN NOT NULL,
    lisa_cluster TEXT,
    data_quality_flags TEXT[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (release_id, health_region_code),
    FOREIGN KEY (release_id, geography_version)
        REFERENCES meta.releases (release_id, geography_version),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions (geography_version, health_region_code)
);

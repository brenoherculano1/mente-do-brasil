CREATE TABLE meta.advanced_versions (
    version_id TEXT PRIMARY KEY,
    release_id TEXT NOT NULL REFERENCES meta.releases(release_id),
    content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    files JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE analytics.health_region_temporal (
    temporal_version TEXT NOT NULL REFERENCES meta.advanced_versions(version_id),
    release_id TEXT NOT NULL REFERENCES meta.releases(release_id),
    geography_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    year INTEGER NOT NULL CHECK (year IN (2022, 2023, 2024)),
    values JSONB NOT NULL CHECK (jsonb_typeof(values) = 'object'),
    PRIMARY KEY (temporal_version, year, health_region_code),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions(geography_version, health_region_code),
    CHECK ((values->>'population')::bigint > 0),
    CHECK ((values->>'person_years')::bigint > 0),
    CHECK ((values->>'need_score')::float8 BETWEEN 0 AND 1),
    CHECK ((values->>'capacity_score')::float8 BETWEEN 0 AND 1),
    CHECK ((values->>'mismatch_score')::float8 BETWEEN -1 AND 1)
);

CREATE TABLE analytics.health_region_changes (
    change_version TEXT NOT NULL REFERENCES meta.advanced_versions(version_id),
    geography_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    from_year INTEGER NOT NULL,
    to_year INTEGER NOT NULL,
    matched_change_families INTEGER NOT NULL CHECK (matched_change_families BETWEEN 0 AND 5),
    values JSONB NOT NULL CHECK (jsonb_typeof(values) = 'object'),
    PRIMARY KEY (change_version, from_year, to_year, health_region_code),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions(geography_version, health_region_code),
    CHECK ((from_year, to_year) IN ((2022, 2023), (2023, 2024), (2022, 2024)))
);

CREATE TABLE analytics.hospitalization_flows (
    flow_version TEXT NOT NULL REFERENCES meta.advanced_versions(version_id),
    contribution_id INTEGER NOT NULL CHECK (contribution_id >= 0),
    geography_version TEXT NOT NULL,
    origin_region VARCHAR(5) NOT NULL,
    destination_region VARCHAR(5) NOT NULL,
    admissions BIGINT CHECK (admissions >= 5),
    suppressed BOOLEAN NOT NULL,
    PRIMARY KEY (flow_version, contribution_id),
    FOREIGN KEY (geography_version, origin_region)
        REFERENCES geo.health_regions(geography_version, health_region_code),
    FOREIGN KEY (geography_version, destination_region)
        REFERENCES geo.health_regions(geography_version, health_region_code),
    CHECK (suppressed = (admissions IS NULL))
);

CREATE TABLE analytics.health_region_flow_summary (
    flow_version TEXT NOT NULL REFERENCES meta.advanced_versions(version_id),
    geography_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    values JSONB NOT NULL CHECK (jsonb_typeof(values) = 'object'),
    PRIMARY KEY (flow_version, health_region_code),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions(geography_version, health_region_code)
);

CREATE INDEX hospitalization_flows_origin ON analytics.hospitalization_flows(origin_region);
CREATE INDEX hospitalization_flows_destination ON analytics.hospitalization_flows(destination_region);

ALTER TABLE analytics.health_region_financing
    ADD CONSTRAINT financing_version_fk FOREIGN KEY(financing_version)
        REFERENCES meta.advanced_versions(version_id),
    ADD CONSTRAINT financing_population_covered_valid
        CHECK (population_covered BETWEEN 0 AND population_expected),
    ADD CONSTRAINT financing_per_capita_availability
        CHECK (headline_available = (health_expenditure_per_capita_brl IS NOT NULL));

GRANT SELECT ON meta.advanced_versions, analytics.health_region_temporal,
    analytics.health_region_changes, analytics.hospitalization_flows,
    analytics.health_region_flow_summary, analytics.health_region_financing
    TO mente_do_brasil_api;

CREATE OR REPLACE VIEW serving.health_region_profile AS
SELECT
    r.release_id,
    r.canonical_version,
    r.method_version,
    r.geography_version,
    r.release_status,
    r.quality_status,
    r.release_gate,
    r.public_release_status,
    g.health_region_code,
    g.health_region_name,
    g.uf_code,
    g.uf,
    g.municipality_count,
    g.area_km2,
    m.population,
    m.population_density,
    m.suicide_deaths,
    m.suicide_asmr,
    m.suicide_percentile,
    m.psychiatric_admissions,
    m.psychiatric_admission_rate,
    m.psychiatric_admission_percentile,
    m.caps_count,
    m.caps_rate,
    m.caps_percentile,
    m.mental_health_beds_sus_count,
    m.mental_health_beds_sus_rate,
    m.beds_percentile,
    m.psychiatrist_fte,
    m.psychiatrist_fte_rate,
    m.psychiatrist_fte_percentile,
    m.need_score,
    m.capacity_score,
    m.mismatch_score,
    m.lisa_local_i,
    m.lisa_p,
    m.lisa_q,
    m.lisa_significant,
    m.lisa_cluster,
    m.data_quality_flags,
    r.health_regions_sha256,
    r.crosswalk_sha256,
    r.canonical_generated_at
FROM meta.releases r
JOIN analytics.health_region_metrics m
    ON m.release_id = r.release_id
    AND m.geography_version = r.geography_version
JOIN geo.health_regions g
    ON g.geography_version = m.geography_version
    AND g.health_region_code = m.health_region_code;

CREATE OR REPLACE VIEW serving.health_region_map AS
SELECT
    r.release_id,
    r.geography_version,
    g.health_region_code,
    g.health_region_name,
    g.uf,
    m.population,
    m.need_score,
    m.capacity_score,
    m.mismatch_score,
    m.suicide_asmr,
    m.psychiatric_admission_rate,
    m.caps_rate,
    m.mental_health_beds_sus_rate,
    m.psychiatrist_fte_rate,
    m.lisa_significant,
    m.lisa_cluster,
    m.data_quality_flags,
    g.geom
FROM meta.releases r
JOIN analytics.health_region_metrics m
    ON m.release_id = r.release_id
    AND m.geography_version = r.geography_version
JOIN geo.health_regions g
    ON g.geography_version = m.geography_version
    AND g.health_region_code = m.health_region_code;

CREATE OR REPLACE VIEW serving.health_region_lookup AS
SELECT
    g.health_region_code,
    g.health_region_name,
    g.uf,
    r.geography_version,
    r.release_id
FROM meta.releases r
JOIN geo.health_regions g
    ON g.geography_version = r.geography_version;

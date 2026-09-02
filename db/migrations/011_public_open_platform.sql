CREATE OR REPLACE VIEW serving.v_public_health_regions_current AS
SELECT
    p.release_id, p.method_version, p.geography_version, p.health_region_code,
    p.health_region_name, p.uf, p.municipality_count, p.population, p.area_km2,
    p.population_density, p.suicide_asmr, p.suicide_percentile,
    p.psychiatric_admission_rate, p.psychiatric_admission_percentile,
    p.caps_count, p.caps_rate, p.caps_percentile,
    p.mental_health_beds_sus_count, p.mental_health_beds_sus_rate,
    p.beds_percentile, p.psychiatrist_fte, p.psychiatrist_fte_rate,
    p.psychiatrist_fte_percentile, p.need_score, p.capacity_score,
    p.mismatch_score, p.lisa_local_i, p.lisa_p, p.lisa_q,
    p.lisa_significant, p.lisa_cluster, p.data_quality_flags
FROM serving.health_region_profile p;

CREATE OR REPLACE VIEW serving.v_public_temporal AS
SELECT
    t.health_region_code,
    g.health_region_name,
    g.uf,
    t.geography_version,
    (t.values->>'population')::bigint AS population,
    (t.values->>'person_years')::bigint AS person_years,
    (t.values->>'suicide_asmr')::double precision AS suicide_asmr,
    (t.values->>'psychiatric_admissions')::bigint AS psychiatric_admissions,
    (t.values->>'psychiatric_admission_rate')::double precision AS psychiatric_admission_rate,
    (t.values->>'caps_count')::integer AS caps_count,
    (t.values->>'mental_health_beds_sus_count')::integer AS mental_health_beds_sus_count,
    (t.values->>'psychiatrist_fte')::double precision AS psychiatrist_fte,
    (t.values->>'caps_rate')::double precision AS caps_rate,
    (t.values->>'mental_health_beds_sus_rate')::double precision AS mental_health_beds_sus_rate,
    (t.values->>'psychiatrist_fte_rate')::double precision AS psychiatrist_fte_rate,
    (t.values->>'suicide_percentile')::double precision AS suicide_percentile,
    (t.values->>'psychiatric_admission_percentile')::double precision AS psychiatric_admission_percentile,
    (t.values->>'caps_percentile')::double precision AS caps_percentile,
    (t.values->>'beds_percentile')::double precision AS beds_percentile,
    (t.values->>'psychiatrist_fte_percentile')::double precision AS psychiatrist_fte_percentile,
    (t.values->>'need_score')::double precision AS need_score,
    (t.values->>'capacity_score')::double precision AS capacity_score,
    (t.values->>'mismatch_score')::double precision AS mismatch_score,
    t.year,
    t.values->>'need_window_start' AS need_window_start,
    t.values->>'need_window_end' AS need_window_end,
    t.values->>'capacity_competence' AS capacity_competence,
    t.temporal_version,
    t.release_id,
    COALESCE(ARRAY(SELECT jsonb_array_elements_text(t.values->'quality_flags')), '{}') AS quality_flags
FROM analytics.health_region_temporal t
JOIN geo.health_regions g
  ON g.geography_version = t.geography_version
 AND g.health_region_code = t.health_region_code;

CREATE OR REPLACE VIEW serving.v_public_changes AS
SELECT
    c.health_region_code,
    (c.values->>'delta_need_score')::double precision AS delta_need_score,
    (c.values->>'delta_capacity_score')::double precision AS delta_capacity_score,
    (c.values->>'delta_mismatch_score')::double precision AS delta_mismatch_score,
    (c.values->>'delta_suicide_percentile')::double precision AS delta_suicide_percentile,
    (c.values->>'delta_psychiatric_admission_percentile')::double precision AS delta_psychiatric_admission_percentile,
    (c.values->>'delta_caps_percentile')::double precision AS delta_caps_percentile,
    (c.values->>'delta_beds_percentile')::double precision AS delta_beds_percentile,
    (c.values->>'delta_psychiatrist_fte_percentile')::double precision AS delta_psychiatrist_fte_percentile,
    (c.values->>'NEED_POSITION_UP')::boolean AS "NEED_POSITION_UP",
    (c.values->>'CAPACITY_POSITION_DOWN')::boolean AS "CAPACITY_POSITION_DOWN",
    (c.values->>'MISMATCH_POSITION_UP')::boolean AS "MISMATCH_POSITION_UP",
    (c.values->>'NEED_COMPONENT_POSITION_UP')::boolean AS "NEED_COMPONENT_POSITION_UP",
    (c.values->>'CAPACITY_COMPONENT_POSITION_DOWN')::boolean AS "CAPACITY_COMPONENT_POSITION_DOWN",
    c.matched_change_families, c.from_year, c.to_year, c.change_version,
    g.uf
FROM analytics.health_region_changes c
JOIN geo.health_regions g
  ON g.geography_version = c.geography_version
 AND g.health_region_code = c.health_region_code;

CREATE OR REPLACE VIEW serving.v_public_financing AS
SELECT
    f.financing_version, f.siops_snapshot_id, f.year, f.health_region_code,
    f.municipalities_expected, f.municipalities_observed, f.population_expected,
    f.population_covered, f.coverage_share, f.coverage_population_share,
    f.total_health_expenditure_brl, f.health_expenditure_per_capita_brl,
    f.headline_available, f.quality_flags, f.source_period, f.source_indicator, g.uf
FROM analytics.health_region_financing f
JOIN geo.health_regions g
  ON g.geography_version = 'BR_HEALTH_REGIONS_END2024_V1'
 AND g.health_region_code = f.health_region_code;

CREATE OR REPLACE VIEW serving.v_public_flow_edges AS
SELECT flow_version, contribution_id, origin_region, destination_region, admissions
FROM analytics.hospitalization_flows
WHERE suppressed = false AND admissions >= 5;

CREATE OR REPLACE VIEW serving.v_public_flow_summary AS
SELECT
    s.flow_version, s.health_region_code,
    (s.values->>'total_admissions')::bigint AS total_admissions,
    (s.values->>'within_region_share')::double precision AS within_region_share,
    (s.values->>'outflow_share')::double precision AS outflow_share,
    (s.values->>'cross_state_outflow_share')::double precision AS cross_state_outflow_share,
    (s.values->>'nonsuppressed_destinations')::integer AS nonsuppressed_destinations,
    s.values->>'unit' AS unit
FROM analytics.health_region_flow_summary s;

CREATE OR REPLACE VIEW serving.v_public_peers AS
SELECT release_id, peer_method_version, health_region_code,
       peer_health_region_code, peer_rank, structural_distance
FROM analytics.health_region_peers;

CREATE OR REPLACE VIEW serving.v_public_municipality_crosswalk AS
SELECT municipality_code_ibge, municipality_name, uf,
       health_region_code, health_region_name, geography_version
FROM geo.municipality_health_region_crosswalk;

GRANT SELECT ON
    serving.v_public_health_regions_current,
    serving.v_public_temporal,
    serving.v_public_changes,
    serving.v_public_financing,
    serving.v_public_flow_edges,
    serving.v_public_flow_summary,
    serving.v_public_peers,
    serving.v_public_municipality_crosswalk
TO mente_do_brasil_api;

DROP VIEW serving.v_public_temporal;

CREATE VIEW serving.v_public_temporal AS
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
    (t.values->>'need_window_start')::integer AS need_window_start,
    (t.values->>'need_window_end')::integer AS need_window_end,
    t.values->>'capacity_competence' AS capacity_competence,
    t.temporal_version,
    t.release_id,
    COALESCE(ARRAY(SELECT jsonb_array_elements_text(t.values->'quality_flags')), '{}') AS quality_flags
FROM analytics.health_region_temporal t
JOIN geo.health_regions g
  ON g.geography_version = t.geography_version
 AND g.health_region_code = t.health_region_code;

GRANT SELECT ON serving.v_public_temporal TO mente_do_brasil_api;

ALTER TABLE meta.releases
    ADD CONSTRAINT releases_release_gate_check
        CHECK (release_gate IN ('PASS', 'FAIL', 'BLOCKED')),
    ADD CONSTRAINT releases_quality_status_check
        CHECK (quality_status IN ('VALIDATED', 'VALIDATING', 'DRAFT', 'FAILED')),
    ADD CONSTRAINT releases_public_status_check
        CHECK (public_release_status IN ('NOT_RELEASED', 'RELEASED'));

ALTER TABLE geo.health_regions
    ADD CONSTRAINT health_regions_code_length_check CHECK (length(health_region_code) = 5),
    ADD CONSTRAINT health_regions_uf_code_length_check CHECK (length(uf_code) = 2),
    ADD CONSTRAINT health_regions_municipality_count_check CHECK (municipality_count > 0),
    ADD CONSTRAINT health_regions_area_check CHECK (area_km2 > 0),
    ADD CONSTRAINT health_regions_valid_uf_check CHECK (
        uf IN (
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        )
    ),
    ADD CONSTRAINT health_regions_geom_srid_check CHECK (ST_SRID(geom) = 4674),
    ADD CONSTRAINT health_regions_geom_valid_check CHECK (ST_IsValid(geom));

ALTER TABLE geo.municipality_health_region_crosswalk
    ADD CONSTRAINT crosswalk_ibge_code_length_check CHECK (length(municipality_code_ibge) = 7),
    ADD CONSTRAINT crosswalk_datasus_code_length_check CHECK (length(municipality_code_datasus6) = 6),
    ADD CONSTRAINT crosswalk_region_code_length_check CHECK (length(health_region_code) = 5),
    ADD CONSTRAINT crosswalk_valid_uf_check CHECK (
        uf IN (
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        )
    );

ALTER TABLE analytics.health_region_metrics
    ADD CONSTRAINT metrics_population_check CHECK (population > 0),
    ADD CONSTRAINT metrics_population_density_check CHECK (population_density >= 0),
    ADD CONSTRAINT metrics_suicide_deaths_check CHECK (suicide_deaths >= 0),
    ADD CONSTRAINT metrics_suicide_asmr_check CHECK (suicide_asmr >= 0),
    ADD CONSTRAINT metrics_psychiatric_admissions_check CHECK (psychiatric_admissions >= 0),
    ADD CONSTRAINT metrics_psychiatric_admission_rate_check
        CHECK (psychiatric_admission_rate >= 0),
    ADD CONSTRAINT metrics_caps_count_check CHECK (caps_count >= 0),
    ADD CONSTRAINT metrics_caps_rate_check CHECK (caps_rate >= 0),
    ADD CONSTRAINT metrics_beds_count_check CHECK (mental_health_beds_sus_count >= 0),
    ADD CONSTRAINT metrics_beds_rate_check CHECK (mental_health_beds_sus_rate >= 0),
    ADD CONSTRAINT metrics_psychiatrist_fte_check CHECK (psychiatrist_fte >= 0),
    ADD CONSTRAINT metrics_psychiatrist_fte_rate_check CHECK (psychiatrist_fte_rate >= 0),
    ADD CONSTRAINT metrics_suicide_percentile_check CHECK (suicide_percentile BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_admission_percentile_check
        CHECK (psychiatric_admission_percentile BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_caps_percentile_check CHECK (caps_percentile BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_beds_percentile_check CHECK (beds_percentile BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_fte_percentile_check
        CHECK (psychiatrist_fte_percentile BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_need_score_check CHECK (need_score BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_capacity_score_check CHECK (capacity_score BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_mismatch_score_check CHECK (mismatch_score BETWEEN -1 AND 1),
    ADD CONSTRAINT metrics_lisa_p_check CHECK (lisa_p IS NULL OR lisa_p BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_lisa_q_check CHECK (lisa_q IS NULL OR lisa_q BETWEEN 0 AND 1),
    ADD CONSTRAINT metrics_mismatch_integrity_check
        CHECK (abs(mismatch_score - (need_score - capacity_score)) <= 1e-12);

CREATE INDEX IF NOT EXISTS health_regions_geom_gix ON geo.health_regions USING gist (geom);
CREATE INDEX IF NOT EXISTS health_regions_uf_idx ON geo.health_regions (uf);
CREATE INDEX IF NOT EXISTS health_regions_name_idx ON geo.health_regions (health_region_name);

CREATE INDEX IF NOT EXISTS crosswalk_ibge_idx
    ON geo.municipality_health_region_crosswalk (municipality_code_ibge);
CREATE INDEX IF NOT EXISTS crosswalk_datasus_idx
    ON geo.municipality_health_region_crosswalk (municipality_code_datasus6);
CREATE INDEX IF NOT EXISTS crosswalk_uf_idx
    ON geo.municipality_health_region_crosswalk (uf);
CREATE INDEX IF NOT EXISTS crosswalk_region_code_idx
    ON geo.municipality_health_region_crosswalk (health_region_code);

CREATE INDEX IF NOT EXISTS metrics_release_idx ON analytics.health_region_metrics (release_id);
CREATE INDEX IF NOT EXISTS metrics_mismatch_idx ON analytics.health_region_metrics (mismatch_score);
CREATE INDEX IF NOT EXISTS metrics_need_idx ON analytics.health_region_metrics (need_score);
CREATE INDEX IF NOT EXISTS metrics_capacity_idx ON analytics.health_region_metrics (capacity_score);

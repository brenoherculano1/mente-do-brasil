CREATE TABLE IF NOT EXISTS meta.product_intelligence_versions (
    release_id TEXT NOT NULL REFERENCES meta.releases (release_id),
    intelligence_version TEXT NOT NULL,
    radar_ruleset_version TEXT NOT NULL,
    decomposition_version TEXT NOT NULL,
    peer_method_version TEXT NOT NULL,
    status TEXT NOT NULL,
    canonical_input_sha256 TEXT NOT NULL,
    intelligence_sha256 TEXT NOT NULL,
    peers_sha256 TEXT NOT NULL,
    benchmarks_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (release_id, intelligence_version),
    CHECK (status IN ('VALIDATED_LOCAL'))
);

CREATE TABLE IF NOT EXISTS analytics.health_region_intelligence (
    release_id TEXT NOT NULL,
    geography_version TEXT NOT NULL,
    intelligence_version TEXT NOT NULL,
    radar_ruleset_version TEXT NOT NULL,
    decomposition_version TEXT NOT NULL,
    peer_method_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    health_region_name TEXT NOT NULL,
    uf CHAR(2) NOT NULL,
    population BIGINT NOT NULL,
    population_density DOUBLE PRECISION NOT NULL,
    municipality_count INTEGER NOT NULL,
    need_score DOUBLE PRECISION NOT NULL,
    capacity_score DOUBLE PRECISION NOT NULL,
    mismatch_score DOUBLE PRECISION NOT NULL,
    suicide_percentile DOUBLE PRECISION NOT NULL,
    psychiatric_admission_percentile DOUBLE PRECISION NOT NULL,
    caps_percentile DOUBLE PRECISION NOT NULL,
    beds_percentile DOUBLE PRECISION NOT NULL,
    psychiatrist_fte_percentile DOUBLE PRECISION NOT NULL,
    need_high BOOLEAN NOT NULL,
    capacity_low BOOLEAN NOT NULL,
    mismatch_marked_positive BOOLEAN NOT NULL,
    capacity_component_low BOOLEAN NOT NULL,
    spatial_hh_mismatch BOOLEAN NOT NULL,
    caps_low BOOLEAN NOT NULL,
    beds_low BOOLEAN NOT NULL,
    psychiatrist_fte_low BOOLEAN NOT NULL,
    zero_registered_beds BOOLEAN NOT NULL,
    small_suicide_count BOOLEAN NOT NULL,
    matched_signal_families INTEGER NOT NULL,
    suicide_contribution DOUBLE PRECISION NOT NULL,
    admissions_contribution DOUBLE PRECISION NOT NULL,
    caps_contribution DOUBLE PRECISION NOT NULL,
    beds_contribution DOUBLE PRECISION NOT NULL,
    psychiatrist_contribution DOUBLE PRECISION NOT NULL,
    decomposition_sum DOUBLE PRECISION NOT NULL,
    data_quality_flags TEXT[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (release_id, intelligence_version, health_region_code),
    FOREIGN KEY (release_id, geography_version)
        REFERENCES meta.releases (release_id, geography_version),
    FOREIGN KEY (geography_version, health_region_code)
        REFERENCES geo.health_regions (geography_version, health_region_code),
    CHECK (matched_signal_families BETWEEN 0 AND 5),
    CHECK (
        matched_signal_families =
        need_high::int +
        capacity_low::int +
        mismatch_marked_positive::int +
        capacity_component_low::int +
        spatial_hh_mismatch::int
    ),
    CHECK (abs(decomposition_sum - mismatch_score) <= 1e-12)
);

CREATE TABLE IF NOT EXISTS analytics.health_region_peers (
    release_id TEXT NOT NULL,
    peer_method_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    peer_health_region_code VARCHAR(5) NOT NULL,
    peer_rank INTEGER NOT NULL,
    structural_distance DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (release_id, peer_method_version, health_region_code, peer_rank),
    UNIQUE (release_id, peer_method_version, health_region_code, peer_health_region_code),
    FOREIGN KEY (release_id, health_region_code)
        REFERENCES analytics.health_region_metrics (release_id, health_region_code),
    FOREIGN KEY (release_id, peer_health_region_code)
        REFERENCES analytics.health_region_metrics (release_id, health_region_code),
    CHECK (health_region_code <> peer_health_region_code),
    CHECK (peer_rank BETWEEN 1 AND 10),
    CHECK (structural_distance >= 0)
);

CREATE TABLE IF NOT EXISTS analytics.health_region_peer_benchmarks (
    release_id TEXT NOT NULL,
    peer_method_version TEXT NOT NULL,
    health_region_code VARCHAR(5) NOT NULL,
    metric_id TEXT NOT NULL,
    target_value DOUBLE PRECISION NOT NULL,
    peer_n_observed INTEGER NOT NULL,
    peer_median DOUBLE PRECISION,
    peer_q1 DOUBLE PRECISION,
    peer_q3 DOUBLE PRECISION,
    peer_min DOUBLE PRECISION,
    peer_max DOUBLE PRECISION,
    relative_to_peer_iqr TEXT,
    insufficient_reason TEXT,
    PRIMARY KEY (release_id, peer_method_version, health_region_code, metric_id),
    FOREIGN KEY (release_id, health_region_code)
        REFERENCES analytics.health_region_metrics (release_id, health_region_code),
    CHECK (peer_n_observed BETWEEN 0 AND 10),
    CHECK (
        relative_to_peer_iqr IS NULL OR
        relative_to_peer_iqr IN (
            'BELOW_PEER_IQR',
            'WITHIN_PEER_IQR',
            'ABOVE_PEER_IQR'
        )
    )
);

CREATE INDEX IF NOT EXISTS intelligence_release_signal_idx
    ON analytics.health_region_intelligence (
        release_id,
        intelligence_version,
        matched_signal_families DESC,
        mismatch_score DESC,
        health_region_code
    );

CREATE INDEX IF NOT EXISTS intelligence_release_uf_idx
    ON analytics.health_region_intelligence (release_id, intelligence_version, uf);

CREATE INDEX IF NOT EXISTS peers_target_idx
    ON analytics.health_region_peers (release_id, peer_method_version, health_region_code);

CREATE INDEX IF NOT EXISTS benchmarks_target_idx
    ON analytics.health_region_peer_benchmarks (
        release_id,
        peer_method_version,
        health_region_code
    );

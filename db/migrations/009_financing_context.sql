CREATE TABLE IF NOT EXISTS analytics.health_region_financing (
    financing_version TEXT NOT NULL,
    siops_snapshot_id TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    health_region_code VARCHAR(5) NOT NULL,
    municipalities_expected INTEGER NOT NULL CHECK (municipalities_expected >= 0),
    municipalities_observed INTEGER NOT NULL CHECK (municipalities_observed >= 0),
    population_expected BIGINT NOT NULL CHECK (population_expected > 0),
    population_covered BIGINT,
    coverage_share DOUBLE PRECISION NOT NULL CHECK (coverage_share BETWEEN 0 AND 1),
    coverage_population_share DOUBLE PRECISION CHECK (coverage_population_share BETWEEN 0 AND 1),
    total_health_expenditure_brl NUMERIC(20, 2),
    health_expenditure_per_capita_brl NUMERIC(20, 2),
    headline_available BOOLEAN NOT NULL,
    quality_flags TEXT[] NOT NULL DEFAULT '{}',
    source_period VARCHAR(2) NOT NULL,
    source_indicator TEXT NOT NULL,
    PRIMARY KEY (financing_version, year, health_region_code),
    CHECK (municipalities_observed <= municipalities_expected),
    CHECK (headline_available = (coverage_share = 1 AND total_health_expenditure_brl IS NOT NULL)),
    CHECK (headline_available OR total_health_expenditure_brl IS NULL)
);

CREATE INDEX IF NOT EXISTS financing_year_region_idx
    ON analytics.health_region_financing (year, health_region_code);

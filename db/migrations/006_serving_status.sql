CREATE TABLE IF NOT EXISTS meta.serving_database_status (
    release_id TEXT PRIMARY KEY REFERENCES meta.releases (release_id),
    serving_database_status TEXT NOT NULL,
    validated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (serving_database_status IN ('VALIDATED_LOCAL'))
);

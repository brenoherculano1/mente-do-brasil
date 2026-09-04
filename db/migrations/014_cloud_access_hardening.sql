-- The browser does not access Supabase Data API tables for this application.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON SCHEMA meta, geo, analytics, serving, web FROM anon;
        REVOKE ALL ON ALL TABLES IN SCHEMA meta, geo, analytics, serving, web FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON SCHEMA meta, geo, analytics, serving, web FROM authenticated;
        REVOKE ALL ON ALL TABLES IN SCHEMA meta, geo, analytics, serving, web FROM authenticated;
    END IF;
END
$$;

ALTER DEFAULT PRIVILEGES IN SCHEMA meta, geo, analytics, serving, web
    REVOKE ALL ON TABLES FROM PUBLIC;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mente_do_brasil_api') THEN
        REVOKE CREATE ON SCHEMA public FROM mente_do_brasil_api;
        EXECUTE format(
            'REVOKE TEMPORARY ON DATABASE %I FROM mente_do_brasil_api',
            current_database()
        );
    END IF;
END
$$;

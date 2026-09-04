-- The public API never needs temporary objects; PostgreSQL grants TEMP to PUBLIC by default.
DO $$
BEGIN
    EXECUTE format('REVOKE TEMPORARY ON DATABASE %I FROM PUBLIC', current_database());
END
$$;

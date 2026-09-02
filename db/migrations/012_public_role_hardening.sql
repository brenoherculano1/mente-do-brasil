-- The public API never needs temporary objects; PostgreSQL grants TEMP to PUBLIC by default.
REVOKE TEMPORARY ON DATABASE mente_do_brasil FROM PUBLIC;

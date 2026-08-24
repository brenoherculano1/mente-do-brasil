# Serving Database

This folder contains SQL migrations for the local Mente do Brasil PostgreSQL /
PostGIS serving database.

Run migrations in filename order against an empty local database:

```bash
python scripts/load_serving_database.py
```

The loader applies the migrations, verifies canonical hashes, imports the locked
canonical release, and validates row counts, geometry, LISA locks, flags, and
immutability. It does not recalculate scientific metrics.

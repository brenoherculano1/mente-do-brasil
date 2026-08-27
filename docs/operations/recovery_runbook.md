# Recovery Runbook

## Source of Truth

The scientific source of truth is the versioned canonical and metadata artifacts
in the repository:

- `metadata/releases/MDB_ANALYTICAL_2024_1*.yaml`
- `data/canonical/MDB_ANALYTICAL_2024_1/`
- `metadata/canonical/`
- `metadata/web_geometry/`

The serving PostgreSQL database is operational infrastructure and is
rebuildable. A database backup helps operational recovery, but it does not
replace the canonical analytical source of truth.

## If the Database Disappears

1. Confirm Docker/Postgres or the future DB provider is available.
2. Rebuild the serving database from canonical artifacts:
   `scripts/rebuild_serving_db.sh mdb_rebuild_<timestamp>`.
3. Validate with `scripts/validate_serving_database.py`.
4. Confirm locked counts and known values:
   health regions 439, municipalities 5570, profiles 439, map rows 439,
   geometry 439, AC 3, SP 62, DF 1, 12001 Alto Acre, and 1100015 to 11005.
5. Point staging/production only after validation passes.

## If the API Breaks

1. Check FastAPI `/health` and `/ready`.
2. Check Next `/healthz` and `/readyz`.
3. Use `X-Request-ID` from the failing response to correlate Next and FastAPI logs.
4. Run API regression: `PATH="$PWD/.venv/bin:$PATH" ./.venv/bin/python -m pytest tests/api/test_api_contract.py -q`.

## Backup

Create an operational serving DB backup:

```bash
scripts/backup_serving_db.sh
```

The script writes a timestamped custom compressed `pg_dump` file under
`backups/serving_db/` by default. Dumps are not committed.

Suggested future retention for production, because the serving DB is rebuildable:
7 daily backups plus 4 weekly backups. Provider-managed backups can reinforce
this procedure, but should not be the only recovery path.

## Restore

Restore only to an explicit target database:

```bash
scripts/restore_serving_db.sh backups/serving_db/<dump>.dump mdb_restore_<timestamp>
```

By default the script refuses target names that do not begin with
`mdb_restore_`. Restoring over production requires an explicit override and a
human release decision.

Validate the restored database:

```bash
MDB_DB_NAME=mdb_restore_<timestamp> ./.venv/bin/python scripts/validate_serving_database.py
```

## Rebuild

Run the deterministic loader against an explicit target database:

```bash
scripts/rebuild_serving_db.sh mdb_rebuild_<timestamp>
```

The wrapper uses the existing serving DB loader and validation scripts. It does
not recalculate science or change canonical artifacts.

## Rollback

Application rollback should use a previous Git commit or release image known to
be compatible with `MDB_ANALYTICAL_2024_1`. Rollbacks must not silently point to
an incompatible analytical release.

The current public release status remains `NOT_RELEASED`; changing it requires a
separate human-approved release step.

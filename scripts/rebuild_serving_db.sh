#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/rebuild_serving_db.sh <target_db> [--allow-production-target]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DB="$1"
ALLOW="${2:-}"

if [[ "$TARGET_DB" != mdb_rebuild_* && "$ALLOW" != "--allow-production-target" ]]; then
  echo "refusing_target_db_without_safe_prefix" >&2
  exit 2
fi

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
# Never create or drop a database until the complete artifact gate is satisfied.
./.venv/bin/python scripts/preflight_local_artifacts.py
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" dropdb -U "$POSTGRES_USER" --if-exists "$1"' sh "$TARGET_DB"
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" createdb -U "$POSTGRES_USER" "$1"' sh "$TARGET_DB"
MDB_DB_NAME="$TARGET_DB" ./.venv/bin/python scripts/load_serving_database.py
MDB_DB_NAME="$TARGET_DB" ./.venv/bin/python scripts/load_serving_database_release.py
MDB_DB_NAME="$TARGET_DB" ./.venv/bin/python scripts/build_web_geometry.py
MDB_DB_NAME="$TARGET_DB" ./.venv/bin/python scripts/load_advanced_territorial.py
MDB_DB_NAME="$TARGET_DB" ./.venv/bin/python scripts/grant_runtime_access.py
MDB_DB_NAME="$TARGET_DB" ./.venv/bin/python scripts/validate_rebuilt_phase3.py
printf 'rebuild_target=%s\n' "$TARGET_DB"
printf 'rebuild_exit=0\n'

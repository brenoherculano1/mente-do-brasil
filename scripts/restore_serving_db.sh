#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: scripts/restore_serving_db.sh <dump_file> <target_db> [--allow-production-target]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DUMP_FILE="$1"
TARGET_DB="$2"
ALLOW="${3:-}"

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "dump_file_not_found" >&2
  exit 2
fi

if [[ "$TARGET_DB" != mdb_restore_* && "$ALLOW" != "--allow-production-target" ]]; then
  echo "refusing_target_db_without_safe_prefix" >&2
  exit 2
fi

cd "$ROOT"
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" dropdb -U "$POSTGRES_USER" --if-exists "$1"' sh "$TARGET_DB"
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" createdb -U "$POSTGRES_USER" "$1"' sh "$TARGET_DB"
docker compose exec -T postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -U "$POSTGRES_USER" -d "$1" --no-owner --no-acl' sh "$TARGET_DB" < "$DUMP_FILE"
printf 'restore_target=%s\n' "$TARGET_DB"
printf 'restore_exit=0\n'

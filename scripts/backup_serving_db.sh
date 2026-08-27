#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT/backups/serving_db}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="$OUT_DIR/mente_do_brasil_serving_${STAMP}.dump"

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR" 2>/dev/null || true

cd "$ROOT"
docker compose exec -T postgres sh -lc \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -Z 6 --no-owner --no-acl' \
  > "$OUT_FILE"
chmod 600 "$OUT_FILE" 2>/dev/null || true

SIZE="$(wc -c < "$OUT_FILE" | tr -d ' ')"
SHA="$(shasum -a 256 "$OUT_FILE" | awk '{print $1}')"
printf 'backup_file=%s\n' "$OUT_FILE"
printf 'size_bytes=%s\n' "$SIZE"
printf 'sha256=%s\n' "$SHA"
printf 'format=pg_dump_custom_compressed\n'

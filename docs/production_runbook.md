# Production runbook

## Architecture

`Internet -> Vercel CDN/web -> Next.js same-origin facade -> token-protected FastAPI -> Supabase Postgres/PostGIS`.

The web and API are separate Vercel projects in the dedicated paid team. Both run in
`gru1`. The database is a dedicated Supabase Pro project in `sa-east-1`. Runtime traffic
uses Supavisor transaction mode with prepared statements disabled, a pool bounded at
four connections, TLS `verify-full`, and the `mente_do_brasil_api` read-only role.

Non-secret provider identifiers belong in
`metadata/production/provider_inventory_v1.yaml`. Secrets exist only in provider
environment settings. The browser never receives database credentials,
`MDB_INTERNAL_API_TOKEN`, or Supabase privileged keys.

## Deploy

1. Run `.github/workflows/ci.yml` on the exact candidate commit.
2. Build staging from locked migrations and artifacts; validate it completely.
3. Deploy API and web previews, run external QA, then promote the exact validated
   deployments. Do not rebuild during promotion.
4. Record immutable deployment IDs and commit in the deployment manifest.
5. Attach the domain only after the pre-release gate passes.

## Health and release checks

- `/healthz`: Next.js process is alive.
- `/readyz`: protected backend, database, required views, and current release are ready.
- `/api/public/v1/releases`: Open Data and analytical release identifiers are correct.
- Download the public ZIP and verify 914294 bytes and SHA-256
  `2b3b1fc749bfd71181115c2cd9467bf26cb1572bd0c0e9687dabccffab3775bc`.

## Logs and routine operation

Use Vercel deployment/runtime logs, Supabase Postgres/platform logs, and GitHub Actions
monitor histories. Investigate 5xx clusters, readiness failure, connection exhaustion,
permissions errors, slow queries, and integrity-monitor failures. No fourth monitoring
vendor is part of version 1.0.

Redeploy or restart only from a known passing commit. Never alter an immutable Open Data
release in place. Common response procedures are in `docs/incident_response.md`; rollback
and recovery are in their dedicated runbooks.

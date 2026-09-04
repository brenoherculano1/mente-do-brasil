# Rollback runbook

## Web and API

Use Vercel's rollback or promote operation to point the production alias at the exact
previous validated deployment. Confirm the deployment commit and environment scope
before changing aliases. Re-run `/healthz`, `/readyz`, representative routes, direct
backend denial, and release hash checks after rollback.

## Database

Prefer forward-compatible corrective migrations. If recovery is required, build or
restore into a separate project/database, validate every locked count and scientific
identity, then switch the server-side connection. Do not destructively restore over the
production database and do not delete historical release rows.

Open Data releases are immutable. A defective new release is superseded by a new version;
`MDB_OPEN_DATA_2024_1` is never repacked, edited, or deleted to simulate rollback.

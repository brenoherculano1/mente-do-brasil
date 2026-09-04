# Backup and restore runbook

## Recovery mechanisms

1. Supabase Pro daily provider backups with the actual dashboard retention recorded in
   the provider inventory. PITR is not purchased or claimed.
2. Deterministic rebuild from locked migrations, canonical artifacts, geography, and
   advanced territorial artifacts. This is the primary independently controlled path.

## Restore drill

Create a temporary isolated Supabase project or provider-supported duplicate. Restore or
rebuild there, never over production. Use the direct/admin connection for migrations and
load; use the transaction pooler only for application traffic. Credentials are obtained
from the provider and stored only in local ignored environment files or provider secrets.

After recovery, run serving database validation, foundation validation, exact counts,
geometry validity/SRID, Moran/LISA locks, flags, advanced content identity, read-only role
tests, Data API denial, and application smoke tests. Record observed RPO and wall-clock RTO.
Delete or pause the temporary project after evidence is retained.

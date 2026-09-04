# Incident response

## Severity

- `SEV1`: entire site unavailable, confirmed privacy/raw-data leak, wrong scientific
  release publicly served, or data-integrity compromise.
- `SEV2`: critical route, API family, downloads, map, or readiness check unavailable;
  sustained major performance degradation.
- `SEV3`: isolated noncritical route, cosmetic issue, intermittent latency, or monitor
  warning without user-visible failure.

## Response sequence

1. Record UTC time, affected URL/deployment, reporter, and observed status without
   copying credentials or private request bodies.
2. Contain. For a disclosure or wrong-release incident, disable indexing/public ingress
   or roll back the web deployment immediately. Preserve evidence.
3. Inspect Vercel logs, deployment diff, GitHub CI/monitor results, Supabase logs, role
   permissions, and release hashes.
4. Restore the last known-good Vercel deployment or rebuild the database in a new target.
   Never overwrite production during diagnosis.
5. Re-run readiness, security, science, privacy, and immutable release gates.
6. Document cause, impact, correction, validation evidence, and preventive action.

For suspected exposed secrets, revoke/rotate in the provider first, then redeploy and
scan Git history. Never place the exposed value in an issue or audit package.

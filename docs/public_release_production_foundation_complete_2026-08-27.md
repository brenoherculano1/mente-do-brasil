# Mente do Brasil — Production Foundation Complete

## Scope

This phase closes application-side production foundation work for indexing,
robots, sitemap, canonical URLs, privacy, contact, security reporting,
structured logging, request correlation, health/readiness, backup, restore,
rebuild, recovery documentation, and public release configuration validation.

It does not deploy remotely, configure DNS, define dataset licensing, publish
downloads, expose a public API product, or add advanced product features.

## Scientific Revalidation

The first gate investigated the 11 skipped tests seen after Hardening 04. They
were caused by the local FastAPI service not running. With FastAPI available,
the locked scientific regression returned to `76 passed`.

## Indexing Architecture

`MDB_PUBLIC_INDEXING_ENABLED` defaults to disabled. Disabled, absent, false,
zero, no, and invalid values all keep indexing closed.

When indexing is enabled, `MDB_PUBLIC_SITE_URL` must be a valid HTTPS origin and
`MDB_PUBLIC_CONTACT_EMAIL` must be configured.

## Robots

Prelaunch robots disallow all crawling. Public-mode simulation allows crawling
and points to the sitemap generated from `MDB_PUBLIC_SITE_URL`.

## Sitemap

The sitemap is empty in prelaunch mode. In public mode it includes static pages,
27 state routes, and 439 region routes derived from the locked canonical
health-region Parquet artifact.

## Canonical URLs

Canonical metadata is prepared for home, methodology, data, about, privacy,
contact, state, and region pages. Lowercase state URLs redirect to uppercase
canonical routes.

## Dynamic-Route HTTP Semantics

Invalid state and region routes are expected to return HTTP 404 in production
serving. Lowercase state routes redirect to uppercase.

## Privacy Notice

`/privacidade` is a factual draft pre-release privacy notice. It states the
current product has no intentional analytics, tracking pixels, or marketing
cookies, uses aggregated public data, and does not provide patient-level data.

## Contact / Corrections

`/contato` prepares contact, correction, and security categories without a form,
database, response-time promise, or invented mailbox. Human contact email
configuration is still required before public release.

## Security Reporting

`/.well-known/security.txt` is prepared and returns 404/no-store until a site URL
and contact or security email are configured.

## Observability

Structured logs, request IDs, and health/readiness endpoints are prepared
without binding the project to an external provider.

## Request Correlation

Next emits and forwards `X-Request-ID`; FastAPI propagates it in responses. It
is for debugging correlation only.

## Health / Readiness

FastAPI exposes `/health` and `/ready`. Next exposes `/healthz` and `/readyz`.
Readiness fails closed when FastAPI is unavailable.

## Backup

`scripts/backup_serving_db.sh` creates a timestamped compressed custom-format
serving DB dump using Docker Compose and does not hardcode passwords.

## Restore Drill

The restore drill restores the backup into a temporary database and validates
locked counts and known values before cleanup.

## Rebuild

`scripts/rebuild_serving_db.sh` rebuilds a temporary serving DB using the
existing loader and validation scripts.

## Recovery Runbook

Operational recovery procedures are documented in
`docs/operations/recovery_runbook.md`.

## Public Release Config Validator

`scripts/validate_public_release_config.py` validates prelaunch and future
public modes without changing release status.

## Human Configuration Still Required

- `MDB_PUBLIC_CONTACT_EMAIL`
- `MDB_PUBLIC_SECURITY_EMAIL` if separate from contact
- actual staging/production provider
- actual monitoring provider
- actual database provider

## What Is Now Complete

Application-side production foundation is complete when validation passes:
indexing fail-closed, robots/sitemap/canonical prepared, privacy/contact routes
created, security reporting prepared, structured logs/request ID added,
health/readiness endpoints added, backup/restore/rebuild scripts and runbook
created, and public release config validation prepared.

## What Belongs to Future Product Phases

Advanced territorial intelligence, public API/downloads/licensing, remote
staging/production infrastructure, and final release remain future large phases.

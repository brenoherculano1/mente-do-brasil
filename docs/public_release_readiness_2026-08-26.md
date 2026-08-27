# Mente do Brasil - Public Release Readiness Audit

## Executive verdict

If we put the project on the internet today, would I release it?

NAO.

- The functional V1 is technically and scientifically strong, and all regression
  suites passed in this audit.
- The release remains correctly locked as `public_release_status: NOT_RELEASED`.
- No committed real secrets were found in tracked files or the audited Git
  history window.
- The operational API is read-only and SQL-injection-shaped inputs were rejected
  or safely parameterized.
- The browser-to-FastAPI exposure model was mitigated in the second
  public-release hardening round: browser data requests now use same-origin
  `/api/v1/...` paths through the Next runtime.
- `geometry_profile=full` was reachable on the operational API in the original
  audit and returned 146,130,129 bytes. This specific blocker was mitigated in
  the first public-release hardening round by blocking `full` by default.
- Security headers and operational FastAPI docs posture were mitigated in the
  third public-release hardening round. Rate limiting, production cache policy,
  remote staging/production infrastructure, human mailbox configuration, and
  explicit release approval are not complete.
- Public data downloads and a public API product are separate releases and are
  not ready because licensing/reuse, attribution/legal review, and API product
  controls are unresolved.

## Current V1 state

Starting locked commit:

`ab8e1c70d756eae54b4948538a62d85119e10154`

Release metadata remains:

- `release_status`: `VALIDATING`
- `quality_status`: `VALIDATED`
- `release_gate`: `PASS`
- `release_readiness`: `READY`
- `public_release_status`: `NOT_RELEASED`

Functional routes are locked:

- `/`
- `/regiao/[codigo]`
- `/metodologia`
- `/dados`
- `/sobre`
- `/estado/[uf]`

No release status value was changed in this audit.

## Recovery from interrupted audit

The audit resumed from a partially completed previous run. The repository was at
the expected locked commit, but the working tree contained audit logs and one
legacy screenshot rewritten by E2E execution. The audit classified this as a
safe recovery case: partial audit artifacts were inspected, reproducible logs
were regenerated where needed, and the legacy screenshot was treated as a test
artifact outside this audit's scope.

No production code, scientific code, API contract, Docker architecture, release
metadata, DNS, deployment, or public status was changed.

## Website release gate

`WEBSITE_RELEASE_READY: NO`

`APPLICATION_PRODUCTION_FOUNDATION: COMPLETE`

The application-side production foundation is complete. The V1 website should
still not be made public until remote staging/production infrastructure, human
mailbox configuration, monitoring provider setup, and explicit release approval
are complete.

## Public data release gate

`PUBLIC_DATA_RELEASE_READY: NO`

The current website can remain an informational product without data downloads,
but public downloadable datasets or public reuse require a human licensing
decision and source attribution/legal review.

## Public API product gate

`PUBLIC_API_PRODUCT_READY: NO`

The existing FastAPI service is an operational backend for the website, not a
public API product. A public API product would require explicit API docs, usage
terms, abuse controls, versioning policy, possibly API keys, and support/SLA
decisions. It is not required for V1 website launch.

## Security findings

### Summary by audit dimension

| Dimension | Status | Rationale |
|---|---:|---|
| Application security | PASS | XSS, SQL tests, baseline security headers, and same-origin API rate limiting pass locally. |
| Infrastructure security | WARNING | Local DB is bound to `127.0.0.1`; production architecture is not defined. |
| API exposure | PASS | `full` geometry is blocked by default, browser requests use same-origin `/api/v1`, FastAPI docs are off by default, rate limits are active, and API cache policy is explicit. |
| Production deployment readiness | BLOCKER | Application foundation is complete, but remote staging/production infrastructure and release approval do not exist yet. |
| Privacy / data collection | HUMAN_CONFIGURATION_REQUIRED | Dataset is aggregate-only and factual privacy/contact pages exist; public mailbox configuration is still required. |
| Legal / licensing / attribution | HUMAN_DECISION_REQUIRED | Public data license and attribution/legal review are unresolved. |
| Reliability / observability / recovery | PASS application-side | Structured logs, request IDs, health/ready endpoints, backup/restore/rebuild scripts, and recovery runbook are prepared. |
| Product / SEO / disclosure | PASS application-side | Indexing fail-closed, robots, sitemap, canonical metadata, OG/Twitter metadata, privacy, and contact routes are prepared. |

### Findings matrix

| Requirement | Status | Evidence | Severity | Action | Owner |
|---|---:|---|---:|---|---|
| Secret exposure | PASS | `audit_results/secret_scan.txt` | REQUIRED_BEFORE_LAUNCH | Keep `.env` ignored; rotate if future secret appears. | CODEX |
| Git history secrets | PASS | `audit_results/git_history_secret_scan.txt` | REQUIRED_BEFORE_LAUNCH | Repeat before public repo/deploy. | CODEX |
| Frontend dependency audit | PASS | `audit_results/dependency_audit_frontend.txt` | REQUIRED_BEFORE_LAUNCH | Re-run before deploy. | CODEX |
| Python dependency audit | PASS | `audit_results/dependency_audit_python.txt` | REQUIRED_BEFORE_LAUNCH | Re-run before deploy. | CODEX |
| XSS sinks | PASS | `audit_results/xss_audit.txt` | REQUIRED_BEFORE_LAUNCH | Preserve `setDOMContent` + `textContent`. | CODEX |
| Client bundle secret exposure | PASS | `audit_results/client_env_exposure.txt` | REQUIRED_BEFORE_LAUNCH | Keep only non-secret `NEXT_PUBLIC_*`. | CODEX |
| SQL safety | PASS | `audit_results/sql_safety_public_release.txt` | REQUIRED_BEFORE_LAUNCH | Keep validation and parameterized SQL. | CODEX |
| DB read-only runtime | PASS | `audit_results/readonly_db_validation.txt` | REQUIRED_BEFORE_LAUNCH | Use read-only runtime role in production. | CODEX |
| DB network exposure | PASS local | `audit_results/db_network_validation.txt` | REQUIRED_BEFORE_LAUNCH | Production Postgres must not be public. | CODEX |
| CORS production origin | PASS | `audit_results/cors_after_same_origin.txt` | PREPARED | Normal browser path is same-origin; FastAPI wildcard remains rejected. | CODEX |
| Direct browser API model | PASS | `audit_results/browser_network_same_origin.txt` | CLOSED | Browser data requests go to the Next origin `/api/v1/*`; direct FastAPI browser requests were 0. | CODEX |
| FastAPI docs exposure | PASS | `audit_results/fastapi_docs_posture.txt` | CLOSED | Docs, Redoc, and OpenAPI HTTP endpoints are disabled by default and require explicit server-side opt-in. | CODEX |
| Full geometry exposure | PASS | `audit_results/api_regression.txt`, `audit_results/full_geometry_policy_validation.txt` | CLOSED | `full` is blocked by default before the heavy query path. | CODEX |
| Detail geometry exposure | WARNING | `audit_results/geometry_exposure_audit.txt` | RECOMMENDED | Restrict or heavily cache if not needed. | CODEX |
| Rate limiting | PASS | `audit_results/rate_limit_validation.txt`, `audit_results/rate_limit_policy.txt` | MITIGATED | Preserve class-based limits and document any future edge reinforcement separately. | CODEX |
| Cache/compression | PASS | `audit_results/cache_policy.txt`, `audit_results/overview_cache_validation.txt` | MITIGATED | Preserve API Cache-Control policy; future CDN may honor these headers. | CODEX |
| Security headers | PASS | `audit_results/security_headers_validation.txt` | CLOSED | CSP, HSTS, nosniff, Referrer-Policy, Permissions-Policy, and X-Frame-Options are emitted by Next. | CODEX |
| Privacy dataset | PASS | `audit_results/privacy_dataset_audit.txt` | REQUIRED_BEFORE_LAUNCH | Keep aggregate-only data contract. | CODEX |
| Website trackers/cookies | PASS | `audit_results/privacy_website_audit.txt` | RECOMMENDED | Recheck if analytics are added. | CODEX |
| Third-party network requests | PASS | `audit_results/third_party_requests.txt` | RECOMMENDED | Keep no external basemap/token dependency. | CODEX |
| Privacy policy/disclosure | PASS application-side | `audit_results/privacy_validation.txt`, `metadata/legal/privacy_notice.yaml` | CONFIG_REQUIRED_BEFORE_RELEASE | Configure human contact mailbox before public release. | HUMAN |
| Dataset license | HUMAN_DECISION_REQUIRED | `audit_results/licensing_attribution_audit.txt` | BLOCKER for data downloads | Choose license/reuse terms. | HUMAN |
| Source attribution/legal review | EXTERNAL_RESEARCH_REQUIRED | `audit_results/licensing_attribution_audit.txt` | REQUIRED_BEFORE_DATA_RELEASE | Verify DATASUS/SIM/SIH/CNES/IBGE attribution/reuse obligations. | EXTERNAL_RESEARCH |
| Contact/correction channel | HUMAN_DECISION_REQUIRED | `audit_results/contact_correction_audit.txt` | REQUIRED_BEFORE_LAUNCH | Provide contact/correction/security channel. | HUMAN |
| SEO basics | PASS application-side | `audit_results/canonical_validation.txt`, `audit_results/http_public_mode_validation.txt` | CONFIG_REQUIRED_BEFORE_RELEASE | Keep indexing disabled until explicit release approval and production URL configuration are complete. | CODEX |
| Robots/indexing | PASS application-side | `audit_results/robots_validation.txt` | CONFIG_REQUIRED_BEFORE_RELEASE | Keep indexing disabled until explicit public release approval. | HUMAN + CODEX |
| Sitemap | PASS application-side | `audit_results/sitemap_validation.txt` | CONFIG_REQUIRED_BEFORE_RELEASE | Public-mode sitemap is ready with 27 states and 439 regions; activate only after final public release approval. | HUMAN + CODEX |
| Observability | PASS application-side | `audit_results/health_ready_validation.txt`, `docs/operations/observability.md` | PROVIDER_REQUIRED_BEFORE_RELEASE | Configure future remote provider alerts. | CODEX + HUMAN |
| Backup/recovery | PASS application-side | `audit_results/backup_validation.txt`, `audit_results/restore_drill.txt`, `audit_results/rebuild_drill.txt` | PROVIDER_REQUIRED_BEFORE_RELEASE | Configure remote/provider backup policy in deployment phase. | CODEX + HUMAN |
| Rebuildability | PASS | `audit_results/rebuildability_recovery_audit.txt` | REQUIRED_BEFORE_LAUNCH | Preserve deterministic rebuild path. | CODEX |
| README public consistency | WARNING | `audit_results/readme_public_consistency_audit.txt` | RECOMMENDED | Update stale public-facing README language. | CODEX |

## Repository / secret findings

No committed real secrets were found in tracked files or the audited Git history
window. `.env` is ignored by Git. `.env.example` and `web/.env.example` are
tracked and contain placeholders only.

Reviewed keyword hits included expected code references to password variables
and DSN construction. Those are not committed secret values.

## Dependency findings

Frontend:

- Command: `npm audit --omit=dev`
- Critical: 0
- High: 0
- Moderate: 0
- Low: 0

Python:

- Method: `uv export` + isolated `uvx pip-audit --disable-pip --no-deps`
- Known vulnerabilities: 0
- No lockfile or project dependencies were modified.

## API exposure findings

The audited OpenAPI surface contains:

- `GET /health`
- `GET /ready`
- `GET /api/v1/releases`
- `GET /api/v1/releases/{release_id}`
- `GET /api/v1/indicators`
- `GET /api/v1/indicators/{indicator_id}`
- `GET /api/v1/health-regions`
- `GET /api/v1/health-regions/{health_region_code}`
- `GET /api/v1/states/{uf}`
- `GET /api/v1/map/health-regions`
- `GET /api/v1/municipalities/{municipality_code_ibge}/health-region`
- `GET /api/v1/ufs`

The frontend now uses same-origin `/api/v1/...` browser requests through a
single Next Route Handler at `web/app/api/v1/[...path]/route.ts`. The browser no
longer needs `NEXT_PUBLIC_MDB_API_BASE_URL`.

FastAPI docs were enabled locally during the original audit:

- `/docs`: 200
- `/redoc`: 200
- `/openapi.json`: 200

They are now disabled by default through `MDB_API_ENABLE_DOCS=false`:

- `/docs`: 404 by default.
- `/redoc`: 404 by default.
- `/openapi.json`: 404 by default.

Internal/local docs access requires explicit `MDB_API_ENABLE_DOCS=true`.
Programmatic `app.openapi()` remains available for internal tooling.

## Geometry endpoint risk

Frontend V1 uses:

- National map: `overview`
- State map: `overview`

Frontend V1 does not use:

- `detail`
- `full`

Audited geometry sizes:

- `overview`: 756,156 bytes JSON; 200,382 bytes gzip in API validation.
- `detail`: 2,763,517 bytes JSON.
- `full`: 146,130,129 bytes JSON; 33.5 seconds in the original
  public-readiness API regression before hardening.

`full` was a CRITICAL public operational API risk because it created bandwidth
amplification, worker exhaustion, memory pressure, accidental client request
risk, and denial-of-service exposure. It is now blocked by default before the
heavy query path.

Recommended policy:

Keep `full` blocked on the production operational API unless explicitly enabled
server-side for internal validation. Keep full scientific geometry for
internal/admin use or future versioned download after licensing, caching, and
distribution terms are decided. Keep V1 website maps on `overview`.

## Database / infrastructure

Local PostgreSQL exposure is correct:

- Docker Compose maps `127.0.0.1:5432 -> 5432/tcp`.
- `lsof` confirmed listener on `127.0.0.1:5432`.

The API runtime role is `mente_do_brasil_api`.

Read-only checks:

- `default_transaction_read_only`: `on`
- `INSERT`: rejected.
- `UPDATE`: rejected.
- `DELETE`: rejected before mutation.
- `DDL`: rejected.

Production must preserve separate credentials:

- Runtime API role: read-only.
- Migration/admin role: separate, not used by the runtime.
- Database: private network only, not internet-exposed.

Container findings:

- Compose has local loopback port binding, named volume, healthcheck, and
  `restart: unless-stopped`.
- The local PostGIS image is versioned as
  `mente-do-brasil-postgis:18-3.6.4`.
- The Dockerfile pins PostgreSQL 18 PostGIS package versions.
- Container user is not explicitly changed from the base Postgres image.
- Production image digest pinning and non-root/runtime policy should be decided
  in the deployment hardening step.

## Privacy

Scientific/API data are territorial aggregate data. The canonical schemas do not
contain patient-level fields, CPF, email, phone, address, medical record, or
patient identifiers.

The website currently has no detected cookies, `localStorage`, `sessionStorage`,
Google Analytics, Meta Pixel, Hotjar, Sentry, external fonts, Mapbox token, OSM
tile dependency, or external analytics scripts.

Because a public site still produces technical server logs, a minimal privacy
disclosure and contact/correction channel should be defined before launch.

## Licensing / attribution

The public data reuse license is not defined. The data page states that the
license for the first public release will be defined before publication.

This blocks public downloads and public data/API reuse, but does not necessarily
block making the website visible if no downloads are offered and the public
copy remains clear.

Source attribution exists in repository metadata for DATASUS, SIM, SIH/SUS,
CNES, and IBGE-related sources. Exact public attribution and legal reuse
language should be reviewed before public data release.

Manuscript status remains limited to:

`Status: manuscrito submetido ao Health & Place.`

Do not claim accepted, published, in press, or peer reviewed.

## SEO / indexing

Observed:

- `lang="pt-BR"` present.
- Viewport metadata present.
- Titles and descriptions present.
- `/estado/AC` has canonical uppercase behavior.

Gaps:

- `robots.txt`: not implemented.
- `sitemap.xml`: not implemented.
- OpenGraph/Twitter cards: not implemented.
- Favicon/app icon coverage: not confirmed.
- Canonical URLs are incomplete outside the state route.

If deployed accidentally today, search engines could index public pages by
default because no robots/indexing policy is configured.

## Reliability / observability

Rebuildability is strong: the serving database is derived from locked raw/import
manifests, canonical release metadata, migrations, hashes, and the serving
loader. If the serving DB disappears, it can be rebuilt deterministically from
the locked artifacts.

Missing production controls:

- Structured logs.
- Error monitoring.
- Uptime monitor.
- Metrics/tracing.
- Alerting.
- Production backup/restore or rebuild drill.
- Deployment rollback procedure.

Minimum V1 should be deliberately small: health checks for `/health` and
`/ready`, basic error alerting, log retention/redaction, managed database
backup, and one restore/rebuild rehearsal.

## Performance baseline

Local production-mode baseline, single sample:

- `/health`: 37.6 ms.
- `/ready`: 8.4 ms.
- National overview map: 72.2 ms, 756,156 bytes.
- State AC: 4.5 ms.
- State SP: 5.6 ms.
- Profile 12001: 3.6 ms.
- Municipality lookup: 3.7 ms.
- Home page: 53.1 ms.
- State AC page: 31.7 ms.

This is local evidence only, not an internet benchmark.

## Deployment architecture recommendation

Recommended architecture:

Use the implemented same-origin public website architecture:

- User-facing origin: `https://mentedobrasil.com.br`.
- Next runtime serves the web app.
- FastAPI runs as a private operational backend.
- Public app calls go through same-origin `/api/v1/...` Next operational
  ingress.
- PostgreSQL/PostGIS is private-network only.
- CDN/reverse proxy handles TLS, compression, cache, rate limiting, request size
  controls, and security headers.
- Runtime API credentials are read-only.
- Migration/admin credentials are separate and never used by the web runtime.
- Logs, health checks, and backups are configured before flipping release
  status.

This replaces the browser-to-separate-FastAPI-host model, simplifies CORS,
hides backend topology, centralizes future cache/rate-limit controls, keeps the
product cohesive, and remains reversible.

Cost class: LOW to MODERATE for V1 if using managed Next/container/Postgres/CDN
components and avoiding enterprise observability.

## Required environment variables

Required variables found:

1. `MDB_API_DB_PASSWORD`
2. `MDB_API_DB_USER`
3. `MDB_API_HOST`
4. `MDB_API_PORT`
5. `MDB_DB_HOST`
6. `MDB_DB_NAME`
7. `MDB_DB_PASSWORD`
8. `MDB_DB_PORT`
9. `MDB_DB_USER`
10. `MDB_DEFAULT_RELEASE_ID`
11. `MDB_IMPORTED_AT`
12. `MDB_API_INTERNAL_BASE_URL`

Secret variables:

- `MDB_API_DB_PASSWORD`
- `MDB_DB_PASSWORD`

`MDB_API_INTERNAL_BASE_URL` is server-only. It is required for production
runtime API ingress and server-rendered API requests. `NEXT_PUBLIC_MDB_API_BASE_URL`
is removed from the production frontend runtime requirement.

## Static / dynamic rendering

Full static export is not currently possible.

Routes from production build:

- `/`: dynamic server-rendered on demand and client map dependent.
- `/estado/[uf]`: dynamic server-rendered on demand plus client map request.
- `/regiao/[codigo]`: dynamic server-rendered on demand.
- `/metodologia`: static.
- `/dados`: static.
- `/sobre`: static.

Next server runtime is required for the current V1.

## Threat model

| Asset | Threat | Existing control | Missing control | Severity |
|---|---|---|---|---|
| Scientific integrity | Silent recalculation | Locked regressions and release hashes | Production release flip procedure | HIGH |
| Scientific integrity | Release mixing | Release IDs and API tests | Public release operational checklist | MEDIUM |
| Scientific integrity | NULL to zero | Regression tests and copy discipline | Continue tests for new pages | MEDIUM |
| API availability | DoS via full geometry | `full` blocked by default before heavy query | Rate limits and response size gate | MEDIUM |
| API availability | Scraping heavy endpoints | Read-only API | Edge throttling and cache | HIGH |
| Database | Mutation through API role | Read-only role and transaction mode | Production role separation proof | HIGH |
| Credentials | Secret leak | `.env` ignored, secret scan pass | Production secret manager | HIGH |
| Browser users | XSS | `setDOMContent`, validation, tests, CSP | Continue avoiding HTML injection | LOW |
| Website availability | Runtime failure | `/health` and `/ready` | Uptime alerts and rollback | MEDIUM |
| Product readiness | Premature indexing | None | Robots/staging/prod index policy | MEDIUM |

## Release checklist

Required before website launch:

- [x] Block/restrict `geometry_profile=full`.
- [x] Choose same-origin production architecture.
- [x] Configure production CORS or remove cross-origin need through proxy.
- [x] Disable/protect FastAPI docs if backend is reachable.
- [x] Add production security headers.
- [x] Add endpoint-class rate limiting.
- [x] Add API cache/compression policy.
- [x] Configure robots/indexing fail-closed with public-mode switch.
- [ ] Define contact/correction/security reporting channel.
- [x] Add minimal factual privacy disclosure.
- [x] Add application health/readiness and structured-log foundation.
- [x] Add backup/restore/rebuild scripts and local restore/rebuild drills.
- [ ] Configure human contact/security mailbox.
- [ ] Configure remote staging/production infrastructure and monitoring provider.
- [ ] Run full regression and staging smoke test.
- [ ] Obtain explicit human public release decision.

Required before public data/API release:

- [ ] Decide dataset license.
- [ ] Complete source attribution/legal review.
- [ ] Define citation/reuse language.
- [ ] Package downloads or API product separately.
- [ ] Define public API documentation/support/abuse controls if API product is
  launched.

## Human decisions required

- Confirm whether `mentedobrasil.com.br` is the launch domain.
- Choose contact/correction/security reporting channel.
- Approve minimal privacy disclosure text.
- Decide robots/indexing posture for launch and staging.
- Decide public data license/reuse posture.
- Give explicit approval before `public_release_status` changes.

## External research required

- Verify source attribution and reuse obligations for DATASUS, SIM, SIH/SUS,
  CNES, and IBGE before public downloads/API reuse.
- Verify current legal/privacy wording requirements before publishing a public
  privacy disclosure, if the site adds analytics, forms, or cookies later.

## Recommended implementation sequence

1. Configure human contact/security mailbox values.
2. Deploy staging only, run full regression plus smoke/security checks.
3. Configure remote monitoring and backup provider policies.
4. Obtain explicit human release approval.
5. Deploy production/domain and change `public_release_status` only in the
    approved release step.

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
- The current public exposure model is not launch-hardened: the browser talks
  directly to FastAPI through `NEXT_PUBLIC_MDB_API_BASE_URL`.
- `geometry_profile=full` is reachable on the operational API and returned
  146,130,129 bytes in the API regression, making it a pre-launch blocker.
- Security headers, rate limiting, production cache policy, robots/indexing,
  observability, privacy/contact disclosures, and production backup/restore
  procedure are not launch-ready.
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

The V1 website should not be made public until the operational hardening items
below are closed:

- Block or restrict `geometry_profile=full` on the production operational API.
- Choose and implement a production same-origin or equivalent API ingress model.
- Configure production CORS for the final origin.
- Add production security headers.
- Add endpoint-class rate limiting and response-size controls.
- Add cache policy for versioned release data and geometry.
- Define robots/indexing behavior before first public URL.
- Define privacy/contact/correction/security reporting channel.
- Add minimum production observability and backup/restore procedure.

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
| Application security | WARNING | XSS and SQL tests pass, but production headers and rate limits are missing. |
| Infrastructure security | WARNING | Local DB is bound to `127.0.0.1`; production architecture is not defined. |
| API exposure | BLOCKER | `full` geometry is expensive and currently reachable. |
| Production deployment readiness | BLOCKER | No production ingress/CORS/cache/rate-limit/headers/observability plan implemented. |
| Privacy / data collection | HUMAN_DECISION_REQUIRED | Dataset is aggregate-only; public privacy/contact posture is not defined. |
| Legal / licensing / attribution | HUMAN_DECISION_REQUIRED | Public data license and attribution/legal review are unresolved. |
| Reliability / observability / recovery | WARNING | Rebuildability passes; production backup/restore and observability are missing. |
| Product / SEO / disclosure | WARNING | Titles/descriptions exist; robots, sitemap, OG/Twitter, and canonical coverage are incomplete. |

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
| CORS production origin | WARNING | `audit_results/cors_audit.txt` | REQUIRED_BEFORE_LAUNCH | Configure final origin or same-origin proxy. | CODEX |
| Direct browser API model | WARNING | `audit_results/api_exposure_model.txt` | REQUIRED_BEFORE_LAUNCH | Prefer same-origin `/api` ingress. | CODEX |
| FastAPI docs exposure | WARNING | `audit_results/fastapi_docs_audit.txt` | REQUIRED_BEFORE_LAUNCH | Disable/protect docs if backend is internet-reachable. | CODEX |
| Full geometry exposure | BLOCKER | `audit_results/api_regression.txt`, `geometry_exposure_audit.txt` | BLOCKER | Block/restrict full on operational API. | CODEX |
| Detail geometry exposure | WARNING | `audit_results/geometry_exposure_audit.txt` | RECOMMENDED | Restrict or heavily cache if not needed. | CODEX |
| Rate limiting | WARNING | `audit_results/rate_limit_audit.txt` | REQUIRED_BEFORE_LAUNCH | Add class-based limits and size gates. | CODEX |
| Cache/compression | WARNING | `audit_results/cache_audit.txt` | REQUIRED_BEFORE_LAUNCH | Add CDN/API cache policy for versioned data. | CODEX |
| Security headers | WARNING | `audit_results/production_security_headers.txt` | REQUIRED_BEFORE_LAUNCH | Add CSP/HSTS/referrer/permissions/content-type/frame policy. | CODEX |
| Privacy dataset | PASS | `audit_results/privacy_dataset_audit.txt` | REQUIRED_BEFORE_LAUNCH | Keep aggregate-only data contract. | CODEX |
| Website trackers/cookies | PASS | `audit_results/privacy_website_audit.txt` | RECOMMENDED | Recheck if analytics are added. | CODEX |
| Third-party network requests | PASS | `audit_results/third_party_requests.txt` | RECOMMENDED | Keep no external basemap/token dependency. | CODEX |
| Privacy policy/disclosure | HUMAN_DECISION_REQUIRED | `audit_results/contact_correction_audit.txt` | REQUIRED_BEFORE_LAUNCH | Decide minimal public privacy/contact text. | HUMAN |
| Dataset license | HUMAN_DECISION_REQUIRED | `audit_results/licensing_attribution_audit.txt` | BLOCKER for data downloads | Choose license/reuse terms. | HUMAN |
| Source attribution/legal review | EXTERNAL_RESEARCH_REQUIRED | `audit_results/licensing_attribution_audit.txt` | REQUIRED_BEFORE_DATA_RELEASE | Verify DATASUS/SIM/SIH/CNES/IBGE attribution/reuse obligations. | EXTERNAL_RESEARCH |
| Contact/correction channel | HUMAN_DECISION_REQUIRED | `audit_results/contact_correction_audit.txt` | REQUIRED_BEFORE_LAUNCH | Provide contact/correction/security channel. | HUMAN |
| SEO basics | WARNING | `audit_results/seo_audit.txt` | RECOMMENDED | Add canonical coverage, OG/Twitter, icons. | CODEX |
| Robots/indexing | WARNING | `audit_results/robots_indexing_audit.txt` | REQUIRED_BEFORE_LAUNCH | Decide staging/prod index strategy. | HUMAN + CODEX |
| Sitemap | WARNING | `audit_results/seo_audit.txt` | RECOMMENDED | Decide whether to index 27 states and 439 regions. | HUMAN + CODEX |
| Observability | WARNING | `audit_results/logging_observability_audit.txt` | REQUIRED_BEFORE_LAUNCH | Add uptime/error/logging minimum. | CODEX |
| Backup/recovery | WARNING | `audit_results/rebuildability_recovery_audit.txt` | REQUIRED_BEFORE_LAUNCH | Add production backup/restore or rebuild drill. | CODEX |
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

The frontend currently uses the operational API directly from the browser via
`NEXT_PUBLIC_MDB_API_BASE_URL`. This means the backend hostname would be visible
unless production uses same-origin routing or an equivalent reverse proxy.

FastAPI docs are enabled locally:

- `/docs`: 200
- `/redoc`: 200
- `/openapi.json`: 200

If the backend is internet-reachable in production, those should be disabled or
protected unless there is an explicit decision to expose operational API docs.

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
- `full`: 146,130,129 bytes JSON; 33.5 seconds in this API regression.

`full` is a CRITICAL public operational API risk because it creates bandwidth
amplification, worker exhaustion, memory pressure, accidental client request
risk, and denial-of-service exposure. It should not remain publicly reachable on
the production operational API.

Recommended policy:

Block `full` on the production operational API. Keep full scientific geometry
for internal/admin use or future versioned download after licensing, caching,
and distribution terms are decided. Keep V1 website maps on `overview`.

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

Use a same-origin public website architecture:

- User-facing origin: `https://mentedobrasil.com.br`.
- Next runtime serves the web app.
- FastAPI runs as a private operational backend.
- Public app calls go through same-origin `/api/...` reverse proxy or managed
  ingress equivalent.
- PostgreSQL/PostGIS is private-network only.
- CDN/reverse proxy handles TLS, compression, cache, rate limiting, request size
  controls, and security headers.
- Runtime API credentials are read-only.
- Migration/admin credentials are separate and never used by the web runtime.
- Logs, health checks, and backups are configured before flipping release
  status.

This is preferable to browser-to-separate-FastAPI-host because it simplifies
CORS, hides backend topology, centralizes cache/rate-limit controls, keeps the
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
12. `NEXT_PUBLIC_MDB_API_BASE_URL`

Secret variables:

- `MDB_API_DB_PASSWORD`
- `MDB_DB_PASSWORD`

`NEXT_PUBLIC_MDB_API_BASE_URL` is intentionally public and must not include a
secret.

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
| API availability | DoS via full geometry | 30s DB statement timeout, pool size 4 | Full block, rate limits, response size gate | CRITICAL |
| API availability | Scraping heavy endpoints | Read-only API | Edge throttling and cache | HIGH |
| Database | Mutation through API role | Read-only role and transaction mode | Production role separation proof | HIGH |
| Credentials | Secret leak | `.env` ignored, secret scan pass | Production secret manager | HIGH |
| Browser users | XSS | `setDOMContent`, validation, tests | CSP | MEDIUM |
| Website availability | Runtime failure | `/health` and `/ready` | Uptime alerts and rollback | MEDIUM |
| Product readiness | Premature indexing | None | Robots/staging/prod index policy | MEDIUM |

## Release checklist

Required before website launch:

- [ ] Block/restrict `geometry_profile=full`.
- [ ] Choose same-origin production architecture.
- [ ] Configure production CORS or remove cross-origin need through proxy.
- [ ] Disable/protect FastAPI docs if backend is reachable.
- [ ] Add production security headers.
- [ ] Add rate limiting and response-size controls.
- [ ] Add cache/compression policy.
- [ ] Configure robots/indexing.
- [ ] Define contact/correction/security reporting channel.
- [ ] Add minimal privacy disclosure.
- [ ] Add observability and health monitoring.
- [ ] Add production backup/restore or deterministic rebuild drill.
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

1. Block/restrict `geometry_profile=full` and optionally restrict `detail`.
2. Implement same-origin `/api` production ingress/proxy strategy.
3. Configure CORS for the final production origin or eliminate cross-origin
   browser calls.
4. Add production security headers and disable/protect FastAPI docs.
5. Add endpoint-class rate limiting, response-size controls, and cache policy.
6. Add robots/indexing policy, privacy disclosure, and contact/correction
   channel after human decisions.
7. Add minimal observability, health checks, and backup/restore or rebuild drill.
8. Deploy staging only, run full regression plus smoke/security checks.
9. Obtain explicit human release approval.
10. Deploy production/domain and change `public_release_status` only in the
    approved release step.

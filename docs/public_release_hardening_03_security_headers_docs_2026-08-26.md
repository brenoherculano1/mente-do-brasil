# Public Release Hardening 03 - Security Headers and API Docs

## Previous posture

The public Next surface did not emit the required baseline security headers, and
FastAPI exposed `/docs`, `/redoc`, and `/openapi.json` by default when reached
directly.

## Threats Addressed

- Browser hardening gaps on the public Next surface.
- Unnecessary framework fingerprinting through `X-Powered-By`.
- Upstream `Server: uvicorn` leakage through the same-origin proxy.
- Default exposure of operational FastAPI docs.

## Next Security Headers

Next is the public surface and now emits:

- `Content-Security-Policy`
- `Strict-Transport-Security: max-age=31536000`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()`
- `X-Frame-Options: DENY`

`poweredByHeader: false` removes `X-Powered-By: Next.js`.

## CSP Policy

The enforced CSP is:

```text
default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; manifest-src 'self'; frame-src 'none'; media-src 'none'
```

It intentionally allows inline scripts/styles for the current Next/React/MapLibre
runtime and does not include `unsafe-eval`, wildcard sources, or
`upgrade-insecure-requests`.

## HSTS Scope

The app emits `Strict-Transport-Security: max-age=31536000`. It does not include
`includeSubDomains` or `preload`.

HSTS application posture is prepared; real HTTPS enforcement still depends on
production TLS/reverse proxy configuration.

## Proxy Fingerprint Sanitization

The same-origin `/api/v1/*` Route Handler removes upstream `server` and
`x-powered-by` headers before returning responses to the public origin.

## FastAPI Docs Policy

FastAPI docs are controlled by server-only `MDB_API_ENABLE_DOCS`.

- Default/absent: disabled.
- `false`, `0`, `no`, invalid value: disabled.
- `true`, `1`, `yes`, `on`: enabled for explicit local/internal use.

With docs disabled, direct FastAPI `/docs`, `/redoc`, and `/openapi.json` return
`404`. Programmatic `app.openapi()` remains available.

## Environment Variable

`MDB_API_ENABLE_DOCS` is server-only and is not present in the browser bundle.
Operational production should run with this setting absent or `false`.

## Local/Internal Opt-In

Set `MDB_API_ENABLE_DOCS=true` only for explicit local/internal API documentation
access. The same-origin Next proxy still exposes only `/api/v1/*`, so `/api/docs`,
`/api/redoc`, and `/api/openapi.json` remain `404`.

## Client Exposure Audit

The browser bundle had zero matches for:

- `MDB_API_ENABLE_DOCS`
- `MDB_API_INTERNAL_BASE_URL`
- `127.0.0.1:8000`
- `localhost:8000`

## Tests

- `audit_results/security_headers_validation.txt`
- `audit_results/csp_browser_validation.txt`
- `audit_results/proxy_header_sanitization.txt`
- `audit_results/fastapi_docs_posture.txt`
- `audit_results/fastapi_docs_env_validation.txt`
- `audit_results/client_backend_exposure.txt`
- `audit_results/same_origin_regression.txt`
- `audit_results/cors_regression.txt`
- `audit_results/full_geometry_regression.txt`
- `audit_results/api_regression.txt`
- `audit_results/scientific_regression.txt`
- `audit_results/frontend_unit.txt`
- `audit_results/frontend_e2e.txt`
- `audit_results/production_e2e.txt`
- `audit_results/lint.txt`
- `audit_results/typecheck.txt`
- `audit_results/production_build.txt`
- `audit_results/release_status_validation.txt`

## Regression Results

- CSP browser violations: `0`.
- Page errors: `0`.
- Console errors: `0`.
- Third-party requests: `0`.
- Direct browser FastAPI requests: `0`.
- Full geometry direct and same-origin: `403 FULL_GEOMETRY_RESTRICTED`.
- FastAPI docs default: `404`.
- FastAPI docs opt-in: `200`.
- Scientific regression: `76/76`.
- Frontend unit: `36/36`.
- Production E2E: `17 passed`, `9 skipped`.

## Remaining Blockers

`public_release_status` remains `NOT_RELEASED`.

The website remains not release-ready because rate limiting, cache policy,
robots/indexing, privacy/contact, observability, and backup/recovery remain
unresolved.

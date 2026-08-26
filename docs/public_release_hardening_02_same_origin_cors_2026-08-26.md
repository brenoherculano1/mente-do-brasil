# Public Release Hardening 02 - Same-Origin API and CORS

## Previous architecture

The browser previously fetched the operational FastAPI backend directly through
`NEXT_PUBLIC_MDB_API_BASE_URL`.

## Risk

Direct browser-to-FastAPI traffic exposed backend topology, made browser CORS a
launch-critical dependency, and split future controls such as rate limiting,
cache, request size policy, and endpoint restrictions.

## Chosen architecture

The browser now calls the Next origin only:

```text
/api/v1/*
```

Next handles that path with one Route Handler:

```text
web/app/api/v1/[...path]/route.ts
```

The handler proxies only `/api/v1/*` to the internal FastAPI base URL. This was
chosen over `next.config` rewrites because the Route Handler preserves a narrow
scope, supports streaming pass-through, allows controlled upstream-unavailable
errors, and gives a single future insertion point for rate limits, cache,
request size policy, and endpoint restrictions.

## Browser request model

Browser data requests use relative same-origin paths such as:

- `/api/v1/map/health-regions`
- `/api/v1/states/AC`
- `/api/v1/health-regions/12001`
- `/api/v1/municipalities/1100015/health-region`

Browser network audit found `direct_fastapi_browser_requests=0`.

## Server request model

Server-rendered pages call FastAPI directly through
`MDB_API_INTERNAL_BASE_URL`, using `web/lib/api/server.ts`. This avoids routing
server components through their own public ingress.

## Environment variables

- `MDB_API_INTERNAL_BASE_URL`: server-only; required in production runtime.
- `NEXT_PUBLIC_MDB_API_BASE_URL`: removed from production frontend runtime.
- `MDB_API_ALLOWED_ORIGINS`: preserved for FastAPI CORS.

## Proxy/rewrite scope

Only `/api/v1/*` is proxied. The same-origin layer does not expose:

- `/docs`
- `/redoc`
- `/openapi.json`
- `/health`
- `/ready`

## CORS policy

The browser's normal path is same-origin, so browser CORS is not needed for V1
data traffic. FastAPI keeps explicit CORS origins for local/direct internal
access. Wildcard origins remain rejected.

Validated behavior:

- `MDB_API_ALLOWED_ORIGINS=*`: rejected.
- `Origin: http://localhost:3000`: allowed locally.
- `Origin: https://evil.example`: no permissive
  `Access-Control-Allow-Origin`.

## Error propagation

The proxy preserves upstream status/body semantics for FastAPI responses:

- State AC: `200`.
- Region 12001: `200`.
- Municipality 1100015: `200`.
- Overview map: `200`, `439` features.
- Full geometry: `403 FULL_GEOMETRY_RESTRICTED`.
- Invalid profile: `422`.
- Invalid region: `404`.

If the backend is unavailable, the proxy returns:

```json
{"error":{"code":"UPSTREAM_UNAVAILABLE","message":"Operational API is temporarily unavailable."}}
```

with status `503`, without leaking the internal URL, env var name, stack trace,
filesystem path, or credentials.

## Internal URL Protection

Client bundle audit over `web/.next/static` and `web/.next/types` found zero
matches for:

- `NEXT_PUBLIC_MDB_API_BASE_URL`
- `MDB_API_INTERNAL_BASE_URL`
- `127.0.0.1:8000`
- `localhost:8000`

## Performance

Small local sample, three requests per path:

- State AC: direct `34.81 ms`, proxy `52.95 ms`.
- Profile 12001: direct `7.32 ms`, proxy `12.54 ms`.
- Overview geometry: direct `202.14 ms`, proxy `370.47 ms`.

This is local evidence only. Full geometry was not benchmarked.

## Tests

- `audit_results/browser_network_same_origin.txt`
- `audit_results/same_origin_proxy_validation.txt`
- `audit_results/cors_after_same_origin.txt`
- `audit_results/client_backend_exposure.txt`
- `audit_results/same_origin_error_leakage.txt`
- `audit_results/same_origin_performance.txt`
- `audit_results/full_geometry_policy_validation.txt`
- `audit_results/api_regression.txt`
- `audit_results/scientific_regression.txt`
- `audit_results/frontend_unit.txt`
- `audit_results/frontend_e2e.txt`
- `audit_results/production_e2e.txt`
- `audit_results/lint.txt`
- `audit_results/typecheck.txt`
- `audit_results/production_build.txt`
- `audit_results/release_status_validation.txt`

## Remaining blockers

`public_release_status` remains `NOT_RELEASED`.

The website remains not release-ready because production security headers,
rate limiting, cache policy, FastAPI docs posture, robots/indexing,
privacy/contact, observability, and backup/recovery remain unresolved.

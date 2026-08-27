# Public Release Hardening 04 — Rate Limiting and Cache

## Previous posture

The previous locked posture was commit `1044b97ec7abdf4f697e93dbf81c07ceaf321f17`.
The website used same-origin browser requests through the Next Route Handler at
`/api/v1/*`, FastAPI docs were disabled by default, full geometry was blocked by
default, CORS wildcard exposure was rejected, and `public_release_status`
remained `NOT_RELEASED`.

## Abuse model

The V1 public ingress needs protection against accidental refresh loops, basic
scraping, and repeated downloads of large geometry responses. This is not a
public API product or an SLA-backed abuse-control system.

## Endpoint cost classes

| Class | Endpoint patterns | Cost rationale |
|---|---|---|
| A_METADATA | `/api/v1/releases`, `/api/v1/indicators`, `/api/v1/ufs` | Small static release metadata. |
| B_NORMAL_READ | `/api/v1/states/*`, `/api/v1/health-regions*`, `/api/v1/municipalities/*/health-region`, non-geometry map rows | Normal profile, lookup, and search reads. |
| C_GEOMETRY_OVERVIEW | `/api/v1/map/health-regions?include_geometry=true&geometry_profile=overview` | Public map GeoJSON, 439 features, about 756 KB raw locally. |
| D_GEOMETRY_DETAIL | `/api/v1/map/health-regions?include_geometry=true&geometry_profile=detail` | Largest public geometry payload, 439 features, about 2.76 MB raw locally. |

`geometry_profile=full` remains restricted and returns 403 with `no-store`.

## Rate limiting algorithm

The ingress uses an in-memory token bucket. Each class has a fixed token
capacity and a 60-second refill window. The limiter calculates `Retry-After`
from the time until the next token is available.

## Limits

| Class | Limit |
|---|---:|
| A_METADATA | 180 requests / 60 seconds / client |
| B_NORMAL_READ | 120 requests / 60 seconds / client |
| C_GEOMETRY_OVERVIEW | 30 requests / 60 seconds / client |
| D_GEOMETRY_DETAIL | 6 requests / 60 seconds / client |

These are V1 operational defaults, not future SLA limits.

## Client key policy

By default, arbitrary proxy headers are not trusted and the fallback key is
`anonymous-global`, so rate limiting remains active even without a reliable
client identifier. If a trusted production reverse proxy overwrites client IP
headers, `MDB_RATE_LIMIT_TRUST_PROXY_HEADERS=true` may be set server-side to use
`x-forwarded-for`, `x-real-ip`, or `forwarded`. The identifier is hashed in
memory only.

No IP address is persisted, written to permanent logs by the limiter, or stored
in a database.

## Memory bounds

The store is bounded to 5,000 buckets with a 120-second TTL. Cleanup removes
expired buckets. If capacity is reached, expired buckets are removed first and
then the oldest-expiring bucket is evicted.

## 429 contract

Over-limit responses return HTTP 429:

```json
{"error":{"code":"RATE_LIMITED","message":"Too many requests. Try again shortly."}}
```

The response includes `Retry-After`, `RateLimit-Limit`,
`RateLimit-Remaining`, `RateLimit-Reset`, `Cache-Control: no-store`, and the
same public security header baseline used by the operational API ingress.

## Cache classes

| Cache class | Cache-Control |
|---|---|
| A_METADATA | `public, max-age=300, s-maxage=3600, stale-while-revalidate=86400` |
| B_NORMAL_READ | `public, max-age=60, s-maxage=900, stale-while-revalidate=3600` |
| C_GEOMETRY_OVERVIEW | `public, max-age=300, s-maxage=3600, stale-while-revalidate=86400` |
| D_GEOMETRY_DETAIL | `public, max-age=60, s-maxage=900, stale-while-revalidate=3600` |

The V1 implementation deliberately does not add `immutable`.

## Cache-Control policies

Cache policy is declared through HTTP headers at the same-origin Next ingress.
The route remains dynamic and still fetches upstream with `cache: "no-store"`;
this hardening does not implement an internal Node cache, Redis, object cache,
or CDN cache.

## Error caching

All non-2xx responses use `Cache-Control: no-store`, including 403 full
geometry, 404/422 validation errors, 429 rate limiting, and 503 upstream
unavailability.

## Geometry policy

Overview and detail geometry remain available with class-specific limits and
cache policy. Overview is gzip-compressible through streaming when the client
sends `Accept-Encoding: gzip`. Full geometry remains blocked with 403.

## Performance

Limiter overhead is an in-process map lookup plus token arithmetic. The unit
suite validates the helper without real-time waits. Local HTTP validation showed
normal overview/detail responses remained available; no E2E test hit rate
limits.

## Limitations of per-instance rate limiting

This is per-process state. If production uses multiple instances, the effective
aggregate limit can multiply by the number of instances. Before large-scale
traffic, an edge or distributed limiter should reinforce this application-level
control.

## Future edge reinforcement

A future CDN, WAF, or reverse proxy can enforce equivalent or stricter limits at
the edge and honor the `Cache-Control` policies declared here. No provider was
selected in this hardening.

## Tests

Validation covered endpoint classification, token bucket behavior, client key
fallback, hashed trusted proxy keys, memory cleanup, bucket cap, stable 429
body, upstream short-circuit, cache policy classification, gzip transport,
security headers, FastAPI docs default 404, full geometry 403, CORS wildcard
blocking, API/scientific regressions, frontend unit tests, production build, and
Playwright production E2E.

## Remaining blockers

The website remains not public-release-ready until robots/indexing,
privacy/contact/correction/security reporting, observability, and backup or
rebuild drills are closed by the appropriate future steps.

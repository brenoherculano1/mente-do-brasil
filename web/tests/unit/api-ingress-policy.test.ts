import { describe, expect, it } from "vitest";
import {
  CACHE_CONTROL_POLICIES,
  InMemoryRateLimiter,
  NO_STORE_CACHE_CONTROL,
  RATE_LIMIT_BUCKET_TTL_MS,
  RATE_LIMIT_POLICIES,
  applyOperationalApiHeaders,
  classifyApiCachePolicy,
  classifyApiRateLimit,
  rateLimitExceededResponse,
  resolveClientKey,
} from "@/lib/api/ingress-policy";

describe("operational API ingress policy", () => {
  it("classifies endpoint rate limit classes", () => {
    expect(classifyApiRateLimit("/api/v1/releases", new URLSearchParams())).toBe("A_METADATA");
    expect(classifyApiRateLimit("/api/v1/indicators", new URLSearchParams())).toBe("A_METADATA");
    expect(classifyApiRateLimit("/api/v1/ufs", new URLSearchParams())).toBe("A_METADATA");
    expect(classifyApiRateLimit("/api/v1/states/AC", new URLSearchParams())).toBe("B_NORMAL_READ");
    expect(classifyApiRateLimit("/api/v1/health-regions/12001", new URLSearchParams())).toBe(
      "B_NORMAL_READ",
    );
    expect(
      classifyApiRateLimit(
        "/api/v1/map/health-regions",
        new URLSearchParams("include_geometry=true&geometry_profile=overview"),
      ),
    ).toBe("C_GEOMETRY_OVERVIEW");
    expect(
      classifyApiRateLimit(
        "/api/v1/map/health-regions",
        new URLSearchParams("include_geometry=true&geometry_profile=detail"),
      ),
    ).toBe("D_GEOMETRY_DETAIL");
    expect(
      classifyApiRateLimit("/api/v1/health-regions/12001/report.pdf", new URLSearchParams()),
    ).toBe("D_GEOMETRY_DETAIL");
  });

  it("uses no-store for operational errors and cacheable policies for 2xx responses", () => {
    expect(classifyApiCachePolicy("/api/v1/releases", new URLSearchParams(), 200)).toBe(
      CACHE_CONTROL_POLICIES.A_METADATA,
    );
    expect(classifyApiCachePolicy("/api/v1/states/AC", new URLSearchParams(), 200)).toBe(
      CACHE_CONTROL_POLICIES.B_NORMAL_READ,
    );
    expect(
      classifyApiCachePolicy(
        "/api/v1/map/health-regions",
        new URLSearchParams("include_geometry=true&geometry_profile=overview"),
        200,
      ),
    ).toBe(CACHE_CONTROL_POLICIES.C_GEOMETRY_OVERVIEW);
    expect(
      classifyApiCachePolicy(
        "/api/v1/map/health-regions",
        new URLSearchParams("include_geometry=true&geometry_profile=detail"),
        200,
      ),
    ).toBe(CACHE_CONTROL_POLICIES.D_GEOMETRY_DETAIL);
    expect(
      classifyApiCachePolicy(
        "/api/v1/health-regions/12001/report.pdf",
        new URLSearchParams(),
        200,
      ),
    ).toBe(CACHE_CONTROL_POLICIES.D_GEOMETRY_DETAIL);
    expect(classifyApiCachePolicy("/api/v1/releases/unknown", new URLSearchParams(), 404)).toBe(
      NO_STORE_CACHE_CONTROL,
    );
    expect(classifyApiCachePolicy("/api/v1/map/health-regions", new URLSearchParams(), 503)).toBe(
      NO_STORE_CACHE_CONTROL,
    );
  });

  it("allows requests within limit and rejects the request above the limit", () => {
    const limiter = new InMemoryRateLimiter();
    const policy = RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL;
    let decision;
    for (let i = 0; i < policy.limit; i += 1) {
      decision = limiter.consume("client-a", policy, 1_000);
      expect(decision.allowed).toBe(true);
    }

    decision = limiter.consume("client-a", policy, 1_000);

    expect(decision.allowed).toBe(false);
    expect(decision.retryAfterSeconds).toBeGreaterThan(0);
  });

  it("refills after the token window without waiting in real time", () => {
    const limiter = new InMemoryRateLimiter();
    const policy = RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL;
    for (let i = 0; i < policy.limit + 1; i += 1) {
      limiter.consume("client-a", policy, 1_000);
    }

    const decision = limiter.consume("client-a", policy, 1_000 + policy.windowMs);

    expect(decision.allowed).toBe(true);
  });

  it("keeps classes and clients independent", () => {
    const limiter = new InMemoryRateLimiter();
    for (let i = 0; i < RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL.limit; i += 1) {
      limiter.consume("client-a", RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL, 1_000);
    }

    expect(limiter.consume("client-a", RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL, 1_000).allowed).toBe(
      false,
    );
    expect(limiter.consume("client-a", RATE_LIMIT_POLICIES.A_METADATA, 1_000).allowed).toBe(true);
    expect(limiter.consume("client-b", RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL, 1_000).allowed).toBe(
      true,
    );
  });

  it("uses an anonymous protected fallback unless proxy headers are explicitly trusted", () => {
    const headers = new Headers({ "x-forwarded-for": "203.0.113.10" });

    expect(resolveClientKey(headers, {}).source).toBe("anonymous-global");
    const trusted = resolveClientKey(headers, { MDB_RATE_LIMIT_TRUST_PROXY_HEADERS: "true" });
    expect(trusted.source).toBe("x-forwarded-for");
    expect(trusted.key).not.toContain("203.0.113.10");
  });

  it("cleans up expired buckets and bounds bucket count", () => {
    const limiter = new InMemoryRateLimiter({ maxBuckets: 8, bucketTtlMs: RATE_LIMIT_BUCKET_TTL_MS });
    for (let i = 0; i < 16; i += 1) {
      limiter.consume(`client-${i}`, RATE_LIMIT_POLICIES.B_NORMAL_READ, 1_000 + i);
    }
    expect(limiter.bucketCount).toBeLessThanOrEqual(8);

    const deleted = limiter.cleanup(1_000 + 16 + RATE_LIMIT_BUCKET_TTL_MS + 1);

    expect(deleted).toBeGreaterThan(0);
    expect(limiter.bucketCount).toBe(0);
  });

  it("builds a stable 429 response contract with Retry-After and no-store", async () => {
    const response = rateLimitExceededResponse({
      allowed: false,
      limit: 6,
      remaining: 0,
      resetSeconds: 10,
      retryAfterSeconds: 10,
    });

    expect(response.status).toBe(429);
    expect(response.headers.get("Retry-After")).toBe("10");
    expect(response.headers.get("Cache-Control")).toBe(NO_STORE_CACHE_CONTROL);
    expect(response.headers.get("Content-Security-Policy")).toContain("default-src 'self'");
    expect(response.headers.get("Strict-Transport-Security")).toBe("max-age=31536000");
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("X-Powered-By")).toBeNull();
    await expect(response.json()).resolves.toEqual({
      error: {
        code: "RATE_LIMITED",
        message: "Too many requests. Try again shortly.",
      },
    });
  });

  it("adds operational headers while preserving upstream Vary", () => {
    const headers = new Headers({ Vary: "Origin" });

    applyOperationalApiHeaders(
      headers,
      { allowed: true, limit: 120, remaining: 119, resetSeconds: 60 },
      CACHE_CONTROL_POLICIES.B_NORMAL_READ,
    );

    expect(headers.get("Cache-Control")).toBe(CACHE_CONTROL_POLICIES.B_NORMAL_READ);
    expect(headers.get("RateLimit-Limit")).toBe("120");
    expect(headers.get("Vary")).toBe("Origin, Accept-Encoding");
  });
});

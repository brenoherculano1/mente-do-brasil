import { createHash } from "node:crypto";

export type ApiRateLimitClass = "A_METADATA" | "B_NORMAL_READ" | "C_GEOMETRY_OVERVIEW" | "D_GEOMETRY_DETAIL";
export type ApiCacheClass = "A_METADATA" | "B_NORMAL_READ" | "C_GEOMETRY_OVERVIEW" | "D_GEOMETRY_DETAIL";

export type RateLimitDecision = {
  allowed: boolean;
  limit: number;
  remaining: number;
  resetSeconds: number;
  retryAfterSeconds?: number;
};

type Bucket = {
  tokens: number;
  updatedAtMs: number;
  expiresAtMs: number;
};

type RateLimitPolicy = {
  className: ApiRateLimitClass;
  limit: number;
  windowMs: number;
  rationale: string;
};

type RateLimiterOptions = {
  maxBuckets?: number;
  bucketTtlMs?: number;
};

export const RATE_LIMIT_POLICIES: Record<ApiRateLimitClass, RateLimitPolicy> = {
  A_METADATA: {
    className: "A_METADATA",
    limit: 180,
    windowMs: 60_000,
    rationale: "Cheap release, indicator, and UF metadata.",
  },
  B_NORMAL_READ: {
    className: "B_NORMAL_READ",
    limit: 120,
    windowMs: 60_000,
    rationale: "Normal profile, state, lookup, and search reads.",
  },
  C_GEOMETRY_OVERVIEW: {
    className: "C_GEOMETRY_OVERVIEW",
    limit: 30,
    windowMs: 60_000,
    rationale: "Large overview GeoJSON payload used by the public map.",
  },
  D_GEOMETRY_DETAIL: {
    className: "D_GEOMETRY_DETAIL",
    limit: 6,
    windowMs: 60_000,
    rationale: "Largest public geometry detail payload.",
  },
};

export const CACHE_CONTROL_POLICIES: Record<ApiCacheClass, string> = {
  A_METADATA: "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400",
  B_NORMAL_READ: "public, max-age=60, s-maxage=900, stale-while-revalidate=3600",
  C_GEOMETRY_OVERVIEW: "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400",
  D_GEOMETRY_DETAIL: "public, max-age=60, s-maxage=900, stale-while-revalidate=3600",
};

export const NO_STORE_CACHE_CONTROL = "no-store";
export const MAX_RATE_LIMIT_BUCKETS = 5_000;
export const RATE_LIMIT_BUCKET_TTL_MS = 120_000;
const TRUST_PROXY_HEADERS_ENV = "MDB_RATE_LIMIT_TRUST_PROXY_HEADERS";
const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  "connect-src 'self'",
  "worker-src 'self' blob:",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "manifest-src 'self'",
  "frame-src 'none'",
  "media-src 'none'",
].join("; ");

export const OPERATIONAL_API_SECURITY_HEADERS: Record<string, string> = {
  "Content-Security-Policy": CONTENT_SECURITY_POLICY,
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  "X-Frame-Options": "DENY",
};

export class InMemoryRateLimiter {
  private readonly buckets = new Map<string, Bucket>();
  private readonly maxBuckets: number;
  private readonly bucketTtlMs: number;

  constructor(options: RateLimiterOptions = {}) {
    this.maxBuckets = options.maxBuckets ?? MAX_RATE_LIMIT_BUCKETS;
    this.bucketTtlMs = options.bucketTtlMs ?? RATE_LIMIT_BUCKET_TTL_MS;
  }

  get bucketCount(): number {
    return this.buckets.size;
  }

  consume(key: string, policy: RateLimitPolicy, nowMs = Date.now()): RateLimitDecision {
    this.cleanup(nowMs);
    const bucketKey = `${policy.className}:${key}`;
    let bucket = this.buckets.get(bucketKey);

    if (!bucket) {
      this.evictForCapacity(nowMs);
      bucket = {
        tokens: policy.limit,
        updatedAtMs: nowMs,
        expiresAtMs: nowMs + this.bucketTtlMs,
      };
      this.buckets.set(bucketKey, bucket);
    }

    const refillRatePerMs = policy.limit / policy.windowMs;
    const elapsedMs = Math.max(0, nowMs - bucket.updatedAtMs);
    bucket.tokens = Math.min(policy.limit, bucket.tokens + elapsedMs * refillRatePerMs);
    bucket.updatedAtMs = nowMs;
    bucket.expiresAtMs = nowMs + this.bucketTtlMs;

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return {
        allowed: true,
        limit: policy.limit,
        remaining: Math.floor(bucket.tokens),
        resetSeconds: Math.ceil(policy.windowMs / 1000),
      };
    }

    const retryAfterSeconds = Math.max(1, Math.ceil((1 - bucket.tokens) / refillRatePerMs / 1000));
    return {
      allowed: false,
      limit: policy.limit,
      remaining: 0,
      resetSeconds: retryAfterSeconds,
      retryAfterSeconds,
    };
  }

  reset(): void {
    this.buckets.clear();
  }

  cleanup(nowMs = Date.now()): number {
    let deleted = 0;
    for (const [key, bucket] of this.buckets) {
      if (bucket.expiresAtMs <= nowMs) {
        this.buckets.delete(key);
        deleted += 1;
      }
    }
    return deleted;
  }

  private evictForCapacity(nowMs: number): void {
    if (this.buckets.size < this.maxBuckets) return;
    this.cleanup(nowMs);
    while (this.buckets.size >= this.maxBuckets) {
      let oldestKey: string | undefined;
      let oldestExpiry = Number.POSITIVE_INFINITY;
      for (const [key, bucket] of this.buckets) {
        if (bucket.expiresAtMs < oldestExpiry) {
          oldestKey = key;
          oldestExpiry = bucket.expiresAtMs;
        }
      }
      if (!oldestKey) return;
      this.buckets.delete(oldestKey);
    }
  }
}

const globalRateLimiter = new InMemoryRateLimiter();

export function classifyApiRateLimit(pathname: string, searchParams: URLSearchParams): ApiRateLimitClass {
  return classifyByPath(pathname, searchParams);
}

export function classifyApiCachePolicy(pathname: string, searchParams: URLSearchParams, status: number): string {
  if (status < 200 || status >= 300) return NO_STORE_CACHE_CONTROL;
  return CACHE_CONTROL_POLICIES[classifyByPath(pathname, searchParams)];
}

export function checkApiRateLimit(
  headers: Headers,
  pathname: string,
  searchParams: URLSearchParams,
  nowMs = Date.now(),
): RateLimitDecision & { className: ApiRateLimitClass; clientKeySource: string } {
  const className = classifyApiRateLimit(pathname, searchParams);
  const client = resolveClientKey(headers);
  return {
    ...globalRateLimiter.consume(client.key, RATE_LIMIT_POLICIES[className], nowMs),
    className,
    clientKeySource: client.source,
  };
}

export function resetApiRateLimiterForTests(): void {
  globalRateLimiter.reset();
}

export function rateLimitExceededResponse(decision: RateLimitDecision): Response {
  const headers = rateLimitHeaders(decision, NO_STORE_CACHE_CONTROL);
  applySecurityHeaders(headers);
  return Response.json(
    {
      error: {
        code: "RATE_LIMITED",
        message: "Too many requests. Try again shortly.",
      },
    },
    {
      status: 429,
      headers,
    },
  );
}

export function applyOperationalApiHeaders(
  headers: Headers,
  decision: RateLimitDecision,
  cacheControl: string,
): Headers {
  headers.set("Cache-Control", cacheControl);
  applySecurityHeaders(headers);
  for (const [key, value] of rateLimitHeaders(decision, cacheControl)) {
    headers.set(key, value);
  }
  const vary = headers.get("Vary");
  if (!vary) {
    headers.set("Vary", "Accept-Encoding");
  } else if (!vary.toLowerCase().split(",").map((part) => part.trim()).includes("accept-encoding")) {
    headers.set("Vary", `${vary}, Accept-Encoding`);
  }
  return headers;
}

export function applyOperationalSecurityHeaders(headers: Headers): Headers {
  applySecurityHeaders(headers);
  return headers;
}

function applySecurityHeaders(headers: Headers): void {
  for (const [key, value] of Object.entries(OPERATIONAL_API_SECURITY_HEADERS)) {
    if (!headers.has(key)) headers.set(key, value);
  }
  headers.delete("X-Powered-By");
}

export function resolveClientKey(
  headers: Headers,
  env: Partial<Record<string, string | undefined>> = process.env,
): { key: string; source: string } {
  if (env.VERCEL === "1" && env[TRUST_PROXY_HEADERS_ENV] === "true") {
    const forwardedFor = firstForwardedFor(headers.get("x-forwarded-for"));
    if (forwardedFor) return hashedClientKey(forwardedFor, "x-forwarded-for");
    const realIp = headers.get("x-real-ip")?.trim();
    if (realIp) return hashedClientKey(realIp, "x-real-ip");
    const forwarded = parseForwardedFor(headers.get("forwarded"));
    if (forwarded) return hashedClientKey(forwarded, "forwarded");
  }
  return { key: "anonymous-global", source: "anonymous-global" };
}

function rateLimitHeaders(decision: RateLimitDecision, cacheControl: string): Headers {
  return new Headers({
    "Cache-Control": cacheControl,
    "RateLimit-Limit": String(decision.limit),
    "RateLimit-Remaining": String(decision.remaining),
    "RateLimit-Reset": String(decision.resetSeconds),
    ...(decision.retryAfterSeconds ? { "Retry-After": String(decision.retryAfterSeconds) } : {}),
  });
}

function classifyByPath(pathname: string, searchParams: URLSearchParams): ApiRateLimitClass {
  const normalized = pathname.replace(/\/+$/, "");
  const segments = normalized.replace(/^\/api\/v1\/?/, "").split("/").filter(Boolean);
  const [first, second, third] = segments;

  if (first === "map" && second === "health-regions") {
    if (searchParams.get("include_geometry")?.toLowerCase() === "true") {
      return searchParams.get("geometry_profile")?.toLowerCase() === "detail"
        ? "D_GEOMETRY_DETAIL"
        : "C_GEOMETRY_OVERVIEW";
    }
    return "B_NORMAL_READ";
  }

  if (first === "releases" || first === "indicators" || first === "ufs") {
    return "A_METADATA";
  }

  if (first === "intelligence" && second === "methods") {
    return "A_METADATA";
  }

  if (first === "radar" && second === "health-regions") {
    return searchParams.get("include_geometry")?.toLowerCase() === "true"
      ? "C_GEOMETRY_OVERVIEW"
      : "B_NORMAL_READ";
  }

  if (first === "health-regions" && third === "report.pdf") {
    return "D_GEOMETRY_DETAIL";
  }

  if (
    first === "health-regions" ||
    first === "states" ||
    (first === "municipalities" && third === "health-region")
  ) {
    return "B_NORMAL_READ";
  }

  return "B_NORMAL_READ";
}

function hashedClientKey(identifier: string, source: string): { key: string; source: string } {
  const digest = createHash("sha256").update(identifier).digest("hex").slice(0, 32);
  return { key: `${source}:${digest}`, source };
}

function firstForwardedFor(value: string | null): string | undefined {
  return value?.split(",")[0]?.trim() || undefined;
}

function parseForwardedFor(value: string | null): string | undefined {
  if (!value) return undefined;
  const match = value.match(/(?:^|;|,)\s*for=(?:"([^"]+)"|([^;,]+))/i);
  return (match?.[1] ?? match?.[2])?.trim();
}

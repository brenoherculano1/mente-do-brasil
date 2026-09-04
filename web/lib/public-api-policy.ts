import { createHash } from "node:crypto";
import { NextRequest } from "next/server";
import { resolveClientKey } from "@/lib/api/ingress-policy";

export const PUBLIC_RATE_LIMIT = 120;
export const PUBLIC_RATE_WINDOW_SECONDS = 60;

type Bucket = { count: number; resetAt: number };
const buckets = new Map<string, Bucket>();

export function checkPublicRateLimit(request: NextRequest) {
  const now = Date.now();
  const key = resolveClientKey(request.headers).key;
  let bucket = buckets.get(key);
  if (!bucket || now >= bucket.resetAt) {
    bucket = { count: 0, resetAt: now + PUBLIC_RATE_WINDOW_SECONDS * 1000 };
    buckets.set(key, bucket);
  }
  bucket.count += 1;
  return {
    allowed: bucket.count <= PUBLIC_RATE_LIMIT,
    remaining: Math.max(0, PUBLIC_RATE_LIMIT - bucket.count),
    resetSeconds: Math.max(1, Math.ceil((bucket.resetAt - now) / 1000)),
  };
}

export function publicApiHeaders(rate: ReturnType<typeof checkPublicRateLimit>) {
  return new Headers({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Accept, If-None-Match",
    "Access-Control-Expose-Headers":
      "ETag, RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset, X-MDB-Open-Data-Release, X-MDB-Analytical-Release",
    "Cache-Control": "public, max-age=3600, s-maxage=86400",
    "RateLimit-Limit": String(PUBLIC_RATE_LIMIT),
    "RateLimit-Remaining": String(rate.remaining),
    "RateLimit-Reset": String(rate.resetSeconds),
    Vary: "Accept-Encoding",
    "X-MDB-Open-Data-Release": "MDB_OPEN_DATA_2024_1",
    "X-MDB-Analytical-Release": "MDB_ANALYTICAL_2024_2",
    "X-Content-Type-Options": "nosniff",
  });
}

export function responseEtag(bytes: Uint8Array) {
  return `"${createHash("sha256").update(bytes).digest("hex")}"`;
}

export function problem(status: number, title: string, detail: string, instance: string) {
  return JSON.stringify({
    type: `https://mentedobrasil.com.br/problems/${status}`,
    title,
    status,
    detail,
    instance,
  });
}

import { NextRequest } from "next/server";
import {
  checkPublicRateLimit,
  problem,
  publicApiHeaders,
  responseEtag,
} from "@/lib/public-api-policy";
import { internalApiHeaders } from "@/lib/api/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const LOCAL_INTERNAL_API_BASE_URL = "http://127.0.0.1:8000";

function internalApiBaseUrl() {
  const configured = process.env.MDB_API_INTERNAL_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;
  if (process.env.NODE_ENV !== "production") return LOCAL_INTERNAL_API_BASE_URL;
  throw new Error("Internal API base URL is required.");
}

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
  head = false,
) {
  const { path } = await context.params;
  const pathname = `/api/public/v1/${path.join("/")}`;
  const rate = checkPublicRateLimit(request);
  const headers = publicApiHeaders(rate);
  if (!rate.allowed) {
    headers.set("Content-Type", "application/problem+json");
    headers.set("Retry-After", String(rate.resetSeconds));
    return new Response(problem(429, "Rate limit exceeded", "Try again later.", pathname), {
      status: 429,
      headers,
    });
  }

  const url = new URL(`/api/public/v1/${path.map(encodeURIComponent).join("/")}`, internalApiBaseUrl());
  url.search = request.nextUrl.search;
  let upstream: Response;
  try {
    upstream = await fetch(url, {
      headers: internalApiHeaders({ Accept: "application/json" }),
      cache: "no-store",
    });
  } catch {
    headers.set("Content-Type", "application/problem+json");
    return new Response(problem(503, "Service unavailable", "The private data service is unavailable.", pathname), { status: 503, headers });
  }
  const bytes = new Uint8Array(await upstream.arrayBuffer());
  const etag = responseEtag(bytes);
  headers.set("ETag", etag);
  headers.set("Content-Type", upstream.headers.get("content-type") ?? "application/json; charset=utf-8");
  if (request.headers.get("if-none-match") === etag && upstream.ok) {
    return new Response(null, { status: 304, headers });
  }
  return new Response(head ? null : bytes, { status: upstream.status, headers });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function HEAD(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context, true);
}

export function OPTIONS(request: NextRequest) {
  const rate = checkPublicRateLimit(request);
  return new Response(null, { status: 204, headers: publicApiHeaders(rate) });
}

function methodNotAllowed(request: NextRequest) {
  const headers = publicApiHeaders(checkPublicRateLimit(request));
  headers.set("Allow", "GET, HEAD, OPTIONS");
  headers.set("Content-Type", "application/problem+json");
  return new Response(problem(405, "Method not allowed", "This API is read-only.", request.nextUrl.pathname), { status: 405, headers });
}

export const POST = methodNotAllowed;
export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
export const DELETE = methodNotAllowed;

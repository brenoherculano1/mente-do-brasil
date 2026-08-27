import { NextRequest, NextResponse } from "next/server";
import {
  applyOperationalApiHeaders,
  checkApiRateLimit,
  classifyApiCachePolicy,
  rateLimitExceededResponse,
} from "@/lib/api/ingress-policy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const LOCAL_INTERNAL_API_BASE_URL = "http://127.0.0.1:8000";

function internalApiBaseUrl(): string {
  const configured = process.env.MDB_API_INTERNAL_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;
  if (process.env.NODE_ENV !== "production") return LOCAL_INTERNAL_API_BASE_URL;
  throw new Error("Internal API base URL is required.");
}

function upstreamUrl(request: NextRequest, path: string[]): string {
  const url = new URL(`/api/v1/${path.map(encodeURIComponent).join("/")}`, internalApiBaseUrl());
  url.search = request.nextUrl.search;
  return url.toString();
}

function maybeCompressBody(request: NextRequest, response: Response, headers: Headers): BodyInit | null {
  if (!response.body) return response.body;
  if (headers.has("content-encoding")) return response.body;
  if (!request.headers.get("accept-encoding")?.toLowerCase().includes("gzip")) return response.body;
  if (response.status < 200 || response.status >= 300) return response.body;
  headers.set("Content-Encoding", "gzip");
  return response.body.pipeThrough(new CompressionStream("gzip"));
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const pathname = `/api/v1/${path.join("/")}`;
  const rateLimit = checkApiRateLimit(request.headers, pathname, request.nextUrl.searchParams);
  if (!rateLimit.allowed) {
    return rateLimitExceededResponse(rateLimit);
  }

  let response: Response;
  try {
    response = await fetch(upstreamUrl(request, path), {
      headers: {
        Accept: request.headers.get("accept") ?? "application/json",
      },
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "UPSTREAM_UNAVAILABLE",
          message: "Operational API is temporarily unavailable.",
        },
      },
      {
        status: 503,
        headers: applyOperationalApiHeaders(
          new Headers(),
          rateLimit,
          classifyApiCachePolicy(pathname, request.nextUrl.searchParams, 503),
        ),
      },
    );
  }

  const headers = new Headers(response.headers);
  headers.delete("content-encoding");
  headers.delete("content-length");
  headers.delete("server");
  headers.delete("transfer-encoding");
  headers.delete("x-powered-by");
  applyOperationalApiHeaders(
    headers,
    rateLimit,
    classifyApiCachePolicy(pathname, request.nextUrl.searchParams, response.status),
  );
  const body = maybeCompressBody(request, response, headers);

  return new Response(body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

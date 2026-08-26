import { NextRequest, NextResponse } from "next/server";

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

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
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
      { status: 503 },
    );
  }

  const headers = new Headers(response.headers);
  headers.delete("content-encoding");
  headers.delete("content-length");
  headers.delete("server");
  headers.delete("transfer-encoding");
  headers.delete("x-powered-by");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

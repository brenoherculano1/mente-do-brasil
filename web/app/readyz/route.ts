import { NextResponse } from "next/server";
import { applyOperationalSecurityHeaders } from "@/lib/api/ingress-policy";
import { internalApiBaseUrl, internalApiHeaders } from "@/lib/api/server";
import { operationalLog, requestIdFromHeaders } from "@/lib/observability";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const requestId = requestIdFromHeaders(request.headers);
  try {
    const response = await fetch(`${internalApiBaseUrl()}/ready`, {
      cache: "no-store",
      headers: internalApiHeaders({ Accept: "application/json", "X-Request-ID": requestId }),
    });
    if (!response.ok) {
      operationalLog("readyz_failed", { request_id: requestId, status: response.status });
      return readyResponse(503, requestId);
    }
    return readyResponse(200, requestId);
  } catch {
    operationalLog("readyz_failed", { request_id: requestId, status: 503 });
    return readyResponse(503, requestId);
  }
}

function readyResponse(status: 200 | 503, requestId: string) {
  return NextResponse.json(
    { status: status === 200 ? "ready" : "unavailable" },
    {
      status,
      headers: applyOperationalSecurityHeaders(
        new Headers({ "Cache-Control": "no-store", "X-Request-ID": requestId }),
      ),
    },
  );
}

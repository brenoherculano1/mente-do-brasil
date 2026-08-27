import { NextResponse } from "next/server";
import { applyOperationalSecurityHeaders } from "@/lib/api/ingress-policy";
import { requestIdFromHeaders } from "@/lib/observability";

export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const requestId = requestIdFromHeaders(request.headers);
  return NextResponse.json(
    { status: "ok" },
    {
      status: 200,
      headers: applyOperationalSecurityHeaders(
        new Headers({ "Cache-Control": "no-store", "X-Request-ID": requestId }),
      ),
    },
  );
}

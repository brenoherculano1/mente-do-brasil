import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET } from "@/app/api/v1/[...path]/route";
import { RATE_LIMIT_POLICIES, resetApiRateLimiterForTests } from "@/lib/api/ingress-policy";

describe("operational API route rate limit", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    resetApiRateLimiterForTests();
  });

  it("short-circuits over-limit requests before calling the upstream FastAPI service", async () => {
    const fetchSpy = vi.fn(async () => Response.json({ ok: true }));
    vi.stubGlobal("fetch", fetchSpy);
    resetApiRateLimiterForTests();

    const context = { params: Promise.resolve({ path: ["map", "health-regions"] }) };
    const url =
      "http://127.0.0.1:3000/api/v1/map/health-regions?include_geometry=true&geometry_profile=detail";
    let response: Response | undefined;

    for (let i = 0; i < RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL.limit + 1; i += 1) {
      response = await GET(new NextRequest(url), context);
    }

    expect(response?.status).toBe(429);
    expect(fetchSpy).toHaveBeenCalledTimes(RATE_LIMIT_POLICIES.D_GEOMETRY_DETAIL.limit);
    expect(response?.headers.get("Retry-After")).toBeTruthy();
    expect(response?.headers.get("Cache-Control")).toBe("no-store");
  });
});

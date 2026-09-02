import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import {
  checkPublicRateLimit,
  publicApiHeaders,
  responseEtag,
} from "@/lib/public-api-policy";

describe("public API boundary", () => {
  it("allows only credential-free public CORS headers", () => {
    const request = new NextRequest("http://localhost/api/public/v1/releases");
    const headers = publicApiHeaders(checkPublicRateLimit(request));
    expect(headers.get("Access-Control-Allow-Origin")).toBe("*");
    expect(headers.get("Access-Control-Allow-Methods")).toBe("GET, HEAD, OPTIONS");
    expect(headers.get("Access-Control-Allow-Credentials")).toBeNull();
    expect(headers.get("RateLimit-Limit")).toBe("120");
  });

  it("creates deterministic strong ETags", () => {
    const bytes = new TextEncoder().encode('{"data":[]}');
    expect(responseEtag(bytes)).toBe(responseEtag(bytes));
    expect(responseEtag(bytes)).toMatch(/^"[a-f0-9]{64}"$/);
  });

  it("rejects request 121 inside one local window", () => {
    const request = new NextRequest("http://localhost/api/public/v1/releases");
    let result = checkPublicRateLimit(request);
    for (let index = 0; index < 120; index += 1) result = checkPublicRateLimit(request);
    expect(result.allowed).toBe(false);
    expect(result.remaining).toBe(0);
  });
});

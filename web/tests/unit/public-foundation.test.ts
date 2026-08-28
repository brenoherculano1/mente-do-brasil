import { describe, expect, it, vi } from "vitest";
import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { GET as securityTxt } from "@/app/.well-known/security.txt/route";
import {
  normalizePublicSiteUrl,
  parsePublicFlag,
  publicSiteConfig,
  robotsPolicy,
} from "@/lib/public-config";
import { requestIdFromHeaders, sanitizeLogFields } from "@/lib/observability";
import { PUBLIC_ROUTE_HEALTH_REGION_CODES, PUBLIC_ROUTE_UFS } from "@/lib/public-route-inventory";

describe("public production foundation config", () => {
  it("parses indexing fail-closed", () => {
    expect(parsePublicFlag(undefined)).toBe(false);
    expect(parsePublicFlag("false")).toBe(false);
    expect(parsePublicFlag("0")).toBe(false);
    expect(parsePublicFlag("no")).toBe(false);
    expect(parsePublicFlag("unexpected")).toBe(false);
    expect(parsePublicFlag("true")).toBe(true);
  });

  it("validates site URL as https origin only", () => {
    expect(normalizePublicSiteUrl("https://mentedobrasil.com.br")).toBe(
      "https://mentedobrasil.com.br",
    );
    expect(normalizePublicSiteUrl("http://mentedobrasil.com.br")).toBeNull();
    expect(normalizePublicSiteUrl("https://user:pass@mentedobrasil.com.br")).toBeNull();
    expect(normalizePublicSiteUrl("https://mentedobrasil.com.br/path")).toBeNull();
  });

  it("emits fail-closed robots by default and public robots with sitemap when configured", () => {
    expect(robots()).toEqual({ rules: { userAgent: "*", disallow: "/" } });
    const config = {
      indexingEnabled: true,
      siteUrl: "https://mentedobrasil.com.br",
      contactEmail: "contato@example.org",
      securityEmail: "security@example.org",
    };
    expect(robotsPolicy(config)).toEqual({
      rules: { userAgent: "*", allow: "/" },
      sitemap: "https://mentedobrasil.com.br/sitemap.xml",
    });
  });

  it("builds deterministic public sitemap counts from generated canonical inventory", () => {
    vi.stubEnv("MDB_PUBLIC_INDEXING_ENABLED", "true");
    vi.stubEnv("MDB_PUBLIC_SITE_URL", "https://mentedobrasil.com.br");
    vi.stubEnv("MDB_PUBLIC_CONTACT_EMAIL", "contato@example.org");
    const urls = sitemap();

    expect(PUBLIC_ROUTE_UFS).toHaveLength(27);
    expect(PUBLIC_ROUTE_HEALTH_REGION_CODES).toHaveLength(439);
    expect(urls).toHaveLength(7 + 27 + 439);
    expect(urls.some((entry) => entry.url.endsWith("/estado/AC"))).toBe(true);
    expect(urls.some((entry) => entry.url.endsWith("/estado/ac"))).toBe(false);
    expect(urls.some((entry) => entry.url.endsWith("/regiao/12001"))).toBe(true);
    vi.unstubAllEnvs();
  });

  it("resolves contact and security email fallback without inventing mailboxes", () => {
    expect(publicSiteConfig({}).contactEmail).toBeNull();
    expect(
      publicSiteConfig({
        MDB_PUBLIC_CONTACT_EMAIL: "contato@example.org",
      }).securityEmail,
    ).toBe("contato@example.org");
  });

  it("prepares security.txt only when contact and site URL are configured", async () => {
    let response = securityTxt(new Request("http://localhost/.well-known/security.txt"));
    expect(response.status).toBe(404);
    expect(response.headers.get("Cache-Control")).toBe("no-store");

    vi.stubEnv("MDB_PUBLIC_SITE_URL", "https://mentedobrasil.com.br");
    vi.stubEnv("MDB_PUBLIC_SECURITY_EMAIL", "security@example.org");
    response = securityTxt(new Request("http://localhost/.well-known/security.txt"));
    const body = await response.text();

    expect(response.status).toBe(200);
    expect(body).toContain("Contact: mailto:security@example.org");
    expect(body).toContain("Preferred-Languages: pt-BR, en");
    expect(body).toContain("Canonical: https://mentedobrasil.com.br/.well-known/security.txt");
    vi.unstubAllEnvs();
  });

  it("accepts safe request IDs and sanitizes sensitive log fields", () => {
    expect(requestIdFromHeaders(new Headers({ "x-request-id": "request_123456" }))).toBe(
      "request_123456",
    );
    expect(requestIdFromHeaders(new Headers({ "x-request-id": "127.0.0.1" }))).not.toBe(
      "127.0.0.1",
    );
    const sanitized = sanitizeLogFields({
      DATABASE_URL: "postgres://user:password@127.0.0.1/db",
      authorization: "Bearer token",
      route: "/api/v1/releases",
      forwarded_for: "127.0.0.1",
    });
    expect(sanitized.DATABASE_URL).toBe("[REDACTED]");
    expect(sanitized.authorization).toBe("[REDACTED]");
    expect(sanitized.forwarded_for).toBe("[REDACTED]");
    expect(sanitized.route).toBe("/api/v1/releases");
  });
});

const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);

export const PRIVACY_NOTICE_VERSION = "MDB_PRIVACY_NOTICE_1.0";
export const PRIVACY_NOTICE_STATUS = "DRAFT_PRE_RELEASE";
export const DEFAULT_SITE_URL = "https://mentedobrasil.com.br";

export type PublicSiteConfig = {
  indexingEnabled: boolean;
  siteUrl: string | null;
  contactEmail: string | null;
  securityEmail: string | null;
};

export function parsePublicFlag(value: string | undefined): boolean {
  return TRUE_VALUES.has((value ?? "").trim().toLowerCase());
}

export function normalizePublicSiteUrl(value: string | undefined): string | null {
  const raw = (value ?? "").trim();
  if (!raw) return null;
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return null;
  }
  if (url.protocol !== "https:") return null;
  if (!url.hostname || url.username || url.password) return null;
  if (url.pathname !== "/" || url.search || url.hash) return null;
  return url.origin;
}

export function isValidPublicEmail(value: string | undefined): boolean {
  const raw = (value ?? "").trim();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw);
}

export function publicSiteConfig(
  env: Partial<Record<string, string | undefined>> = process.env,
): PublicSiteConfig {
  const indexingEnabled = parsePublicFlag(env.MDB_PUBLIC_INDEXING_ENABLED);
  const siteUrl = normalizePublicSiteUrl(env.MDB_PUBLIC_SITE_URL);
  const contactEmail = isValidPublicEmail(env.MDB_PUBLIC_CONTACT_EMAIL)
    ? env.MDB_PUBLIC_CONTACT_EMAIL!.trim()
    : null;
  const securityEmail = isValidPublicEmail(env.MDB_PUBLIC_SECURITY_EMAIL)
    ? env.MDB_PUBLIC_SECURITY_EMAIL!.trim()
    : contactEmail;
  return { indexingEnabled, siteUrl, contactEmail, securityEmail };
}

export function assertPublicIndexingConfig(config = publicSiteConfig()): void {
  if (!config.indexingEnabled) return;
  if (!config.siteUrl) {
    throw new Error("MDB_PUBLIC_SITE_URL must be a valid https origin when indexing is enabled.");
  }
  if (!config.contactEmail) {
    throw new Error("MDB_PUBLIC_CONTACT_EMAIL must be configured when indexing is enabled.");
  }
}

export function absolutePublicUrl(path: string, config = publicSiteConfig()): string {
  const base = config.siteUrl ?? DEFAULT_SITE_URL;
  return new URL(path, `${base}/`).toString();
}

export function robotsPolicy(config = publicSiteConfig()) {
  if (!config.indexingEnabled) {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
  assertPublicIndexingConfig(config);
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: absolutePublicUrl("/sitemap.xml", config),
  };
}

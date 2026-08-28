import type { MetadataRoute } from "next";
import { absolutePublicUrl, publicSiteConfig } from "@/lib/public-config";
import { PUBLIC_ROUTE_HEALTH_REGION_CODES, PUBLIC_ROUTE_UFS } from "@/lib/public-route-inventory";

export const dynamic = "force-dynamic";

const STATIC_PATHS = ["/", "/radar", "/metodologia", "/dados", "/sobre", "/privacidade", "/contato"];

export default function sitemap(): MetadataRoute.Sitemap {
  const config = publicSiteConfig();
  if (!config.indexingEnabled) return [];
  return [
    ...STATIC_PATHS,
    ...PUBLIC_ROUTE_UFS.map((uf) => `/estado/${uf}`),
    ...PUBLIC_ROUTE_HEALTH_REGION_CODES.map((code) => `/regiao/${code}`),
  ].map((path) => ({ url: absolutePublicUrl(path, config) }));
}

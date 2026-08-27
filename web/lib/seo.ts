import type { Metadata } from "next";
import { absolutePublicUrl, publicSiteConfig } from "@/lib/public-config";

const SITE_NAME = "Mente do Brasil";
const DESCRIPTION = "Inteligência territorial em saúde mental no Brasil.";

export function pageMetadata(path: string, title: string, description = DESCRIPTION): Metadata {
  const config = publicSiteConfig();
  const url = absolutePublicUrl(path, config);
  return {
    title,
    description,
    alternates: { canonical: url },
    robots: config.indexingEnabled
      ? { index: true, follow: true }
      : { index: false, follow: false },
    openGraph: {
      title,
      description,
      url,
      siteName: SITE_NAME,
      locale: "pt_BR",
      type: "website",
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
  };
}

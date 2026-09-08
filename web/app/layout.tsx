import type { Metadata, Viewport } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";
import { AppFooter } from "@/components/AppFooter";
import { AppHeader } from "@/components/AppHeader";
import {
  DEFAULT_SITE_URL,
  assertPublicIndexingConfig,
  publicSiteConfig,
} from "@/lib/public-config";

const publicConfig = publicSiteConfig();
assertPublicIndexingConfig(publicConfig);

export const metadata: Metadata = {
  title: "Mente do Brasil — Saúde mental nas regiões brasileiras",
  description: "Entenda a situação da saúde mental na sua região e os principais desafios territoriais.",
  metadataBase: new URL(publicConfig.siteUrl ?? DEFAULT_SITE_URL),
  robots: publicConfig.indexingEnabled
    ? { index: true, follow: true }
    : { index: false, follow: false },
  openGraph: {
    title: "Mente do Brasil",
    description: "Entenda a saúde mental nas regiões brasileiras com dados públicos.",
    siteName: "Mente do Brasil",
    locale: "pt_BR",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Mente do Brasil",
    description: "Entenda a saúde mental nas regiões brasileiras com dados públicos.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  colorScheme: "light",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" data-scroll-behavior="smooth">
      <body>
        <AppHeader />
        <main>{children}</main>
        <AppFooter />
      </body>
    </html>
  );
}

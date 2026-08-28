import type { Metadata } from "next";
import { RadarPage } from "@/features/intelligence/RadarPage";
import { pageMetadata } from "@/lib/seo";

type RadarRouteProps = {
  searchParams?: Promise<{ uf?: string | string[] }>;
};

export const metadata: Metadata = pageMetadata(
  "/radar",
  "Radar Territorial | Mente do Brasil",
  "Explore sinais territoriais que merecem investigação mais cuidadosa no Mente do Brasil.",
);

export default async function Page({ searchParams }: RadarRouteProps) {
  const params = await searchParams;
  const uf = Array.isArray(params?.uf) ? params?.uf[0] : params?.uf;
  return <RadarPage initialUf={uf?.toUpperCase()} />;
}

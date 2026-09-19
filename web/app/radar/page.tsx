import type { Metadata } from "next";
import { RadarPage } from "@/features/intelligence/RadarPage";
import { pageMetadata } from "@/lib/seo";
import { EditionGate } from "@/features/availability/EditionGate";

type RadarRouteProps = {
  searchParams?: Promise<{ uf?: string | string[]; ano?: string | string[] }>;
};

export const metadata: Metadata = pageMetadata(
  "/radar",
  "Radar de atenção em saúde mental | Mente do Brasil",
  "Veja quais regiões acumulam sinais que merecem investigação mais cuidadosa.",
);

export default async function Page({ searchParams }: RadarRouteProps) {
  const params = await searchParams;
  const uf = Array.isArray(params?.uf) ? params?.uf[0] : params?.uf;
  return <EditionGate year={params?.ano} context="Sinais regionais"><RadarPage initialUf={uf?.toUpperCase()} /></EditionGate>;
}

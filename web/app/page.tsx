import { ExplorerPage } from "@/features/explorer/ExplorerPage";
import { parseMetric } from "@/lib/metrics";
import { EditionGate } from "@/features/availability/EditionGate";

type HomeProps = {
  searchParams?: Promise<{ indicador?: string | string[]; ano?: string | string[] }>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;
  return <EditionGate year={params?.ano} context="Mapa"><ExplorerPage initialMetric={parseMetric(params?.indicador)} /></EditionGate>;
}

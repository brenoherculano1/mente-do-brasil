import { ExplorerPage } from "@/features/explorer/ExplorerPage";
import { parseMetric } from "@/lib/metrics";
import { EditionGate } from "@/features/availability/EditionGate";
import { historicalYear } from "@/lib/historical";

type HomeProps = {
  searchParams?: Promise<{ indicador?: string | string[]; ano?: string | string[] }>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;
  const year = historicalYear(params?.ano);
  return <EditionGate year={params?.ano} context="Mapa" historical>{year && <ExplorerPage key={year} year={year} initialMetric={parseMetric(params?.indicador)} />}</EditionGate>;
}

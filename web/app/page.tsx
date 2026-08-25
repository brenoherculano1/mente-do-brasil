import { ExplorerPage } from "@/features/explorer/ExplorerPage";
import { parseMetric } from "@/lib/metrics";

type HomeProps = {
  searchParams?: Promise<{ indicador?: string | string[] }>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;
  return <ExplorerPage initialMetric={parseMetric(params?.indicador)} />;
}

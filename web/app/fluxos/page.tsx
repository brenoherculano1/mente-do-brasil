import { FlowsPage } from "@/features/advanced/FlowsPage";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata("/fluxos", "Fluxos | Mente do Brasil", "Fluxos territoriais agregados de internações psiquiátricas.");
export default async function Page({ searchParams }: { searchParams: Promise<{ regiao?: string }> }) {
  const { regiao } = await searchParams;
  return <FlowsPage initialCode={regiao && /^\d{5}$/.test(regiao) ? regiao : undefined} />;
}

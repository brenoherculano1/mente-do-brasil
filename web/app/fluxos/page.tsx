import { FlowsPage } from "@/features/advanced/FlowsPage";
import { pageMetadata } from "@/lib/seo";
import { EditionGate } from "@/features/availability/EditionGate";

export const metadata = pageMetadata("/fluxos", "Fluxos | Mente do Brasil", "Fluxos territoriais agregados de internações psiquiátricas.");
export default async function Page({ searchParams }: { searchParams: Promise<{ regiao?: string; ano?: string }> }) {
  const { regiao, ano } = await searchParams;
  return <EditionGate year={ano} context="Fluxos hospitalares"><FlowsPage initialCode={regiao && /^\d{5}$/.test(regiao) ? regiao : undefined} /></EditionGate>;
}

import { ChangesPage } from "@/features/advanced/ChangesPage";
import { pageMetadata } from "@/lib/seo";
import { EditionGate } from "@/features/availability/EditionGate";

export const metadata = pageMetadata("/mudancas", "Mudanças | Mente do Brasil", "Mudanças de posição territorial entre 2022, 2023 e 2024.");
export default async function Page({ searchParams }: { searchParams: Promise<{ ano?: string }> }) {
  const { ano } = await searchParams;
  return <EditionGate year={ano} context="Evolução temporal"><ChangesPage /></EditionGate>;
}

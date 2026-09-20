import type { Metadata } from "next";
import { FinancingPage } from "@/features/financing/FinancingPage";
import { pageMetadata } from "@/lib/seo";
import { EditionGate } from "@/features/availability/EditionGate";

export const metadata: Metadata = pageMetadata(
  "/financiamento",
  "Recursos e estrutura de saúde | Mente do Brasil",
  "Contexto de recursos gerais da saúde por Região de Saúde, com limites de interpretação claros.",
);

export default async function Page({ searchParams }: { searchParams: Promise<{ ano?: string }> }) {
  const { ano } = await searchParams;
  return <EditionGate year={ano} context="Recursos gerais da saúde" period="Financiamento: série própria por exercício fiscal, independente do ano analítico."><FinancingPage /></EditionGate>;
}

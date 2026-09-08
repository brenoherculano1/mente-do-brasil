import type { Metadata } from "next";
import { FinancingPage } from "@/features/financing/FinancingPage";
import { pageMetadata } from "@/lib/seo";

export const metadata: Metadata = pageMetadata(
  "/financiamento",
  "Recursos e estrutura de saúde | Mente do Brasil",
  "Contexto de recursos gerais da saúde por Região de Saúde, com limites de interpretação claros.",
);

export default function Page() {
  return <FinancingPage />;
}

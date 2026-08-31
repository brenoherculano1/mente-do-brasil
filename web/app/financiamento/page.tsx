import type { Metadata } from "next";
import { FinancingPage } from "@/features/financing/FinancingPage";
import { pageMetadata } from "@/lib/seo";

export const metadata: Metadata = pageMetadata(
  "/financiamento",
  "Financiamento | Mente do Brasil",
  "Contexto geral de financiamento da saúde por Região de Saúde.",
);

export default function Page() {
  return <FinancingPage />;
}

import type { Metadata } from "next";
import { ManagerWorkbench } from "@/features/manager/ManagerWorkbench";
import { pageMetadata } from "@/lib/seo";

type ManagerPageProps = {
  searchParams?: Promise<{ regiao?: string | string[]; compare?: string | string[] }>;
};

export const metadata: Metadata = pageMetadata(
  "/gestor",
  "Modo Gestor | Mente do Brasil",
  "Leitura territorial, comparação e preparação de reuniões por Região de Saúde.",
);

export default async function ManagerPage({ searchParams }: ManagerPageProps) {
  const params = await searchParams;
  const regiao = Array.isArray(params?.regiao) ? params?.regiao[0] : params?.regiao;
  const compare = Array.isArray(params?.compare) ? params?.compare[0] : params?.compare;
  return <ManagerWorkbench initialRegionCode={regiao} initialCompare={compare} />;
}

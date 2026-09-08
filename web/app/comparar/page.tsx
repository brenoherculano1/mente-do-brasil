import type { Metadata } from "next";
import { ManagerWorkbench } from "@/features/manager/ManagerWorkbench";
import { pageMetadata } from "@/lib/seo";

type ComparePageProps = {
  searchParams?: Promise<{ compare?: string | string[] }>;
};

export const metadata: Metadata = pageMetadata(
  "/comparar",
  "Compare regiões | Mente do Brasil",
  "Compare de duas a quatro Regiões de Saúde usando os mesmos indicadores territoriais.",
);

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const params = await searchParams;
  const compare = Array.isArray(params?.compare) ? params.compare[0] : params?.compare;
  return (
    <ManagerWorkbench
      initialCompare={compare ?? "12001,31001"}
      title="Compare regiões"
      eyebrow="Comparação territorial"
      description="Compare de duas a quatro Regiões de Saúde e veja onde elas se aproximam ou se diferenciam. A ferramenta não cria ranking."
      comparisonOnly
    />
  );
}

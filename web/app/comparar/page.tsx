import type { Metadata } from "next";
import { ManagerWorkbench } from "@/features/manager/ManagerWorkbench";
import { pageMetadata } from "@/lib/seo";
import { EditionGate } from "@/features/availability/EditionGate";
import { historicalYear } from "@/lib/historical";
import { HistoricalTerritories } from "@/features/advanced/HistoricalTerritories";

type ComparePageProps = {
  searchParams?: Promise<{ compare?: string | string[]; ano?: string | string[] }>;
};

export const metadata: Metadata = pageMetadata(
  "/comparar",
  "Compare regiões | Mente do Brasil",
  "Compare de duas a quatro Regiões de Saúde usando os mesmos indicadores territoriais.",
);

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const params = await searchParams;
  const compare = Array.isArray(params?.compare) ? params.compare[0] : params?.compare;
  const year = historicalYear(params?.ano);
  return (
    <EditionGate year={params?.ano} context="Comparação" code={compare} historical>
    {year === 2024 ? <ManagerWorkbench
      initialCompare={compare ?? "12001,31001"}
      title="Compare regiões"
      eyebrow="Comparação territorial"
      description="Compare de duas a quatro Regiões de Saúde e veja onde elas se aproximam ou se diferenciam. A ferramenta não cria ranking."
      comparisonOnly
    /> : year && <HistoricalTerritories key={year} year={year} compare={compare} />}
    </EditionGate>
  );
}

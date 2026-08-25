import type { Metadata } from "next";
import { DataPage } from "@/features/data/DataPage";

export const metadata: Metadata = {
  title: "Dados e versões | Mente do Brasil",
  description:
    "Consulte os datasets, fontes, versões, metadados e critérios de publicação que sustentam o Mente do Brasil.",
};

export default function DadosPage() {
  return <DataPage />;
}

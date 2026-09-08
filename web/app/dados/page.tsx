import type { Metadata } from "next";
import { DataPage } from "@/features/data/DataPage";

export const metadata: Metadata = {
  title: "Fontes e cobertura | Mente do Brasil",
  description:
    "Conheça as fontes, os períodos e a cobertura territorial dos indicadores do Mente do Brasil.",
};

export default function DadosPage() {
  return <DataPage />;
}

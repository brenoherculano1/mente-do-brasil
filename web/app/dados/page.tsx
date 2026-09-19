import type { Metadata } from "next";
import { DataPage } from "@/features/data/DataPage";
import { EditionGate } from "@/features/availability/EditionGate";

export const metadata: Metadata = {
  title: "Fontes e cobertura | Mente do Brasil",
  description:
    "Conheça as fontes, os períodos e a cobertura territorial dos indicadores do Mente do Brasil.",
};

export default async function DadosPage({ searchParams }: { searchParams: Promise<{ ano?: string }> }) {
  const { ano } = await searchParams;
  return <EditionGate year={ano} context="Fontes e disponibilidade"><DataPage /></EditionGate>;
}

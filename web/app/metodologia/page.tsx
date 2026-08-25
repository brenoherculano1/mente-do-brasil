import type { Metadata } from "next";
import { MethodologyPage } from "@/features/methodology/MethodologyPage";

export const metadata: Metadata = {
  title: "Metodologia | Mente do Brasil",
  description:
    "Entenda como o Mente do Brasil transforma dados públicos em indicadores comparáveis de necessidade medida, capacidade registrada e mismatch nas Regiões de Saúde brasileiras.",
};

export default function Page() {
  return <MethodologyPage />;
}

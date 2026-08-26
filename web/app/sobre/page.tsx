import type { Metadata } from "next";
import { AboutPage } from "@/features/about/AboutPage";

export const metadata: Metadata = {
  title: "Sobre | Mente do Brasil",
  description:
    "Conheça o Mente do Brasil, uma infraestrutura independente de dados e inteligência territorial em saúde mental construída a partir de dados públicos brasileiros.",
};

export default function Page() {
  return <AboutPage />;
}

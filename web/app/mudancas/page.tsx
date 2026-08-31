import { ChangesPage } from "@/features/advanced/ChangesPage";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata("/mudancas", "Mudanças | Mente do Brasil", "Mudanças de posição territorial entre 2022, 2023 e 2024.");
export default function Page() { return <ChangesPage />; }

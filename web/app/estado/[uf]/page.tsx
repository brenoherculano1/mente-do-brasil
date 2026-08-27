import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import { isNotFound } from "@/lib/api/errors";
import { getStateProfileServer } from "@/lib/api/server";
import { pageMetadata } from "@/lib/seo";
import { isValidUf, normalizeUf, stateNameForUf } from "@/lib/states";
import { StatePage } from "@/features/state/StatePage";

type StatePageProps = {
  params: Promise<{ uf: string }>;
};

export async function generateMetadata({ params }: StatePageProps): Promise<Metadata> {
  const { uf } = await params;
  const normalizedUf = normalizeUf(uf);
  if (!isValidUf(normalizedUf)) {
    return { title: "Estado não encontrado — Mente do Brasil" };
  }
  const stateName = stateNameForUf(normalizedUf);
  return pageMetadata(
    `/estado/${normalizedUf}`,
    `${stateName} | Mente do Brasil`,
    `Explore a distribuição das Regiões de Saúde do ${stateName} nos indicadores de necessidade medida, capacidade registrada e mismatch do Mente do Brasil.`,
  );
}

export default async function Page({ params }: StatePageProps) {
  const { uf } = await params;
  const normalizedUf = normalizeUf(uf);
  if (!isValidUf(normalizedUf)) notFound();
  if (uf !== normalizedUf) permanentRedirect(`/estado/${normalizedUf}`);
  const stateProfile = await loadStateProfile(normalizedUf);
  return <StatePage stateProfile={stateProfile} />;
}

async function loadStateProfile(uf: string) {
  try {
    return await getStateProfileServer(uf);
  } catch (error) {
    if (isNotFound(error)) notFound();
    throw error;
  }
}

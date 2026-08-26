import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { getStateProfile } from "@/lib/api/client";
import { isNotFound } from "@/lib/api/errors";
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
  return {
    title: `${stateName} | Mente do Brasil`,
    description: `Explore a distribuição das Regiões de Saúde do ${stateName} nos indicadores de necessidade medida, capacidade registrada e mismatch do Mente do Brasil.`,
    alternates: { canonical: `/estado/${normalizedUf}` },
  };
}

export default async function Page({ params }: StatePageProps) {
  const { uf } = await params;
  const normalizedUf = normalizeUf(uf);
  if (uf !== normalizedUf) redirect(`/estado/${normalizedUf}`);
  if (!isValidUf(normalizedUf)) notFound();
  const stateProfile = await loadStateProfile(normalizedUf);
  return <StatePage stateProfile={stateProfile} />;
}

async function loadStateProfile(uf: string) {
  try {
    return await getStateProfile(uf);
  } catch (error) {
    if (isNotFound(error)) notFound();
    throw error;
  }
}

import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getHealthRegionProfile } from "@/lib/api/client";
import { isNotFound } from "@/lib/api/errors";
import { formatInteger, formatRate, formatScore } from "@/lib/format";
import { DataQualityNotice } from "@/features/profile/DataQualityNotice";
import { IndicatorMetric } from "@/features/profile/IndicatorMetric";
import { ScoreOverview } from "@/features/profile/ScoreOverview";
import { SpatialContext } from "@/features/profile/SpatialContext";

type RegionPageProps = {
  params: Promise<{ codigo: string }>;
};

export async function generateMetadata({ params }: RegionPageProps): Promise<Metadata> {
  const { codigo } = await params;
  try {
    const profile = await getHealthRegionProfile(codigo);
    return {
      title: `${profile.territory.health_region_name} — Mente do Brasil`,
      description: `Perfil da Região de Saúde ${profile.territory.health_region_name}.`,
    };
  } catch {
    return {
      title: "Região de Saúde não encontrada — Mente do Brasil",
    };
  }
}

export default async function RegionProfilePage({ params }: RegionPageProps) {
  const { codigo } = await params;
  let profile;
  try {
    profile = await getHealthRegionProfile(codigo);
  } catch (error) {
    if (isNotFound(error)) notFound();
    throw error;
  }
  const territory = profile.territory;
  return (
    <div className="profile-shell page-shell">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link href="/">Brasil</Link>
        <span>/</span>
        <span>{territory.uf}</span>
        <span>/</span>
        <span>{territory.health_region_name}</span>
      </nav>

      <section className="profile-hero" aria-labelledby="region-title">
        <p className="eyebrow">Perfil da Região de Saúde</p>
        <h1 id="region-title">{territory.health_region_name}</h1>
        <p>
          {territory.uf} · {formatInteger(territory.municipality_count)} municípios ·
          população {formatInteger(territory.population)}
        </p>
        <p className="small-text">
          Dados: 2022-2024 / dezembro de 2024 conforme indicador. Release:{" "}
          {profile.release.release_id}.
        </p>
      </section>

      <section className="profile-grid">
        <div className="profile-section">
          <h2>Visão geral</h2>
          <ScoreOverview
            need={profile.need.score}
            capacity={profile.capacity.score}
            mismatch={profile.mismatch.score}
          />
          <p>
            O Mismatch compara a posição relativa da região em indicadores de
            necessidade medida com sua posição em capacidade registrada.
          </p>
          <p className="small-text">
            Ele funciona como um sinal para investigação territorial e não como uma
            medida direta de acesso, qualidade ou necessidade não atendida.
          </p>
        </div>

        <div className="profile-section">
          <h2>Território</h2>
          <div className="metric-row">
            <div className="metric-chip">
              <span>Área</span>
              <strong>{formatRate(territory.area_km2)} km²</strong>
            </div>
            <div className="metric-chip">
              <span>Densidade</span>
              <strong>{formatRate(territory.population_density)}</strong>
            </div>
            <div className="metric-chip">
              <span>Código</span>
              <strong>{territory.health_region_code}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="profile-grid">
        <div className="profile-section">
          <h2>Necessidade medida</h2>
          <div className="indicator-grid">
            <IndicatorMetric
              title="Suicídio"
              values={[
                ["ASMR", formatRate(profile.need.suicide.asmr)],
                ["Óbitos", formatInteger(profile.need.suicide.deaths)],
                ["Percentil", `${Math.round(profile.need.suicide.percentile * 100)}`],
              ]}
              percentile={profile.need.suicide.percentile}
            />
            <IndicatorMetric
              title="Internações psiquiátricas registradas no SUS"
              values={[
                ["Contagem", formatInteger(profile.need.psychiatric_admissions.count)],
                ["Taxa", formatRate(profile.need.psychiatric_admissions.rate)],
                ["Percentil", `${Math.round(profile.need.psychiatric_admissions.percentile * 100)}`],
              ]}
              percentile={profile.need.psychiatric_admissions.percentile}
            />
            <div className="metric-chip">
              <span>Need Score</span>
              <strong>{formatScore(profile.need.score)}</strong>
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h2>Capacidade registrada</h2>
          <p className="small-text">
            Capacidade registrada não equivale automaticamente a acesso efetivo,
            disponibilidade imediata ou qualidade assistencial.
          </p>
          <div className="indicator-grid">
            <IndicatorMetric
              title="CAPS"
              values={[
                ["Contagem", formatInteger(profile.capacity.caps.count)],
                ["Taxa", formatRate(profile.capacity.caps.rate)],
                ["Percentil", `${Math.round(profile.capacity.caps.percentile * 100)}`],
              ]}
              percentile={profile.capacity.caps.percentile}
            />
            <IndicatorMetric
              title="Leitos de saúde mental no SUS"
              values={[
                ["Contagem", formatInteger(profile.capacity.mental_health_beds_sus.count)],
                ["Taxa", formatRate(profile.capacity.mental_health_beds_sus.rate)],
                ["Percentil", `${Math.round(profile.capacity.mental_health_beds_sus.percentile * 100)}`],
              ]}
              percentile={profile.capacity.mental_health_beds_sus.percentile}
            />
            <IndicatorMetric
              title="Psiquiatras FTE no SUS"
              values={[
                ["FTE", formatRate(profile.capacity.psychiatrist_fte.fte)],
                ["Taxa", formatRate(profile.capacity.psychiatrist_fte.rate)],
                ["Percentil", `${Math.round(profile.capacity.psychiatrist_fte.percentile * 100)}`],
              ]}
              percentile={profile.capacity.psychiatrist_fte.percentile}
            />
            <div className="metric-chip">
              <span>Capacity Score</span>
              <strong>{formatScore(profile.capacity.score)}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="profile-grid">
        <SpatialContext spatial={profile.spatial} />
        <DataQualityNotice flags={profile.data_quality_flags} />
      </section>

      <section className="profile-section">
        <h2>Navegação</h2>
        <div className="nav-links">
          <Link className="text-button" href="/">
            Voltar ao mapa
          </Link>
          <span className="muted-link">Ver metodologia</span>
          <span className="muted-link">Ver dados</span>
        </div>
      </section>
    </div>
  );
}

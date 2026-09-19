import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isNotFound } from "@/lib/api/errors";
import {
  getHealthRegionExplanationServer,
  getHealthRegionMunicipalitiesServer,
  getHealthRegionPeersServer,
  getHealthRegionProfileServer,
} from "@/lib/api/server";
import { formatInteger, formatRate, formatScore } from "@/lib/format";
import { pageMetadata } from "@/lib/seo";
import { stateNameForUf } from "@/lib/states";
import type { ExplanationResponse, HealthRegionMunicipalities, HealthRegionProfile, PeersResponse } from "@/types/api";
import { RegionIntelligence } from "@/features/intelligence/RegionIntelligence";
import { DataQualityNotice } from "@/features/profile/DataQualityNotice";
import { IndicatorMetric } from "@/features/profile/IndicatorMetric";
import { ScoreOverview } from "@/features/profile/ScoreOverview";
import { SpatialContext } from "@/features/profile/SpatialContext";
import { RegionAdvanced } from "@/features/advanced/RegionAdvanced";
import { ShareButton } from "@/features/share/ShareButton";
import { toneForDirection, toneLabel } from "@/lib/indicator-tone";
import { EditionGate } from "@/features/availability/EditionGate";

type RegionPageProps = {
  params: Promise<{ codigo: string }>;
  searchParams?: Promise<{ ano?: string }>;
};

export async function generateMetadata({ params }: RegionPageProps): Promise<Metadata> {
  const { codigo } = await params;
  if (!/^\d{5}$/.test(codigo)) {
    return { title: "Região de Saúde não encontrada — Mente do Brasil" };
  }
  try {
    const profile = await getHealthRegionProfileServer(codigo);
    return pageMetadata(
      `/regiao/${profile.territory.health_region_code}`,
      `${profile.territory.health_region_name} | Mente do Brasil`,
      `Perfil da Região de Saúde ${profile.territory.health_region_name}.`,
    );
  } catch {
    return {
      title: "Região de Saúde não encontrada — Mente do Brasil",
    };
  }
}

export default async function RegionProfilePage({ params, searchParams }: RegionPageProps) {
  const { codigo } = await params;
  if (!/^\d{5}$/.test(codigo)) notFound();
  const query = await searchParams;
  if (query?.ano === "2025") return <EditionGate year="2025" context="Perfil regional" code={codigo} />;
  let data: [HealthRegionProfile, ExplanationResponse, PeersResponse, HealthRegionMunicipalities];
  try {
    data = await Promise.all([
      getHealthRegionProfileServer(codigo),
      getHealthRegionExplanationServer(codigo),
      getHealthRegionPeersServer(codigo),
      getHealthRegionMunicipalitiesServer(codigo),
    ]);
  } catch (error) {
    if (isNotFound(error)) notFound();
    throw error;
  }
  const [profile, explanation, peers, municipalities] = data;
  const territory = profile.territory;
  const situation = describeSituation(profile.need.score, profile.capacity.score);
  return (
    <div className="profile-shell page-shell">
      <EditionGate year="2024" />
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
          {territory.uf} · População {formatInteger(territory.population)} ·
          {" "}{formatInteger(territory.municipality_count)} municípios integrantes
        </p>
        <div className="region-situation">
          <span>Situação geral</span>
          <strong>{situation}</strong>
          <p>Leitura relativa às 439 Regiões de Saúde, não diagnóstico ou avaliação da qualidade do cuidado.</p>
        </div>
        <div className="nav-links">
          <Link className="text-button" href={`/gestor?regiao=${territory.health_region_code}`}>
            Abrir no painel para gestores
          </Link>
          <Link className="text-button" href={`/comparar?compare=${territory.health_region_code}`}>
            Comparar com outra região
          </Link>
          <a
            className="text-button"
            href={`/api/v1/health-regions/${territory.health_region_code}/report.pdf`}
          >
            Baixar relatório
          </a>
          <ShareButton
            title={`${territory.health_region_name} | Mente do Brasil`}
            text={`Veja os dados públicos da Região de Saúde ${territory.health_region_name}. Indicadores territoriais descritivos, sem ranking de desempenho.`}
          />
        </div>
      </section>

      <section className="profile-grid">
        <div className="profile-section">
          <h2>Necessidade e estrutura</h2>
          <ScoreOverview
            need={profile.need.score}
            capacity={profile.capacity.score}
            mismatch={profile.mismatch.score}
          />
          <p>
            A diferença compara a posição relativa da região em indicadores de
            necessidade em saúde mental com sua estrutura de atendimento registrada.
          </p>
          <p className="small-text">
            Esse indicador funciona como sinal para investigação territorial e não como uma
            medida direta de acesso, qualidade ou volume de recursos a adicionar.
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
          </div>
        </div>
      </section>

      <section className="profile-section" aria-labelledby="municipalities-title">
        <p className="eyebrow">Composição territorial</p>
        <h2 id="municipalities-title">Municípios desta Região de Saúde</h2>
        <p>
          Os indicadores desta página representam o conjunto da Região de Saúde, não
          resultados separados de cada município.
        </p>
        <ul className="municipality-list">
          {municipalities.municipalities.map((municipality) => (
            <li key={municipality.municipality_code_ibge}>{municipality.municipality_name}</li>
          ))}
        </ul>
      </section>

      <section className="profile-grid">
        <div className="profile-section">
          <h2>Necessidade em saúde mental</h2>
          <div className="indicator-grid">
            <IndicatorMetric
              title="Suicídio"
              values={[
                ["Taxa padronizada", formatRate(profile.need.suicide.asmr)],
                ["Óbitos", formatInteger(profile.need.suicide.deaths)],
                ["Posição nacional", `${Math.round(profile.need.suicide.percentile * 100)}/100`],
              ]}
              percentile={profile.need.suicide.percentile}
              direction="need"
            />
            <IndicatorMetric
              title="Internações psiquiátricas registradas no SUS"
              values={[
                ["Contagem", formatInteger(profile.need.psychiatric_admissions.count)],
                ["Taxa", formatRate(profile.need.psychiatric_admissions.rate)],
                ["Posição nacional", `${Math.round(profile.need.psychiatric_admissions.percentile * 100)}/100`],
              ]}
              percentile={profile.need.psychiatric_admissions.percentile}
              direction="need"
            />
            <div className={`metric-chip metric-tone-${toneForDirection(profile.need.score, "need")}`}>
              <span>Índice de necessidade</span>
              <strong>{formatScore(profile.need.score)}</strong>
              <small>{toneLabel(toneForDirection(profile.need.score, "need"))}</small>
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h2>Estrutura disponível</h2>
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
                ["Posição nacional", `${Math.round(profile.capacity.caps.percentile * 100)}/100`],
              ]}
              percentile={profile.capacity.caps.percentile}
              direction="capacity"
            />
            <IndicatorMetric
              title="Leitos de saúde mental no SUS"
              values={[
                ["Contagem", formatInteger(profile.capacity.mental_health_beds_sus.count)],
                ["Taxa", formatRate(profile.capacity.mental_health_beds_sus.rate)],
                ["Posição nacional", `${Math.round(profile.capacity.mental_health_beds_sus.percentile * 100)}/100`],
              ]}
              percentile={profile.capacity.mental_health_beds_sus.percentile}
              direction="capacity"
            />
            <IndicatorMetric
              title="Psiquiatras no SUS"
              values={[
                ["Jornadas equivalentes", formatRate(profile.capacity.psychiatrist_fte.fte)],
                ["Taxa", formatRate(profile.capacity.psychiatrist_fte.rate)],
                ["Posição nacional", `${Math.round(profile.capacity.psychiatrist_fte.percentile * 100)}/100`],
              ]}
              percentile={profile.capacity.psychiatrist_fte.percentile}
              direction="capacity"
            />
            <div className={`metric-chip metric-tone-${toneForDirection(profile.capacity.score, "capacity")}`}>
              <span>Índice de estrutura</span>
              <strong>{formatScore(profile.capacity.score)}</strong>
              <small>{toneLabel(toneForDirection(profile.capacity.score, "capacity"))}</small>
            </div>
          </div>
        </div>
      </section>

      <RegionAdvanced code={codigo} />

      <RegionIntelligence explanation={explanation} peers={peers} />

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
          <Link className="text-button" href={`/estado/${territory.uf}`}>
            Ver estado: {stateNameForUf(territory.uf)}
          </Link>
          <Link className="text-button" href="/metodologia">
            Ver metodologia
          </Link>
          <Link className="text-button" href="/dados">
            Ver dados
          </Link>
        </div>
      </section>
    </div>
  );
}

function describeSituation(need: number, capacity: number) {
  const needLevel = need >= 0.75 ? "alta" : need <= 0.25 ? "baixa" : "intermediária";
  const capacityLevel = capacity >= 0.75 ? "alta" : capacity <= 0.25 ? "baixa" : "intermediária";
  return `Necessidade relativa ${needLevel} e estrutura registrada ${capacityLevel}.`;
}

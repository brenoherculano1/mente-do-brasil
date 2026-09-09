import Link from "next/link";
import { formatInteger, formatMetricValue, formatScore } from "@/lib/format";
import { describeMismatch } from "@/lib/public-language";
import type { HealthRegionFeature, HealthRegionProfile } from "@/types/api";

export function SelectedRegionPanel({
  feature,
  profile,
  loading,
}: {
  feature?: HealthRegionFeature;
  profile: HealthRegionProfile | null;
  loading: boolean;
}) {
  if (!feature) {
    return (
      <div className="selected-panel">
        <p className="field-label">Região selecionada</p>
        <p className="small-text">Clique no mapa ou use a busca para selecionar uma Região de Saúde.</p>
      </div>
    );
  }
  return (
    <div className="selected-panel">
      <p className="field-label">Região selecionada</p>
      <div>
        <strong>{feature.properties.health_region_name}</strong>
        <p className="small-text">
          {feature.properties.uf} · População {formatInteger(feature.properties.population)}
        </p>
      </div>
      {loading && <div className="skeleton" aria-label="Carregando perfil selecionado" />}
      {profile && (
        <>
          <div className="metric-row" aria-label="Resumo de necessidade e estrutura">
            <div className="metric-chip">
              <span>Necessidade</span>
              <strong>{formatScore(profile.need.score)}</strong>
            </div>
            <div className="metric-chip">
              <span>Estrutura</span>
              <strong>{formatScore(profile.capacity.score)}</strong>
            </div>
            <div className="metric-chip">
              <span>Diferença</span>
              <strong>{formatScore(profile.mismatch.score, true)}</strong>
            </div>
          </div>
          <p className="metric-interpretation">{describeMismatch(profile.mismatch.score)}</p>
          <div className="absolute-metrics" aria-label="Quantidades registradas na região">
            <p className="field-label">Quantidades registradas</p>
            <dl>
              <div><dt>CAPS</dt><dd>{formatInteger(profile.capacity.caps.count)}</dd></div>
              <div><dt>Leitos SUS de saúde mental</dt><dd>{formatInteger(profile.capacity.mental_health_beds_sus.count)}</dd></div>
              <div><dt>Jornadas equivalentes de psiquiatras</dt><dd>{formatMetricValue(profile.capacity.psychiatrist_fte.fte, "rate")}</dd></div>
              <div><dt>Internações psiquiátricas</dt><dd>{formatInteger(profile.need.psychiatric_admissions.count)}</dd></div>
              <div><dt>Óbitos por suicídio</dt><dd>{formatInteger(profile.need.suicide.deaths)}</dd></div>
            </dl>
            <p className="small-text">As jornadas equivalentes representam carga horária registrada, não pessoas únicas.</p>
          </div>
        </>
      )}
      {feature.properties.data_quality_flags.length > 0 && (
        <p className="small-text">Dados com observação</p>
      )}
      <Link className="button" href={`/regiao/${feature.properties.health_region_code}`}>
        Ver perfil da região
      </Link>
    </div>
  );
}

import Link from "next/link";
import { formatInteger, formatScore } from "@/lib/format";
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
        <div className="metric-row" aria-label="Resumo Need Capacity Mismatch">
          <div className="metric-chip">
            <span>Need</span>
            <strong>{formatScore(profile.need.score)}</strong>
          </div>
          <div className="metric-chip">
            <span>Capacity</span>
            <strong>{formatScore(profile.capacity.score)}</strong>
          </div>
          <div className="metric-chip">
            <span>Mismatch</span>
            <strong>{formatScore(profile.mismatch.score, true)}</strong>
          </div>
        </div>
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

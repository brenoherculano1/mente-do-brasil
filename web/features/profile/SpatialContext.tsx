import type { HealthRegionProfile } from "@/types/api";

const CLUSTER_COPY: Record<string, string> = {
  HH: "valor alto cercado por valores altos",
  LL: "valor baixo cercado por valores baixos",
  HL: "valor alto cercado por valores baixos",
  LH: "valor baixo cercado por valores altos",
  "high-high": "valor alto cercado por valores altos",
  "low-low": "valor baixo cercado por valores baixos",
  "high-low": "valor alto cercado por valores baixos",
  "low-high": "valor baixo cercado por valores altos",
};

export function SpatialContext({ spatial }: { spatial: HealthRegionProfile["spatial"] }) {
  const text = spatial.lisa_significant
    ? CLUSTER_COPY[spatial.lisa_cluster ?? ""] ?? "associação espacial local significativa"
    : "Não apresentou associação espacial local estatisticamente significativa após correção utilizada no estudo.";
  return (
    <div className="profile-section">
      <h2>Padrão nas regiões vizinhas</h2>
      <p>{text}</p>
      <p className="small-text">
        Esta análise se refere à diferença entre necessidade e capacidade. O detalhe técnico está na metodologia.
      </p>
    </div>
  );
}

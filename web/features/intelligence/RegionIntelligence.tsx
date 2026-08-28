import { formatScore } from "@/lib/format";
import type { ExplanationResponse, PeersResponse } from "@/types/api";
import { DecompositionChart } from "./DecompositionChart";
import { PeerComparison } from "./PeerComparison";

export function RegionIntelligence({
  explanation,
  peers,
}: {
  explanation: ExplanationResponse;
  peers: PeersResponse;
}) {
  return (
    <section className="profile-grid intelligence-profile-grid" id="inteligencia">
      <div className="profile-section intelligence-section">
        <p className="eyebrow">Radar Territorial</p>
        <h2>Por que esta região chama atenção?</h2>
        <p>
          {explanation.matched_signal_families > 0
            ? `${explanation.matched_signal_families} de 5 famílias de sinais foram acionadas neste release.`
            : "Nenhum dos critérios predefinidos do Radar foi acionado neste release."}
        </p>
        {explanation.triggers.length > 0 && (
          <ul className="signal-list">
            {explanation.triggers.map((trigger) => (
              <li key={trigger}>{trigger}</li>
            ))}
          </ul>
        )}
        {explanation.subsignals.length > 0 && (
          <>
            <h3>Sub-sinais</h3>
            <ul className="signal-list compact">
              {explanation.subsignals.map((signal) => (
                <li key={signal}>{signal}</li>
              ))}
            </ul>
          </>
        )}
        {explanation.quality_cautions.length > 0 && (
          <div className="quality-caution">
            {explanation.quality_cautions.map((caution) => (
              <p className="small-text" key={caution}>
                {caution}
              </p>
            ))}
          </div>
        )}
      </div>

      <div className="profile-section intelligence-section">
        <p className="eyebrow">Decomposição do Mismatch</p>
        <h2>Como o Mismatch é formado</h2>
        <p className="small-text">{explanation.interpretation}</p>
        <p className="small-text">
          Soma das contribuições: {formatScore(explanation.decomposition_sum, true)}.
          Mismatch: {formatScore(explanation.mismatch_score, true)}.
        </p>
        <DecompositionChart explanation={explanation} />
      </div>

      <div className="profile-section intelligence-section peer-section" id="peers">
        <p className="eyebrow">Peers estruturais</p>
        <h2>Regiões estruturalmente semelhantes</h2>
        <p>
          Comparação com 10 Regiões de Saúde estruturalmente mais semelhantes
          segundo população, densidade populacional e número de municípios.
        </p>
        <PeerComparison initialPeers={peers} />
      </div>
    </section>
  );
}

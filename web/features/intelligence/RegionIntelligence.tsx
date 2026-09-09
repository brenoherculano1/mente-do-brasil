import { formatScore } from "@/lib/format";
import { describeMismatch, publicLanguage } from "@/lib/public-language";
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
        <p className="eyebrow">O que investigar?</p>
        <h2>Por que esta região chama atenção?</h2>
        <p>
          {explanation.matched_signal_families > 0
            ? `${explanation.matched_signal_families} de 5 sinais de atenção foram identificados nos dados disponíveis.`
            : "Nenhum dos cinco critérios predefinidos de atenção foi identificado nos dados disponíveis."}
        </p>
        {explanation.triggers.length > 0 && (
          <ul className="signal-list">
            {explanation.triggers.map((trigger) => (
                <li key={trigger}>{publicLanguage(trigger)}</li>
            ))}
          </ul>
        )}
        {explanation.subsignals.length > 0 && (
          <>
            <h3>Detalhes adicionais</h3>
            <ul className="signal-list compact">
              {explanation.subsignals.map((signal) => (
                <li key={signal}>{publicLanguage(signal)}</li>
              ))}
            </ul>
          </>
        )}
        {explanation.quality_cautions.length > 0 && (
          <div className="quality-caution">
            {explanation.quality_cautions.map((caution) => (
              <p className="small-text" key={caution}>
              {publicLanguage(caution)}
              </p>
            ))}
          </div>
        )}
      </div>

      <div className="profile-section intelligence-section">
        <p className="eyebrow">Entenda a diferença</p>
        <h2>O que mais influencia esta leitura?</h2>
        <p className="small-text">{publicLanguage(explanation.interpretation)}</p>
        <p className="small-text">
          Soma das contribuições: {formatScore(explanation.decomposition_sum, true)}.
          Diferença: {formatScore(explanation.mismatch_score, true)}.
        </p>
        <p className="metric-interpretation">{describeMismatch(explanation.mismatch_score)}</p>
        <DecompositionChart explanation={explanation} />
      </div>

      <div className="profile-section intelligence-section peer-section" id="peers">
        <p className="eyebrow">Comparação</p>
        <h2>Regiões estruturalmente semelhantes</h2>
        <p>
          Comparação com 10 Regiões de Saúde de perfil territorial mais semelhante
          segundo população, densidade populacional e número de municípios.
        </p>
        <PeerComparison initialPeers={peers} />
      </div>
    </section>
  );
}

import { formatPercentile } from "@/lib/format";
import { publicLanguage } from "@/lib/public-language";
import type { ExplanationResponse } from "@/types/api";

export function DecompositionChart({ explanation }: { explanation: ExplanationResponse }) {
  const maxAbs = Math.max(
    1,
    ...explanation.decomposition.map((item) => Math.abs(item.contribution * 100)),
  );
  return (
    <div className="decomposition-chart" aria-label="Contribuições para a diferença entre necessidade e estrutura">
      {explanation.decomposition.map((item) => {
        const points = item.contribution * 100;
        const width = `${Math.max(2, (Math.abs(points) / maxAbs) * 48)}%`;
        return (
          <div className="decomposition-row" key={item.component}>
            <div className="decomposition-label">
              <strong>{publicLanguage(item.label)}</strong>
              <span>
                {formatPercentile(item.source_percentile)} · {formatPoints(points)}
              </span>
              {item.caution && <span className="quality-note">{publicLanguage(item.caution)}</span>}
            </div>
            <div className="decomposition-bar" aria-hidden="true">
              <span className="zero-line" />
              <span
                className={points >= 0 ? "bar-positive" : "bar-negative"}
                style={points >= 0 ? { left: "50%", width } : { right: "50%", width }}
              />
            </div>
          </div>
        );
      })}
      <p className="small-text">
        Valores positivos aumentam a diferença entre necessidade e estrutura; valores
        negativos atuam no sentido oposto. Esta composição matemática não identifica causas.
      </p>
    </div>
  );
}

function formatPoints(value: number) {
  const formatted = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
  return `${value > 0 ? "+" : ""}${formatted} pontos`;
}

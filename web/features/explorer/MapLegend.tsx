import { getScaleDomain, MAP_COLORS } from "@/lib/map/color-scale";
import type { MetricConfig } from "@/lib/metrics";

export function MapLegend({ metric, values }: { metric: MetricConfig; values: Array<number | null> }) {
  const domain = getScaleDomain(values);
  const gradient =
    metric.scale === "diverging"
      ? `linear-gradient(90deg, ${MAP_COLORS.negative}, ${MAP_COLORS.neutral}, ${MAP_COLORS.positive})`
      : metric.scale === "score"
        ? `linear-gradient(90deg, ${MAP_COLORS.scoreLow}, ${MAP_COLORS.scoreHigh})`
        : `linear-gradient(90deg, ${MAP_COLORS.rateLow}, ${MAP_COLORS.rateHigh})`;
  return (
    <div className="control-group">
      <p className="field-label">Legenda</p>
      <strong>{metric.label}</strong>
      <div className="legend-scale" aria-label={`Escala visual para ${metric.label}`}>
        <div className="legend-gradient" style={{ background: gradient }} />
        <div className="legend-labels">
          {metric.scale === "diverging" ? (
            <>
              <span>negativo</span>
              <span>0</span>
              <span>positivo</span>
            </>
          ) : (
            <>
              <span>{domain.min.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}</span>
              <span>{domain.max.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}</span>
            </>
          )}
        </div>
      </div>
      <p className="small-text">
        {metric.scale === "diverging"
          ? "Mismatch é um sinal relativo, não uma medida direta de acesso ou qualidade."
          : "Escala visual calculada apenas para colorir os valores recebidos da API."}
      </p>
      <p className="small-text">Sem dado: cinza.</p>
    </div>
  );
}

import { formatScore } from "@/lib/format";
import { describeCompositeScore, describeMismatch } from "@/lib/public-language";
import { toneForMismatch, toneLabel } from "@/lib/indicator-tone";

export function ScoreOverview({
  need,
  capacity,
  mismatch,
}: {
  need: number;
  capacity: number;
  mismatch: number;
}) {
  return (
    <div>
      <div className="score-track" aria-label="Necessidade e estrutura em escala de 0 a 1">
        <span className="score-marker" style={{ left: `${clampPercent(need)}%` }} title="Necessidade" />
        <span
          className="score-marker capacity"
          style={{ left: `${clampPercent(capacity)}%` }}
          title="Estrutura"
        />
      </div>
      <div className="score-pair">
        <span>Necessidade {formatScore(need)}</span>
        <span>Estrutura {formatScore(capacity)}</span>
      </div>
      <div className="score-explanations">
        <p>{describeCompositeScore(need, "need")}</p>
        <p>{describeCompositeScore(capacity, "capacity")}</p>
      </div>
      <div className={`metric-chip metric-tone-${toneForMismatch(mismatch)}`} style={{ marginTop: 14 }}>
        <span>Diferença necessidade-capacidade</span>
        <strong>{formatScore(mismatch, true)}</strong>
        <small>{toneLabel(toneForMismatch(mismatch))}</small>
      </div>
      <p className="metric-interpretation">{describeMismatch(mismatch)}</p>
    </div>
  );
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, value * 100));
}

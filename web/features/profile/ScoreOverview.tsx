import { formatScore } from "@/lib/format";

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
      <div className="metric-chip" style={{ marginTop: 14 }}>
        <span>Diferença necessidade-capacidade</span>
        <strong>{formatScore(mismatch, true)}</strong>
      </div>
    </div>
  );
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, value * 100));
}

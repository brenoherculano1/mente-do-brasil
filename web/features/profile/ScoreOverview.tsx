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
      <div className="score-track" aria-label="Need e Capacity em escala de 0 a 1">
        <span className="score-marker" style={{ left: `${clampPercent(need)}%` }} title="Need" />
        <span
          className="score-marker capacity"
          style={{ left: `${clampPercent(capacity)}%` }}
          title="Capacity"
        />
      </div>
      <div className="score-pair">
        <span>Need {formatScore(need)}</span>
        <span>Capacity {formatScore(capacity)}</span>
      </div>
      <div className="metric-chip" style={{ marginTop: 14 }}>
        <span>Mismatch</span>
        <strong>{formatScore(mismatch, true)}</strong>
      </div>
    </div>
  );
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, value * 100));
}

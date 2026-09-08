import type { CSSProperties } from "react";

export function IndicatorMetric({
  title,
  values,
  percentile,
}: {
  title: string;
  values: Array<[string, string]>;
  percentile: number;
}) {
  return (
    <article className="indicator-card">
      <h3>{title}</h3>
      <div className="indicator-values">
        {values.map(([label, value]) => (
          <div className="metric-chip" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div
        className="percentile"
        aria-label={`Posição relativa nacional: ${Math.round(percentile * 100)} de 100`}
        style={
          {
            "--percentile-position": `${Math.max(0, Math.min(100, percentile * 100))}%`,
          } as CSSProperties
        }
      >
        <span />
      </div>
      <p className="small-text">Posição relativa nacional: {Math.round(percentile * 100)} de 100</p>
    </article>
  );
}

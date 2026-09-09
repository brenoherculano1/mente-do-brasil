import type { CSSProperties } from "react";
import { describePercentile, type IndicatorDirection } from "@/lib/public-language";
import { toneForDirection, toneLabel } from "@/lib/indicator-tone";

export function IndicatorMetric({
  title,
  values,
  percentile,
  direction,
}: {
  title: string;
  values: Array<[string, string]>;
  percentile: number;
  direction: IndicatorDirection;
}) {
  return (
    <article className="indicator-card">
      <h3>{title}</h3>
      <div className="indicator-values">
        {values.map(([label, value]) => {
          const tone = label === "Posição nacional" ? toneForDirection(percentile, direction) : null;
          return <div className={`metric-chip${tone ? ` metric-tone-${tone}` : ""}`} key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            {tone && <small>{toneLabel(tone)}</small>}
          </div>
        })}
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
      <p className="metric-interpretation">{describePercentile(percentile, direction)}</p>
    </article>
  );
}

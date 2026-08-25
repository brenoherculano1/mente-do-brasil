import type { MetricId } from "@/types/api";
import { METRICS } from "@/lib/metrics";

export function MetricSelector({
  value,
  onChange,
}: {
  value: MetricId;
  onChange: (metric: MetricId) => void;
}) {
  return (
    <label className="control-group">
      <span className="field-label">Indicador</span>
      <select
        className="select"
        value={value}
        onChange={(event) => onChange(event.target.value as MetricId)}
      >
        {METRICS.map((metric) => (
          <option key={metric.id} value={metric.id}>
            {metric.label}
          </option>
        ))}
      </select>
    </label>
  );
}

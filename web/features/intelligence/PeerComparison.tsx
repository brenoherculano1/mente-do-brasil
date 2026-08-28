"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { getHealthRegionPeers } from "@/lib/api/client";
import { formatInteger, formatMetricValue, formatRate } from "@/lib/format";
import { getMetricConfig, METRICS } from "@/lib/metrics";
import type { MetricId, PeerBenchmark, PeersResponse } from "@/types/api";

export function PeerComparison({ initialPeers }: { initialPeers: PeersResponse }) {
  const [metric, setMetric] = useState<MetricId>(initialPeers.selected_metric);
  const [peers, setPeers] = useState(initialPeers);
  const [loading, setLoading] = useState(false);
  const metricConfig = getMetricConfig(metric);
  const benchmark = useMemo(
    () => peers.benchmarks.find((item) => item.metric_id === metric) ?? peers.benchmarks[0],
    [metric, peers.benchmarks],
  );

  async function onMetricChange(nextMetric: MetricId) {
    setMetric(nextMetric);
    setLoading(true);
    try {
      setPeers(await getHealthRegionPeers(initialPeers.health_region_code, nextMetric));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="peer-comparison">
      <label className="control-group compact-control">
        <span className="field-label">Indicador</span>
        <select
          className="input"
          value={metric}
          onChange={(event) => void onMetricChange(event.target.value as MetricId)}
        >
          {METRICS.map((option) => (
            <option key={option.id} value={option.id}>
              {option.shortLabel}
            </option>
          ))}
        </select>
      </label>
      {benchmark && (
        <PeerDotPlot
          benchmark={benchmark}
          peers={peers}
          metric={metric}
          metricLabel={metricConfig.shortLabel}
        />
      )}
      <p className="small-text">{loading ? "Atualizando comparação..." : peers.method.selection}</p>
      <div className="peer-why">
        <h3>Comparabilidade usada</h3>
        <div className="metric-row">
          <span>População</span>
          <span>Densidade</span>
          <span>Municípios</span>
        </div>
        <p className="small-text">
          Peers V1 não incorpora renda, urbanização formal, perfil etário,
          vulnerabilidade social ou financiamento.
        </p>
      </div>
      <ul className="peer-list" aria-label="Lista de peers estruturais">
        {peers.peers.map((peer) => (
          <li key={peer.health_region_code}>
            <div>
              <strong>{peer.health_region_name}</strong>
              <span className="small-text">
                {peer.uf} · população {formatInteger(peer.population)} · densidade{" "}
                {formatRate(peer.population_density)} · {peer.municipality_count} municípios
              </span>
            </div>
            <span>{formatMetricValue(peer.metric_value, metricConfig.scale)}</span>
            <Link className="text-button" href={`/regiao/${peer.health_region_code}`}>
              Ver perfil
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PeerDotPlot({
  benchmark,
  peers,
  metric,
  metricLabel,
}: {
  benchmark: PeerBenchmark;
  peers: PeersResponse;
  metric: MetricId;
  metricLabel: string;
}) {
  const values = [
    benchmark.target_value,
    benchmark.peer_min,
    benchmark.peer_max,
    ...peers.peers
      .map((peer) => peer.metric_value)
      .filter((value): value is number => value !== null && Number.isFinite(value)),
  ].filter((value): value is number => value !== null && Number.isFinite(value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const position = (value: number | null) =>
    value === null ? "0%" : `${Math.max(0, Math.min(100, ((value - min) / range) * 100))}%`;
  const metricConfig = getMetricConfig(metric);
  return (
    <div className="peer-dot-plot">
      <div className="peer-axis" aria-hidden="true">
        {benchmark.peer_q1 !== null && benchmark.peer_q3 !== null && (
          <span
            className="peer-iqr"
            style={{
              left: position(benchmark.peer_q1),
              width: `${Math.max(2, ((benchmark.peer_q3 - benchmark.peer_q1) / range) * 100)}%`,
            }}
          />
        )}
        {benchmark.peer_median !== null && (
          <span className="peer-median" style={{ left: position(benchmark.peer_median) }} />
        )}
        {peers.peers.map((peer) =>
          peer.metric_value === null ? null : (
            <span
              className="peer-dot"
              key={peer.health_region_code}
              style={{ left: position(peer.metric_value) }}
              title={`${peer.health_region_name}: ${formatMetricValue(peer.metric_value, metricConfig.scale)}`}
            />
          ),
        )}
        <span
          className="peer-target"
          style={{ left: position(benchmark.target_value) }}
          title={`${peers.health_region_name}: ${formatMetricValue(benchmark.target_value, metricConfig.scale)}`}
        />
      </div>
      <p className="small-text">
        {metricLabel}: região {formatMetricValue(benchmark.target_value, metricConfig.scale)};
        mediana dos peers {formatMetricValue(benchmark.peer_median, metricConfig.scale)};{" "}
        {describePeerPosition(benchmark.relative_to_peer_iqr)}.
      </p>
    </div>
  );
}

function describePeerPosition(value: PeerBenchmark["relative_to_peer_iqr"]) {
  if (value === "BELOW_PEER_IQR") return "abaixo do intervalo interquartil dos peers";
  if (value === "ABOVE_PEER_IQR") return "acima do intervalo interquartil dos peers";
  if (value === "WITHIN_PEER_IQR") return "dentro do intervalo interquartil dos peers";
  return "comparação indisponível por dados insuficientes";
}

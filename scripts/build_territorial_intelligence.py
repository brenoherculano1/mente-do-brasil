"""Build the derived Territorial Intelligence layer for Mente do Brasil."""

from __future__ import annotations

import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

RELEASE_ID = "MDB_ANALYTICAL_2024_1"
INTELLIGENCE_VERSION = "MDB_TERRITORIAL_INTELLIGENCE_1.0"
RADAR_RULESET_VERSION = "MDB_RADAR_RULESET_1.0"
DECOMPOSITION_VERSION = "MDB_MISMATCH_DECOMPOSITION_1.0"
PEER_METHOD_VERSION = "MDB_PEER_METHOD_1.0"
CANONICAL_INPUT_HASH = "a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515"

CANONICAL_INPUT = Path("data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet")
OUTPUT_DIR = Path("data/product_intelligence/MDB_ANALYTICAL_2024_1")
METADATA_DIR = Path("metadata/product_intelligence")

RADAR_FAMILIES = [
    "need_high",
    "capacity_low",
    "mismatch_marked_positive",
    "capacity_component_low",
    "spatial_hh_mismatch",
]

PEER_FEATURES = ["population", "population_density", "municipality_count"]
PEER_METRICS = [
    "need_score",
    "capacity_score",
    "mismatch_score",
    "suicide_asmr",
    "psychiatric_admission_rate",
    "caps_rate",
    "mental_health_beds_sus_rate",
    "psychiatrist_fte_rate",
]
MIN_OBSERVED_PEERS = 5


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_canonical(root: Path) -> pd.DataFrame:
    path = root / CANONICAL_INPUT
    observed = sha256_file(path)
    if observed != CANONICAL_INPUT_HASH:
        raise AssertionError(
            f"BLOCKED: canonical input hash mismatch: {observed} != {CANONICAL_INPUT_HASH}"
        )
    df = pq.read_table(path).to_pandas()
    if len(df) != 439 or df["health_region_code"].nunique() != 439:
        raise AssertionError("Expected 439 unique Health Regions.")
    if int(((df["lisa_significant"]) & (df["lisa_cluster"] == "high-high")).sum()) != 60:
        raise AssertionError("Expected 60 significant HH LISA regions.")
    return df.sort_values("health_region_code").reset_index(drop=True)


def has_flag(value: Any, flag: str) -> bool:
    if value is None:
        return False
    return flag in list(value)


def build_intelligence(
    df: pd.DataFrame,
    intelligence_version: str = INTELLIGENCE_VERSION,
    expected_hh: int | None = 60,
) -> pd.DataFrame:
    out = df[
        [
            "release_id",
            "geography_version",
            "health_region_code",
            "health_region_name",
            "uf",
            "population",
            "population_density",
            "municipality_count",
            "need_score",
            "capacity_score",
            "mismatch_score",
            "suicide_percentile",
            "psychiatric_admission_percentile",
            "caps_percentile",
            "beds_percentile",
            "psychiatrist_fte_percentile",
            "data_quality_flags",
        ]
    ].copy()
    out["intelligence_version"] = intelligence_version
    out["radar_ruleset_version"] = RADAR_RULESET_VERSION
    out["decomposition_version"] = DECOMPOSITION_VERSION
    out["peer_method_version"] = PEER_METHOD_VERSION
    out["need_high"] = out["need_score"] >= 0.75
    out["capacity_low"] = out["capacity_score"] <= 0.25
    out["mismatch_marked_positive"] = out["mismatch_score"] >= 0.25
    out["caps_low"] = out["caps_percentile"] <= 0.25
    out["beds_low"] = out["beds_percentile"] <= 0.25
    out["psychiatrist_fte_low"] = out["psychiatrist_fte_percentile"] <= 0.25
    out["capacity_component_low"] = out["caps_low"] | out["beds_low"] | out["psychiatrist_fte_low"]
    out["spatial_hh_mismatch"] = df["lisa_significant"] & (df["lisa_cluster"] == "high-high")
    out["zero_registered_beds"] = df["data_quality_flags"].map(
        lambda flags: has_flag(flags, "ZERO_REGISTERED_BEDS")
    )
    out["small_suicide_count"] = df["data_quality_flags"].map(
        lambda flags: has_flag(flags, "SMALL_SUICIDE_COUNT")
    )
    out["matched_signal_families"] = out[RADAR_FAMILIES].sum(axis=1).astype("int16")
    out["suicide_contribution"] = 0.5 * (out["suicide_percentile"] - 0.5)
    out["admissions_contribution"] = 0.5 * (out["psychiatric_admission_percentile"] - 0.5)
    out["caps_contribution"] = -(1.0 / 3.0) * (out["caps_percentile"] - 0.5)
    out["beds_contribution"] = -(1.0 / 3.0) * (out["beds_percentile"] - 0.5)
    out["psychiatrist_contribution"] = -(1.0 / 3.0) * (
        out["psychiatrist_fte_percentile"] - 0.5
    )
    out["decomposition_sum"] = out[
        [
            "suicide_contribution",
            "admissions_contribution",
            "caps_contribution",
            "beds_contribution",
            "psychiatrist_contribution",
        ]
    ].sum(axis=1)
    max_error = (out["decomposition_sum"] - out["mismatch_score"]).abs().max()
    if max_error > 1e-12:
        raise AssertionError(f"Decomposition identity failed: max_error={max_error}")
    if expected_hh is not None and out["spatial_hh_mismatch"].sum() != expected_hh:
        raise AssertionError(f"SPATIAL_HH_MISMATCH must equal {expected_hh}.")
    if out["matched_signal_families"].min() < 0 or out["matched_signal_families"].max() > 5:
        raise AssertionError("matched_signal_families must be 0-5.")
    return out


def transformed_peer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    transformed = pd.DataFrame(index=df.index)
    stats: dict[str, dict[str, float]] = {}
    for column in PEER_FEATURES:
        values = np.log1p(df[column].astype(float).to_numpy())
        mean = float(values.mean())
        std = float(values.std(ddof=0))
        if std <= 0:
            raise AssertionError(f"Peer feature has zero population std: {column}")
        transformed[f"z_{column}"] = (values - mean) / std
        stats[column] = {
            "log1p_mean": mean,
            "log1p_population_std_ddof0": std,
            "original_min": float(df[column].min()),
            "original_median": float(df[column].median()),
            "original_max": float(df[column].max()),
            "z_min": float(transformed[f"z_{column}"].min()),
            "z_median": float(transformed[f"z_{column}"].median()),
            "z_max": float(transformed[f"z_{column}"].max()),
        }
    return transformed, stats


def build_peers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    z, stats = transformed_peer_features(df)
    codes = df["health_region_code"].tolist()
    values = z[[f"z_{column}" for column in PEER_FEATURES]].to_numpy()
    rows = []
    for i, code in enumerate(codes):
        distances = []
        for j, peer_code in enumerate(codes):
            if i == j:
                continue
            distance = sqrt(float(((values[i] - values[j]) ** 2).sum()))
            distances.append((distance, peer_code))
        distances.sort(key=lambda item: (item[0], item[1]))
        for rank, (distance, peer_code) in enumerate(distances[:10], start=1):
            rows.append(
                {
                    "release_id": df.iloc[i]["release_id"],
                    "peer_method_version": PEER_METHOD_VERSION,
                    "health_region_code": code,
                    "peer_health_region_code": peer_code,
                    "peer_rank": rank,
                    "structural_distance": distance,
                }
            )
    peers = pd.DataFrame(rows)
    validate_peers(peers)
    return peers, stats


def validate_peers(peers: pd.DataFrame) -> None:
    if len(peers) != 4390:
        raise AssertionError("Expected 4390 peer rows.")
    if (peers["health_region_code"] == peers["peer_health_region_code"]).sum() != 0:
        raise AssertionError("Self peers are not allowed.")
    counts = peers.groupby("health_region_code")["peer_health_region_code"].count()
    if counts.min() != 10 or counts.max() != 10:
        raise AssertionError("Each Health Region must have exactly 10 peers.")
    duplicates = peers.duplicated(["health_region_code", "peer_health_region_code"]).sum()
    if duplicates:
        raise AssertionError("Duplicate peers found for a target Health Region.")
    ranks = peers.groupby("health_region_code")["peer_rank"].agg(["min", "max"]).reset_index()
    if ranks["min"].min() != 1 or ranks["max"].max() != 10:
        raise AssertionError("Peer ranks must be 1-10.")
    if (peers["structural_distance"] < 0).any():
        raise AssertionError("Peer structural distance must be non-negative.")


def quantile(values: np.ndarray, q: float) -> float:
    return float(np.quantile(values, q, method="linear"))


def iqr_category(target: float, q1: float, q3: float) -> str:
    if target < q1:
        return "BELOW_PEER_IQR"
    if target > q3:
        return "ABOVE_PEER_IQR"
    return "WITHIN_PEER_IQR"


def build_peer_benchmarks(df: pd.DataFrame, peers: pd.DataFrame) -> pd.DataFrame:
    by_code = df.set_index("health_region_code")
    rows = []
    for target_code, peer_rows in peers.groupby("health_region_code", sort=True):
        peer_codes = peer_rows.sort_values("peer_rank")["peer_health_region_code"].tolist()
        for metric_id in PEER_METRICS:
            target = float(by_code.loc[target_code, metric_id])
            peer_values = by_code.loc[peer_codes, metric_id].dropna().astype(float).to_numpy()
            observed = int(len(peer_values))
            if observed < MIN_OBSERVED_PEERS:
                rows.append(
                    {
                        "release_id": by_code.loc[target_code, "release_id"],
                        "peer_method_version": PEER_METHOD_VERSION,
                        "health_region_code": target_code,
                        "metric_id": metric_id,
                        "target_value": target,
                        "peer_n_observed": observed,
                        "peer_median": None,
                        "peer_q1": None,
                        "peer_q3": None,
                        "peer_min": None,
                        "peer_max": None,
                        "relative_to_peer_iqr": None,
                        "insufficient_reason": "INSUFFICIENT_OBSERVED_PEERS",
                    }
                )
                continue
            q1 = quantile(peer_values, 0.25)
            q3 = quantile(peer_values, 0.75)
            rows.append(
                {
                    "release_id": by_code.loc[target_code, "release_id"],
                    "peer_method_version": PEER_METHOD_VERSION,
                    "health_region_code": target_code,
                    "metric_id": metric_id,
                    "target_value": target,
                    "peer_n_observed": observed,
                    "peer_median": quantile(peer_values, 0.5),
                    "peer_q1": q1,
                    "peer_q3": q3,
                    "peer_min": float(peer_values.min()),
                    "peer_max": float(peer_values.max()),
                    "relative_to_peer_iqr": iqr_category(target, q1, q3),
                    "insufficient_reason": None,
                }
            )
    return (
        pd.DataFrame(rows)
        .sort_values(["health_region_code", "metric_id"])
        .reset_index(drop=True)
    )


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression="zstd", version="2.6")


def write_metadata(
    root: Path, output_hashes: dict[str, str], peer_feature_stats: dict[str, Any]
) -> None:
    metadata_dir = root / METADATA_DIR
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "intelligence_version": INTELLIGENCE_VERSION,
        "status": "VALIDATED_LOCAL",
        "release_id": RELEASE_ID,
        "canonical_input": str(CANONICAL_INPUT),
        "canonical_input_sha256": CANONICAL_INPUT_HASH,
        "outputs": output_hashes,
        "submethods": {
            "radar_ruleset_version": RADAR_RULESET_VERSION,
            "decomposition_version": DECOMPOSITION_VERSION,
            "peer_method_version": PEER_METHOD_VERSION,
        },
        "radar": {
            "signal_families": {
                "NEED_HIGH": "need_score >= 0.75",
                "CAPACITY_LOW": "capacity_score <= 0.25",
                "MISMATCH_MARKED_POSITIVE": "mismatch_score >= 0.25",
                "CAPACITY_COMPONENT_LOW": (
                    "caps_percentile <= 0.25 OR beds_percentile <= 0.25 OR "
                    "psychiatrist_fte_percentile <= 0.25"
                ),
                "SPATIAL_HH_MISMATCH": "lisa_significant = true AND lisa_cluster = high-high",
            },
            "matched_signal_families": "Unweighted count of the five transparent families.",
            "exclusions": [
                "Data quality flags do not increase the signal count.",
                "ZERO_REGISTERED_BEDS is preserved as a subsignal and caution, not a sixth family.",
            ],
        },
        "decomposition": {
            "reference": "P50 national percentile position",
            "identity": "sum of five centered algebraic contributions equals mismatch_score",
            "etiological_interpretation": "not allowed",
        },
        "peers": {
            "structural_variables": PEER_FEATURES,
            "transform": "log1p then national z-score using population std ddof=0",
            "distance": "Euclidean distance with equal dimension weighting",
            "selection": "10 nearest regions, self excluded, tie-break by health_region_code",
            "benchmark_quantiles": "numpy quantile method=linear",
            "minimum_observed_peers": MIN_OBSERVED_PEERS,
            "outcome_variables_used_for_selection": False,
            "limitations": [
                "No income, formal urbanization, age profile, social vulnerability, or financing.",
                "Similar means similar only across population, population density, "
                "and municipality count.",
            ],
            "feature_stats": peer_feature_stats,
        },
    }
    (metadata_dir / "MDB_TERRITORIAL_INTELLIGENCE_1.0.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def qc_payload(
    intelligence: pd.DataFrame,
    peers: pd.DataFrame,
    benchmarks: pd.DataFrame,
    output_hashes: dict[str, str],
    peer_feature_stats: dict[str, Any],
) -> dict[str, Any]:
    reciprocal = 0
    peer_pairs = set(
        zip(peers["health_region_code"], peers["peer_health_region_code"], strict=False)
    )
    for target, peer in peer_pairs:
        if (peer, target) in peer_pairs:
            reciprocal += 1
    hubness = peers["peer_health_region_code"].value_counts().sort_values(ascending=False)
    return {
        "radar_rows": int(len(intelligence)),
        "radar_counts": {
            "NEED_HIGH": int(intelligence["need_high"].sum()),
            "CAPACITY_LOW": int(intelligence["capacity_low"].sum()),
            "MISMATCH_MARKED_POSITIVE": int(intelligence["mismatch_marked_positive"].sum()),
            "CAPACITY_COMPONENT_LOW": int(intelligence["capacity_component_low"].sum()),
            "SPATIAL_HH_MISMATCH": int(intelligence["spatial_hh_mismatch"].sum()),
        },
        "matched_signal_families_distribution": {
            str(k): int(v)
            for k, v in intelligence["matched_signal_families"]
            .value_counts()
            .reindex(range(0, 6), fill_value=0)
            .sort_index()
            .items()
        },
        "decomposition_max_absolute_error": float(
            (intelligence["decomposition_sum"] - intelligence["mismatch_score"]).abs().max()
        ),
        "peer_rows": int(len(peers)),
        "peers_per_region_min": int(peers.groupby("health_region_code").size().min()),
        "peers_per_region_max": int(peers.groupby("health_region_code").size().max()),
        "self_peers": int((peers["health_region_code"] == peers["peer_health_region_code"]).sum()),
        "duplicate_peers": int(
            peers.duplicated(["health_region_code", "peer_health_region_code"]).sum()
        ),
        "benchmark_rows": int(len(benchmarks)),
        "reciprocal_peer_rate": reciprocal / len(peer_pairs),
        "peer_hubness": {
            "min": int(hubness.min()),
            "median": float(hubness.median()),
            "max": int(hubness.max()),
            "top10": {str(k): int(v) for k, v in hubness.head(10).items()},
        },
        "peer_feature_stats": peer_feature_stats,
        "output_hashes": output_hashes,
    }


def main() -> int:
    root = repo_root()
    df = load_canonical(root)
    out_dir = root / OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    intelligence = build_intelligence(df)
    peers, peer_feature_stats = build_peers(df)
    benchmarks = build_peer_benchmarks(df, peers)
    outputs = {
        "health_region_intelligence.parquet": intelligence,
        "health_region_peers.parquet": peers,
        "peer_benchmarks.parquet": benchmarks,
    }
    for name, frame in outputs.items():
        write_parquet(frame, out_dir / name)
    output_hashes = {name: sha256_file(out_dir / name) for name in outputs}
    write_metadata(root, output_hashes, peer_feature_stats)
    qc = qc_payload(intelligence, peers, benchmarks, output_hashes, peer_feature_stats)
    (out_dir / "territorial_intelligence_qc.json").write_text(
        json.dumps(qc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("TERRITORIAL INTELLIGENCE BUILD")
    print(json.dumps(qc, indent=2, sort_keys=True))
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

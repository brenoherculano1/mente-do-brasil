from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet"
PRODUCT_DIR = ROOT / "data/product_intelligence/MDB_ANALYTICAL_2024_1"
QC_PATH = PRODUCT_DIR / "territorial_intelligence_qc.json"

CANONICAL_HASH = "a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515"
INTELLIGENCE_HASH = "130480cb4423bbe5bd0999293dd2310e8d5860f4847ccb3622988c864a27ed1d"
PEERS_HASH = "e084f8e775b8788afdd9a57c09154d0cb829bae061a6fcb9a3b7fc60ebad7d00"
BENCHMARKS_HASH = "aab4ae0ae5dce321d847195b52272e0a3f715c52348e2a7463a750472005712f"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(name: str):
    return pq.read_table(PRODUCT_DIR / name).to_pandas()


def qc() -> dict:
    return json.loads(QC_PATH.read_text(encoding="utf-8"))


def test_canonical_fingerprint_is_locked():
    assert sha256(CANONICAL) == CANONICAL_HASH


def test_product_output_hashes_are_locked():
    assert sha256(PRODUCT_DIR / "health_region_intelligence.parquet") == INTELLIGENCE_HASH
    assert sha256(PRODUCT_DIR / "health_region_peers.parquet") == PEERS_HASH
    assert sha256(PRODUCT_DIR / "peer_benchmarks.parquet") == BENCHMARKS_HASH


def test_radar_rules_and_quality_flags_are_materialized():
    intelligence = read("health_region_intelligence.parquet")
    assert len(intelligence) == 439
    assert intelligence["matched_signal_families"].between(0, 5).all()
    expected = (
        intelligence["need_high"].astype(int)
        + intelligence["capacity_low"].astype(int)
        + intelligence["mismatch_marked_positive"].astype(int)
        + intelligence["capacity_component_low"].astype(int)
        + intelligence["spatial_hh_mismatch"].astype(int)
    )
    assert (intelligence["matched_signal_families"] == expected).all()
    assert int(intelligence["spatial_hh_mismatch"].sum()) == 60
    assert int(intelligence["zero_registered_beds"].sum()) == 275
    assert int(intelligence["small_suicide_count"].sum()) == 7


def test_decomposition_identity_holds_for_all_regions():
    intelligence = read("health_region_intelligence.parquet")
    total = (
        intelligence["suicide_contribution"]
        + intelligence["admissions_contribution"]
        + intelligence["caps_contribution"]
        + intelligence["beds_contribution"]
        + intelligence["psychiatrist_contribution"]
    )
    assert (total - intelligence["mismatch_score"]).abs().max() <= 1e-12


def test_peer_selection_contract():
    peers = read("health_region_peers.parquet")
    assert len(peers) == 4390
    counts = peers.groupby("health_region_code")["peer_health_region_code"].count()
    assert counts.min() == 10
    assert counts.max() == 10
    assert (peers["health_region_code"] == peers["peer_health_region_code"]).sum() == 0
    assert peers.duplicated(["health_region_code", "peer_health_region_code"]).sum() == 0
    assert peers["peer_rank"].between(1, 10).all()
    assert (peers["structural_distance"] >= 0).all()


def test_peer_benchmarks_are_complete_long_format():
    benchmarks = read("peer_benchmarks.parquet")
    assert len(benchmarks) == 439 * 8
    assert set(benchmarks["metric_id"]) == {
        "need_score",
        "capacity_score",
        "mismatch_score",
        "suicide_asmr",
        "psychiatric_admission_rate",
        "caps_rate",
        "mental_health_beds_sus_rate",
        "psychiatrist_fte_rate",
    }
    assert set(benchmarks["peer_n_observed"]) == {10}
    assert benchmarks["relative_to_peer_iqr"].isin(
        ["BELOW_PEER_IQR", "WITHIN_PEER_IQR", "ABOVE_PEER_IQR"]
    ).all()


def test_peer_qc_records_feature_stats_hubness_and_reciprocity():
    payload = qc()
    assert payload["peer_rows"] == 4390
    assert payload["peers_per_region_min"] == 10
    assert payload["peers_per_region_max"] == 10
    assert payload["self_peers"] == 0
    assert payload["duplicate_peers"] == 0
    assert set(payload["peer_feature_stats"]) == {
        "population",
        "population_density",
        "municipality_count",
    }
    assert payload["reciprocal_peer_rate"] > 0
    assert payload["peer_hubness"]["max"] == 19


def test_radar_qc_counts_are_locked():
    payload = qc()
    assert payload["radar_counts"] == {
        "NEED_HIGH": 71,
        "CAPACITY_LOW": 38,
        "MISMATCH_MARKED_POSITIVE": 68,
        "CAPACITY_COMPONENT_LOW": 184,
        "SPATIAL_HH_MISMATCH": 60,
    }
    assert payload["matched_signal_families_distribution"] == {
        "0": 187,
        "1": 139,
        "2": 67,
        "3": 39,
        "4": 4,
        "5": 3,
    }

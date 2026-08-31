"""Versioned ASMR correction. Historical files are read-only inputs, never outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import subprocess
import tempfile
import zipfile
from decimal import Decimal
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from esda.moran import Moran, Moran_Local
from libpysal.weights import KNN, W
from scipy.stats import spearmanr

from scripts import build_territorial_intelligence as ti
from scripts.validate_phase3_source_gate import selected_dbf

ROOT = Path(__file__).resolve().parents[1]
OLD = "MDB_ANALYTICAL_2024_1"
NEW = "MDB_ANALYTICAL_2024_2"
METHOD = "MDB_METHOD_1.1"
INTELLIGENCE = "MDB_TERRITORIAL_INTELLIGENCE_1.1"
AUDIT = ROOT / "audit_results/scientific_correction"
EVIDENCE = ROOT / "metadata/corrections/evidence"
BUNDLE = ROOT / "data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle"
WHO_URL = (
    "https://cdn.who.int/media/docs/default-source/gho-documents/"
    "global-health-estimates/gpe_discussion_paper_series_paper31_2001_age_standardization_rates.pdf"
)
WHO_TABLE4 = (
    "8.86",
    "8.69",
    "8.60",
    "8.47",
    "8.22",
    "7.93",
    "7.61",
    "7.15",
    "6.59",
    "6.04",
    "5.37",
    "4.55",
    "3.72",
    "2.96",
    "2.21",
    "1.52",
    "0.91",
    "0.44",
    "0.15",
    "0.04",
    "0.005",
)
SEED = 20260823
PERMUTATIONS = 9999


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def weights(table1=False):
    detailed = [Decimal(v) for v in WHO_TABLE4]
    terminal = Decimal("1.54") if table1 else sum(detailed[16:])
    collapsed = detailed[:16] + [terminal]
    return np.array([float(v / sum(collapsed)) for v in collapsed])


def percentile(values):
    return (values.rank(method="average") - 1) / max(values.notna().sum() - 1, 1)


def verify_history():
    checks = json.loads((ROOT / "audit_results/phase3_protected_hashes.json").read_text())["files"]
    for item in checks:
        item["observed"] = sha256(ROOT / item["path"])
        if item["observed"] != item["expected"]:
            raise ValueError(f"Historical hash mismatch: {item['path']}")
    return checks


def materialized_source(path, url, expected_hash):
    if path.exists() and not (path.stat().st_flags & 0x40000000):
        if sha256(path) != expected_hash:
            raise ValueError(f"Source hash mismatch: {path}")
        return path
    recovery = ROOT / "data/raw/scientific_correction_recovery" / path.name
    if recovery.exists() and sha256(recovery) == expected_hash:
        return recovery
    recovery.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mdb-source-recovery-") as directory:
        target = Path(directory) / path.name
        subprocess.run(
            ["curl", "-fsSL", "--retry", "2", "--max-time", "300", url, "-o", str(target)],
            check=True,
        )
        if sha256(target) != expected_hash:
            raise ValueError(f"Official recovery hash mismatch: {path.name}")
        recovery.write_bytes(target.read_bytes())
    return recovery


def asmr_from_bands(deaths, population, table1=False):
    """Both inputs have a complete region x 17 observable-band index."""
    if population.index.has_duplicates or deaths.index.has_duplicates:
        raise ValueError("Duplicate region/age-band")
    if not population.index.equals(deaths.index):
        raise ValueError("Numerator/denominator age alignment mismatch")
    if (population <= 0).any() or not np.isfinite(population).all():
        raise ValueError("Nonpositive or missing age denominator")
    if (deaths < 0).any() or not np.isfinite(deaths).all():
        raise ValueError("Invalid death numerator")
    age_weights = population.index.get_level_values("band").map(dict(enumerate(weights(table1))))
    if pd.isna(age_weights).any():
        raise ValueError("Unsupported age band")
    return (deaths / population * 100000 * age_weights).groupby(level=0).sum()


def load_ages(old):
    cross = pd.read_parquet(
        ROOT / f"data/canonical/{OLD}/municipality_health_region_crosswalk.parquet"
    )
    mapping = dict(
        zip(cross.municipality_code_ibge.astype(str).str[:6], cross.health_region_code, strict=True)
    )
    manifest = list(
        csv.DictReader(
            (ROOT / "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv").open()
        )
    )
    population_parts, provenance = [], []
    for year in (2022, 2023, 2024):
        entry = next(r for r in manifest if Path(r["filename"]).name == f"POPSBR{year % 100}.zip")
        path = Path(entry["filename"])
        path = materialized_source(path, entry["url"], entry["sha256"])
        if sha256(path) != entry["sha256"]:
            raise ValueError("POPSVS source hash mismatch")
        provenance.append({"path": str(path), "sha256": entry["sha256"]})
        with tempfile.TemporaryDirectory(prefix="mdb-pop-") as directory:
            with zipfile.ZipFile(path) as archive:
                members = [n for n in archive.namelist() if n.lower().endswith(".dbf")]
                if len(members) != 1:
                    raise ValueError("Ambiguous population archive")
                extracted = Path(directory) / "population.dbf"
                extracted.write_bytes(archive.read(members[0]))
            frame = selected_dbf(extracted, ["COD_MUN", "ANO", "SEXO", "IDADE", "POP"])
        if frame.duplicated(["COD_MUN", "ANO", "SEXO", "IDADE"]).any():
            raise ValueError("Duplicate population key")
        if set(frame.IDADE.astype(int)) != set(range(81)) or set(frame.ANO) != {str(year)}:
            raise ValueError("Unexpected POPSVS age/year definition")
        frame["health_region_code"] = frame.COD_MUN.str[:6].map(mapping)
        if frame.health_region_code.isna().any():
            raise ValueError("Unmapped population municipality")
        frame["band"] = np.minimum(frame.IDADE.astype(int) // 5, 16)
        frame["population"] = frame.POP.astype("int64")
        population_parts.append(frame.groupby(["health_region_code", "band"]).population.sum())
    population = pd.concat(population_parts).groupby(level=[0, 1]).sum().sort_index()
    cached = ROOT / "data/staging/phase3/sim_locked_suicide_age.parquet"
    deaths = pd.read_parquet(cached)
    provenance.append(
        {
            "path": str(cached.relative_to(ROOT)),
            "sha256": sha256(cached),
            "derivation": "81 hash-verified SIM 2022-2024 sources; Phase 3 source audit",
        }
    )
    deaths["health_region_code"] = deaths.CODMUNRES.map(mapping)
    unmapped = int(deaths.loc[deaths.health_region_code.isna(), "deaths"].sum())
    deaths = deaths.dropna(subset=["health_region_code"])
    total = (
        deaths.groupby("health_region_code")
        .deaths.sum()
        .reindex(old.health_region_code, fill_value=0)
    )
    if not np.array_equal(total.to_numpy(), old.suicide_deaths.to_numpy()):
        raise ValueError("Crude suicide counts differ from historical source")
    restored = int(deaths.loc[deaths.band >= 17, "deaths"].sum())
    unknown = int(deaths.loc[deaths.band < 0, "deaths"].sum())
    included = deaths.loc[deaths.band >= 0].copy()
    included["band"] = included.band.clip(upper=16)
    numerator = included.groupby(["health_region_code", "band"]).deaths.sum()
    numerator = numerator.reindex(population.index, fill_value=0)
    if len(population) != 439 * 17 or numerator.sum() + unknown != total.sum():
        raise ValueError("Age-band conservation failure")
    joined = pd.concat([population.rename("person_years"), numerator.rename("deaths")], axis=1)
    joined.to_csv(AUDIT / "corrected_age_specific_inputs.csv")
    return (
        numerator,
        population,
        {
            "restored_85plus_deaths": restored,
            "unknown_age_excluded": unknown,
            "unmapped_deaths": unmapped,
            "all_mapped_suicide_deaths": int(total.sum()),
            "sources": provenance,
        },
    )


def spatial(frame, geom, kind="queen"):
    order = sorted(frame.health_region_code.astype(str))
    a = frame.set_index("health_region_code").loc[order]
    g = geom.set_index("health_region_code").loc[order].reset_index()
    if len(order) != 439 or len(set(order)) != 439:
        raise ValueError("Expected 439 unique spatial IDs")
    if kind == "queen":
        neighbors = {c: set() for c in order}
        left, right = g.sindex.query(g.geometry, predicate="intersects")
        for i, j in zip(left, right, strict=True):
            if i != j:
                neighbors[order[i]].add(order[j])
                neighbors[order[j]].add(order[i])
        w = W({c: sorted(ns) for c, ns in neighbors.items()}, ids=order)
    else:
        w = KNN.from_dataframe(g.to_crs("EPSG:5880"), k=6, ids=order)
    w.transform = "R"
    if list(w.id_order) != order or w.islands:
        raise ValueError("Spatial order mismatch or islands")
    raw = a.mismatch_score.to_numpy(float)
    x = (raw - raw.mean()) / raw.std(ddof=1)
    np.random.seed(SEED)
    mor = Moran(x, w, permutations=PERMUTATIONS)
    np.random.seed(SEED)
    # Preserve historical NumPy-seeded ESDA call, including seed=None behavior.
    loc = Moran_Local(x, w, permutations=PERMUTATIONS, n_jobs=1)
    p = np.asarray(loc.p_sim)
    indices = np.argsort(p, kind="mergesort")
    q = np.empty(len(p))
    q[indices] = np.minimum(
        1, np.minimum.accumulate((p[indices] * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    )
    lag = w.sparse @ x
    cluster = np.select(
        [(x > 0) & (lag > 0), (x < 0) & (lag < 0), (x > 0) & (lag < 0), (x < 0) & (lag > 0)],
        ["high-high", "low-low", "high-low", "low-high"],
        default="zero",
    )
    result = pd.DataFrame(
        {
            "health_region_code": order,
            "lisa_local_i": loc.Is,
            "lisa_p": p,
            "lisa_q": q,
            "lisa_significant": q <= 0.10,
            "lisa_cluster": np.where(q <= 0.10, cluster, "not_significant"),
        }
    )
    manual = len(x) / w.s0 * float(x @ w.sparse @ x) / float(x @ x)
    if abs(manual - mor.I) > 1e-12:
        raise ValueError("Independent Moran identity failed")
    return result, {
        "I": float(mor.I),
        "pseudo_p": float(mor.p_sim),
        "manual_I": manual,
        "permutations": PERMUTATIONS,
        "seed": SEED,
        "weights": kind,
        "islands": len(w.islands),
        "FDR_q": 0.10,
        "clusters": {
            c: int((result.lisa_cluster == c).sum())
            for c in ["high-high", "low-low", "high-low", "low-high", "not_significant"]
        },
    }


def corrected_frame(old, asmr):
    new = old.copy(deep=True)
    new["release_id"] = NEW
    new["method_version"] = METHOD
    new["suicide_asmr"] = asmr.reindex(old.health_region_code).to_numpy()
    new["suicide_percentile"] = percentile(new.suicide_asmr)
    new["need_score"] = (new.suicide_percentile + new.psychiatric_admission_percentile) / 2
    new["mismatch_score"] = new.need_score - new.capacity_score
    return new


def apply_spatial(frame, lisa):
    out = frame.copy()
    for c in lisa.columns.drop("health_region_code"):
        out[c] = lisa.set_index("health_region_code")[c].reindex(out.health_region_code).to_numpy()
    return out


def set_comparison(old, new):
    result = {}
    for label in ["significant", "high-high", "low-low", "high-low", "low-high"]:
        a = set(
            old.loc[
                old.lisa_significant if label == "significant" else old.lisa_cluster.eq(label),
                "health_region_code",
            ]
        )
        b = set(
            new.loc[
                new.lisa_significant if label == "significant" else new.lisa_cluster.eq(label),
                "health_region_code",
            ]
        )
        result[label] = {
            "legacy_n": len(a),
            "corrected_n": len(b),
            "gained": sorted(b - a),
            "lost": sorted(a - b),
            "jaccard": len(a & b) / len(a | b) if a | b else 1.0,
        }
    return result


def write_parquet_immutable(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = pa.BufferOutputStream()
    pq.write_table(
        pa.Table.from_pandas(frame, preserve_index=False), buffer, compression="zstd", version="2.6"
    )
    payload = buffer.getvalue().to_pybytes()
    digest = hashlib.sha256(payload).hexdigest()
    if path.exists():
        if sha256(path) != digest:
            raise ValueError(f"IMMUTABILITY VIOLATION: {path}")
    else:
        path.write_bytes(payload)
    return digest


def sensitivities(old, new, geom):
    source = pd.read_csv(
        BUNDLE / "analytical_release/health_region_analysis_dataset_corrected.csv",
        dtype={"health_region_code": str},
    ).set_index("health_region_code")
    source = source.loc[new.health_region_code].reset_index()
    adm = new.psychiatric_admission_percentile
    cap = new.capacity_score
    global_rate = source.deaths_pooled.sum() / source.person_years.sum() * 100000
    shrink = source.deaths_pooled / (source.deaths_pooled + 10)
    def z(s):
        return (s - s.mean()) / s.std(ddof=1)
    specs = {
        "S1": ((percentile(source.deaths_2024 / source.population_2024 * 100000) + adm) / 2, cap),
        "S2": ((percentile(source.crude_rate) + adm) / 2, cap),
        "S3": ((percentile(shrink * new.suicide_asmr + (1 - shrink) * global_rate) + adm) / 2, cap),
        "S4": (percentile(new.suicide_asmr), cap),
        "S5": (
            new.need_score,
            (new.caps_percentile + new.beds_percentile + percentile(source.headcount_rate_per_100k))
            / 3,
        ),
        "S6": (new.need_score, cap),
        "S7": (
            (z(new.suicide_asmr) + z(new.psychiatric_admission_rate)) / 2,
            (z(new.caps_rate) + z(new.mental_health_beds_sus_rate) + z(new.psychiatrist_fte_rate))
            / 3,
        ),
        "S8": (
            new.need_score,
            pd.concat(
                [
                    (new.beds_percentile + new.psychiatrist_fte_percentile) / 2,
                    (new.caps_percentile + new.psychiatrist_fte_percentile) / 2,
                    (new.caps_percentile + new.beds_percentile) / 2,
                ],
                axis=1,
            ).mean(axis=1),
        ),
        "S9": (new.need_score, cap),
    }
    summaries = []
    for sid, (need, capacity) in specs.items():
        frame = new.copy()
        frame["need_score"], frame["capacity_score"] = need, capacity
        frame["mismatch_score"] = need - capacity
        lisa, stat = spatial(frame, geom, "knn" if sid == "S6" else "queen")
        if sid == "S9":
            frame["low_count_flag_only_not_excluded"] = frame.suicide_deaths < 10
        frame[["health_region_code", "need_score", "capacity_score", "mismatch_score"]].to_csv(
            AUDIT / f"{sid}_scores.csv", index=False
        )
        lisa.to_csv(AUDIT / f"{sid}_lisa.csv", index=False)
        hh = set(lisa.loc[lisa.lisa_cluster.eq("high-high"), "health_region_code"])
        hh_primary = set(new.loc[new.lisa_cluster.eq("high-high"), "health_region_code"])
        summaries.append(
            {
                "sensitivity": sid,
                "moran": stat["I"],
                "pseudo_p": stat["pseudo_p"],
                "significant": int(lisa.lisa_significant.sum()),
                "HH": len(hh),
                "HH_overlap_primary": len(hh & hh_primary),
                "spearman_primary": float(
                    spearmanr(new.mismatch_score, frame.mismatch_score).statistic
                ),
                "legacy_method_limitation": "flag-only; not an exclusion analysis"
                if sid == "S9"
                else "average of three leave-one-out capacity means is algebraically original mean"
                if sid == "S8"
                else "prespecified count-weighted shrinkage; not a fitted EB model"
                if sid == "S3"
                else "",
            }
        )
        print(f"Sensitivity {sid}: Moran={stat['I']:.9f}, HH={len(hh)}", flush=True)
    pd.DataFrame(summaries).to_csv(AUDIT / "sensitivity_summary.csv", index=False)
    return summaries


def downstream(old, new):
    intel = ti.build_intelligence(new, INTELLIGENCE, int(new.lisa_cluster.eq("high-high").sum()))
    peers, peer_stats = ti.build_peers(new)
    benchmarks = ti.build_peer_benchmarks(new, peers)
    previous = ROOT / f"data/product_intelligence/{OLD}"
    old_peers = pd.read_parquet(previous / "health_region_peers.parquet")
    columns = ["health_region_code", "peer_health_region_code", "peer_rank", "structural_distance"]
    pd.testing.assert_frame_equal(peers[columns], old_peers[columns], check_exact=True)
    old_benchmarks = pd.read_parquet(previous / "peer_benchmarks.parquet")
    keep = ~benchmarks.metric_id.isin(["need_score", "mismatch_score", "suicide_asmr"])
    pd.testing.assert_frame_equal(
        benchmarks.loc[keep].drop(columns="release_id").reset_index(drop=True),
        old_benchmarks.loc[keep].drop(columns="release_id").reset_index(drop=True),
        check_exact=True,
    )
    output = ROOT / f"data/product_intelligence/{NEW}"
    hashes = {
        name: write_parquet_immutable(frame, output / name)
        for name, frame in [
            ("health_region_intelligence.parquet", intel),
            ("health_region_peers.parquet", peers),
            ("peer_benchmarks.parquet", benchmarks),
        ]
    }
    old_intel = pd.read_parquet(previous / "health_region_intelligence.parquet")
    counts = {
        c.upper(): {"legacy": int(old_intel[c].sum()), "corrected": int(intel[c].sum())}
        for c in ti.RADAR_FAMILIES
    }
    write_json(AUDIT / "radar_comparison.json", counts)
    version = yaml.safe_load(
        (ROOT / "metadata/product_intelligence/MDB_TERRITORIAL_INTELLIGENCE_1.0.yaml").read_text()
    )
    version.update(
        {
            "intelligence_version": INTELLIGENCE,
            "status": "CANDIDATE_VALIDATION_PENDING",
            "release_id": NEW,
            "canonical_input": f"data/canonical/{NEW}/health_regions.parquet",
            "canonical_input_sha256": sha256(ROOT / f"data/canonical/{NEW}/health_regions.parquet"),
            "outputs": hashes,
        }
    )
    (ROOT / f"metadata/product_intelligence/{INTELLIGENCE}.yaml").write_text(
        yaml.safe_dump(version, sort_keys=False)
    )
    return counts, hashes, intel, old_intel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    history = verify_history()
    old = pd.read_parquet(ROOT / f"data/canonical/{OLD}/health_regions.parquet")
    old = old.sort_values("health_region_code").reset_index(drop=True)
    geom = gpd.read_file(BUNDLE / "geography/health_regions_LOCKED.gpkg")
    geom.health_region_code = geom.health_region_code.astype(str)
    print("Reproducing historical spatial baseline", flush=True)
    lisa, stats = spatial(old, geom)
    agreement = {
        c: bool(np.allclose(lisa[c], old[c], atol=1e-12, rtol=0))
        for c in ["lisa_local_i", "lisa_p", "lisa_q", "lisa_significant"]
    }
    lisa.to_csv(AUDIT / "historical_spatial_recomputed.csv", index=False)
    differences = {
        c: {
            "max_abs": float((lisa[c] - old[c]).abs().max()),
            "rows": int(((lisa[c] - old[c]).abs() > 1e-12).sum()),
        }
        for c in ["lisa_local_i", "lisa_p", "lisa_q"]
    }
    write_json(
        AUDIT / "historical_spatial_reproduction.json",
        {
            "spatial": stats,
            "column_agreement": agreement,
            "differences": differences,
            "history": history,
            "runtime": {
                p: importlib.metadata.version(p)
                for p in ["numpy", "pandas", "esda", "libpysal", "numba", "geopandas", "pyarrow"]
            },
        },
    )
    print(
        json.dumps({"historical": stats, "agreement": agreement, "differences": differences}),
        flush=True,
    )
    if (
        not agreement["lisa_local_i"]
        or not agreement["lisa_significant"]
        or abs(stats["I"] - 0.5254943888435958) > 1e-12
    ):
        raise ValueError("Historical spatial reproduction failed; investigate before release")
    if args.baseline_only:
        return
    deaths, population, source_qc = load_ages(old)
    new = corrected_frame(old, asmr_from_bands(deaths, population))
    new_lisa, new_stats = spatial(new, geom)
    new = apply_spatial(new, new_lisa)
    write_json(AUDIT / "corrected_spatial.json", new_stats)
    new_lisa.to_csv(AUDIT / "corrected_lisa.csv", index=False)
    write_json(AUDIT / "age_source_qc.json", source_qc)
    output = ROOT / f"data/canonical/{NEW}"
    output.mkdir(parents=True, exist_ok=True)
    changed_columns = {
        "release_id",
        "method_version",
        "suicide_asmr",
        "suicide_percentile",
        "need_score",
        "mismatch_score",
        *new_lisa.columns.drop("health_region_code"),
    }
    unchanged = [c for c in old if c not in changed_columns]
    pd.testing.assert_frame_equal(old[unchanged], new[unchanged], check_exact=True)
    canonical_hash = write_parquet_immutable(new, output / "health_regions.parquet")
    rounding = corrected_frame(old, asmr_from_bands(deaths, population, table1=True))
    rounding_lisa, rounding_stats = spatial(rounding, geom)
    rounding = apply_spatial(rounding, rounding_lisa)
    rounding_result = {
        "primary_terminal_raw": 1.545,
        "sensitivity_terminal_raw": 1.54,
        "max_abs": {
            c: float((new[c] - rounding[c]).abs().max())
            for c in ["suicide_asmr", "suicide_percentile", "need_score", "mismatch_score"]
        },
        "moran_difference": rounding_stats["I"] - new_stats["I"],
        "lisa_membership_difference": int(
            (new.lisa_significant != rounding.lisa_significant).sum()
        ),
        "lisa_label_difference": int((new.lisa_cluster != rounding.lisa_cluster).sum()),
    }
    write_json(AUDIT / "who_rounding_sensitivity.json", rounding_result)
    sensitivity_results = sensitivities(old, new, geom)
    radar, intelligence_hashes, intel, old_intel = downstream(old, new)
    impact = new[["health_region_code", "health_region_name", "uf"]].rename(
        columns={"health_region_name": "name"}
    )
    impact["capacity"] = new.capacity_score
    summary = {}
    for c in ["suicide_asmr", "suicide_percentile", "need_score", "mismatch_score"]:
        label = c.removesuffix("_score")
        delta = new[c] - old[c]
        impact[f"legacy_{label}"], impact[f"corrected_{label}"], impact[f"delta_{label}"] = (
            old[c],
            new[c],
            delta,
        )
        summary[c] = {
            "changed_regions": int((delta.abs() > 1e-12).sum()),
            "min_delta": float(delta.min()),
            "median_delta": float(delta.median()),
            "max_delta": float(delta.max()),
            "legacy_median": float(old[c].median()),
            "corrected_median": float(new[c].median()),
        }
    impact["legacy_lisa"], impact["corrected_lisa"] = old.lisa_cluster, new.lisa_cluster
    for label, frame in [("legacy", old_intel), ("corrected", intel)]:
        impact[f"{label}_radar_families"] = frame.apply(
            lambda row: ";".join(c.upper() for c in ti.RADAR_FAMILIES if row[c]), axis=1
        )
    impact["flags"] = new.data_quality_flags.map(lambda v: ";".join(v))
    impact.to_csv(ROOT / "audit_results/scientific_correction_region_impact.csv", index=False)
    heterogeneity = pd.DataFrame(
        {
            "legacy_iqr": old.groupby("uf").mismatch_score.quantile(0.75)
            - old.groupby("uf").mismatch_score.quantile(0.25),
            "corrected_iqr": new.groupby("uf").mismatch_score.quantile(0.75)
            - new.groupby("uf").mismatch_score.quantile(0.25),
        }
    )
    heterogeneity.to_csv(AUDIT / "state_heterogeneity.csv")
    comparison = set_comparison(old, new)
    write_json(AUDIT / "spatial_comparison.json", comparison)
    qc = {
        "status": "CANDIDATE_SCIENTIFIC_OUTPUTS_COMPUTED_NOT_CURRENT",
        "canonical_sha256": canonical_hash,
        "impact": summary,
        "spatial": new_stats,
        "spatial_comparison": comparison,
        "radar": radar,
        "intelligence_hashes": intelligence_hashes,
        "peer_relationships_unchanged": True,
        "capacity_changed_regions": 0,
        "admissions_changed_regions": 0,
        "crude_suicide_counts_unchanged": True,
        "small_suicide_count": int((new.suicide_deaths < 10).sum()),
        "zero_registered_beds": int((new.mental_health_beds_sus_count == 0).sum()),
        "who_terminal_normalized": float(weights()[-1]),
        "rounding": rounding_result,
        "source_qc": source_qc,
        "sensitivities": sensitivity_results,
        "historical_spatial_runtime_difference": differences,
        "historical_hashes": verify_history(),
    }
    write_json(AUDIT / "correction_summary.json", qc)
    print(json.dumps(new_stats), flush=True)


if __name__ == "__main__":
    main()

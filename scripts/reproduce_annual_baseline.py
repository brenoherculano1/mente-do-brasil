"""Read-only reproduction gate for the corrected 2024 canonical release."""

import argparse
import importlib.metadata
import json
import tempfile
from pathlib import Path

import pandas as pd

from scripts import build_scientific_correction as correction


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must not already exist")
    root = correction.ROOT
    target = root / f"data/canonical/{correction.NEW}/health_regions.parquet"
    protected = sorted(
        set(
            list((root / "data/canonical").rglob("*.parquet"))
            + list((root / "metadata/releases").glob("*.yaml"))
            + list((root / "metadata/methods").glob("*.yaml"))
        )
    )
    before = {str(p.relative_to(root)): correction.sha256(p) for p in protected}
    result = {
        "release": correction.NEW,
        "status": "FAIL",
        "scope": (
            "Current correction builder from frozen prior canonical, cached SIM age counts "
            "and original POPSVS; not a full raw SIM/SIH/CNES re-extraction"
        ),
        "runtime": {
            p: package_version(p)
            for p in ["numpy", "pandas", "esda", "libpysal", "numba", "geopandas", "pyarrow"]
        },
        "protected_before": before,
    }
    original_materializer = correction.materialized_source
    original_audit = correction.AUDIT

    def read_only_source(path, url, expected_hash):
        candidate = root / "data/raw/scientific_correction_recovery" / path.name
        if not candidate.exists():
            candidate = path
        if not candidate.exists() or correction.sha256(candidate) != expected_hash:
            raise ValueError(f"Missing or changed frozen population input: {path.name}")
        return candidate

    try:
        correction.verify_history()
        correction.materialized_source = read_only_source
        with tempfile.TemporaryDirectory(prefix="mdb-baseline-") as directory:
            correction.AUDIT = Path(directory)
            old = pd.read_parquet(root / f"data/canonical/{correction.OLD}/health_regions.parquet")
            old = old.sort_values("health_region_code").reset_index(drop=True)
            deaths, population, qc = correction.load_ages(old)
            rebuilt = correction.corrected_frame(
                old, correction.asmr_from_bands(deaths, population)
            )
            geom = correction.gpd.read_file(
                correction.BUNDLE / "geography/health_regions_LOCKED.gpkg"
            )
            geom.health_region_code = geom.health_region_code.astype(str)
            lisa, spatial = correction.spatial(rebuilt, geom)
            rebuilt = correction.apply_spatial(rebuilt, lisa)
            expected = pd.read_parquet(target)
            result["spatial"] = spatial
            result["source_qc"] = qc
            result["column_exact_match"] = {
                column: rebuilt[column].equals(expected[column]) for column in expected.columns
            }
            digest = correction.write_parquet_immutable(
                rebuilt, Path(directory) / "reproduced.parquet"
            )
            result["reproduced_sha256"] = digest
            result["expected_sha256"] = before[str(target.relative_to(root))]
            result["byte_identical"] = digest == result["expected_sha256"]
            result["status"] = "PASS" if result["byte_identical"] else "FAIL"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        correction.materialized_source = original_materializer
        correction.AUDIT = original_audit
        result["protected_changed"] = [
            name for name, digest in before.items() if correction.sha256(root / name) != digest
        ]
        if result["protected_changed"]:
            result["status"] = "FAIL"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k not in {"protected_before", "source_qc"}})
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

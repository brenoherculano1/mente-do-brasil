"""Run the existing serving loader against an explicit versioned release."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path


def configure(loader, release_id: str) -> None:
    if release_id != "MDB_ANALYTICAL_2024_2":
        raise ValueError("This wrapper is only for the explicit corrected release.")
    loader.RELEASE_ID = release_id
    loader.CANONICAL_VERSION = "MDB_CANONICAL_1.1"
    loader.METHOD_VERSION = "MDB_METHOD_1.1"
    loader.INTELLIGENCE_VERSION = "MDB_TERRITORIAL_INTELLIGENCE_1.1"
    loader.CANONICAL_INPUT_HASH = loader.sha256_file(
        loader.repo_root() / f"data/canonical/{release_id}/health_regions.parquet"
    )
    loader.CANONICAL_MANIFEST = Path(f"metadata/releases/{release_id}_canonical.yaml")
    loader.SCIENTIFIC_RELEASE = Path(f"metadata/releases/{release_id}.yaml")
    loader.SERVING_RELEASE = Path(f"metadata/releases/{release_id}_serving.yaml")
    loader.PRODUCT_INTELLIGENCE_DIR = Path(f"data/product_intelligence/{release_id}")
    loader.GLOBAL_MORAN = Path("audit_results/scientific_correction/corrected_spatial.json")
    loader.LOCKED_GLOBAL_MORAN_I = 0.5256454566660947
    loader.EXPECTED_LISA = {"total": 136, "high-high": 60, "low-low": 65,
                            "high-low": 5, "low-high": 6}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", default="MDB_ANALYTICAL_2024_2")
    args = parser.parse_args()
    loader = importlib.import_module("scripts.load_serving_database")
    configure(loader, args.release)
    return loader.main()


if __name__ == "__main__":
    raise SystemExit(main())

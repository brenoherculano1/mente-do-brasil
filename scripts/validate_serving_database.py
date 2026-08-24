"""Validate the local Mente do Brasil serving database."""

from __future__ import annotations

import json
from pathlib import Path

import importlib.util


def load_loader_module():
    path = Path(__file__).resolve().with_name("load_serving_database.py")
    spec = importlib.util.spec_from_file_location("load_serving_database", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    loader = load_loader_module()
    print("SERVING DATABASE VALIDATION")
    try:
        root = loader.repo_root()
        manifest = loader.validate_canonical_manifest(root)
        loader.validate_scientific_locks(root)
        release = loader.release_values(manifest)
        with loader.connect() as connection:
            checks = loader.validate_database(connection, release)
    except Exception as exc:
        print("release: FAIL")
        print("geography: FAIL")
        print("metrics: FAIL")
        print("geometry: FAIL")
        print("LISA: FAIL")
        print("flags: FAIL")
        print("constraints: FAIL")
        print("views: FAIL")
        print("immutability: FAIL")
        print(f"FAIL: {exc}")
        return 1

    sections = {
        "release": checks["releases"] == 1,
        "geography": checks["health_regions"] == 439 and checks["municipalities"] == 5570,
        "metrics": checks["metrics"] == 439,
        "geometry": checks["srid_4674"] == 439 and checks["valid_geom"] == 439,
        "LISA": checks["lisa_significant"] == 135,
        "flags": checks["small_suicide"] == 7 and checks["zero_beds"] == 275,
        "constraints": True,
        "views": checks["profile"] == 439 and checks["map"] == 439 and checks["lookup"] == 439,
        "immutability": True,
    }
    for name, passed in sections.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(json.dumps(checks, indent=2, sort_keys=True))
    if not all(sections.values()):
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# ruff: noqa: E501
"""Build the immutable, deterministic MDB_OPEN_DATA_2024_1 candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from scripts.open_platform_spec import (
    ANALYTICAL_RELEASE,
    CORE_DESCRIPTIONS,
    DATA_GOVERNANCE_VERSION,
    DATASET_CAVEATS,
    DATASETS,
    FIELD_REGISTRY_VERSION,
    GEOGRAPHY_VERSION,
    OPEN_DATA_RELEASE,
    OPEN_PLATFORM_VERSION,
    PUBLIC_API_VERSION,
    PUBLIC_RELEASE_DIR,
    ROOT,
    SOURCE_RIGHTS_VERSION,
    WEB_GEOMETRY_VERSION,
)

BUILT_AT = "2026-09-01T00:00:00Z"
ZIP_TIME = (2026, 9, 1, 0, 0, 0)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_lists(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in frame.columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].map(
                lambda value: (
                    "|".join(map(str, value))
                    if isinstance(value, (list, tuple)) or type(value).__name__ == "ndarray"
                    else value
                )
            )
    return frame


def public_frame(name: str, spec: dict) -> pd.DataFrame:
    frame = pd.read_parquet(spec["source"])
    if spec.get("filter") == "public_flows":
        frame = frame.loc[(~frame["suppressed"]) & frame["admissions"].notna()]
        frame = frame.loc[frame["admissions"] >= 5]
        frame["admissions"] = frame["admissions"].astype("int64")
    if "columns" in spec:
        frame = frame[spec["columns"]]
    if "exclude" in spec:
        frame = frame.drop(columns=spec["exclude"])
    for column, decimals in spec.get("round", {}).items():
        frame[column] = frame[column].round(decimals)
    frame = normalize_lists(frame).sort_values(spec["key"], kind="stable").reset_index(drop=True)
    if "rows" in spec:
        assert len(frame) == spec["rows"], (name, len(frame), spec["rows"])
    assert not frame.duplicated(spec["key"]).any(), name
    return frame


def semantic_fingerprint(frame: pd.DataFrame) -> str:
    normalized = frame.where(pd.notna(frame), None).to_dict("records")
    return digest(json.dumps(normalized, sort_keys=True, ensure_ascii=True).encode())


def field_definition(dataset: str, field: str, series: pd.Series) -> dict:
    pt, en = CORE_DESCRIPTIONS.get(
        field,
        (
            field.replace("_", " ").capitalize() + ".",
            field.replace("_", " ").capitalize() + ".",
        ),
    )
    privacy = (
        "AGGREGATED_SMALL_CELL_PROTECTED"
        if dataset == "hospitalization_flows_public"
        else "PUBLIC_AGGREGATED"
    )
    return {
        "field_name": field,
        "dataset": dataset,
        "type": str(series.dtype),
        "nullable": bool(series.isna().any()),
        "unit": "documented_in_data_dictionary",
        "description_pt": pt,
        "description_en": en,
        "scientific_source": ANALYTICAL_RELEASE,
        "source_field": field,
        "transformation": (
            "allowlisted projection; BRL value rounded to database NUMERIC(20,2)"
            if dataset == "health_region_financing"
            and field in {"total_health_expenditure_brl", "health_expenditure_per_capita_brl"}
            else "allowlisted projection; no scientific recalculation"
        ),
        "privacy_class": privacy,
        "small_cell_rule": "exact values below five excluded"
        if dataset == "hospitalization_flows_public"
        else "not_applicable",
        "public_status": "PUBLIC",
        "reason": "Approved derived aggregate field.",
    }


def deterministic_parquet(frame: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(
        table,
        path,
        compression="zstd",
        compression_level=9,
        use_dictionary=False,
        write_statistics=True,
        version="2.6",
        data_page_version="1.0",
    )


def frictionless_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    return "string"


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n")


def legal_files(output: Path) -> None:
    docs = ROOT / "docs"
    write_text(output / "LICENSE_DATA.md", (docs / "licensing_and_attribution.md").read_text())
    write_text(output / "ATTRIBUTION.md", (docs / "open_data_attribution.md").read_text())
    write_text(output / "THIRD_PARTY_NOTICES.md", (docs / "third_party_notices.md").read_text())
    write_text(output / "SOURCES.md", (docs / "open_data_sources.md").read_text())
    write_text(output / "README.pt-BR.md", (docs / "open_data_readme_pt.md").read_text())
    write_text(output / "README.en.md", (docs / "open_data_readme_en.md").read_text())
    write_text(
        output / "CHANGELOG.md",
        "# Changelog\n\n## MDB_OPEN_DATA_2024_1\n\nInitial locked-local open-data release candidate. Not publicly launched.",
    )
    shutil.copyfile(ROOT / "CITATION.cff", output / "CITATION.cff")


def build(output: Path = PUBLIC_RELEASE_DIR) -> dict:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    legal_files(output)
    registry = {"version": FIELD_REGISTRY_VERSION, "fields": []}
    dictionary = []
    resources = []
    dataset_metadata = {}
    for name, spec in DATASETS.items():
        frame = public_frame(name, spec)
        csv_path, parquet_path = output / f"{name}.csv", output / f"{name}.parquet"
        frame.to_csv(csv_path, index=False, lineterminator="\n", float_format="%.17g")
        deterministic_parquet(frame, parquet_path)
        for field in frame.columns:
            definition = field_definition(name, field, frame[field])
            registry["fields"].append(definition)
            dictionary.append(
                {
                    "dataset": name,
                    "field": field,
                    "type": definition["type"],
                    "nullable": definition["nullable"],
                    "unit": definition["unit"],
                    "definition_pt": definition["description_pt"],
                    "definition_en": definition["description_en"],
                    "interpretation": DATASET_CAVEATS[name],
                    "source": ANALYTICAL_RELEASE,
                    "caveat": DATASET_CAVEATS[name],
                }
            )
        dataset_metadata[name] = {
            "rows": len(frame),
            "fields": list(frame.columns),
            "key": spec["key"],
            "semantic_sha256": semantic_fingerprint(frame),
            "caveat": DATASET_CAVEATS[name],
            "distributions": [
                {
                    "path": csv_path.name,
                    "bytes": csv_path.stat().st_size,
                    "sha256": digest(csv_path.read_bytes()),
                },
                {
                    "path": parquet_path.name,
                    "bytes": parquet_path.stat().st_size,
                    "sha256": digest(parquet_path.read_bytes()),
                },
            ],
        }
        resources.append(
            {
                "name": name,
                "path": f"{name}.csv",
                "format": "csv",
                "schema": {
                    "fields": [
                        {"name": column, "type": frictionless_type(frame[column])}
                        for column in frame.columns
                    ],
                    "primaryKey": spec["key"],
                },
            }
        )
    registry_path = ROOT / "metadata/open_platform/public_field_registry_v1.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False, allow_unicode=True))
    pd.DataFrame(dictionary).to_csv(
        output / "DATA_DICTIONARY.csv", index=False, lineterminator="\n"
    )
    write_text(
        output / "DATA_DICTIONARY.json", json.dumps(dictionary, indent=2, ensure_ascii=False)
    )
    write_text(
        output / "datapackage.json",
        json.dumps(
            {
                "profile": "tabular-data-package",
                "name": OPEN_DATA_RELEASE.lower(),
                "title": "Mente do Brasil Open Data 2024",
                "version": OPEN_DATA_RELEASE,
                "licenses": [{"name": "CC-BY-4.0", "path": "LICENSE_DATA.md"}],
                "resources": resources,
            },
            indent=2,
        ),
    )
    write_text(
        output / "dataset.jsonld",
        json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "Dataset",
                "name": "Mente do Brasil Open Data 2024",
                "description": "Derived regional mental-health territorial intelligence for Brazil.",
                "creator": {"@type": "Project", "name": "Mente do Brasil"},
                "version": OPEN_DATA_RELEASE,
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "temporalCoverage": "2022/2024",
                "spatialCoverage": "Brazil",
                "url": "https://mentedobrasil.com.br",
                "isAccessibleForFree": True,
                "keywords": [
                    "mental health",
                    "Brazil",
                    "health regions",
                    "territorial intelligence",
                ],
                "citation": "Mente do Brasil. Inteligência territorial em saúde mental no Brasil. Open Data Release MDB_OPEN_DATA_2024_1. 2026.",
            },
            indent=2,
            ensure_ascii=False,
        ),
    )
    release = {
        "open_platform_version": OPEN_PLATFORM_VERSION,
        "open_data_release_id": OPEN_DATA_RELEASE,
        "public_api_version": PUBLIC_API_VERSION,
        "data_governance_version": DATA_GOVERNANCE_VERSION,
        "analytical_release_id": ANALYTICAL_RELEASE,
        "method_version": "MDB_METHOD_1.1",
        "geography_version": GEOGRAPHY_VERSION,
        "web_geometry_version": WEB_GEOMETRY_VERSION,
        "built_at": BUILT_AT,
        "published_at": None,
        "status": "LOCKED_LOCAL",
        "public_release_status": "NOT_RELEASED",
        "writer": {"pyarrow": pyarrow.__version__, "pandas": pd.__version__},
        "license": "CC BY 4.0 for licensable Mente do Brasil original/derived rights; third-party exclusions apply.",
        "source_matrix_version": SOURCE_RIGHTS_VERSION,
        "datasets": dataset_metadata,
        "geometry_downloads": "NOT_PUBLISHED_PENDING_EXACT_SOURCE_RIGHTS",
        "supersedes": None,
        "superseded_by": None,
    }
    write_text(output / "release.json", json.dumps(release, indent=2, ensure_ascii=False))
    return finalize(output)


def finalize(output: Path) -> dict:
    excluded = {"MANIFEST.json", "CHECKSUMS.sha256"}
    entries = []
    for path in sorted(p for p in output.iterdir() if p.is_file() and p.name not in excluded):
        data = path.read_bytes()
        entries.append({"relative_path": path.name, "bytes": len(data), "sha256": digest(data)})
    manifest = {"release": OPEN_DATA_RELEASE, "files": entries}
    write_text(output / "MANIFEST.json", json.dumps(manifest, indent=2))
    checks = [f"{entry['sha256']}  {entry['relative_path']}" for entry in entries]
    checks.append(f"{digest((output / 'MANIFEST.json').read_bytes())}  MANIFEST.json")
    write_text(output / "CHECKSUMS.sha256", "\n".join(checks))
    archive = output.parent / f"{OPEN_DATA_RELEASE}.zip"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in sorted(output.iterdir()):
            if path.is_file():
                info = zipfile.ZipInfo(path.name, ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                package.writestr(info, path.read_bytes())
    return {
        "status": "PASS",
        "release_dir": str(output),
        "zip": str(archive),
        "zip_bytes": archive.stat().st_size,
        "zip_sha256": digest(archive.read_bytes()),
        "files": len(list(output.iterdir())),
        "built_at": datetime.fromisoformat(BUILT_AT.replace("Z", "+00:00")).isoformat(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PUBLIC_RELEASE_DIR)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))

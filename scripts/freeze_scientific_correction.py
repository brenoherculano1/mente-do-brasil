"""Freeze validated correction metadata without editing historical release metadata."""

import json
from datetime import datetime, timezone

import yaml

from scripts.build_scientific_correction import (
    AUDIT,
    EVIDENCE,
    INTELLIGENCE,
    METHOD,
    NEW,
    OLD,
    ROOT,
    WHO_TABLE4,
    WHO_URL,
    sha256,
    verify_history,
    weights,
)


def write_yaml(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def main():
    summary = json.loads((AUDIT / "correction_summary.json").read_text())
    determinism = json.loads((AUDIT / "determinism.json").read_text())
    sources = json.loads((AUDIT / "source_hash_verification.json").read_text())
    assert determinism["status"] == "PASS" and not determinism["mismatches"]
    assert sources["status"] == "PASS" and sources["rows"] == 980
    assert summary["source_qc"]["restored_85plus_deaths"] == 495
    assert summary["capacity_changed_regions"] == summary["admissions_changed_regions"] == 0
    verify_history()
    population_evidence = json.loads(
        (
            ROOT / "metadata/provenance/phase3_catalogs/"
            "NT-POPULACAO-RESIDENTE-2000-2024.text-extraction.json"
        ).read_text()
    )
    method = {
        "method_version": METHOD,
        "release_id": NEW,
        "status": "VALIDATED_SCIENTIFIC",
        "supersedes_method_for_current_use": "MDB_METHOD_1.0",
        "change_scope": (
            "ASMR observable terminal age group and official WHO weight representation only"
        ),
        "age_bands": [f"{i}-{i + 4}" for i in range(0, 80, 5)] + ["80+"],
        "popsvs_terminal_code": "080",
        "popsvs_terminal_definition": "80 years and over",
        "who_source_url": WHO_URL,
        "who_source_table": 4,
        "who_source_printed_page": 12,
        "published_detailed_weights": list(WHO_TABLE4),
        "published_weight_sum": "100.035",
        "raw_terminal_weight": "1.545",
        "normalized_weights": weights().tolist(),
        "unknown_age": "exclude from age-specific numerator; preserve crude counts and QC",
        "percentile": "(less + (equal - 1) / 2) / max(n_observed - 1, 1)",
        "unchanged": [
            "SIM years/ICD/residence",
            "admissions",
            "capacity",
            "geography",
            "spatial algorithm",
        ],
        "provenance": {
            "who_pdf_sha256": sha256(EVIDENCE / "WHO_Ahmad_2001_age_standardization.pdf"),
            "population_technical_note": population_evidence,
            "source_manifest": "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv",
            "correction_script_sha256": sha256(ROOT / "scripts/build_scientific_correction.py"),
        },
        "historical_runtime_local_p_limitation": summary["historical_spatial_runtime_difference"],
        "scientific_gate_evidence": "audit_results/scientific_correction/determinism.json",
    }
    write_yaml(ROOT / f"metadata/methods/{METHOD}.yaml", method)
    canonical = yaml.safe_load((ROOT / f"metadata/releases/{OLD}_canonical.yaml").read_text())
    canonical.update(
        {
            "release_id": NEW,
            "method_version": METHOD,
            "canonical_version": "MDB_CANONICAL_1.1",
            "generated_at": datetime.fromtimestamp(
                (ROOT / f"data/canonical/{NEW}/health_regions.parquet").stat().st_mtime,
                timezone.utc,
            ).isoformat(timespec="seconds"),
        }
    )
    canonical["outputs"][0].update(
        {
            "path": f"data/canonical/{NEW}/health_regions.parquet",
            "sha256": summary["canonical_sha256"],
            "source_files": [
                f"data/canonical/{OLD}/health_regions.parquet",
                "audit_results/scientific_correction/corrected_age_specific_inputs.csv",
                "audit_results/scientific_correction/corrected_lisa.csv",
            ],
        }
    )
    canonical["crosswalk_policy"] = (
        "Reference historical byte-preserved crosswalk; geography unchanged"
    )
    write_yaml(ROOT / f"metadata/releases/{NEW}_canonical.yaml", canonical)
    release = yaml.safe_load((ROOT / f"metadata/releases/{OLD}.yaml").read_text())
    release.update(
        {
            "release_id": NEW,
            "method_version": METHOD,
            "created_at": "2026-08-31",
            "correction_of": OLD,
            "scientific_status": "VALIDATED_CORRECTED",
            "immutability_rule": "Never overwrite different bytes under an existing release ID",
        }
    )
    spatial = release["locked_spatial_results"]
    spatial.update(
        {
            "recalculated_in_this_repository_foundation": True,
            "global_moran_i": summary["spatial"]["I"],
            "lisa_fdr_significant": 136,
            "hh": 60,
            "ll": 65,
            "hl": 5,
            "lh": 6,
        }
    )
    release["provenance"]["generated_outputs_manifest"] = f"metadata/releases/{NEW}_canonical.yaml"
    release["provenance"]["correction_method"] = f"metadata/methods/{METHOD}.yaml"
    write_yaml(ROOT / f"metadata/releases/{NEW}.yaml", release)
    notice = {
        "affected_release": OLD,
        "status": "SUPERSEDED_INTERNAL_BY_SCIENTIFIC_CORRECTION",
        "identified_date": "2026-08-31",
        "affected_indicator": "suicide_asmr",
        "issue": "495 mapped deaths age 85+ omitted from age-standardized contributions",
        "root_cause": "Population-supported terminal 80+ assigned to narrower 80-84 join key",
        "population_source_definition": "80+",
        "historical_implementation": "80+ denominator treated as 80-84",
        "excluded_85plus_deaths_from_asmr": 495,
        "replacement_release": NEW,
        "public_exposure": "NONE / NOT_RELEASED",
        "manuscript_impact": "MODERATE_RESULT_SET_CHANGE",
        "journal_action_required": True,
        "journal_action_executed": False,
        "history_preserved": True,
    }
    write_yaml(ROOT / f"metadata/corrections/{OLD}_ASMR_AGE_BAND_NOTICE.yaml", notice)
    old_indicators = ROOT / "metadata/indicators"
    for path in sorted(old_indicators.glob("*.yaml")):
        indicator = yaml.safe_load(path.read_text())
        indicator.update({"release_id": NEW, "method_version": METHOD})
        if path.stem == "suicide_asmr":
            indicator.update(
                {
                "standardization_method": (
                    "WHO 2001 Table 4 direct standardization; five-year bands "
                    "0-4 through 75-79, terminal 80+"
                ),
                "description": (
                    "Pooled 2022-2024 suicide mortality directly age-standardized "
                    "with observable terminal 80+"
                ),
                    "code_version": {
                        "script": "scripts/build_scientific_correction.py",
                        "sha256": sha256(ROOT / "scripts/build_scientific_correction.py"),
                    },
                }
            )
        write_yaml(old_indicators / NEW / path.name, indicator)
    path = ROOT / f"metadata/product_intelligence/{INTELLIGENCE}.yaml"
    metadata = yaml.safe_load(path.read_text())
    metadata["status"] = "VALIDATED_SCIENTIFIC"
    write_yaml(path, metadata)
    print("Scientific metadata frozen; current product pointer not changed by this command.")


if __name__ == "__main__":
    main()

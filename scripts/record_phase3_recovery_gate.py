"""Record the recovered inputs and offline financing dependency gate."""

import csv
import json
from pathlib import Path

import yaml

from scripts.preflight_local_artifacts import inspect_artifacts
from scripts.recover_phase3_artifacts import (
    BUNDLE,
    FINANCING_HASH,
    LOCKS,
    ROOT,
    SNAPSHOT,
    fingerprint,
    snapshot_semantics,
)


def main():
    artifacts = {}

    def add(
        relative,
        kind,
        version,
        provenance,
        required_for,
        expected=None,
        acceptance="ACCEPTED",
        source_class="versioned_release_artifact",
    ):
        relative = str(relative)
        observed = fingerprint(ROOT / relative) if (ROOT / relative).is_file() else None
        if expected and observed and acceptance == "ACCEPTED":
            assert observed == expected, relative
        locked = expected or observed or {}
        artifacts[relative] = {
            "relative_path": relative,
            "artifact_type": kind,
            "version": version,
            "bytes": locked.get("bytes"),
            "sha256": locked.get("sha256") if acceptance == "ACCEPTED" else None,
            "provenance": provenance,
            "source_location_class": source_class,
            "required_for": required_for,
            "redistributable_status": "NOT_ASSESSED",
            "acceptance_status": acceptance,
        }

    for version in ("MDB_ANALYTICAL_2024_1", "MDB_ANALYTICAL_2024_2"):
        manifest = f"metadata/releases/{version}_canonical.yaml"
        for output in yaml.safe_load((ROOT / manifest).read_text())["outputs"]:
            path = output["path"]
            add(
                path,
                "canonical_parquet",
                version,
                manifest,
                ["serving_rebuild"],
                {"bytes": (ROOT / path).stat().st_size, "sha256": output["sha256"]},
            )
        method = "1.0" if version.endswith("_1") else "1.1"
        provenance = f"metadata/product_intelligence/MDB_TERRITORIAL_INTELLIGENCE_{method}.yaml"
        for name, sha in yaml.safe_load((ROOT / provenance).read_text())["outputs"].items():
            path = f"data/product_intelligence/{version}/{name}"
            add(
                path,
                "intelligence_parquet",
                version,
                provenance,
                ["serving_rebuild"],
                {"bytes": (ROOT / path).stat().st_size, "sha256": sha},
            )
    for path, sha in LOCKS.items():
        if path not in artifacts:
            add(
                path,
                "advanced_parquet",
                "MDB_ANALYTICAL_2024_2",
                "phase3_recovery_user_locked_hashes_2026-08-31",
                ["serving_rebuild"],
                {"bytes": (ROOT / path).stat().st_size, "sha256": sha},
                source_class="allowlisted_read_only_donor",
            )
    financing = "data/product_intelligence/MDB_ANALYTICAL_2024_2/health_region_financing.parquet"
    add(
        financing,
        "advanced_parquet",
        "MDB_FINANCING_CONTEXT_1.0",
        "audit_results/financing_hash_transition.txt",
        ["serving_rebuild", "siops_reproduction_target"],
        {"bytes": (ROOT / financing).stat().st_size, "sha256": FINANCING_HASH},
    )
    manifest = json.loads((ROOT / BUNDLE / "IMPORT_MANIFEST.json").read_text())
    for item in manifest["files"]:
        add(
            BUNDLE / item["path"],
            "validated_import_bundle_member",
            manifest["bundle_id"],
            str(BUNDLE / "IMPORT_MANIFEST.json"),
            ["scientific_regression", "serving_rebuild"],
            {"bytes": item["bytes"], "sha256": item["sha256"]},
            source_class="allowlisted_read_only_donor",
        )
    add(
        BUNDLE / "IMPORT_MANIFEST.json",
        "validated_import_manifest",
        manifest["bundle_id"],
        "audit_results/phase3_import_bundle_validation.json",
        ["scientific_regression"],
        source_class="allowlisted_read_only_donor",
    )
    add(
        SNAPSHOT,
        "siops_snapshot_candidate",
        "MDB_SIOPS_SNAPSHOT_20260831_1",
        "metadata/provenance/siops_snapshot_recovery_2026-08-31.yaml",
        ["siops_reproduction_gate"],
        acceptance="PENDING_DERIVED_REPRODUCTION",
        source_class="allowlisted_read_only_donor",
    )
    source_manifest = "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv"
    pops = [
        r
        for r in csv.DictReader((ROOT / source_manifest).open())
        if r["source"] == "DATASUS IBGE POPSVS" and r["period"] in {"2022", "2023", "2024"}
    ]
    assert len(pops) == 3
    for item in pops:
        add(
            f"data/raw/scientific_correction_recovery/{Path(item['filename']).name}",
            "locked_population_source",
            f"POPSVS_{item['period']}",
            source_manifest,
            ["siops_reproduction_gate"],
            {"bytes": int(item["size"]), "sha256": item["sha256"]},
            source_class="locked_source_backup_recovery_not_yet_authorized",
        )
    # Include the exact versioned files consumed by the loaders, not just their data.
    dependencies = set((ROOT / "db/migrations").glob("*.sql"))
    dependencies.update((ROOT / "metadata/indicators").glob("*.yaml"))
    for version in ("MDB_ANALYTICAL_2024_1", "MDB_ANALYTICAL_2024_2"):
        dependencies.update(
            ROOT / f"metadata/releases/{version}{suffix}.yaml"
            for suffix in ("", "_canonical", "_serving")
        )
    dependencies.add(ROOT / "audit_results/scientific_correction/corrected_spatial.json")
    for path in sorted(dependencies):
        add(
            path.relative_to(ROOT),
            "versioned_loader_dependency",
            "phase3_recovery_gate_v1",
            "git_tracked_loader_input",
            ["serving_rebuild"],
            source_class="git_repository",
        )
    inventory = {
        "schema_version": 1,
        "scope": (
            "Complete serving artifact inputs plus mandatory SIOPS acceptance gate; "
            "not full raw science acquisition"
        ),
        "principle": "CODE REPOSITORY != COMPLETE DATA RELEASE PACKAGE",
        "artifacts": sorted(artifacts.values(), key=lambda e: e["relative_path"]),
    }
    (ROOT / "metadata/provenance/required_local_artifacts_v1.json").write_text(
        json.dumps(inventory, indent=2) + "\n"
    )
    preflight = inspect_artifacts(ROOT, inventory)
    (ROOT / "audit_results/phase3_artifact_preflight.json").write_text(
        json.dumps(preflight, indent=2) + "\n"
    )
    candidate = fingerprint(ROOT / SNAPSHOT)
    semantics = snapshot_semantics(ROOT / SNAPSHOT)
    siops = {
        "status": "BLOCKED_MISSING_AUTHORIZED_POPSVS_INPUTS",
        "recovered_snapshot_sha256": None,
        "observed_candidate_sha256": candidate["sha256"],
        "bytes": candidate["bytes"],
        **semantics,
        "derived_output_sha256": None,
        "accepted_existing_financing_sha256": FINANCING_HASH,
        "builder": "scripts/build_financing_context.py",
        "builder_executed": False,
        "automatic_source_download_executed": False,
        "reason": (
            "Builder populations() requires three absent POPSVS archives "
            "outside authorized recovery allowlist."
        ),
        "missing_inputs": [
            e for e in inventory["artifacts"] if e["artifact_type"] == "locked_population_source"
        ],
    }
    (ROOT / "metadata/provenance/siops_snapshot_recovery_2026-08-31.yaml").write_text(
        yaml.safe_dump(siops, sort_keys=False)
    )
    (ROOT / "audit_results/phase3_siops_snapshot_validation.json").write_text(
        json.dumps(siops, indent=2) + "\n"
    )
    rebuild = {
        "status": "BLOCKED_BEFORE_DATABASE_CREATION",
        "database_operations": 0,
        "reason": siops["reason"],
        "preflight": "audit_results/phase3_artifact_preflight.json",
        "complete_loader_orchestration": "NOT_IMPLEMENTED_PENDING_SOURCE_GATE",
    }
    (ROOT / "audit_results/database_rebuild_final.txt").write_text(
        json.dumps(rebuild, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "inventory_entries": len(artifacts),
                "preflight_status": preflight["status"],
                "failures": preflight["failures"],
                "snapshot": siops["status"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

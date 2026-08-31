"""Package this blocked closure without mislabeling it as a locked release."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "3b1bfa7ca5b5bac9df547b0a0e3d81f5bd4055a2"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    assert not git("status", "--porcelain"), "Commit the audited changes before packaging"
    commit = git("rev-parse", "HEAD")
    name = f"mente-do-brasil_advanced_territorial_phase3_BLOCKED_{commit[:7]}_20260831"
    folder = ROOT / "audit_packages" / name
    folder.mkdir(parents=True, exist_ok=False)
    files = {}
    for relative in git("diff", "--name-only", BASE, commit).splitlines():
        path = ROOT / relative
        assert path.is_file(), relative
        assert path.name != ".env" and path.suffix not in {".dump", ".sql.gz"}
        files[relative] = path.read_bytes()
    prior = [
        "audit_results/advanced_temporal/temporal_2024_reproduction.json",
        "audit_results/phase3_full_flow_reconciliation.json",
        "audit_results/phase3_protected_hashes.json",
        "audit_results/siops_financing_build.json",
        "audit_results/phase3_raw_hash_validation.json",
        "audit_results/scientific_correction/source_hash_verification.json",
    ]
    for relative in prior:
        files[f"PRIOR_EVIDENCE/{relative}"] = (ROOT / relative).read_bytes()
    audit = ROOT / "audit_results/phase3_closure"
    context = {
        "status": "BLOCKED_MISSING_MIGRATED_SOURCE_ARTIFACTS",
        "starting_commit": BASE,
        "final_commit": commit,
        "branch": git("branch", "--show-current"),
        "repository": str(ROOT),
        "fileprovider_blocker": "RESOLVED",
        "rescued_diff": {"uv.lock": "KEEP; already declared sources extra"},
        "current_release": "MDB_ANALYTICAL_2024_2",
        "historical_release": "MDB_ANALYTICAL_2024_1",
        "scientific_recomputation": "BLOCKED_MISSING_SOURCE_FILES",
        "moran_stored_lock": 0.5256454566660947,
        "pseudo_p_stored_lock": 0.0001,
        "backend": {"passed": 87, "failed": 4, "skipped": 24},
        "frontend_unit": {"passed": 57, "failed": 0},
        "production_e2e": {"passed": 30, "failed": 0, "skipped_by_viewport": 14},
        "frontend_development_e2e": "NOT_RUN_SEPARATELY; same suite run in production",
        "build": "PASS",
        "lint": "PASS",
        "typecheck": "PASS",
        "pdf_visual": "PASS; all 40 corrected pages inspected",
        "ui_visual": "PASS_BOUNDED; verified_ui is authoritative",
        "accessibility": "PARTIAL; native-select keyboard probe inconclusive; not WCAG certification",
        "reportlab_warning": "DOCUMENTED_UPSTREAM",
        "idempotent_file_reload": "NOT_RETESTED_MISSING_ARTIFACTS",
        "file_immutability_guard": "NOT_RETESTED_MISSING_ARTIFACTS",
        "advanced_phase_status": "NOT_LOCKED_LOCAL",
        "public_release_status": "NOT_RELEASED",
        "open_platform": "NOT_STARTED",
        "prior_evidence_rule": "PRIOR_EVIDENCE is inherited evidence, not a fresh successful run",
        "blocker_action": (
            "Restore byte-identical validated files listed in source_inventory.json into "
            "the new repository, then run full empty-DB loader chain and regressions."
        ),
    }
    for key, filename in {
        "serving_database": "database_advanced_validation.json",
        "clean_rebuild": "database_rebuild.txt",
        "backup_restore": "restore_drill.txt",
        "financing_hash_transition": "financing_hash_transition.txt",
        "runtime_versions": "runtime_versions.json",
        "apis_security": "api_security_live.json",
        "advanced_live_checks": "advanced_live_checks.json",
        "source_inventory": "source_inventory.json",
        "canvas_pixels": "canvas_pixels.json",
    }.items():
        context[key] = json.loads((audit / filename).read_text())
    for filename, content in {
        "AUDIT_CONTEXT.json": json.dumps(context, indent=2, ensure_ascii=True).encode(),
        "AUDIT_README.md": (ROOT / "docs/phase3_operational_closure_2026-08-31.md").read_bytes(),
    }.items():
        files[filename] = content
        (folder / filename).write_bytes(content)
    manifest = {
        "files": [
            {
                "relative_path": path,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for path, content in sorted(files.items())
        ]
    }
    manifest_bytes = json.dumps(manifest, indent=2).encode()
    (folder / "AUDIT_MANIFEST.json").write_bytes(manifest_bytes)
    archive = folder.parent / f"{name}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path, content in sorted(files.items()):
            z.writestr(path, content)
        z.writestr("AUDIT_MANIFEST.json", manifest_bytes)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        entries = json.loads(z.read("AUDIT_MANIFEST.json"))["files"]
        expected = {r["relative_path"] for r in entries}
        actual = set(z.namelist()) - {"AUDIT_MANIFEST.json"}
        assert expected == actual and len(actual) == len(entries)
        for row in entries:
            content = z.read(row["relative_path"])
            assert len(content) == row["size_bytes"]
            assert hashlib.sha256(content).hexdigest() == row["sha256"]
    result = {
        "path": str(archive),
        "size_bytes": archive.stat().st_size,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files_excluding_manifest": len(files),
        "manifest_entries": len(entries),
        "missing": 0,
        "extra": 0,
        "size_mismatches": 0,
        "sha256_mismatches": 0,
        "final_commit": commit,
    }
    (folder / "PACKAGE_VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

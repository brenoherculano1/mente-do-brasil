import csv
import re
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
METADATA_PATHS = [
    REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1.yaml",
    REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1_outputs.yaml",
    REPO_ROOT / "metadata/sources/source_manifest_initial.yaml",
    *sorted((REPO_ROOT / "metadata/indicators").glob("*.yaml")),
]
RAW_PROVENANCE = REPO_ROOT / "metadata/provenance/phase2_raw_data_manifest_2026-08-23.csv"

EXPECTED_SOURCE_DISTRIBUTION = {
    "DATASUS IBGE POPSVS": 3,
    "SIM/DATASUS DORES": 81,
    "SIH/SUS RD": 972,
    "CNES ST": 27,
    "CNES LT": 27,
    "CNES PF": 27,
}

EXPECTED_HASHES = {
    "config_sha256": "3e81c8924848fa47e1efd78c85f3145459b5df891801e655e102c0e453d9d26e",
    "crosswalk_sha256": "71239b3c9ec6d08422273e950b1227e31fca856fa8ee7aedb69ac0f8157377cb",
    "geometry_sha256": "657355adb0df88dfcfff2400751eff6ae97b367effe8e90223d0267e0437ba48",
    "phase2_script": "8612690ed9e6dfb70be526c307d1696a04c7550e3c27a3bda57f1a1bb6a44e4e",
    "phase2c_corrected_script": "e3073122ed63a434b087c5a61c1e9ec6c38c49d68d45c3de7eb16fe39a837bfe",
}


def read_rows():
    with RAW_PROVENANCE.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReleaseProvenanceGateTests(unittest.TestCase):
    def test_no_unresolved_placeholders_in_release_indicator_or_source_metadata(self):
        offenders = []
        for path in METADATA_PATHS:
            text = path.read_text(encoding="utf-8")
            if "PLACEHOLDER_" in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(offenders, [])

    def test_release_is_not_marked_released(self):
        release = (REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("release_status: VALIDATING", release)
        self.assertIn("quality_status: VALIDATED", release)
        self.assertIn("release_gate: PASS", release)
        self.assertIn("release_readiness: READY", release)
        self.assertIn("public_release_status: NOT_RELEASED", release)
        self.assertNotRegex(release, re.compile(r"^release_status:\s+RELEASED$", re.MULTILINE))

    def test_generated_outputs_manifest_exists(self):
        release = (REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1.yaml").read_text(
            encoding="utf-8"
        )
        match = re.search(r"generated_outputs_manifest:\s+(.+)", release)
        self.assertIsNotNone(match)
        manifest_path = REPO_ROOT / match.group(1).strip()
        self.assertTrue(manifest_path.exists(), manifest_path)

    def test_detailed_raw_provenance_manifest_exists(self):
        self.assertTrue(RAW_PROVENANCE.exists())

    def test_raw_provenance_has_1137_records(self):
        self.assertEqual(len(read_rows()), 1137)

    def test_raw_provenance_source_distribution(self):
        rows = read_rows()
        self.assertEqual(Counter(row["source"] for row in rows), EXPECTED_SOURCE_DISTRIBUTION)

    def test_raw_provenance_access_date(self):
        rows = read_rows()
        self.assertEqual({row["access_date"] for row in rows}, {"2026-08-23"})

    def test_critical_hashes_are_recorded(self):
        release = (REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1.yaml").read_text(
            encoding="utf-8"
        )
        provenance_text = "\n".join(
            [
                (REPO_ROOT / "metadata/provenance/phase2_run_manifest_2026-08-23.md").read_text(
                    encoding="utf-8"
                ),
                (
                    REPO_ROOT
                    / "metadata/provenance/phase2_script_hashes_2026-08-23.txt"
                ).read_text(encoding="utf-8"),
                (
                    REPO_ROOT
                    / "metadata/provenance/phase2c_script_hashes_2026-08-23.txt"
                ).read_text(encoding="utf-8"),
            ]
        )
        phase2c_hash_text = (
            REPO_ROOT
            / "metadata/provenance/phase2c_corrected_reproducibility_hashes_2026-08-23.txt"
        ).read_text(encoding="utf-8")

        for hash_value in EXPECTED_HASHES.values():
            self.assertIn(hash_value, release + provenance_text + phase2c_hash_text)


if __name__ == "__main__":
    unittest.main()

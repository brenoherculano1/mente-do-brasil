import subprocess
import unittest

from mente_do_brasil.constants import INVALID_SPATIAL_VALUES, LOCKED_SPATIAL_RESULTS
from mente_do_brasil.import_validation import (
    BUNDLE_ID,
    CRITICAL_FILES,
    EXPECTED_HEALTH_REGION_COUNT,
    EXPECTED_MUNICIPALITY_COUNT,
    RAW_IMPORT_RELATIVE_ROOT,
    analytical_rows,
    bundle_paths,
    crosswalk_rows,
    gpkg_health_region_count,
    lisa_rows,
    load_primary_moran,
    manifest_file_entries,
    validate_analytical_dataset,
    validate_geography_alignment,
    validate_locked_spatial_results,
    validate_manifest_integrity,
)


class ValidatedImportBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = bundle_paths()
        if not cls.paths.raw_root.exists():
            raise unittest.SkipTest(f"Raw import bundle not present: {cls.paths.raw_root}")

    def test_import_manifest_integrity(self):
        validate_manifest_integrity(self.paths.raw_root)

    def test_expected_bundle_files_exist(self):
        manifest_paths = {entry["path"] for entry in manifest_file_entries(self.paths.raw_root)}
        expected = CRITICAL_FILES - {"IMPORT_MANIFEST.json"}
        self.assertTrue((self.paths.raw_root / "IMPORT_MANIFEST.json").exists())
        self.assertFalse(sorted(expected - manifest_paths))
        for entry in manifest_file_entries(self.paths.raw_root):
            self.assertTrue((self.paths.raw_root / entry["path"]).exists(), entry["path"])

    def test_health_region_count_439(self):
        row_count, unique_codes, null_codes = gpkg_health_region_count(self.paths.raw_root)
        self.assertEqual(row_count, EXPECTED_HEALTH_REGION_COUNT)
        self.assertEqual(unique_codes, EXPECTED_HEALTH_REGION_COUNT)
        self.assertEqual(null_codes, 0)
        self.assertEqual(len(analytical_rows(self.paths.raw_root)), EXPECTED_HEALTH_REGION_COUNT)

    def test_municipality_count_5570(self):
        rows = crosswalk_rows(self.paths.raw_root)
        codes = {row["municipality_code_ibge"] for row in rows}
        self.assertEqual(len(codes), EXPECTED_MUNICIPALITY_COUNT)

    def test_unique_municipality_assignment(self):
        rows = crosswalk_rows(self.paths.raw_root)
        codes = [row["municipality_code_ibge"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        validate_geography_alignment(self.paths.raw_root)

    def test_unique_health_region_code(self):
        rows = analytical_rows(self.paths.raw_root)
        codes = [row["health_region_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))

    def test_no_missing_health_region_code(self):
        crosswalk_codes = [row["health_region_code"] for row in crosswalk_rows(self.paths.raw_root)]
        dataset_codes = [row["health_region_code"] for row in analytical_rows(self.paths.raw_root)]
        self.assertTrue(all(crosswalk_codes))
        self.assertTrue(all(dataset_codes))

    def test_primary_moran_locked(self):
        moran = load_primary_moran(self.paths.raw_root)
        self.assertAlmostEqual(moran["I"], LOCKED_SPATIAL_RESULTS["global_moran_i"], places=12)
        self.assertEqual(moran["pseudo_p"], LOCKED_SPATIAL_RESULTS["pseudo_p"])
        self.assertEqual(moran["permutations"], LOCKED_SPATIAL_RESULTS["permutations"])
        self.assertEqual(moran["seed"], LOCKED_SPATIAL_RESULTS["seed"])

    def test_invalid_moran_never_primary(self):
        moran = load_primary_moran(self.paths.raw_root)
        self.assertNotAlmostEqual(
            moran["I"],
            INVALID_SPATIAL_VALUES["old_global_moran_i"],
            places=12,
        )
        validate_locked_spatial_results(self.paths.raw_root)

    def test_lisa_locked_counts(self):
        significant = [
            row for row in lisa_rows(self.paths.raw_root) if row["significant_at_q_0.10"] == "True"
        ]
        self.assertEqual(len(significant), LOCKED_SPATIAL_RESULTS["lisa_fdr_significant"])
        self.assertEqual(
            sum(row["cluster_label"] == "high-high" for row in significant),
            LOCKED_SPATIAL_RESULTS["hh"],
        )
        self.assertEqual(
            sum(row["cluster_label"] == "low-low" for row in significant),
            LOCKED_SPATIAL_RESULTS["ll"],
        )
        self.assertEqual(
            sum(row["cluster_label"] == "high-low" for row in significant),
            LOCKED_SPATIAL_RESULTS["hl"],
        )
        self.assertEqual(
            sum(row["cluster_label"] == "low-high" for row in significant),
            LOCKED_SPATIAL_RESULTS["lh"],
        )

    def test_score_ranges(self):
        validate_analytical_dataset(self.paths.raw_root)

    def test_raw_files_ignored_by_git(self):
        result = subprocess.run(
            ["git", "check-ignore", str(RAW_IMPORT_RELATIVE_ROOT)],
            cwd=self.paths.repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(BUNDLE_ID, result.stdout)


if __name__ == "__main__":
    unittest.main()

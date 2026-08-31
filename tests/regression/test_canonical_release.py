import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by system Python only.
    pd = None
    pa = None
    pq = None
    yaml = None
    MISSING_DEPENDENCY = exc.name
else:
    MISSING_DEPENDENCY = None


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = REPO_ROOT / "scripts/build_canonical_release.py"
RAW_ROOT = REPO_ROOT / "data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle"
CANONICAL_ROOT = REPO_ROOT / "data/canonical/MDB_ANALYTICAL_2024_1"
HEALTH_REGIONS = CANONICAL_ROOT / "health_regions.parquet"
CROSSWALK = CANONICAL_ROOT / "municipality_health_region_crosswalk.parquet"
MANIFEST = REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1_canonical.yaml"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_canonical_release", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def isolated_builder_root(path):
    (path / "scripts").mkdir()
    shutil.copyfile(BUILDER_PATH, path / "scripts/build_canonical_release.py")
    (path / "data").mkdir()
    (path / "data/raw").symlink_to(REPO_ROOT / "data/raw", target_is_directory=True)
    (path / "metadata/releases").mkdir(parents=True)
    source = REPO_ROOT / "metadata/releases/MDB_ANALYTICAL_2024_1_outputs.yaml"
    shutil.copyfile(source, path / "metadata/releases" / source.name)
    return path


@unittest.skipIf(MISSING_DEPENDENCY is not None, f"missing dependency: {MISSING_DEPENDENCY}")
class CanonicalReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not RAW_ROOT.exists():
            raise unittest.SkipTest(f"Raw import bundle not present: {RAW_ROOT}")
        cls.builder = load_builder()
        cls.health_table = pq.read_table(HEALTH_REGIONS)
        cls.crosswalk_table = pq.read_table(CROSSWALK)
        cls.health_rows = cls.health_table.to_pylist()
        cls.crosswalk_rows = cls.crosswalk_table.to_pylist()
        cls.health_by_code = {row["health_region_code"]: row for row in cls.health_rows}

    def test_canonical_row_count_439(self):
        self.assertEqual(self.health_table.num_rows, 439)
        self.assertEqual(len(self.health_by_code), 439)

    def test_canonical_schema(self):
        self.assertEqual(self.health_table.schema.names, self.builder.CANONICAL_COLUMNS)
        flags_field = self.health_table.schema.field("data_quality_flags")
        self.assertTrue(pa.types.is_list(flags_field.type))
        self.assertTrue(pa.types.is_string(flags_field.type.value_type))
        self.assertEqual(self.health_table.num_columns, 35)

    def test_key_uniqueness_and_code_formatting(self):
        codes = [row["health_region_code"] for row in self.health_rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(isinstance(code, str) and len(code) == 5 for code in codes))

    def test_lisa_join_439_and_locked_counts(self):
        self.assertTrue(all(row["lisa_cluster"] for row in self.health_rows))
        significant = [row for row in self.health_rows if row["lisa_significant"]]
        self.assertEqual(len(significant), 135)
        self.assertEqual(sum(row["lisa_cluster"] == "high-high" for row in significant), 60)
        self.assertEqual(sum(row["lisa_cluster"] == "low-low" for row in significant), 66)
        self.assertEqual(sum(row["lisa_cluster"] == "high-low" for row in significant), 4)
        self.assertEqual(sum(row["lisa_cluster"] == "low-high" for row in significant), 5)

    def test_score_ranges(self):
        percentiles = [
            "suicide_percentile",
            "psychiatric_admission_percentile",
            "caps_percentile",
            "beds_percentile",
            "psychiatrist_fte_percentile",
            "need_score",
            "capacity_score",
        ]
        for row in self.health_rows:
            self.assertGreater(row["population"], 0)
            self.assertGreater(row["municipality_count"], 0)
            for field in [
                "suicide_asmr",
                "psychiatric_admission_rate",
                "caps_rate",
                "mental_health_beds_sus_rate",
                "psychiatrist_fte_rate",
            ]:
                self.assertGreaterEqual(row[field], 0)
            for field in percentiles:
                self.assertGreaterEqual(row[field], 0)
                self.assertLessEqual(row[field], 1)
            self.assertGreaterEqual(row["mismatch_score"], -1)
            self.assertLessEqual(row["mismatch_score"], 1)

    def test_no_scientific_recalculation_integrity_only(self):
        for row in self.health_rows:
            expected = row["need_score"] - row["capacity_score"]
            self.assertAlmostEqual(row["mismatch_score"], expected, places=12)

    def test_quality_flag_counts(self):
        self.assertEqual(
            sum("SMALL_SUICIDE_COUNT" in row["data_quality_flags"] for row in self.health_rows),
            7,
        )
        self.assertEqual(
            sum("ZERO_REGISTERED_BEDS" in row["data_quality_flags"] for row in self.health_rows),
            275,
        )
        self.assertTrue(all(row["data_quality_flags"] is not None for row in self.health_rows))

    def test_crosswalk_5570(self):
        self.assertEqual(self.crosswalk_table.num_rows, 5570)
        codes = [row["municipality_code_ibge"] for row in self.crosswalk_rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(isinstance(code, str) and len(code) == 7 for code in codes))
        self.assertTrue(
            all(len(row["municipality_code_datasus6"]) == 6 for row in self.crosswalk_rows)
        )
        self.assertTrue(all(len(row["health_region_code"]) == 5 for row in self.crosswalk_rows))

    def test_exact_source_mapping(self):
        raw = pd.read_csv(
            RAW_ROOT / "analytical_release/health_region_analysis_dataset_corrected.csv",
            dtype=str,
            keep_default_na=False,
        )
        raw["health_region_code"] = raw["health_region_code"].str.zfill(5)
        raw_by_code = raw.set_index("health_region_code")
        for code, row in self.health_by_code.items():
            source = raw_by_code.loc[code]
            for target, source_field in self.builder.SOURCE_MAPPING.items():
                if target == "health_region_code":
                    self.assertEqual(row[target], code)
                elif target == "health_region_name":
                    self.assertEqual(row[target], source[source_field])
                elif isinstance(row[target], int):
                    self.assertEqual(row[target], int(float(source[source_field])))
                else:
                    self.assertAlmostEqual(row[target], float(source[source_field]), places=12)

    def test_output_manifest_paths_and_hashes(self):
        with MANIFEST.open(encoding="utf-8") as handle:
            manifest = yaml.safe_load(handle)
        self.assertEqual(manifest["canonical_version"], "MDB_CANONICAL_1.0")
        paths = {entry["path"]: entry for entry in manifest["outputs"]}
        self.assertIn("data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet", paths)
        self.assertIn(
            "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet",
            paths,
        )
        for entry in paths.values():
            path = REPO_ROOT / entry["path"]
            self.assertTrue(path.exists())
            self.assertEqual(self.builder.sha256_file(path), entry["sha256"])

    def test_deterministic_rebuild(self):
        before = {
            "health_regions": self.builder.sha256_file(HEALTH_REGIONS),
            "crosswalk": self.builder.sha256_file(CROSSWALK),
        }
        with tempfile.TemporaryDirectory(prefix="mdb-historical-builder-test-") as directory:
            root = isolated_builder_root(Path(directory))
            hashes = []
            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, "scripts/build_canonical_release.py"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                hashes.append(
                    {
                        p.name: self.builder.sha256_file(p)
                        for p in (root / "data/canonical/MDB_ANALYTICAL_2024_1").glob("*.parquet")
                    }
                )
            self.assertEqual(hashes[0], hashes[1])
        after = {
            "health_regions": self.builder.sha256_file(HEALTH_REGIONS),
            "crosswalk": self.builder.sha256_file(CROSSWALK),
        }
        self.assertEqual(before, after)

    def test_builder_executable(self):
        with tempfile.TemporaryDirectory(prefix="mdb-builder-cli-test-") as directory:
            result = subprocess.run(
                [sys.executable, "scripts/build_canonical_release.py"],
                cwd=isolated_builder_root(Path(directory)),
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

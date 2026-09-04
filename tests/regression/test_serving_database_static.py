import ast
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class ServingDatabaseStaticTests(unittest.TestCase):
    def test_migration_files_exist_in_order(self):
        migrations = sorted((REPO_ROOT / "db/migrations").glob("*.sql"))
        self.assertEqual(
            [path.name for path in migrations],
            [
                "001_extensions.sql",
                "002_schemas.sql",
                "003_tables.sql",
                "004_constraints_indexes.sql",
                "005_serving_views.sql",
                "006_serving_status.sql",
                "007_web_geometry.sql",
                "008_product_intelligence.sql",
                "009_financing_context.sql",
                "010_advanced_territorial.sql",
                "011_public_open_platform.sql",
                "012_public_role_hardening.sql",
                "013_public_temporal_type_alignment.sql",
                "014_cloud_access_hardening.sql",
            ],
        )

    def test_expected_schemas_tables_and_views_exist(self):
        sql = "\n".join(
            path.read_text() for path in sorted((REPO_ROOT / "db/migrations").glob("*.sql"))
        )
        for fragment in [
            "CREATE SCHEMA IF NOT EXISTS meta",
            "CREATE SCHEMA IF NOT EXISTS geo",
            "CREATE SCHEMA IF NOT EXISTS analytics",
            "CREATE SCHEMA IF NOT EXISTS serving",
            "CREATE TABLE IF NOT EXISTS meta.releases",
            "CREATE TABLE IF NOT EXISTS meta.indicators",
            "CREATE TABLE IF NOT EXISTS geo.health_regions",
            "CREATE TABLE IF NOT EXISTS geo.municipality_health_region_crosswalk",
            "CREATE TABLE IF NOT EXISTS analytics.health_region_metrics",
            "CREATE TABLE IF NOT EXISTS meta.serving_database_status",
            "CREATE TABLE IF NOT EXISTS web.health_region_geometry",
            "CREATE TABLE IF NOT EXISTS meta.product_intelligence_versions",
            "CREATE TABLE IF NOT EXISTS analytics.health_region_intelligence",
            "CREATE TABLE IF NOT EXISTS analytics.health_region_peers",
            "CREATE TABLE IF NOT EXISTS analytics.health_region_peer_benchmarks",
            "CREATE OR REPLACE VIEW serving.health_region_profile",
            "CREATE OR REPLACE VIEW serving.health_region_map",
            "CREATE OR REPLACE VIEW serving.health_region_lookup",
            "CREATE OR REPLACE VIEW serving.v_public_health_regions_current",
            "CREATE OR REPLACE VIEW serving.v_public_flow_edges",
        ]:
            self.assertIn(fragment, sql)

    def test_postgis_geometry_contract(self):
        sql = (REPO_ROOT / "db/migrations/003_tables.sql").read_text()
        checks = (REPO_ROOT / "db/migrations/004_constraints_indexes.sql").read_text()
        self.assertIn("geometry(MultiPolygon, 4674)", sql)
        self.assertIn("ST_SRID(geom) = 4674", checks)
        self.assertIn("ST_IsValid(geom)", checks)
        self.assertIn("USING gist (geom)", checks)

    def test_primary_foreign_keys_and_integrity_constraints(self):
        sql = "\n".join(
            path.read_text() for path in sorted((REPO_ROOT / "db/migrations").glob("*.sql"))
        )
        for fragment in [
            "PRIMARY KEY (geography_version, health_region_code)",
            "PRIMARY KEY (geography_version, municipality_code_ibge)",
            "PRIMARY KEY (release_id, health_region_code)",
            "REFERENCES meta.releases (release_id, geography_version)",
            "REFERENCES geo.health_regions (geography_version, health_region_code)",
            "CHECK (population > 0)",
            "CHECK (mismatch_score BETWEEN -1 AND 1)",
            "CHECK (lisa_p IS NULL OR lisa_p BETWEEN 0 AND 1)",
            "CHECK (lisa_q IS NULL OR lisa_q BETWEEN 0 AND 1)",
            "abs(mismatch_score - (need_score - capacity_score)) <= 1e-12",
            "matched_signal_families BETWEEN 0 AND 5",
            "abs(decomposition_sum - mismatch_score) <= 1e-12",
            "peer_rank BETWEEN 1 AND 10",
        ]:
            self.assertIn(fragment, sql)

    def test_compose_uses_non_beta_postgis(self):
        compose = (REPO_ROOT / "compose.yaml").read_text()
        dockerfile = (REPO_ROOT / "db/docker/Dockerfile").read_text()
        self.assertIn("mente-do-brasil-postgis:18-3.6.4", compose)
        self.assertIn("FROM postgres:18", dockerfile)
        self.assertIn("postgresql-18-postgis-3=3.6.4", dockerfile)
        self.assertNotRegex(compose, r"19|3\.7|beta|alpha")
        self.assertIn("127.0.0.1:${MDB_DB_PORT:-5432}:5432", compose)
        self.assertNotIn("0.0.0.0", compose)
        self.assertIn("${MDB_DB_PASSWORD:?Set MDB_DB_PASSWORD in local .env}", compose)
        self.assertNotIn("POSTGRES_PASSWORD: ${MDB_DB_PASSWORD:-CHANGE_ME}", compose)
        self.assertIn("healthcheck:", compose)
        self.assertIn("mente_do_brasil_pgdata", compose)
        self.assertIn(":/var/lib/postgresql", compose)
        self.assertNotIn(":/var/lib/postgresql/data", compose)

    def test_env_example_has_local_database_settings_without_real_secret(self):
        env = (REPO_ROOT / ".env.example").read_text()
        for key in [
            "MDB_DB_HOST=127.0.0.1",
            "MDB_DB_PORT=5432",
            "MDB_DB_NAME=mente_do_brasil",
            "MDB_DB_USER=mente_do_brasil",
            "MDB_DB_PASSWORD=SET_A_LOCAL_PASSWORD",
        ]:
            self.assertIn(key, env)
        self.assertNotIn("MDB_DB_PASSWORD=CHANGE_ME", env)

    def test_loader_has_canonical_hash_and_release_gate_checks(self):
        loader = (REPO_ROOT / "scripts/load_serving_database.py").read_text()
        for fragment in [
            "validate_canonical_manifest",
            "source_release_gate",
            "PASS",
            "source_quality_status",
            "VALIDATED",
            "sha256_file",
            "health_regions.parquet",
            "municipality_health_region_crosswalk.parquet",
            'release["geography_version"]',
            "WHERE geography_version = %s",
            "load_local_env",
            "MDB_DB_PASSWORD must be set",
        ]:
            self.assertIn(fragment, loader)
        self.assertNotIn('"CHANGE_ME"', loader)

    def test_loader_has_immutability_guard(self):
        loader = (REPO_ROOT / "scripts/load_serving_database.py").read_text()
        self.assertIn("IMMUTABILITY VIOLATION", loader)
        self.assertIn("existing release_id has different canonical hashes", loader)
        self.assertIn("ON CONFLICT (release_id) DO NOTHING", loader)

    def test_api_role_can_read_analytics_layer(self):
        provisioner = (REPO_ROOT / "scripts/provision_api_db_role.py").read_text()
        self.assertIn('"analytics"', provisioner)
        self.assertIn("GRANT SELECT ON ALL TABLES IN SCHEMA", provisioner)

    def test_loader_does_not_recalculate_scientific_rates(self):
        loader = (REPO_ROOT / "scripts/load_serving_database.py").read_text()
        prohibited_assignment_patterns = [
            r"suicide_asmr\s*=",
            r"psychiatric_admission_rate\s*=",
            r"caps_rate\s*=",
            r"mental_health_beds_sus_rate\s*=",
            r"psychiatrist_fte_rate\s*=",
            r"need_score\s*=",
            r"capacity_score\s*=",
            r"mismatch_score\s*=",
        ]
        for pattern in prohibited_assignment_patterns:
            self.assertIsNone(re.search(pattern, loader))

    def test_validator_reports_required_sections(self):
        validator = (REPO_ROOT / "scripts/validate_serving_database.py").read_text()
        for label in [
            "SERVING DATABASE VALIDATION",
            "release",
            "geography",
            "metrics",
            "geometry",
            "LISA",
            "flags",
            "constraints",
            "views",
            "immutability",
            "product_intelligence",
        ]:
            self.assertIn(label, validator)

    def test_scripts_are_parseable(self):
        for path in [
            REPO_ROOT / "scripts/load_serving_database.py",
            REPO_ROOT / "scripts/validate_serving_database.py",
        ]:
            ast.parse(path.read_text())


if __name__ == "__main__":
    unittest.main()

import ast
from pathlib import Path

import pandas as pd

from api.release_metadata import RELEASE_JSON
from scripts.open_platform_spec import DATASETS, FORBIDDEN_PUBLIC_FIELDS

ROOT = Path(__file__).resolve().parents[2]


def test_bundled_api_release_metadata_is_byte_identical():
    assert RELEASE_JSON.encode("utf-8") == (
        ROOT / "web/public/releases/MDB_OPEN_DATA_2024_1/release.json"
    ).read_bytes()


def test_public_spec_has_locked_datasets_and_no_forbidden_fields():
    assert len(DATASETS) == 9
    public_fields = set()
    for spec in DATASETS.values():
        frame = pd.read_parquet(spec["source"])
        columns = list(spec.get("columns", frame.columns))
        columns = [field for field in columns if field not in spec.get("exclude", [])]
        public_fields.update(columns)
    assert not ({field.lower() for field in public_fields} & FORBIDDEN_PUBLIC_FIELDS)


def test_public_flow_view_enforces_suppression_in_sql():
    sql = (ROOT / "db/migrations/011_public_open_platform.sql").read_text()
    assert "WHERE suppressed = false AND admissions >= 5" in sql
    assert "SELECT *" not in sql.upper()


def test_public_role_cannot_create_temporary_objects():
    sql = (ROOT / "db/migrations/012_public_role_hardening.sql").read_text()
    assert "REVOKE TEMPORARY ON DATABASE %I FROM PUBLIC" in sql
    assert "current_database()" in sql


def test_public_router_is_parseable_and_has_no_select_star():
    router = (ROOT / "api/routers/public.py").read_text()
    ast.parse(router)
    assert "SELECT *" not in router.upper()
    for route in [
        "/releases",
        "/health-regions",
        "/health-regions/{code}/timeline",
        "/changes",
        "/financing",
        "/health-regions/{code}/flows",
        "/health-regions/{code}/peers",
        "/municipalities/{ibge_code}/health-region",
        "/metadata/indicators",
        "/metadata/methodology",
        "/openapi.json",
    ]:
        assert route in router


def test_release_status_remains_not_released():
    builder = (ROOT / "scripts/build_open_data_release.py").read_text()
    footer = (ROOT / "web/components/AppFooter.tsx").read_text()
    assert '"public_release_status": "NOT_RELEASED"' in builder
    assert '"status": "LOCKED_LOCAL"' in builder
    assert "Release: {ACTIVE_RELEASE_ID}" in footer
    assert "Release: MDB_ANALYTICAL_2024_1" not in footer

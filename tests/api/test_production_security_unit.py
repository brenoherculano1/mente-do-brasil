from __future__ import annotations

import pytest

from api.config import get_settings
from api.security import has_valid_internal_token


def base_environment(monkeypatch):
    monkeypatch.setenv("MDB_API_DB_PASSWORD", "unit-test-password")
    monkeypatch.setenv("MDB_PRODUCTION_MODE", "true")
    monkeypatch.setenv("MDB_INTERNAL_API_TOKEN", "x" * 32)
    monkeypatch.setenv("MDB_DB_SSLMODE", "verify-full")


def test_production_configuration_is_fail_closed(monkeypatch):
    base_environment(monkeypatch)
    monkeypatch.delenv("MDB_INTERNAL_API_TOKEN")
    with pytest.raises(RuntimeError, match="MDB_INTERNAL_API_TOKEN"):
        get_settings()

    base_environment(monkeypatch)
    monkeypatch.setenv("MDB_DB_SSLMODE", "require")
    with pytest.raises(RuntimeError, match="SSL mode"):
        get_settings()


def test_production_pool_and_constant_time_token_boundary(monkeypatch):
    base_environment(monkeypatch)
    settings = get_settings()
    assert settings.pool_min_size == 0
    assert settings.pool_max_size == 4
    assert has_valid_internal_token("x" * 32, settings.internal_api_token)
    assert not has_valid_internal_token(None, settings.internal_api_token)
    assert not has_valid_internal_token("y" * 32, settings.internal_api_token)

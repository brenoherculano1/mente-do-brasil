"""Configuration for the local read-only API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    env_path = repo_root() / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    default_release_id: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    api_host: str
    api_port: int
    allowed_origins: tuple[str, ...]
    allow_full_geometry: bool
    enable_docs: bool
    production_mode: bool
    internal_api_token: str | None
    db_sslmode: str
    db_sslrootcert: str | None
    pool_min_size: int
    pool_max_size: int

    @property
    def dsn(self) -> str:
        dsn = (
            f"host={self.db_host} port={self.db_port} dbname={self.db_name} "
            f"user={self.db_user} password={self.db_password} sslmode={self.db_sslmode}"
        )
        if self.db_sslrootcert:
            dsn += f" sslrootcert={self.db_sslrootcert}"
        return dsn


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    load_local_env()
    password = os.environ.get("MDB_API_DB_PASSWORD")
    if not password:
        raise RuntimeError("MDB_API_DB_PASSWORD must be set in local .env.")
    origins = tuple(
        origin.strip()
        for origin in os.environ.get(
            "MDB_API_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    )
    if "*" in origins:
        raise RuntimeError("Wildcard CORS origins are not allowed.")
    api_host = os.environ.get("MDB_API_HOST", "127.0.0.1")
    if api_host == "0.0.0.0":
        raise RuntimeError("The local API must not bind to 0.0.0.0 by default.")
    production_mode = env_flag("MDB_PRODUCTION_MODE")
    internal_api_token = os.environ.get("MDB_INTERNAL_API_TOKEN") or None
    if production_mode and (internal_api_token is None or len(internal_api_token) < 32):
        raise RuntimeError(
            "MDB_INTERNAL_API_TOKEN must contain at least 32 characters in production."
        )
    sslmode = os.environ.get("MDB_DB_SSLMODE", "prefer").strip().lower()
    if production_mode and sslmode not in {"verify-ca", "verify-full"}:
        raise RuntimeError("Production database SSL mode must be verify-ca or verify-full.")
    pool_min_size = int(os.environ.get("MDB_DB_POOL_MIN_SIZE", "0" if production_mode else "1"))
    pool_max_size = int(os.environ.get("MDB_DB_POOL_MAX_SIZE", "4"))
    if not 0 <= pool_min_size <= pool_max_size <= 10:
        raise RuntimeError("Database pool sizes must satisfy 0 <= min <= max <= 10.")
    return Settings(
        default_release_id=os.environ.get("MDB_DEFAULT_RELEASE_ID", "MDB_ANALYTICAL_2024_2"),
        db_host=os.environ.get("MDB_DB_HOST", "127.0.0.1"),
        db_port=int(os.environ.get("MDB_DB_PORT", "5432")),
        db_name=os.environ.get("MDB_DB_NAME", "mente_do_brasil"),
        db_user=os.environ.get("MDB_API_DB_USER", "mente_do_brasil_api"),
        db_password=password,
        api_host=api_host,
        api_port=int(os.environ.get("MDB_API_PORT", "8000")),
        allowed_origins=origins,
        allow_full_geometry=env_flag("MDB_API_ALLOW_FULL_GEOMETRY"),
        enable_docs=env_flag("MDB_API_ENABLE_DOCS"),
        production_mode=production_mode,
        internal_api_token=internal_api_token,
        db_sslmode=sslmode,
        db_sslrootcert=os.environ.get("MDB_DB_SSLROOTCERT") or None,
        pool_min_size=pool_min_size,
        pool_max_size=pool_max_size,
    )

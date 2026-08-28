"""Provision the local PostgreSQL read-only role used by the API."""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.load_serving_database import dsn, load_local_env, repo_root

API_USER = "mente_do_brasil_api"


def ensure_api_env() -> None:
    root = repo_root()
    env_path = root / ".env"
    if not env_path.exists():
        raise RuntimeError("Local .env must exist before provisioning the API role.")
    lines = env_path.read_text(encoding="utf-8").splitlines()
    keys = {line.split("=", 1)[0] for line in lines if line and "=" in line}
    changed = False
    if "MDB_DEFAULT_RELEASE_ID" not in keys:
        lines.append("MDB_DEFAULT_RELEASE_ID=MDB_ANALYTICAL_2024_1")
        changed = True
    if "MDB_API_HOST" not in keys:
        lines.append("MDB_API_HOST=127.0.0.1")
        changed = True
    if "MDB_API_PORT" not in keys:
        lines.append("MDB_API_PORT=8000")
        changed = True
    if "MDB_API_ALLOWED_ORIGINS" not in keys:
        lines.append("MDB_API_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000")
        changed = True
    if "MDB_API_DB_USER" not in keys:
        lines.append(f"MDB_API_DB_USER={API_USER}")
        changed = True
    if "MDB_API_DB_PASSWORD" not in keys:
        lines.append("MDB_API_DB_PASSWORD=" + secrets.token_urlsafe(40))
        changed = True
    if changed:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        env_path.chmod(0o600)


def api_password() -> str:
    load_local_env()
    from os import environ

    value = environ.get("MDB_API_DB_PASSWORD")
    if not value:
        raise RuntimeError("MDB_API_DB_PASSWORD is missing from local .env.")
    return value


def provision() -> None:
    ensure_api_env()
    password = api_password()
    with psycopg.connect(dsn(), autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (API_USER,),
        ).fetchone()
        if not exists:
            connection.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(API_USER)))
        connection.execute(
            sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
                sql.Identifier(API_USER), sql.Literal(password)
            )
        )
        connection.execute(
            sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(
                sql.Identifier(API_USER)
            )
        )
        connection.execute(
            sql.SQL("ALTER ROLE {} SET statement_timeout = '30s'").format(sql.Identifier(API_USER))
        )
        connection.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier("mente_do_brasil"), sql.Identifier(API_USER)
            )
        )
        for schema_name in ["meta", "geo", "analytics", "serving", "web"]:
            connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema_name), sql.Identifier(API_USER)
                )
            )
            connection.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(
                    sql.Identifier(schema_name), sql.Identifier(API_USER)
                )
            )
        connection.execute(
            sql.SQL("REVOKE CREATE ON SCHEMA public FROM {}").format(sql.Identifier(API_USER))
        )
    print("API DB ROLE PROVISIONED")
    print("role=mente_do_brasil_api")
    print("privileges=read-only")


if __name__ == "__main__":
    provision()

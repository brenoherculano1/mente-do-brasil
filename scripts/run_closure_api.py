"""Run a temporary read-only API login; remove the login on exit."""

import argparse
import os
import secrets
import subprocess
import sys
import uuid

from psycopg import sql

from scripts.audit_phase3_recovery import ROOT, connect, container_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8101)
    parser.add_argument("--release", default="MDB_ANALYTICAL_2024_2")
    parser.add_argument("--backend-tests", action="store_true")
    args = parser.parse_args()
    role = "mdb_closure_" + uuid.uuid4().hex[:12]
    password = secrets.token_hex(32)
    settings = container_settings()
    with connect(settings) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} IN ROLE mente_do_brasil_api").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        admin.execute(
            sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(
                sql.Identifier(role)
            )
        )
        admin.execute(
            sql.SQL("ALTER ROLE {} SET statement_timeout = '30s'").format(sql.Identifier(role))
        )
        env = os.environ.copy()
        env.update(
            MDB_DB_NAME=settings["POSTGRES_DB"],
            MDB_API_DB_USER=role,
            MDB_API_DB_PASSWORD=password,
            MDB_DEFAULT_RELEASE_ID=args.release,
            MDB_API_PORT=str(args.port),
        )
        try:
            command = (
                [sys.executable, "-m", "pytest", "-q"]
                if args.backend_tests
                else [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "api.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(args.port),
                ]
            )
            result = subprocess.run(command, cwd=ROOT, env=env)
            if result.returncode:
                raise SystemExit(result.returncode)
        except KeyboardInterrupt:
            pass
        finally:
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


if __name__ == "__main__":
    main()

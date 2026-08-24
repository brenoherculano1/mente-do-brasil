"""Database pool management for the read-only API."""

from __future__ import annotations

from collections.abc import Iterator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import Settings


def configure_read_only(connection) -> None:
    connection.execute("SET default_transaction_read_only = on")
    connection.execute("SET statement_timeout = '30s'")
    connection.commit()


def create_pool(settings: Settings) -> ConnectionPool:
    return ConnectionPool(
        conninfo=settings.dsn,
        min_size=1,
        max_size=4,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
            "application_name": "mente-do-brasil-api",
        },
        configure=configure_read_only,
        open=False,
    )


class Database:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def rows(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                return list(cursor.fetchall())

    def row(self, sql: str, params: tuple = ()) -> dict | None:
        rows = self.rows(sql, params)
        return rows[0] if rows else None


def get_database(pool: ConnectionPool) -> Iterator[Database]:
    yield Database(pool)

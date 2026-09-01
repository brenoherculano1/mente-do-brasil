"""Grant existing API role read-only access to the selected rebuild database."""

from psycopg import sql

from scripts.load_serving_database import connect


def main() -> None:
    with connect() as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_roles WHERE rolname='mente_do_brasil_api'"
        ).fetchone()
        if not exists:
            raise RuntimeError("Required cluster role mente_do_brasil_api is absent")
        for schema in ("meta", "geo", "analytics", "serving", "web"):
            connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO mente_do_brasil_api").format(
                    sql.Identifier(schema)
                )
            )
            connection.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO mente_do_brasil_api").format(
                    sql.Identifier(schema)
                )
            )
        connection.execute("REVOKE CREATE ON SCHEMA public FROM mente_do_brasil_api")
    print("RUNTIME ACCESS PASS")


if __name__ == "__main__":
    main()

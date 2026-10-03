"""Setup-only, one-time native California import. Never execute archive SQL."""

import asyncio
import json
import os
import re
from pathlib import Path

import asyncpg

from sqlwarden.data import (
    NATIVE_EXPECTED,
    SQLITE_SHA256,
    TABLE_NAMES,
    file_sha256,
    quote_ident,
    read_tables,
)

SCHEMA = "california_schools"
READER = "warden_sandbox_california_schools"
ROLE = quote_ident(READER)
PASSWORD = re.compile(r"[a-f0-9]{48}\Z")
ROOT = Path(__file__).resolve().parents[1]


def setup_connection_options(values: dict) -> dict:
    if (
        values.get("WARDEN_TEST_TARGET") != "sqlwarden-local"
        or values.get("WARDEN_PG_PORT") != "55432"
    ):
        raise ValueError("Import requires the dedicated local target on port 55432")
    password = values.get("WARDEN_BOOTSTRAP_PASSWORD", "")
    if not PASSWORD.fullmatch(password):
        raise ValueError("A valid private setup password is required")
    return {
        "host": "127.0.0.1",
        "port": 55432,
        "database": "sqlwarden",
        "user": "warden_bootstrap",
        "password": password,
        "timeout": 5,
        "command_timeout": 60,
    }


def validate_source(source: Path) -> dict:
    tables = read_tables(source.parent / "california_schools.sqlite", SQLITE_SHA256)
    manifest_path = source / "manifest.json"
    if manifest_path.stat().st_size > 64 * 1024:
        raise ValueError("Native manifest exceeds the metadata budget")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if set(manifest) != set(TABLE_NAMES):
        raise ValueError("Native manifest table selection differs")
    for name in TABLE_NAMES:
        path = source / f"{name}.tsv"
        expected = NATIVE_EXPECTED[name]
        if path.stat().st_size != expected["bytes"] or file_sha256(path) != expected["sha256"]:
            raise ValueError("Native source bytes differ from the pinned data")
        entry = manifest[name]
        columns = [column["name"] for column in tables[name]["columns"]]
        if entry.get("columns") != columns or any(entry.get(k) != v for k, v in expected.items()):
            raise ValueError("Native manifest differs from checked source metadata")
    return tables


async def verify_local_database(conn: asyncpg.Connection) -> None:
    identity = await conn.fetchrow("SELECT current_database(), current_user")
    if (
        tuple(identity) != ("sqlwarden", "warden_bootstrap")
        or conn.get_server_version().major != 16
    ):
        raise ValueError("Import connection is not the reviewed PostgreSQL 16 setup target")
    markers = await conn.fetchval(
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "JOIN pg_roles r ON r.oid=c.relowner WHERE r.rolname='warden_owner' AND NOT r.rolcanlogin "
        "AND c.relkind='r' AND ((n.nspname='app' AND c.relname='boundary_probe') "
        "OR (n.nspname='demo_schools' AND c.relname='schools') "
        "OR (n.nspname='demo_other' AND c.relname='canary'))"
    )
    if markers != 3:
        raise ValueError("Dedicated local database ownership markers differ")


async def verify_native_content(conn: asyncpg.Connection, source: Path, tables: dict) -> None:
    """Setup-only complete typed multiset comparison; caller owns the transaction."""
    for name in TABLE_NAMES:
        target = SCHEMA + "." + quote_ident(name)
        temporary = quote_ident("import_check_" + name)
        await conn.execute(f"CREATE TEMP TABLE {temporary} (LIKE {target}) ON COMMIT DROP")
        columns = [column["name"] for column in tables[name]["columns"]]
        await conn.copy_to_table(
            "import_check_" + name,
            schema_name="pg_temp",
            source=source / f"{name}.tsv",
            columns=columns,
            format="text",
            encoding="UTF8",
            timeout=60,
        )
        projection = ", ".join(quote_ident(column) for column in columns)
        scratch = "pg_temp." + temporary
        different = await conn.fetchval(
            "SELECT EXISTS("
            f"(SELECT {projection} FROM {target} EXCEPT ALL SELECT {projection} FROM {scratch}) "
            "UNION ALL "
            f"(SELECT {projection} FROM {scratch} EXCEPT ALL SELECT {projection} FROM {target}))"
        )
        if different:
            raise ValueError("Native source content differs from imported rows")


async def load_california(conn: asyncpg.Connection, source: Path, password: str) -> dict:
    if not isinstance(password, str) or not PASSWORD.fullmatch(password):
        raise ValueError("Invalid generated dataset password")
    tables = validate_source(source)
    async with asyncio.timeout(120), conn.transaction():
        await verify_local_database(conn)
        if await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) "
            "OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)",
            SCHEMA,
            READER,
        ):
            raise FileExistsError(
                "California schema or login already exists; refusing to change it"
            )
        await conn.execute(
            "SET LOCAL statement_timeout='60s'; SET LOCAL lock_timeout='500ms'; "
            "SET LOCAL work_mem='16MB'; SET LOCAL temp_file_limit='64MB'; "
            "SET LOCAL idle_in_transaction_session_timeout='5s'"
        )
        await conn.execute(
            f"CREATE ROLE {ROLE} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE "
            f"NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD '{password}'"
        )
        await conn.execute(f"GRANT CONNECT ON DATABASE sqlwarden TO {ROLE}")
        settings = {
            "default_transaction_read_only": "on",
            "statement_timeout": "5s",
            "lock_timeout": "500ms",
            "idle_in_transaction_session_timeout": "5s",
            "work_mem": "16MB",
            "temp_file_limit": "64MB",
        }
        for key, value in settings.items():
            await conn.execute(f"ALTER ROLE {ROLE} SET {key}='{value}'")
        await conn.execute(f"ALTER ROLE {ROLE} SET search_path=pg_catalog, {SCHEMA}")
        await conn.execute(f"CREATE SCHEMA {SCHEMA} AUTHORIZATION warden_owner")
        await conn.execute(f"REVOKE ALL ON SCHEMA {SCHEMA} FROM PUBLIC")
        await conn.execute("SET LOCAL ROLE warden_owner")
        for name in TABLE_NAMES:
            table = tables[name]
            definitions = [
                quote_ident(column["name"])
                + " "
                + column["type"]
                + (" NOT NULL" if column["not_null"] else "")
                for column in table["columns"]
            ]
            definitions.append(
                "PRIMARY KEY (" + ", ".join(map(quote_ident, table["primary_key"])) + ")"
            )
            await conn.execute(
                f"CREATE TABLE {SCHEMA}.{quote_ident(name)} ({', '.join(definitions)})"
            )
            await conn.copy_to_table(
                name,
                schema_name=SCHEMA,
                source=source / f"{name}.tsv",
                columns=[column["name"] for column in table["columns"]],
                format="text",
                encoding="UTF8",
                timeout=60,
            )
        for name in ("frpm", "satscores"):
            column, target, target_column = tables[name]["foreign_key"]
            await conn.execute(
                f"ALTER TABLE {SCHEMA}.{quote_ident(name)} ADD FOREIGN KEY ({quote_ident(column)}) "
                f"REFERENCES {SCHEMA}.{quote_ident(target)} ({quote_ident(target_column)})"
            )
        await conn.execute(f"GRANT USAGE ON SCHEMA {SCHEMA} TO {ROLE}")
        await conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO {ROLE}")
        await conn.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA {SCHEMA} "
            f"GRANT SELECT ON TABLES TO {ROLE}"
        )
        counts = {
            name: await conn.fetchval(f"SELECT count(*) FROM {SCHEMA}.{quote_ident(name)}")
            for name in TABLE_NAMES
        }
        if any(counts[name] != NATIVE_EXPECTED[name]["rows"] for name in TABLE_NAMES):
            raise ValueError("Imported row counts differ")
        await conn.execute("SET LOCAL ROLE NONE")
        await verify_native_content(conn, source, tables)
    return {"db_id": SCHEMA, "rows": counts, "typed_content_verified": True}


async def main() -> None:
    try:
        options = setup_connection_options(dict(os.environ))
        password = os.environ.get("WARDEN_CALIFORNIA_PASSWORD", "")
        if not PASSWORD.fullmatch(password):
            raise ValueError("Separate California credentials are required")
        source = ROOT / "data/bird_california/native"
        validate_source(source)
        conn = await asyncpg.connect(**options)
        try:
            result = await load_california(conn, source, password)
        finally:
            await conn.close()
    except (OSError, ValueError, asyncpg.PostgresError, TimeoutError) as error:
        raise SystemExit(
            f"Import refused or rolled back ({type(error).__name__}); "
            "private values are not printed."
        ) from None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

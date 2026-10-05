"""Fixed-target setup importer; no inference, gold SQL or runtime credential wiring."""

import argparse
import asyncio
import json
import math
import os
import sqlite3
import struct
from contextlib import closing
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from secrets import token_hex
from time import monotonic

import asyncpg

from scripts.load_bird import (
    PASSWORD,
    setup_connection_options,
    verify_local_database,
    verify_native_content,
)
from scripts.prepare_import_bundle import BUNDLE, DB_IDS, load_specs, validate_bundle
from scripts.prepare_sources import SOURCE_DIR, checked_file, relative_path
from sqlwarden.data import quote_ident

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TYPES = {"TEXT", "BIGINT", "REAL", "DATE", "TIMESTAMPTZ"}


def password_key(db_id):
    if db_id not in DB_IDS:
        raise ValueError("Unsupported dataset")
    return "WARDEN_DATASET_" + db_id.upper() + "_PASSWORD"


def initialize_credentials(root):
    with (root / ".env.datasets").open("x", encoding="utf-8", newline="\n") as file:
        file.write("".join(password_key(db_id) + "=" + token_hex(24) + "\n" for db_id in DB_IDS))


def table_definition(table):
    columns = []
    for column in table["columns"]:
        if column["native_type"] not in ALLOWED_TYPES:
            raise ValueError("Unsupported reviewed native type")
        columns.append(
            quote_ident(column["name"])
            + " "
            + column["native_type"]
            + (" NOT NULL" if column["declared_not_null"] or column["primary_key_position"] else "")
        )
    if table["primary_key"]:
        columns.append("PRIMARY KEY (" + ", ".join(map(quote_ident, table["primary_key"])) + ")")
    return ", ".join(columns)


def native_sample_value(value, source_type, *, db_id=None):
    if value is None:
        return None
    if source_type == "TEXT" and isinstance(value, str):
        return value
    if source_type == "INTEGER" and type(value) is int:
        return value
    if source_type == "REAL" and type(value) in (int, float) and math.isfinite(value):
        return struct.unpack("!f", struct.pack("!f", value))[0]
    if source_type == "DATE" and isinstance(value, str):
        return date.fromisoformat(value)
    if source_type == "DATETIME" and isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            source_zone = timezone(timedelta(hours=8)) if db_id == "codebase_community" else UTC
            parsed = parsed.replace(tzinfo=source_zone)
        return parsed.astimezone(UTC)
    raise ValueError("Unsupported SQLite representative value")


async def verify_sqlite_samples(conn, db_id, tables, pins):
    source = next(p for p in pins["sqlite_sources"] if p["db_id"] == db_id)
    path = SOURCE_DIR / relative_path(source["output"])
    checked_file(path, source)
    deadline = monotonic() + 120
    verified = {}
    with closing(
        sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as sqlite:
        sqlite.execute("PRAGMA query_only=ON")
        sqlite.execute("PRAGMA trusted_schema=OFF")
        sqlite.execute("PRAGMA cache_size=-8192")
        sqlite.set_progress_handler(lambda: int(monotonic() >= deadline), 10000)
        for name, table in tables.items():
            columns = table["columns"]
            projection = ", ".join(quote_ident(c["source_name"]) for c in columns)
            source_keys = [
                c["source_name"]
                for c in sorted(columns, key=lambda c: c["primary_key_position"])
                if c["primary_key_position"]
            ]
            ordering = ", ".join(map(quote_ident, source_keys)) if source_keys else "rowid"
            count = pins["tables"][name]["copy"]["rows"]
            offsets = sorted({0, count // 2, count - 1}) if count else []
            verified[name] = 0
            for offset in offsets:
                raw = sqlite.execute(
                    f"SELECT {projection} FROM {quote_ident(table['source_name'])} "
                    f"ORDER BY {ordering} LIMIT 1 OFFSET ?",
                    (offset,),
                ).fetchone()
                if (
                    raw is None
                    or sum(len(v.encode("utf-8")) for v in raw if isinstance(v, str)) > 1024 * 1024
                ):
                    raise ValueError("SQLite representative row missing or over budget")
                values = [
                    native_sample_value(v, c["source_type"], db_id=db_id)
                    for v, c in zip(raw, columns, strict=True)
                ]
                predicate = " AND ".join(
                    quote_ident(c["name"]) + " IS NOT DISTINCT FROM $" + str(i)
                    for i, c in enumerate(columns, 1)
                )
                if not await conn.fetchval(
                    f"SELECT EXISTS(SELECT 1 FROM {quote_ident(db_id)}.{quote_ident(name)} "
                    f"WHERE {predicate})",
                    *values,
                ):
                    raise ValueError("SQLite/native representative comparison differs")
                verified[name] += 1
                if monotonic() >= deadline:
                    raise ValueError("SQLite representative deadline exceeded")
    return verified


async def load_dataset(conn, source, db_id, password):
    if not isinstance(password, str) or not PASSWORD.fullmatch(password):
        raise ValueError("Invalid dataset password")
    if db_id not in DB_IDS:
        raise ValueError("Unsupported dataset")
    tables = validate_bundle(source, db_id)
    definitions = {name: table_definition(t) for name, t in tables.items()}
    pins, audit = load_specs()
    role_name = "warden_sandbox_" + db_id
    role, schema = quote_ident(role_name), quote_ident(db_id)
    async with asyncio.timeout(900), conn.transaction():
        await verify_local_database(conn)
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) "
            "OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)",
            db_id,
            role_name,
        )
        if exists:
            raise FileExistsError("Dataset schema or login exists; refusing changes")
        await conn.execute(
            "SET LOCAL statement_timeout='120s'; SET LOCAL lock_timeout='500ms'; "
            "SET LOCAL work_mem='16MB'; SET LOCAL temp_file_limit='2GB'; "
            "SET LOCAL idle_in_transaction_session_timeout='30s'; "
            "SET LOCAL timezone='UTC'; SET LOCAL DateStyle='ISO,YMD'"
        )
        await conn.execute(
            f"CREATE ROLE {role} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE "
            f"NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD '{password}'"
        )
        await conn.execute(f"GRANT CONNECT ON DATABASE sqlwarden TO {role}")
        for key, value in {
            "default_transaction_read_only": "on",
            "statement_timeout": "5s",
            "lock_timeout": "500ms",
            "idle_in_transaction_session_timeout": "5s",
            "work_mem": "16MB",
            "temp_file_limit": "64MB",
        }.items():
            await conn.execute(f"ALTER ROLE {role} SET {key}='{value}'")
        await conn.execute(f"ALTER ROLE {role} SET search_path=pg_catalog, {schema}")
        await conn.execute(f"CREATE SCHEMA {schema} AUTHORIZATION warden_owner")
        await conn.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
        await conn.execute("SET LOCAL ROLE warden_owner")
        for name, table in tables.items():
            await conn.execute(f"CREATE TABLE {schema}.{quote_ident(name)} ({definitions[name]})")
            await conn.copy_to_table(
                name,
                schema_name=db_id,
                source=source / db_id / (name + ".tsv"),
                columns=[c["name"] for c in table["columns"]],
                format="text",
                encoding="UTF8",
                timeout=120,
            )
        await conn.execute(f"GRANT USAGE ON SCHEMA {schema} TO {role}")
        await conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {role}")
        await conn.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA {schema} "
            f"GRANT SELECT ON TABLES TO {role}"
        )
        counts = {}
        for name in tables:
            counts[name] = await conn.fetchval(f"SELECT count(*) FROM {schema}.{quote_ident(name)}")
            if counts[name] != pins["tables"][name]["copy"]["rows"]:
                raise ValueError("Imported row count differs")
        await conn.execute("SET LOCAL ROLE NONE")
        await verify_native_content(
            conn,
            source / db_id,
            tables,
            schema=db_id,
            names=tuple(tables),
            copy_timeout=120,
        )
        samples = await verify_sqlite_samples(conn, db_id, tables, pins)
    return {
        "db_id": db_id,
        "rows": counts,
        "typed_native_content_verified": True,
        "sqlite_full_content_equivalence": "not established",
        "gold_conversion_validity": "not checked",
        "primary_descriptions": "not selected",
        "sqlite_representative_samples": samples,
        "sqlite_sample_policy": (
            "native REAL=float4; DATE=ISO; DATETIME="
            + (
                "UTC+08:00 source -> UTC (Codebase only)"
                if db_id == "codebase_community"
                else "UTC"
            )
            + "; no gold comparator change"
        ),
        "primary_key_tables": sum(bool(t["primary_key"]) for t in tables.values()),
        "foreign_key_enforcement": "metadata only; not installed",
        "source_foreign_key_check_status": audit["databases"][db_id]["foreign_key_check_status"],
        "source_foreign_key_violation_count": audit["databases"][db_id][
            "foreign_key_violation_count"
        ],
    }


async def import_one(db_id):
    options = setup_connection_options(dict(os.environ))
    options["command_timeout"] = 120
    password = os.environ.get(password_key(db_id), "")
    if not PASSWORD.fullmatch(password):
        raise ValueError("Separate dataset credentials required")
    validate_bundle(BUNDLE, db_id)
    conn = await asyncpg.connect(**options)
    try:
        result = await load_dataset(conn, BUNDLE, db_id, password)
    finally:
        await conn.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--init-credentials", action="store_true")
    choice.add_argument("--db", choices=DB_IDS)
    args = parser.parse_args()
    try:
        if args.init_credentials:
            initialize_credentials(ROOT)
            result = {"status": "credentials created; values private", "datasets": len(DB_IDS)}
        else:
            result = asyncio.run(import_one(args.db))
    except Exception as error:
        print(
            json.dumps(
                {"status": "failed", "stage": "dataset import", "error_type": type(error).__name__}
            )
        )
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

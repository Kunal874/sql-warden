"""Real restricted-login and rollback checks; private values are never reported."""

import os
from contextlib import asynccontextmanager

import asyncpg
import pytest
from test_postgres_boundary import LARGE_OBJECT_FUNCTIONS, connected, rolled_back

from scripts import load_release as loader
from scripts.load_bird import verify_native_content
from scripts.prepare_import_bundle import BUNDLE, DB_IDS, load_specs, validate_bundle
from sqlwarden.data import quote_ident

pytestmark = pytest.mark.integration


@asynccontextmanager
async def dataset_connected(db_id):
    key = loader.password_key(db_id)
    if os.environ.get("WARDEN_TEST_TARGET") != "sqlwarden-local" or not os.environ.get(key):
        pytest.skip("Supply dedicated setup and dataset test environments")
    if os.environ.get("WARDEN_PG_PORT") != "55432":
        pytest.fail("Fixed local test port required", pytrace=False)
    conn = None
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=55432,
            database="sqlwarden",
            user="warden_sandbox_" + db_id,
            password=os.environ[key],
            timeout=5,
            command_timeout=10,
        )
    except (OSError, asyncpg.PostgresError):
        pytest.fail("Configured dataset login unavailable", pytrace=False)
    try:
        yield conn
    finally:
        if conn is not None:
            await conn.close()


@pytest.mark.parametrize("db_id", DB_IDS)
async def test_dataset_counts_owned_tables_types_keys_and_null_counts(db_id):
    pins, audit = load_specs()
    wanted = audit["databases"][db_id]["tables"]
    async with dataset_connected(db_id) as conn, conn.transaction(readonly=True):
        for name, table in wanted.items():
            target = quote_ident(db_id) + "." + quote_ident(name)
            assert (
                await conn.fetchval(f"SELECT count(*) FROM {target}")
                == pins["tables"][name]["copy"]["rows"]
            )
            actual = await conn.fetch(
                "SELECT attname,format_type(atttypid,atttypmod),attnotnull "
                "FROM pg_attribute WHERE attrelid=$1::regclass AND attnum>0 "
                "AND NOT attisdropped ORDER BY attnum",
                target,
            )
            expected_types = {
                "TEXT": "text",
                "BIGINT": "bigint",
                "REAL": "real",
                "DATE": "date",
                "TIMESTAMPTZ": "timestamp with time zone",
            }
            assert [tuple(r) for r in actual] == [
                (
                    c["name"],
                    expected_types[c["native_type"]],
                    bool(c["declared_not_null"] or c["primary_key_position"]),
                )
                for c in table["columns"]
            ]
            keys = await conn.fetch(
                "SELECT a.attname FROM pg_constraint p "
                "CROSS JOIN LATERAL unnest(p.conkey) WITH ORDINALITY k(attnum,pos) "
                "JOIN pg_attribute a ON a.attrelid=p.conrelid AND a.attnum=k.attnum "
                "WHERE p.conrelid=$1::regclass AND p.contype='p' ORDER BY k.pos",
                target,
            )
            assert [r["attname"] for r in keys] == table["primary_key"]
            nulls = await conn.fetchrow(
                "SELECT "
                + ",".join(
                    "count(*) FILTER (WHERE " + quote_ident(c["name"]) + " IS NULL)"
                    for c in table["columns"]
                )
                + " FROM "
                + target
            )
            assert all(
                n == 0
                for n, c in zip(nulls, table["columns"], strict=True)
                if c["declared_not_null"] or c["primary_key_position"]
            )
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_constraint p JOIN pg_namespace n ON n.oid=p.connamespace "
                "WHERE n.nspname=$1 AND p.contype='f'",
                db_id,
            )
            == 0
        )  # Proposed metadata-only FKs; not a claim of clean source keys.
        assert await conn.fetchval(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname=$1 "
            "AND c.relkind='r' AND r.rolname='warden_owner'",
            db_id,
        ) == len(wanted)


@pytest.mark.parametrize("db_id", DB_IDS)
async def test_dataset_reader_privileges_memberships_defaults_and_function_acls(db_id):
    async with dataset_connected(db_id) as conn:
        role = await conn.fetchrow(
            "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,"
            "rolinherit,rolconnlimit "
            "FROM pg_roles WHERE rolname=current_user"
        )
        assert tuple(role) == (False, False, False, False, False, False, 2)
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_auth_members WHERE member="
                "(SELECT oid FROM pg_roles WHERE rolname=current_user)"
            )
            == 0
        )
        assert await conn.fetchval("SHOW default_transaction_read_only") == "on"
        assert list(await conn.fetchval("SELECT current_schemas(false)")) == ["pg_catalog", db_id]
        for setting, expected in [
            ("statement_timeout", "5s"),
            ("lock_timeout", "500ms"),
            ("work_mem", "16MB"),
            ("temp_file_limit", "64MB"),
        ]:
            assert await conn.fetchval("SHOW " + setting) == expected
        names = [*LARGE_OBJECT_FUNCTIONS, "pg_read_file", "pg_sleep", "pg_ls_dir"]
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='pg_catalog' AND p.proname=ANY($1::text[]) "
                "AND has_function_privilege(current_user,p.oid,'EXECUTE')",
                names,
            )
            == 0
        )


@pytest.mark.parametrize("db_id", DB_IDS)
@pytest.mark.parametrize(
    "operation",
    [
        "update",
        "delete",
        "create",
        "temp",
        "app",
        "peer",
        "owner",
        "app_role",
        "california_role",
        "function",
    ],
)
async def test_direct_denial_after_read_only_default_disabled(db_id, operation):
    pins, _audit = load_specs()
    name, table = next((n, t) for n, t in pins["tables"].items() if t["db_id"] == db_id)
    target = quote_ident(db_id) + "." + quote_ident(name)
    column = quote_ident(table["columns"][0]["name"])
    statements = {
        "update": f"UPDATE {target} SET {column}={column}",
        "delete": f"DELETE FROM {target}",
        "create": f"CREATE TABLE {quote_ident(db_id)}.forbidden_probe (id int)",
        "temp": "CREATE TEMP TABLE forbidden_probe (id int)",
        "app": "SELECT * FROM app.boundary_probe",
        "peer": "SELECT count(*) FROM california_schools.schools",
        "owner": "SET ROLE warden_owner",
        "app_role": "SET ROLE warden_app",
        "california_role": "SET ROLE warden_sandbox_california_schools",
        "function": "SELECT pg_catalog.lo_create(0)",
    }
    async with dataset_connected(db_id) as conn:
        await conn.execute("SET default_transaction_read_only=off")
        async with rolled_back(conn):
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(statements[operation])


@pytest.mark.parametrize("db_id,other", [(a, b) for a in DB_IDS for b in DB_IDS if a != b])
async def test_all_datasets_cross_read_and_role_denials(db_id, other):
    pins, _audit = load_specs()
    table = next(n for n, t in pins["tables"].items() if t["db_id"] == other)
    async with dataset_connected(db_id) as conn:
        for sql in (
            f"SELECT 1 FROM {quote_ident(other)}.{quote_ident(table)} LIMIT 1",
            "SET ROLE " + quote_ident("warden_sandbox_" + other),
        ):
            async with rolled_back(conn):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await conn.execute(sql)


async def test_mid_copy_failure_rolls_back_named_synthetic_import_probe(tmp_path, monkeypatch):
    db_id = "sqlwarden_import_probe"
    role = "warden_sandbox_" + db_id
    source = tmp_path / db_id
    source.mkdir()
    for name in ("first", "second"):
        (source / (name + ".tsv")).write_bytes(b"1\n")
    table = {
        "columns": [
            {
                "name": "id",
                "native_type": "BIGINT",
                "declared_not_null": False,
                "primary_key_position": 1,
            }
        ],
        "primary_key": ["id"],
    }
    monkeypatch.setattr(loader, "DB_IDS", (db_id,))
    monkeypatch.setattr(
        loader, "validate_bundle", lambda path, ident: {"first": table, "second": table}
    )
    monkeypatch.setattr(loader, "load_specs", lambda: ({}, {}))

    class InterruptAfterFirstCopy:
        def __init__(self, conn):
            self.conn, self.calls = conn, 0

        def __getattr__(self, name):
            return getattr(self.conn, name)

        async def copy_to_table(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 2:
                raise ValueError("injected mid-COPY interruption")
            return await self.conn.copy_to_table(*args, **kwargs)

    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        assert not await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) "
            "OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)",
            db_id,
            role,
        )
        proxy = InterruptAfterFirstCopy(conn)
        with pytest.raises(ValueError, match="mid-COPY"):
            await loader.load_dataset(proxy, tmp_path, db_id, "a" * 48)
        assert proxy.calls == 2
        assert not await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) "
            "OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)",
            db_id,
            role,
        )


@pytest.mark.parametrize("db_id", DB_IDS)
async def test_repeat_import_refuses_and_preserves_counts(db_id):
    async with dataset_connected(db_id):
        pass
    async with connected("warden_bootstrap") as conn:
        pins, _audit = load_specs()
        name = next(n for n, t in pins["tables"].items() if t["db_id"] == db_id)
        target = quote_ident(db_id) + "." + quote_ident(name)
        before = await conn.fetchval("SELECT count(*) FROM " + target)
        with pytest.raises(FileExistsError):
            await loader.load_dataset(conn, BUNDLE, db_id, os.environ[loader.password_key(db_id)])
        assert await conn.fetchval("SELECT count(*) FROM " + target) == before


@pytest.mark.parametrize("db_id", DB_IDS)
async def test_future_owner_defaults_are_dataset_specific(db_id):
    async with dataset_connected(db_id):
        pass
    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        await conn.execute("SET LOCAL ROLE warden_owner")
        target = quote_ident(db_id) + ".future_grant_probe"
        await conn.execute("CREATE TABLE " + target + " (id int)")
        own = "warden_sandbox_" + db_id
        assert await conn.fetchval("SELECT has_table_privilege($1,$2,'SELECT')", own, target)
        assert not await conn.fetchval("SELECT has_table_privilege($1,$2,'INSERT')", own, target)
        roles = await conn.fetch(
            "SELECT rolname FROM pg_roles WHERE "
            "(rolname LIKE 'warden_sandbox_%' OR rolname='warden_app') AND rolname<>$1",
            own,
        )
        for role in (r["rolname"] for r in roles):
            assert not await conn.fetchval(
                "SELECT has_table_privilege($1,$2,'SELECT')", role, target
            )


async def test_toxicology_same_count_mutation_is_detected_and_rolled_back():
    async with dataset_connected("toxicology"):
        pass
    tables = validate_bundle(BUNDLE, "toxicology")
    name, table = next(
        (n, t)
        for n, t in tables.items()
        if t["primary_key"]
        and any(c["native_type"] == "TEXT" and not c["primary_key_position"] for c in t["columns"])
    )
    field = next(
        c["name"]
        for c in table["columns"]
        if c["native_type"] == "TEXT" and not c["primary_key_position"]
    )
    key = table["primary_key"][0]
    target = '"toxicology".' + quote_ident(name)
    async with connected("warden_bootstrap") as conn:
        before = await conn.fetchval("SELECT count(*) FROM " + target)
        async with rolled_back(conn):
            await conn.execute(
                "SET LOCAL statement_timeout='120s'; SET LOCAL temp_file_limit='2GB'"
            )
            value = await conn.fetchval(
                "SELECT "
                + quote_ident(key)
                + " FROM "
                + target
                + " ORDER BY "
                + quote_ident(key)
                + " LIMIT 1"
            )
            await conn.execute(
                "UPDATE "
                + target
                + " SET "
                + quote_ident(field)
                + "=coalesce("
                + quote_ident(field)
                + ",'') || '_verification_probe' WHERE "
                + quote_ident(key)
                + "=$1",
                value,
            )
            assert await conn.fetchval("SELECT count(*) FROM " + target) == before
            with pytest.raises(ValueError, match="content differs"):
                await verify_native_content(
                    conn,
                    BUNDLE / "toxicology",
                    tables,
                    schema="toxicology",
                    names=tuple(tables),
                    copy_timeout=120,
                )
        assert await conn.fetchval("SELECT count(*) FROM " + target) == before
        async with rolled_back(conn):
            await conn.execute(
                "SET LOCAL statement_timeout='120s'; SET LOCAL temp_file_limit='2GB'"
            )
            await verify_native_content(
                conn,
                BUNDLE / "toxicology",
                tables,
                schema="toxicology",
                names=tuple(tables),
                copy_timeout=120,
            )


async def capture_metadata(db_ids=DB_IDS):
    pins, audit = load_specs()
    report = {
        "format_version": 1,
        "track": "native PostgreSQL import preparation",
        "gold_conversion_validity": "not checked",
        "sqlite_full_content_equivalence": "not established",
        "primary_descriptions": "not selected",
        "datasets": {},
    }
    for db_id in db_ids:
        tables = validate_bundle(BUNDLE, db_id)
        actual = {}
        async with dataset_connected(db_id) as conn, conn.transaction(readonly=True):
            for name, table in tables.items():
                target = quote_ident(db_id) + "." + quote_ident(name)
                rows = await conn.fetchval("SELECT count(*) FROM " + target)
                assert rows == pins["tables"][name]["copy"]["rows"]
                nulls = await conn.fetchrow(
                    "SELECT "
                    + ",".join(
                        "count(*) FILTER (WHERE " + quote_ident(c["name"]) + " IS NULL)"
                        for c in table["columns"]
                    )
                    + " FROM "
                    + target
                )
                actual[name] = {
                    "rows": rows,
                    "null_counts": list(nulls),
                    "columns": table["columns"],
                    "primary_key": table["primary_key"],
                    "source_foreign_keys": table["foreign_keys"],
                    "foreign_key_enforcement": "metadata only; not installed",
                    "native_source": pins["tables"][name]["copy"],
                }
        report["datasets"][db_id] = {
            "tables": actual,
            "source_foreign_key_check_status": audit["databases"][db_id][
                "foreign_key_check_status"
            ],
            "source_foreign_key_violation_count": audit["databases"][db_id][
                "foreign_key_violation_count"
            ],
        }
    return report


@pytest.mark.parametrize("db_id", DB_IDS)
@pytest.mark.parametrize(
    "role",
    [
        "warden_app",
        "warden_sandbox_demo_schools",
        "warden_sandbox_demo_other",
        "warden_sandbox_california_schools",
    ],
)
async def test_existing_runtime_logins_cannot_read_new_dataset(db_id, role):
    async with dataset_connected(db_id):
        pass
    pins, _audit = load_specs()
    table = next(n for n, t in pins["tables"].items() if t["db_id"] == db_id)
    async with connected(role) as conn, rolled_back(conn):
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetchval(
                "SELECT count(*) FROM " + quote_ident(db_id) + "." + quote_ident(table)
            )


@pytest.mark.parametrize("db_id", DB_IDS)
@pytest.mark.parametrize("database", ["postgres", "template1"])
async def test_new_reader_cannot_connect_to_unused_cluster_databases(db_id, database):
    async with dataset_connected(db_id):
        pass
    conn = None
    try:
        try:
            conn = await asyncpg.connect(
                host="127.0.0.1",
                port=55432,
                database=database,
                user="warden_sandbox_" + db_id,
                password=os.environ[loader.password_key(db_id)],
                timeout=5,
            )
        except asyncpg.InsufficientPrivilegeError:
            return
        except (OSError, asyncpg.PostgresError):
            pytest.fail("Unexpected connection result; private details suppressed", pytrace=False)
        pytest.fail("Reader connected to unused cluster database", pytrace=False)
    finally:
        if conn is not None:
            await conn.close()


async def save_metadata(destination, db_ids=DB_IDS):
    import json

    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Evidence destination exists")
    report = await capture_metadata(db_ids)
    raw = json.dumps(report, indent=2) + "\n"
    if len(raw.encode("utf-8")) > 512 * 1024:
        raise ValueError("Evidence metadata exceeds budget")
    with destination.open("x", encoding="utf-8", newline="\n") as file:
        file.write(raw)
    return {"status": "metadata captured", "datasets": len(report["datasets"])}

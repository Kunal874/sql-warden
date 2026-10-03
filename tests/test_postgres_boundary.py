"""Real direct-connection checks; no SQL guard is involved."""

import os
from contextlib import asynccontextmanager

import asyncpg
import pytest

pytestmark = pytest.mark.integration

ROLE_KEYS = {
    "warden_sandbox_demo_schools": "WARDEN_SCHOOLS_PASSWORD",
    "warden_sandbox_demo_other": "WARDEN_OTHER_PASSWORD",
    "warden_app": "WARDEN_APP_PASSWORD",
    "warden_bootstrap": "WARDEN_BOOTSTRAP_PASSWORD",
    "warden_sandbox_california_schools": "WARDEN_CALIFORNIA_PASSWORD",
}

LARGE_OBJECT_FUNCTIONS = (
    "lo_create",
    "lo_creat",
    "lo_from_bytea",
    "lo_put",
    "lowrite",
    "lo_unlink",
    "lo_truncate",
    "lo_truncate64",
    "lo_open",
    "lo_close",
    "loread",
    "lo_get",
    "lo_lseek",
    "lo_lseek64",
    "lo_tell",
    "lo_tell64",
    "lo_import",
    "lo_export",
)


@asynccontextmanager
async def connected(role="warden_sandbox_demo_schools"):
    if os.environ.get("WARDEN_TEST_TARGET") != "sqlwarden-local":
        pytest.skip("Use the dedicated local .env.setup file to run PostgreSQL integration tests")
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=int(os.environ["WARDEN_PG_PORT"]),
            user=role,
            password=os.environ[ROLE_KEYS[role]],
            database="sqlwarden",
            timeout=5,
        )
    except (OSError, asyncpg.InvalidPasswordError):
        pytest.fail("The dedicated PostgreSQL server and restricted login must be available")
    try:
        yield conn
    finally:
        await conn.close()


@asynccontextmanager
async def rolled_back(conn):
    """Preserve persistent fixtures even if a denial unexpectedly succeeds."""
    transaction = conn.transaction()
    await transaction.start()
    try:
        yield
    finally:
        await transaction.rollback()


async def test_reader_can_read_its_own_synthetic_rows():
    async with connected() as conn:
        rows = await conn.fetch(
            'SELECT "School Name", enrollment FROM demo_schools.schools ORDER BY id'
        )
        assert [tuple(row) for row in rows] == [("Sample North", 120), ("Sample South", 80)]


@pytest.mark.parametrize("raise_after_write", [False, True])
async def test_probe_transaction_always_rolls_back(raise_after_write):
    async with connected("warden_app") as conn:
        before = await conn.fetch("SELECT value FROM app.boundary_probe ORDER BY value")
        observed_failure = False
        try:
            async with rolled_back(conn):
                await conn.execute("INSERT INTO app.boundary_probe VALUES ('rollback-probe')")
                assert (
                    await conn.fetchval(
                        "SELECT count(*) FROM app.boundary_probe WHERE value = 'rollback-probe'"
                    )
                    == 1
                )
                if raise_after_write:
                    raise AssertionError("simulated unexpected probe success")
        except AssertionError as error:
            assert raise_after_write
            assert str(error) == "simulated unexpected probe success"
            observed_failure = True
        assert observed_failure == raise_after_write
        after = await conn.fetch("SELECT value FROM app.boundary_probe ORDER BY value")
        assert after == before


@pytest.mark.parametrize("role", ["warden_sandbox_demo_schools", "warden_sandbox_demo_other"])
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT pg_catalog.lo_create(0)",
        "SELECT pg_catalog.lo_creat(131072)",
        "SELECT pg_catalog.lo_from_bytea(0, decode('01', 'hex'))",
    ],
)
async def test_reader_cannot_create_large_objects_even_with_read_only_disabled(role, sql):
    async with connected(role) as conn:
        await conn.execute("SET default_transaction_read_only = off")
        async with rolled_back(conn):
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.fetchval(sql)


@pytest.mark.parametrize(
    "role",
    [
        "warden_sandbox_demo_schools",
        "warden_sandbox_demo_other",
        "warden_app",
    ],
)
async def test_all_large_object_overloads_are_denied_to_runtime_logins(role):
    async with connected(role) as conn:
        functions = await conn.fetch(
            "SELECT p.proname, p.oid::regprocedure::text AS signature, "
            "has_function_privilege(current_user, p.oid, 'EXECUTE') AS executable "
            "FROM pg_catalog.pg_proc p "
            "JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace "
            "WHERE n.nspname = 'pg_catalog' AND p.proname = ANY($1::text[])",
            LARGE_OBJECT_FUNCTIONS,
        )
        assert {row["proname"] for row in functions} == set(LARGE_OBJECT_FUNCTIONS)
        assert [row["signature"] for row in functions if row["executable"]] == []


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO demo_schools.schools VALUES (3, 'not allowed', 1)",
        "UPDATE demo_schools.schools SET enrollment = 0",
        "DELETE FROM demo_schools.schools",
        "TRUNCATE demo_schools.schools",
        "DROP TABLE demo_schools.schools",
        "CREATE TABLE demo_schools.forbidden (id int)",
        "CREATE SCHEMA forbidden",
        "CREATE TEMP TABLE forbidden (id int)",
        "SELECT * FROM demo_other.canary",
        "SELECT * FROM app.boundary_probe",
        "SET ROLE warden_sandbox_demo_other",
        "SET ROLE warden_app",
        "SET ROLE warden_owner",
        "SELECT pg_catalog.pg_sleep(0)",
        "SELECT pg_catalog.pg_read_file('/sqlwarden-nonexistent-fixture')",
    ],
)
async def test_privileges_deny_forbidden_sql_even_with_read_only_default_disabled(sql):
    async with connected() as conn:
        await conn.execute("SET default_transaction_read_only = off")
        async with rolled_back(conn):
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(sql)
        assert await conn.fetchval("SELECT count(*) FROM demo_schools.schools") == 2


async def test_search_path_and_custom_settings_do_not_grant_other_dataset_access():
    async with connected() as conn:
        await conn.execute("SET search_path = demo_other")
        await conn.execute("SELECT set_config('app.tenant_id', '99', false)")
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetch("SELECT * FROM demo_other.canary")


async def test_read_only_is_an_additional_transaction_boundary():
    async with connected() as conn:
        assert await conn.fetchval("SHOW default_transaction_read_only") == "on"
        async with conn.transaction(readonly=True):
            with pytest.raises(asyncpg.ReadOnlySQLTransactionError):
                await conn.execute("INSERT INTO demo_schools.schools VALUES (3, 'blocked', 1)")


@pytest.mark.parametrize(
    "role", ["warden_sandbox_demo_schools", "warden_sandbox_demo_other", "warden_app"]
)
async def test_runtime_logins_have_no_privileged_flags_or_role_memberships(role):
    async with connected(role) as conn:
        flags = await conn.fetchrow(
            "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
            "FROM pg_catalog.pg_roles WHERE rolname = current_user"
        )
        assert tuple(flags) == (False, False, False, False, False)
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_catalog.pg_auth_members "
                "WHERE member = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_user)"
            )
            == 0
        )


@pytest.mark.parametrize(
    "sql", ["SELECT * FROM demo_schools.schools", "SELECT * FROM demo_other.canary"]
)
async def test_app_login_cannot_read_dataset_rows(sql):
    async with connected("warden_app") as conn:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetch(sql)


async def test_app_login_can_store_application_state():
    async with connected("warden_app") as conn, rolled_back(conn):
        await conn.execute("INSERT INTO app.boundary_probe (value) VALUES ('local-check')")
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM app.boundary_probe WHERE value = 'local-check'"
            )
            == 1
        )
        await conn.execute("DELETE FROM app.boundary_probe WHERE value = 'local-check'")


async def test_other_reader_is_isolated_in_both_directions():
    async with connected("warden_sandbox_demo_other") as conn:
        assert (
            await conn.fetchval("SELECT value FROM demo_other.canary") == "synthetic-other-dataset"
        )
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetch("SELECT * FROM demo_schools.schools")


async def test_new_owner_created_tables_inherit_only_their_dataset_reader():
    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        await conn.execute("SET LOCAL ROLE warden_owner")
        await conn.execute("CREATE TABLE demo_schools.future_grant_probe (id int)")
        access = await conn.fetchrow(
            "SELECT "
            "has_table_privilege('warden_sandbox_demo_schools', "
            "'demo_schools.future_grant_probe', 'SELECT'), "
            "has_table_privilege('warden_sandbox_demo_other', "
            "'demo_schools.future_grant_probe', 'SELECT'), "
            "has_table_privilege('warden_app', 'demo_schools.future_grant_probe', 'SELECT')"
        )
        assert tuple(access) == (True, False, False)

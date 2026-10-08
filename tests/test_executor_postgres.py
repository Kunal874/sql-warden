"""Actual restricted PostgreSQL bounds, cancellation and connection recovery."""

import asyncio
import os

import pytest
from test_bird_load import california_connected

from sqlwarden.config import QueryLimits
from sqlwarden.executor import QueryExecutor, dataset_password_key, open_california_executor
from sqlwarden.guard import DATASET_POLICIES

pytestmark = pytest.mark.integration


async def ready():
    async with california_connected():
        pass  # skip only when the dedicated target/reader is not supplied


def password():
    return os.environ["WARDEN_CALIFORNIA_PASSWORD"]


def dataset_password(db_id):
    key = dataset_password_key(db_id)
    if os.environ.get("WARDEN_TEST_TARGET") != "sqlwarden-local" or not os.environ.get(key):
        pytest.skip("Supply dedicated setup, California and dataset test environments")
    return os.environ[key]


async def test_real_handwritten_count_and_duplicate_positions():
    await ready()
    async with open_california_executor(password()) as executor:
        count = await executor.execute("SELECT count(*) AS n FROM schools")
        assert (count.status, count.columns, count.rows) == ("ok", ("n",), ((17686,),))
        duplicate = await executor.execute("SELECT 1 AS x, 2 AS x")
        assert duplicate.status == "ok" and duplicate.columns == ("x", "x")
        assert duplicate.rows == ((1, 2),)


async def test_real_empty_and_null_results_are_complete():
    await ready()
    async with open_california_executor(password()) as executor:
        empty = await executor.execute("SELECT cdscode FROM schools WHERE false")
        null = await executor.execute("SELECT NULL AS n")
        assert empty.status == "ok" and empty.rows == ()
        assert null.status == "ok" and null.rows == ((None,),)


async def test_real_row_cap_and_cap_plus_one_do_not_change_order_or_sql():
    await ready()
    limits = QueryLimits(max_rows=2)
    async with open_california_executor(password(), limits) as executor:
        two = await executor.execute("SELECT n FROM (VALUES (2),(1)) x(n) ORDER BY n")
        three = await executor.execute("SELECT n FROM (VALUES (2),(1),(3)) x(n) ORDER BY n")
        assert two.status == "ok" and two.rows == ((1,), (2,))
        assert (three.status, three.reason, three.rows) == ("overflow", "row_limit", ())
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"


@pytest.mark.parametrize("cap, status", [(30, "ok"), (29, "overflow")])
async def test_real_exact_result_bytes(cap, status):
    await ready()
    limits = QueryLimits(max_result_bytes=cap, max_cell_bytes=16)
    async with open_california_executor(password(), limits) as executor:
        result = await executor.execute("SELECT 1 AS n")
        assert result.status == status
        assert result.rows == (((1,),) if status == "ok" else ())


async def test_real_utf8_cell_limit_and_recovery():
    await ready()
    async with open_california_executor(password(), QueryLimits(max_cell_bytes=4)) as executor:
        good = await executor.execute("SELECT 'é' AS n")
        bad = await executor.execute("SELECT 'éé' AS n")
        assert good.status == "ok" and good.rows == (("é",),)
        assert bad.reason == "cell_limit" and bad.rows == ()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"


async def test_real_cost_and_estimated_row_gates():
    await ready()
    async with open_california_executor(password(), QueryLimits(max_estimated_cost=1)) as executor:
        result = await executor.execute("SELECT count(*) FROM schools")
        assert result.reason == "cost_limit" and result.rows == ()
    async with open_california_executor(password(), QueryLimits(max_estimated_rows=1)) as executor:
        result = await executor.execute("SELECT cdscode FROM schools")
        assert result.reason == "plan_row_limit" and result.rows == ()


async def test_real_engine_failure_is_sanitized_and_pool_recovers(caplog, capsys):
    await ready()
    async with open_california_executor(password()) as executor:
        result = await executor.execute("SELECT CAST('private-canary' AS int)")
        assert (result.status, result.reason, result.rows) == ("failed", "database_error", ())
        assert "private-canary" not in repr(result) + caplog.text + str(capsys.readouterr())
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)


async def test_real_pool_acquisition_has_a_finite_bound():
    await ready()
    async with open_california_executor(password()) as executor:
        # Cold authentication uses the normal finite bound; this tests slot contention.
        bounded = QueryExecutor(executor._pool, QueryLimits(pool_timeout_ms=50))
        # White-box test only: occupy its sole slot, never expose a lease to a request.
        async with executor._pool.acquire(timeout=1):
            result = await asyncio.wait_for(bounded.execute("SELECT 1"), 1)
            assert result.reason == "timeout" and result.rows == ()
        assert (await bounded.execute("SELECT 1 AS n")).status == "ok"


async def test_real_query_timeout_discards_then_replaces_connection():
    await ready()
    limits = QueryLimits(
        statement_timeout_ms=50,
        lock_timeout_ms=10,
        pool_timeout_ms=500,
        total_timeout_ms=1000,
        max_estimated_cost=1000000000,
        max_estimated_rows=1000000000,
    )
    async with open_california_executor(password(), limits) as executor:
        result = await asyncio.wait_for(
            executor.execute("SELECT count(*) FROM schools a CROSS JOIN schools b"), 2
        )
        assert result.reason == "timeout" and result.rows == ()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"


async def test_real_external_cancellation_releases_resources_and_pool_recovers():
    await ready()
    limits = QueryLimits(max_estimated_cost=1000000000, max_estimated_rows=1000000000)
    sql = "SELECT count(*) FROM schools a CROSS JOIN schools b"
    async with (
        california_connected() as observer,
        open_california_executor(password(), limits) as executor,
    ):
        task = asyncio.create_task(executor.execute(sql))
        phase = "observe active execution"
        try:
            pid = None
            async with asyncio.timeout(2):
                while pid is None:
                    pid = await observer.fetchval(
                        "SELECT pid FROM pg_catalog.pg_stat_activity "
                        "WHERE usename=current_user AND state='active' AND query=$1",
                        sql,
                        timeout=1,
                    )
                    if pid is not None:
                        break
                    if task.done():
                        pytest.fail(
                            "The bounded control did not reach active execution", pytrace=False
                        )
                    await asyncio.sleep(0.01)
            task.cancel()
            phase = "await caller cancellation"
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 1)
            phase = "observe server connection removal"
            async with asyncio.timeout(1):
                while await observer.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_stat_activity WHERE pid=$1)",
                    pid,
                    timeout=1,
                ):
                    await asyncio.sleep(0.01)
            phase = "replacement connection"
            assert (await executor.execute("SELECT 1 AS n")).status == "ok"
        except TimeoutError:
            pytest.fail("Cancellation control timed out during " + phase, pytrace=False)
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def test_real_transaction_local_overrides_reset_after_release():
    await ready()
    limits = QueryLimits(
        statement_timeout_ms=123, lock_timeout_ms=10, pool_timeout_ms=500, total_timeout_ms=1000
    )
    query = (
        "SELECT current_user, current_database(), "
        "pg_catalog.current_setting('transaction_read_only'), "
        "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='statement_timeout'), "
        "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='lock_timeout'), "
        "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='work_mem')"
    )
    expected = ("warden_sandbox_california_schools", "sqlwarden", "on", 5000, 500, 16384)
    async with open_california_executor(password(), limits) as executor:
        async with executor._pool.acquire(timeout=1) as conn:
            assert not conn.is_in_transaction()
            assert tuple(await conn.fetchrow(query, timeout=1)) == expected
            assert not conn.is_in_transaction()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"
        async with executor._pool.acquire(timeout=1) as conn:
            assert not conn.is_in_transaction()
            assert tuple(await conn.fetchrow(query, timeout=1)) == expected
            assert not conn.is_in_transaction()


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT missing_column FROM schools",
        "SELECT lower(1)",
    ],
)
async def test_real_undefined_objects_fail_and_next_query_recovers(sql):
    await ready()
    async with open_california_executor(password()) as executor:
        result = await executor.execute(sql)
        assert (result.status, result.reason, result.rows) == ("failed", "undefined_object", ())
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)


async def test_real_invalid_password_returns_only_a_connection_category(caplog, capsys):
    await ready()
    async with open_california_executor("incorrect-test-password") as executor:
        result = await executor.execute("SELECT 1")
        assert (result.status, result.reason, result.rows) == ("failed", "connection_error", ())
        assert "incorrect-test-password" not in (
            repr(result) + caplog.text + str(capsys.readouterr())
        )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM schools",
        "SELECT * FROM app.runs",
        "SELECT pg_sleep(1)",
    ],
)
async def test_real_guard_denial_never_returns_data(sql):
    await ready()
    async with open_california_executor(password()) as executor:
        result = await executor.execute(sql)
        assert result.status == "blocked" and result.columns == () and result.rows == ()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"


@pytest.mark.parametrize(
    "db_id, table",
    [(db_id, sorted(policy.tables)[0]) for db_id, policy in DATASET_POLICIES.items()],
)
async def test_real_dataset_executor_uses_each_restricted_identity(db_id, table):
    from sqlwarden.executor import open_dataset_executor

    async with open_dataset_executor(db_id, dataset_password(db_id)) as executor:
        result = await executor.execute(f"SELECT count(*) AS n FROM {table}")
        assert result.status == "ok" and type(result.rows[0][0]) is int
        async with executor._pool.acquire(timeout=1) as conn:
            identity = await conn.fetchrow(
                "SELECT current_user AS u, current_schemas(false) AS p", timeout=1
            )
        assert tuple(identity) == (f"warden_sandbox_{db_id}", ["pg_catalog", db_id])
        blocked = await executor.execute("SELECT count(*) AS n FROM app.boundary_probe")
        assert (blocked.status, blocked.reason, blocked.rows) == (
            "blocked",
            "schema_not_allowed",
            (),
        )
        for sql in (f"DELETE FROM {table}", "SET ROLE warden_owner"):
            denied = await executor.execute(sql)
            assert (denied.status, denied.reason, denied.rows) == (
                "blocked",
                "statement_not_allowed",
                (),
            )

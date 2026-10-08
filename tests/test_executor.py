"""Complete results and budgets must not confuse a prefix with an answer."""

import asyncio
import json
import math
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import asyncpg
import pytest

from sqlwarden.config import QueryLimits
from sqlwarden.executor import (
    QueryExecutor,
    QueryResult,
    _check_plan,
    _ResultBuffer,
    dataset_password_key,
)
from sqlwarden.guard import DATASET_POLICIES


def limits(**changes):
    return QueryLimits(**({"max_rows": 2, "max_result_bytes": 128, "max_cell_bytes": 64} | changes))


def test_exact_row_cap_is_complete_but_next_row_discards_prefix():
    buf = _ResultBuffer(("n",), limits())
    assert buf.append((1,)) is None
    assert buf.append((1,)) is None
    result = buf.finish()
    assert (result.status, result.rows, result.result_bytes) == ("ok", ((1,), (1,)), 34)
    assert buf.append((2,)) == "row_limit"
    result = buf.finish()
    assert (result.status, result.columns, result.rows, result.result_bytes) == (
        "overflow",
        (),
        (),
        0,
    )


@pytest.mark.parametrize("cap, status", [(30, "ok"), (29, "overflow")])
def test_result_byte_boundary_includes_names_and_json_framing(cap, status):
    buf = _ResultBuffer(("n",), limits(max_result_bytes=cap, max_cell_bytes=16))
    buf.append((1,))
    assert buf.finish().status == status


@pytest.mark.parametrize("value, reason", [("é", None), ("éé", "cell_limit")])
def test_cell_boundary_uses_encoded_utf8_not_character_count(value, reason):
    buf = _ResultBuffer(("n",), limits(max_cell_bytes=4))
    assert buf.append((value,)) == reason


def test_empty_and_null_results_are_successes_not_repair_triggers():
    empty = _ResultBuffer(("n",), limits()).finish()
    assert (empty.status, empty.rows, empty.result_bytes) == ("ok", (), 27)
    buf = _ResultBuffer(("n",), limits())
    assert buf.append((None,)) is None
    assert buf.finish().rows == ((None,),)


def test_duplicate_column_names_and_cell_types_are_preserved():
    row = (Decimal("1.50"), date(2020, 1, 1), True, 1.5)
    buf = _ResultBuffer(("x", "x", "b", "f"), limits())
    assert buf.append(row) is None
    result = buf.finish()
    assert result.columns == ("x", "x", "b", "f")
    assert result.rows == (row,)
    assert [type(cell) for cell in result.rows[0]] == [Decimal, date, bool, float]


@pytest.mark.parametrize("row", [(object(),), ("\ud800",), (1, 2)])
def test_unrepresentable_or_wrong_width_rows_fail_without_data(row):
    buf = _ResultBuffer(("n",), limits())
    assert buf.append(row) == "unsupported_result"
    result = buf.finish()
    assert (result.status, result.rows, result.columns) == ("failed", (), ())


@pytest.mark.parametrize(
    "cost, rows, reason",
    [
        (100000, 100000, None),
        (100000.01, 1, "cost_limit"),
        (1, 100001, "plan_row_limit"),
        (-1, 1, "plan_error"),
        (True, 1, "plan_error"),
        (1, True, "plan_error"),
    ],
)
def test_plan_estimates_have_exact_finite_boundaries(cost, rows, reason):
    plan = json.dumps([{"Plan": {"Total Cost": cost, "Plan Rows": rows}}])
    assert _check_plan(plan, QueryLimits()) == reason


@pytest.mark.parametrize(
    "plan",
    [
        None,
        "private-canary",
        "[]",
        "[{},{}]",
        '[{"Plan":{"Total Cost":NaN,"Plan Rows":1}}]',
    ],
)
def test_malformed_plans_fail_without_echoing_their_contents(plan):
    assert _check_plan(plan, QueryLimits()) == "plan_error"


def test_metadata_alone_can_exceed_the_result_cap():
    result = _ResultBuffer(("n",), limits(max_result_bytes=26, max_cell_bytes=16)).finish()
    assert (result.status, result.reason, result.rows) == ("overflow", "result_limit", ())


def test_json_escaping_counts_against_a_cell():
    buf = _ResultBuffer(("n",), limits(max_cell_bytes=3))
    assert buf.append(("\n",)) == "cell_limit"


def test_nonfinite_cells_keep_the_original_float():
    value = float("nan")
    buf = _ResultBuffer(("n",), limits())
    assert buf.append((value,)) is None
    result = buf.finish()
    assert result.status == "ok" and math.isnan(result.rows[0][0])


@pytest.mark.parametrize("size, reason", [(65536, None), (65537, "plan_limit")])
def test_plan_byte_limit_is_independent_of_cell_size(size, reason):
    prefix = '[{"Plan":{"Total Cost":1,"Plan Rows":1}}]'
    text = prefix + " " * (size - len(prefix))
    assert _check_plan(text, limits(max_cell_bytes=4)) == reason


def test_result_is_immutable():
    result = QueryResult("ok", "ok")
    with pytest.raises(FrozenInstanceError):
        result.status = "failed"


@pytest.mark.parametrize("columns", [("\ud800",), (1,)])
def test_invalid_metadata_is_a_sanitized_failure(columns):
    result = _ResultBuffer(columns, limits()).finish()
    assert (result.status, result.reason, result.columns, result.rows) == (
        "failed",
        "unsupported_result",
        (),
        (),
    )


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), Decimal("Infinity")])
def test_nonfinite_numbers_keep_their_original_types(value):
    buf = _ResultBuffer(("n",), limits())
    assert buf.append((value,)) is None
    result = buf.finish()
    assert result.status == "ok" and result.rows == ((value,),)
    assert type(result.rows[0][0]) is type(value)


@pytest.mark.parametrize(
    "text",
    [
        '[{"Plan":{"Plan Rows":1}}]',
        '[{"Plan":{"Total Cost":1}}]',
        '[{"Plan":{"Total Cost":Infinity,"Plan Rows":1}}]',
        "[" * 2000 + "0" + "]" * 2000,
        "\ud800",
    ],
)
def test_missing_keys_and_unrepresentable_plans_fail_closed(text):
    assert _check_plan(text, QueryLimits()) == "plan_error"


def test_estimate_defaults_are_explicit_not_calibrated():
    default = QueryLimits()
    assert (default.max_estimated_cost, default.max_estimated_rows) == (100000, 100000)


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rows = iter(conn.rows)

    async def fetch(self, n, *, timeout=None):
        self.conn.calls.append(("fetch", n))
        await self.conn.phase("fetch")
        assert n == 1 and timeout is not None and timeout > 0
        row = next(self.rows, None)
        return [] if row is None else [row]


class FakeStatement:
    def __init__(self, conn):
        self.conn = conn

    def get_attributes(self):
        return tuple(
            asyncpg.types.Attribute(name, asyncpg.types.Type(23, "int4", "scalar", "pg_catalog"))
            for name in self.conn.columns
        )

    async def cursor(self, *, timeout=None):
        self.conn.calls.append(("cursor",))
        await self.conn.phase("cursor")
        return FakeCursor(self.conn)


class FakeTransaction:
    def __init__(self, conn):
        self.conn = conn

    async def start(self):
        self.conn.calls.append(("begin",))
        await self.conn.phase("begin")

    async def rollback(self):
        self.conn.calls.append(("rollback",))
        await self.conn.phase("rollback")


class FakeConnection:
    def __init__(self, pool):
        self.pool = pool
        self.calls = []
        self.rows = [(1,)]
        self.columns = ("n",)
        self.identity = (
            "warden_sandbox_california_schools",
            "sqlwarden",
            "on",
            "pg_catalog, california_schools",
            5000,
            500,
            16384,
            65536,
        )
        self.plan = '[{"Plan":{"Total Cost":1,"Plan Rows":1}}]'
        self.block = None
        self.error = None
        self.started = asyncio.Event()
        self.terminated = False

    async def phase(self, phase):
        if phase == self.block:
            self.started.set()
            await asyncio.Event().wait()
        if self.error and phase == "prepare":
            raise self.error

    def transaction(self, *, readonly=False):
        assert readonly is True
        return FakeTransaction(self)

    async def execute(self, sql, *args, timeout=None):
        self.calls.append(("settings", sql, args))
        await self.phase("settings")

    async def fetchrow(self, sql, *, timeout=None):
        self.calls.append(("identity", sql))
        await self.phase("identity")
        return self.identity

    async def fetchval(self, sql, *, timeout=None):
        self.calls.append(("plan", sql))
        await self.phase("plan")
        return self.plan

    async def prepare(self, sql, *, timeout=None):
        self.calls.append(("prepare", sql))
        await self.phase("prepare")
        return FakeStatement(self)

    def terminate(self):
        self.terminated = True
        self.pool.leased = False


class FakePool:
    def __init__(self):
        self.conn = FakeConnection(self)
        self.acquires = 0
        self.leased = False
        self.block_acquire = False
        self.block_release = False
        self.block_close = False
        self.close_error = None
        self.close_started = asyncio.Event()
        self.closes = 0
        self.terminated = False

    async def acquire(self, *, timeout=None):
        self.acquires += 1
        if self.block_acquire:
            await asyncio.sleep(timeout)
            raise TimeoutError
        self.leased = True
        return self.conn

    async def release(self, conn, *, timeout=None):
        assert conn is self.conn and timeout is not None and timeout > 0
        if self.block_release:
            await asyncio.Event().wait()
        self.leased = False

    async def close(self):
        self.closes += 1
        self.close_started.set()
        if self.block_close:
            await asyncio.Event().wait()
        if self.close_error:
            raise self.close_error

    def terminate(self):
        self.terminated = True
        self.conn.terminate()


@pytest.mark.parametrize(
    "sql",
    ["DELETE FROM schools", "SELECT pg_sleep(1)", "SELECT 1; SELECT 2", "SELECT * FROM app.runs"],
)
async def test_guard_denial_never_acquires_or_explains(sql):
    pool = FakePool()
    result = await QueryExecutor(pool, QueryLimits()).execute(sql)
    assert result.status == "blocked" and result.rows == ()
    assert pool.acquires == 0 and pool.conn.calls == []


async def test_unchanged_sql_uses_guard_then_cost_then_cursor_then_rollback():
    pool = FakePool()
    sql = " SELECT 1 AS n -- keep these bytes\n"
    result = await QueryExecutor(pool, QueryLimits()).execute(sql)
    assert result.status == "ok" and result.rows == ((1,),)
    assert ("plan", "EXPLAIN (FORMAT JSON) " + sql) in pool.conn.calls
    assert ("prepare", sql) in pool.conn.calls
    names = [call[0] for call in pool.conn.calls]
    assert names == [
        "begin",
        "settings",
        "identity",
        "plan",
        "prepare",
        "cursor",
        "fetch",
        "fetch",
        "rollback",
    ]
    assert not pool.leased


async def test_wrong_identity_never_plans_or_executes():
    pool = FakePool()
    pool.conn.identity = ("warden_owner",) + pool.conn.identity[1:]
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "configuration_error" and result.rows == ()
    assert not any(call[0] in {"plan", "prepare", "cursor"} for call in pool.conn.calls)


async def test_dataset_executor_uses_fixed_policy_identity_and_search_path():
    pool = FakePool()
    pool.conn.identity = (
        "warden_sandbox_financial",
        "sqlwarden",
        "on",
        "pg_catalog, financial",
        5000,
        500,
        16384,
        65536,
    )
    result = await QueryExecutor(pool, QueryLimits(), DATASET_POLICIES["financial"]).execute(
        "SELECT count(*) FROM account"
    )
    assert result.status == "ok"
    assert ("settings", pool.conn.calls[1][1], pool.conn.calls[1][2]) == (
        "settings",
        "SELECT pg_catalog.set_config('statement_timeout',$1,true), "
        "pg_catalog.set_config('lock_timeout',$2,true), "
        "pg_catalog.set_config('search_path',$3,true), "
        "pg_catalog.set_config('work_mem','16MB',true)",
        ("5000ms", "500ms", "pg_catalog, financial"),
    )


async def test_dataset_executor_guard_uses_that_dataset_policy():
    pool = FakePool()
    pool.conn.identity = (
        "warden_sandbox_financial",
        "sqlwarden",
        "on",
        "pg_catalog, financial",
        5000,
        500,
        16384,
        65536,
    )
    accepted = await QueryExecutor(pool, QueryLimits(), DATASET_POLICIES["financial"]).execute(
        "SELECT count(*) FROM account"
    )
    denied = await QueryExecutor(pool, QueryLimits(), DATASET_POLICIES["financial"]).execute(
        "SELECT count(*) FROM schools"
    )
    assert accepted.status == "ok"
    assert (denied.status, denied.reason) == ("blocked", "table_not_allowed")


@pytest.mark.parametrize(
    "phase",
    ["begin", "settings", "identity", "plan", "prepare", "cursor", "fetch", "rollback", "release"],
)
async def test_total_deadline_discards_connection_in_every_phase(phase):
    pool = FakePool()
    pool.conn.block = phase
    pool.block_release = phase == "release"
    small = QueryLimits(
        statement_timeout_ms=20, lock_timeout_ms=5, pool_timeout_ms=20, total_timeout_ms=40
    )
    # This fake reports the small settings too; it models server-observed values.
    pool.conn.identity = pool.conn.identity[:4] + (20, 5, 16384, 65536)
    result = await asyncio.wait_for(QueryExecutor(pool, small).execute("SELECT 1"), 1)
    assert result.reason == "timeout" and result.rows == ()
    assert pool.conn.terminated and not pool.leased


@pytest.mark.parametrize(
    "error, reason",
    [
        (asyncpg.PostgresSyntaxError("private-canary"), "syntax_error"),
        (asyncpg.UndefinedColumnError("private-canary"), "undefined_object"),
        (asyncpg.InsufficientPrivilegeError("private-canary"), "permission_error"),
        (asyncpg.InvalidPasswordError("private-canary"), "connection_error"),
        (asyncpg.QueryCanceledError("private-canary"), "timeout"),
        (ValueError("private-canary"), "internal_error"),
    ],
)
async def test_driver_errors_never_return_or_log_private_details(error, reason, caplog, capsys):
    pool = FakePool()
    pool.conn.error = error
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert (result.status, result.reason, result.rows) == ("failed", reason, ())
    assert pool.conn.terminated and not pool.leased
    assert "private-canary" not in repr(result) + caplog.text + str(capsys.readouterr())


@pytest.mark.parametrize(
    "plan, reason",
    [
        ("[]", "plan_error"),
        ('[{"Plan":{"Total Cost":100001,"Plan Rows":1}}]', "cost_limit"),
        ('[{"Plan":{"Total Cost":1,"Plan Rows":100001}}]', "plan_row_limit"),
    ],
)
async def test_plan_denial_never_prepares_the_candidate(plan, reason):
    pool = FakePool()
    pool.conn.plan = plan
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == reason and result.rows == ()
    assert not any(call[0] in {"prepare", "cursor", "fetch"} for call in pool.conn.calls)
    assert not pool.leased


async def test_acquisition_timeout_has_no_query_or_lease():
    pool = FakePool()
    pool.block_acquire = True
    small = QueryLimits(pool_timeout_ms=20)
    result = await QueryExecutor(pool, small).execute("SELECT 1")
    assert result.reason == "timeout" and result.rows == () and not pool.leased
    assert pool.conn.calls == []


async def test_a_forged_guard_decision_is_not_execution_permission():
    from sqlwarden.guard import GuardDecision

    pool = FakePool()
    result = await QueryExecutor(pool, QueryLimits()).execute(
        GuardDecision(True, "accepted", "DELETE FROM schools")
    )
    assert result.reason == "input_invalid" and pool.acquires == 0


@pytest.mark.parametrize(
    "index, value",
    [
        (1, "other"),
        (2, "off"),
        (3, "public"),
        (4, 4999),
        (5, 499),
        (6, 32768),
        (7, -1),
        (7, 65537),
    ],
)
async def test_changed_server_settings_fail_before_candidate_planning(index, value):
    pool = FakePool()
    identity = list(pool.conn.identity)
    identity[index] = value
    pool.conn.identity = tuple(identity)
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "configuration_error" and result.rows == ()
    assert not any(call[0] in {"plan", "prepare"} for call in pool.conn.calls)
    assert not pool.leased


@pytest.mark.parametrize(
    "identity",
    [
        None,
        (),
        ("wrong",),
        (
            "warden_sandbox_california_schools",
            "sqlwarden",
            "on",
            "pg_catalog, california_schools",
            5000,
            500,
            16384,
        ),
    ],
)
async def test_incomplete_identity_metadata_is_configuration_failure(identity):
    pool = FakePool()
    pool.conn.identity = identity
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "configuration_error" and not pool.leased


@pytest.mark.parametrize(
    "changes, expected_fetches, reason",
    [
        ({"max_rows": 2}, 3, "row_limit"),
        ({"max_result_bytes": 30, "max_cell_bytes": 16}, 2, "result_limit"),
        ({"max_result_bytes": 26, "max_cell_bytes": 16}, 0, "result_limit"),
    ],
)
async def test_overflow_stops_fetching_at_the_first_proven_failure(
    changes, expected_fetches, reason
):
    pool = FakePool()
    pool.conn.rows = [(1,), (2,), (3,), (4,)]
    result = await QueryExecutor(pool, QueryLimits(**changes)).execute("SELECT 1")
    assert (result.status, result.reason, result.columns, result.rows) == (
        "overflow",
        reason,
        (),
        (),
    )
    assert sum(call[0] == "fetch" for call in pool.conn.calls) == expected_fetches
    assert not pool.leased


async def test_cell_overflow_does_not_fetch_another_row():
    pool = FakePool()
    pool.conn.rows = [("private-canary",), ("unused",)]
    result = await QueryExecutor(pool, QueryLimits(max_cell_bytes=4)).execute("SELECT 1")
    assert result.reason == "cell_limit" and result.rows == ()
    assert sum(call[0] == "fetch" for call in pool.conn.calls) == 1
    assert "private-canary" not in repr(result) and not pool.leased


async def test_guard_exception_is_sanitized_before_acquisition(monkeypatch, caplog, capsys):
    import sqlwarden.executor as module

    def broken_guard(*args):
        raise ValueError("private-canary")

    monkeypatch.setattr(module, "guard_sql", broken_guard)
    pool = FakePool()
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "internal_error" and pool.acquires == 0
    assert "private-canary" not in repr(result) + caplog.text + str(capsys.readouterr())


async def test_already_detached_proxy_does_not_replace_the_error(monkeypatch):
    pool = FakePool()
    pool.conn.error = asyncpg.PostgresSyntaxError("private-canary")

    def detached():
        pool.leased = False
        raise asyncpg.InterfaceError("private-canary")

    monkeypatch.setattr(pool.conn, "terminate", detached)
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "syntax_error" and not pool.leased


def install_pool(monkeypatch, pool):
    async def create_pool(**options):
        pool.options = options
        return pool

    monkeypatch.setattr(asyncpg, "create_pool", create_pool)


async def test_opener_fixes_identity_bounds_and_closes_its_pool(monkeypatch):
    from sqlwarden.executor import open_california_executor

    pool = FakePool()
    install_pool(monkeypatch, pool)
    async with open_california_executor("credential-canary") as executor:
        assert (await executor.execute("SELECT 1")).status == "ok"
    assert pool.options == {
        "host": "127.0.0.1",
        "port": 55432,
        "database": "sqlwarden",
        "user": "warden_sandbox_california_schools",
        "password": "credential-canary",
        "ssl": False,
        "min_size": 0,
        "max_size": 1,
        "timeout": 5.0,
        "command_timeout": 15.0,
    }
    assert pool.closes == 1 and pool.terminated and not pool.leased


def test_dataset_password_key_uses_only_fixed_database_ids():
    assert dataset_password_key("california_schools") == "WARDEN_CALIFORNIA_PASSWORD"
    assert dataset_password_key("financial") == "WARDEN_DATASET_FINANCIAL_PASSWORD"
    with pytest.raises(ValueError, match="^Unknown dataset id$"):
        dataset_password_key("financial;SET ROLE warden_owner")


async def test_dataset_opener_fixes_role_from_dataset_id(monkeypatch):
    from sqlwarden.executor import open_dataset_executor

    pool = FakePool()
    pool.conn.identity = (
        "warden_sandbox_financial",
        "sqlwarden",
        "on",
        "pg_catalog, financial",
        5000,
        500,
        16384,
        65536,
    )
    install_pool(monkeypatch, pool)
    async with open_dataset_executor("financial", "credential-canary") as executor:
        assert (await executor.execute("SELECT count(*) FROM account")).status == "ok"
    assert pool.options["user"] == "warden_sandbox_financial"
    assert pool.options["password"] == "credential-canary"
    assert pool.closes == 1 and pool.terminated and not pool.leased


async def test_unknown_dataset_never_reaches_pool_creation(monkeypatch):
    from sqlwarden.executor import open_dataset_executor

    async def forbidden_creation(**options):
        pytest.fail("Unknown dataset reached pool creation", pytrace=False)

    monkeypatch.setattr(asyncpg, "create_pool", forbidden_creation)
    with pytest.raises(ValueError, match="^Unknown dataset id$"):
        async with open_dataset_executor("app", "credential-canary"):
            pytest.fail("Unknown dataset opened the executor", pytrace=False)


@pytest.mark.parametrize("credential", [None, 42, "", "\x00"])
async def test_missing_or_invalid_credentials_never_create_a_pool(monkeypatch, credential):
    from sqlwarden.executor import open_california_executor

    async def forbidden_creation(**options):
        pytest.fail("Invalid credentials reached pool creation", pytrace=False)

    monkeypatch.setattr(asyncpg, "create_pool", forbidden_creation)
    with pytest.raises(ValueError, match="^Invalid restricted-reader credential$"):
        async with open_california_executor(credential):
            pytest.fail("Invalid credential opened the executor", pytrace=False)


@pytest.mark.parametrize("phase", ["create", "close", "close_timeout"])
async def test_lifecycle_errors_are_bounded_and_chain_suppressed(
    monkeypatch, phase, caplog, capsys
):
    import traceback

    from sqlwarden.executor import ExecutorLifecycleError, open_california_executor

    pool = FakePool()
    install_pool(monkeypatch, pool)
    if phase == "create":

        async def broken_creation(**options):
            raise OSError("private-canary")

        monkeypatch.setattr(asyncpg, "create_pool", broken_creation)
    else:
        pool.close_error = ValueError("private-canary")
        pool.block_close = phase == "close_timeout"
    with pytest.raises(ExecutorLifecycleError, match="^connection_error$") as error:
        async with asyncio.timeout(1):
            async with open_california_executor(
                "credential-canary", QueryLimits(pool_timeout_ms=20)
            ):
                pass
    assert error.value.__suppress_context__
    rendered = "".join(traceback.format_exception(error.value))
    assert "private-canary" not in rendered + caplog.text + str(capsys.readouterr())
    if phase != "create":
        assert pool.terminated


async def test_caller_body_error_preserves_itself_and_terminates_without_close(monkeypatch):
    from sqlwarden.executor import open_california_executor

    pool = FakePool()
    pool.block_close = True
    install_pool(monkeypatch, pool)
    marker = ValueError("caller-owned-error")
    with pytest.raises(ValueError) as error:
        async with open_california_executor("credential-canary"):
            raise marker
    assert error.value is marker
    assert pool.terminated and pool.closes == 0


@pytest.mark.parametrize("phase", ["body", "close"])
async def test_owner_cancellation_propagates_and_terminates_pool(monkeypatch, phase):
    from sqlwarden.executor import open_california_executor

    pool = FakePool()
    pool.block_close = phase == "close"
    install_pool(monkeypatch, pool)
    body_started = asyncio.Event()

    async def owner():
        async with open_california_executor("credential-canary"):
            if phase == "body":
                body_started.set()
                await asyncio.Event().wait()

    task = asyncio.create_task(owner())
    try:
        await asyncio.wait_for((body_started if phase == "body" else pool.close_started).wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 1)
        assert pool.terminated
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_external_cancellation_is_not_a_successful_result():
    pool = FakePool()
    pool.conn.block = "fetch"
    task = asyncio.create_task(QueryExecutor(pool, QueryLimits()).execute("SELECT 1"))
    await asyncio.wait_for(pool.conn.started.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert pool.conn.terminated and not pool.leased

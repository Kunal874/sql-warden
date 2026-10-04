# Bounded SQL Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Preserve native execution in the current checkout; AGENTS.md forbids parallel implementation without Kunal's request. Steps use checkbox syntax for tracking.

**Goal:** Complete G0.7a's next prerequisite: guard SQL internally, inspect its estimated cost and return only complete, bounded results from the existing restricted California reader.

**Architecture:** One long-lived, one-connection asyncpg pool belongs to the trusted caller, not to individual requests. A small executor consumes the existing guard and QueryLimits, uses one explicit read-only transaction for planning/execution, and fetches one row at a time. Pure result/plan checks are independently testable; failure never returns a successful-looking prefix.

**Tech Stack:** Python 3.12, installed/locked asyncpg 0.31.0 and SQLGlot 30.21.0, pytest/pytest-asyncio, and standard-library asyncio, dataclasses, datetime, decimal, json and math. No dependency addition or upgrade.

**Spec:** [BUILD_SPEC](../../BUILD_SPEC.md), sections 2, 4–6 and 11; [AGENTS](../../../AGENTS.md); [DECISIONS](../../DECISIONS.md), D-003/D-015–D-018. The already approved specification supplies the design; this plan does not change the benchmark or authorize a model-connected SQL run.

**Status:** Kunal's "continue with progress" after the written handoff approves native execution on 2026-10-04. Tasks 1–2 are complete: 88 result/config and 94 executor scoped passes; the latest full suite has 511 passes with the 123 existing PostgreSQL checks. Task 3's actual executor checks and final review remain. Implementation baseline: clean feat/foundation at df07434, 407 passes including 123 actual PostgreSQL checks. Comparator and CLI remain separate.

## Global Constraints

- Workspace: `D:/PROJECTS/SQLWARDEN`. Use the current workspace; do not create a nested `sqlwarden` directory.
- Python 3.12 with uv; PostgreSQL 16 in Docker; native Ollama; React 18/TypeScript later.
- Keep inference local until a hosted configuration is explicitly approved.
- No remote addition or push before the G7 release approval.
- Kunal is the sole author and committer of new project commits.
- Never commit secrets, data downloads, model weights, caches, raw run output or unrelated user changes.
- Real PostgreSQL integration tests must run before database security claims.
- Use tests first for security boundaries, result comparison, voting, budgets and state transitions.
- Preserve the existing named volume, credentials, imported rows and PostgreSQL 17 service.
- No generated SQL executes before the minimum guard, bounded executor and comparator pass.
- After each completed group/subtask, update explaination of project/PROJECT_EXPLAINED.md in simple English.

## Scope, choices and residual limits

This is the executor only. No LLM/SDK client, schema retrieval, EX comparator,
repair/voting, CLI, API, extra dataset, tenant RLS or benchmark run is included.
Keep the guard unchanged and call it inside execute; accepting a GuardDecision
from a caller would not establish authority. Only handwritten test SQL runs here.

Prefer the single existing dataset/pool to a new all-dataset registry. A fresh
connection for every query avoids retained state but does not exercise the required
pool-recovery contract. Later runtime code must own/reuse one executor, not create
a pool per request. The existing California role's cluster-wide connection limit
of two remains unchanged; this executor's pool uses at most one connection.

The fixed local mapping is california_schools -> 127.0.0.1:55432/sqlwarden ->
warden_sandbox_california_schools -> CALIFORNIA_POLICY. SQL cannot choose host,
database, role, policy, password or limits. The opener receives the reader password
from trusted code; it never reads environment files, bootstrap credentials or a
DSN. Tests alone load the existing private test environments. Runtime credential
configuration belongs to the subsequent CLI task, not to this preparation.

Retain current QueryLimits defaults: 1000 rows, 2 MiB result data, 64 KiB per cell,
5s statement, 500ms lock, 5s acquisition and 15s total. Propose two additional
positive-integer server-owned limits: max_estimated_cost=100000 and
max_estimated_rows=100000. These are conservative starting knobs for review,
not calibrated thresholds, currency, benchmark tuning or proof against expensive
queries. C4/development calibration remains a separate recorded task.

Result bytes mean the compact UTF-8 JSON data envelope {columns, rows}, including
names, brackets, separators and JSON escaping. Decimal/date/nonfinite-float values
use text only for sizing; returned cells keep their original types. This is not
EX/voting canonicalization, a wire-protocol limit or a Python-heap guarantee.
Fixed status/reason framing is outside this data envelope and must be bounded by
its later caller. Result order, duplicate rows and duplicate column names remain.

Fetch one row, not the driver's default iterator prefetch. A single row/cell and
the EXPLAIN value have already been received/decoded before their byte checks;
the checks do not prevent that transient allocation. MAX_PLAN_BYTES is 64 KiB.
The total deadline includes acquisition, setup, planning, fetching, rollback and
release. Synchronous guard/JSON work is not preemptible process isolation. Keep
the existing database container limits and document these residual risks.

An error/cancellation terminates the leased connection instead of awaiting an
unbounded rollback/reset on it. PostgreSQL aborts that connection's transaction;
the pool replaces it on a later acquire. Normal success and budget blocks explicitly
roll back before bounded release. External CancelledError propagates; it is not a
successful QueryResult. Pool lifecycle close has its own finite acquisition-sized
bound and always terminates remaining connections.

Do not install query/log listeners or print SQL, plans, rows, credentials or driver
exception text. Stable application errors do not prove PostgreSQL administrator
logs are redacted: server logging is a separate configuration/residual limitation.

## Files and interfaces

- Modify `src/sqlwarden/config.py`: add only the two validated estimate limits.
- Create `src/sqlwarden/executor.py`: result/plan budgets, fixed-reader opener and executor.
- Modify `tests/test_limits.py`; create `tests/test_executor.py`: deterministic boundaries/driver contract tests.
- Create `tests/test_executor_postgres.py`: gated real restricted-reader execution/recovery controls.
- Update PROGRESS, DECISIONS, this plan and the learning notebook after actual tasks.
- Do not change pyproject.toml, uv.lock, guard.py, database grants, data or historical inputs.

Consumed: `guard_sql(sql: str, policy: DatasetPolicy) -> GuardDecision`,
`CALIFORNIA_POLICY`, and `QueryLimits` from **config.py**, not a new limits module.
Produced: immutable `QueryResult`; `QueryExecutor.execute(sql: str) -> QueryResult`;
`open_california_executor(password: str, limits: QueryLimits=QueryLimits())`, an
async context manager yielding one QueryExecutor; ExecutorLifecycleError for a
fixed connection_error on pool creation/close failure. Only status=ok is complete.
Non-ok results contain no columns/rows and result_bytes=0. None/empty results are
valid successful answers when execution itself completes.

## Source checks (2026-10-04)

- [PostgreSQL 16 EXPLAIN](https://www.postgresql.org/docs/16/sql-explain.html):
  use the literal prefix EXPLAIN (FORMAT JSON), never ANALYZE. Planning can still
  evaluate reviewed builtin constants; guard before planning and retain deadlines.
- [PostgreSQL 16 timeouts](https://www.postgresql.org/docs/16/runtime-config-client.html):
  statement and lock limits serve different purposes; use transaction-local values.
- [asyncpg API](https://magicstack.github.io/asyncpg/current/api/index.html):
  prepared attributes preserve positions; explicit cursor fetching avoids iterator
  prefetch; acquire/release/close need finite bounds.
- Installed locked 0.31.0 source was also inspected locally: cursor.py fetch(1),
  prepared_stmt.py get_attributes/cursor, pool.py acquire/release/holder cleanup,
  connection.py terminate/cleanup. terminate releases a pooled holder synchronously;
  release is shielded and close can wait. Do not use these private internals in runtime
  code; prove the public-method behavior with real recovery tests.
- GitHub tag/API reads were unavailable through browsing; no unverified upstream
  commit pin or dependency upgrade is claimed. uv.lock pins the installed artifact.

## Review Focus

1. Exactly-cap results, cap-plus-one, empty/NULL answers and duplicate rows/names: only a proven complete result is returned; no prefix can vote or score.
2. Multibyte/escaped cells, metadata and unexpected value types: measure the defined UTF-8 envelope and fail without retaining private data.
3. Guard rejection, caller-forged decisions, wrong identity or invalid/over-budget plans: no candidate executes and EXPLAIN never contains ANALYZE.
4. Acquisition, setup, planning, fetch, rollback/release and caller cancellation: deadlines stay finite, a bad connection is discarded and the pool recovers.
5. Driver error text, invalid credentials, malformed plan JSON and changed defaults: stable categories and explicit readonly/settings hold without secret/SQL logging.

---

### Task 1: Complete-result and cost-budget contracts

**Files:** Modify config.py/test_limits.py; create executor.py/test_executor.py;
update progress/decisions/notebook.

**Interfaces:** Consume QueryLimits. Produce `QueryResult`, private `_ResultBuffer`
and `_check_plan`; Task 2 consumes their exact names/return categories below.

- [x] **Step 1: Write pure boundary tests first.** Replace only the existing
invalid-value test's parameterization/function in test_limits.py with this
extended control; retain its other tests and imports:

```python
@pytest.mark.parametrize("field", [
    "max_rows", "max_result_bytes", "max_cell_bytes", "statement_timeout_ms",
    "lock_timeout_ms", "pool_timeout_ms", "total_timeout_ms",
    "max_estimated_cost", "max_estimated_rows",
])
@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1000"])
def test_rejects_limits_that_remove_or_misrepresent_a_bound(field, value):
    with pytest.raises(ValueError, match=field):
        QueryLimits(**{field: value})
```

Add these tests to test_executor.py (existing pytest configuration already
supports async tests):

```python
from datetime import date
from decimal import Decimal

import pytest

from sqlwarden.config import QueryLimits
from sqlwarden.executor import QueryResult, _ResultBuffer, _check_plan


def limits(**changes):
    return QueryLimits(**({"max_rows": 2, "max_result_bytes": 128,
                          "max_cell_bytes": 64} | changes))


def test_exact_row_cap_is_complete_but_next_row_discards_prefix():
    buf = _ResultBuffer(("n",), limits())
    assert buf.append((1,)) is None
    assert buf.append((1,)) is None
    result = buf.finish()
    assert (result.status, result.rows, result.result_bytes) == ("ok", ((1,), (1,)), 34)
    assert buf.append((2,)) == "row_limit"
    result = buf.finish()
    assert (result.status, result.columns, result.rows, result.result_bytes) == (
        "overflow", (), (), 0)


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
    [(100000, 100000, None), (100000.01, 1, "cost_limit"),
     (1, 100001, "plan_row_limit"), (-1, 1, "plan_error"),
     (True, 1, "plan_error"), (1, True, "plan_error")],
)
def test_plan_estimates_have_exact_finite_boundaries(cost, rows, reason):
    import json
    plan = json.dumps([{"Plan": {"Total Cost": cost, "Plan Rows": rows}}])
    assert _check_plan(plan, QueryLimits()) == reason


@pytest.mark.parametrize("plan", [None, "private-canary", "[]", "[{},{}]",
                                  '[{"Plan":{"Total Cost":NaN,"Plan Rows":1}}]'])
def test_malformed_plans_fail_without_echoing_their_contents(plan):
    assert _check_plan(plan, QueryLimits()) == "plan_error"
```

- [x] **Step 2: Observe RED.**

```powershell
uv run pytest tests/test_executor.py tests/test_limits.py -q
```

Expected: missing sqlwarden.executor first; after its interface exists, assertions
identify absent estimate fields/budget behavior. Do not run the proposed code blocks
before these tests. No database is needed by this task's new checks.

- [x] **Step 3: Add the two config fields and pure implementation.** Add only
these two field declarations inside the existing QueryLimits dataclass in
config.py, indented with its other fields; do not replace the class:

```python
max_estimated_cost: int = 100000
max_estimated_rows: int = 100000
```

Its existing fields loop already validates positive non-boolean integers. Put the
following in executor.py; it is the byte contract, not a comparator/serializer API:

```python
import json
import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlwarden.config import QueryLimits

Cell = str | int | float | bool | Decimal | date | None
Row = tuple[Cell, ...]
MAX_PLAN_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class QueryResult:
    status: Literal["ok", "blocked", "failed", "overflow"]
    reason: str
    columns: tuple[str, ...] = ()
    rows: tuple[Row, ...] = ()
    result_bytes: int = 0


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _budget_cell(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else str(value)
    if type(value) in (Decimal, date):
        return str(value)
    raise ValueError("Unsupported result type")


class _ResultBuffer:
    def __init__(self, columns: tuple[str, ...], limits: QueryLimits):
        self._limits = limits
        self._columns = columns
        self._rows = []
        self._reason = None
        self._bytes = 0
        try:
            if not all(type(name) is str for name in columns):
                raise ValueError("Unsupported column metadata")
            self._bytes = len(_json_bytes({"columns": list(columns), "rows": []}))
        except (ValueError, UnicodeError):
            self._fail("unsupported_result")
        if self._bytes > limits.max_result_bytes:
            self._fail("result_limit")

    def _fail(self, reason):
        self._reason = reason
        self._columns = ()
        self._rows.clear()
        self._bytes = 0
        return reason

    def append(self, row: Row) -> str | None:
        if self._reason:
            return self._reason
        if len(row) != len(self._columns):
            return self._fail("unsupported_result")
        if len(self._rows) >= self._limits.max_rows:
            return self._fail("row_limit")
        try:
            cells = [_json_bytes(_budget_cell(value)) for value in row]
        except (ValueError, UnicodeError):
            return self._fail("unsupported_result")
        if any(len(cell) > self._limits.max_cell_bytes for cell in cells):
            return self._fail("cell_limit")
        added = 2 + max(0, len(cells) - 1) + sum(map(len, cells)) + bool(self._rows)
        if self._bytes + added > self._limits.max_result_bytes:
            return self._fail("result_limit")
        self._rows.append(row)
        self._bytes += added
        return None

    def finish(self) -> QueryResult:
        if self._reason:
            status = "overflow" if self._reason.endswith("_limit") else "failed"
            return QueryResult(status, self._reason)
        return QueryResult("ok", "ok", self._columns, tuple(self._rows), self._bytes)


def _check_plan(text: str, limits: QueryLimits) -> str | None:
    if not isinstance(text, str):
        return "plan_error"
    try:
        if len(text.encode("utf-8")) > MAX_PLAN_BYTES:
            return "plan_limit"
        data = json.loads(text)
        if type(data) is not list or len(data) != 1:
            return "plan_error"
        plan = data[0]["Plan"]
        cost, rows = plan["Total Cost"], plan["Plan Rows"]
        if type(cost) not in (int, float) or cost < 0 or not math.isfinite(cost):
            return "plan_error"
        if type(rows) is not int or rows < 0:
            return "plan_error"
    except (ValueError, UnicodeError, KeyError, TypeError, RecursionError, OverflowError):
        return "plan_error"
    if cost > limits.max_estimated_cost:
        return "cost_limit"
    if rows > limits.max_estimated_rows:
        return "plan_row_limit"
    return None
```

- [x] **Step 4: Pin remaining budget edges before claiming GREEN.** Add these
literal controls; do not derive expected sizes through production helpers:

```python
def test_metadata_alone_can_exceed_the_result_cap():
    result = _ResultBuffer(("n",), limits(max_result_bytes=26, max_cell_bytes=16)).finish()
    assert (result.status, result.reason, result.rows) == ("overflow", "result_limit", ())


def test_json_escaping_counts_against_a_cell():
    buf = _ResultBuffer(("n",), limits(max_cell_bytes=3))
    assert buf.append(("\n",)) == "cell_limit"  # encoded JSON cell is four bytes


def test_nonfinite_cells_keep_the_original_float():
    import math
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
    from dataclasses import FrozenInstanceError
    result = QueryResult("ok", "ok")
    with pytest.raises(FrozenInstanceError):
        result.status = "failed"


@pytest.mark.parametrize("columns", [("\ud800",), (1,)])
def test_invalid_metadata_is_a_sanitized_failure(columns):
    result = _ResultBuffer(columns, limits()).finish()
    assert (result.status, result.reason, result.columns, result.rows) == (
        "failed", "unsupported_result", (), ())


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), Decimal("Infinity")])
def test_nonfinite_numbers_keep_their_original_types(value):
    buf = _ResultBuffer(("n",), limits())
    assert buf.append((value,)) is None
    result = buf.finish()
    assert result.status == "ok" and result.rows == ((value,),)
    assert type(result.rows[0][0]) is type(value)


@pytest.mark.parametrize("text", [
    '[{"Plan":{"Plan Rows":1}}]',
    '[{"Plan":{"Total Cost":1}}]',
    '[{"Plan":{"Total Cost":Infinity,"Plan Rows":1}}]',
    "[" * 2000 + "0" + "]" * 2000,
    "\ud800",
])
def test_missing_keys_and_unrepresentable_plans_fail_closed(text):
    assert _check_plan(text, QueryLimits()) == "plan_error"


def test_estimate_defaults_are_explicit_not_calibrated():
    default = QueryLimits()
    assert (default.max_estimated_cost, default.max_estimated_rows) == (100000, 100000)
```

Run each added check before any correction it needs; observe RED if behavior is
missing. Existing implementation controls may already pass and characterize the
contract. The controls above pin immutability, invalid metadata, nonfinite values,
missing plan keys and deep malformed JSON without exposing raw exception messages.

```powershell
uv run pytest tests/test_executor.py tests/test_limits.py -q
uv run --env-file .env.setup --env-file .env.california pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Expected: all scoped/full tests pass; real baseline checks run rather than skip;
lint/format/whitespace pass. Format only the changed Python files if needed.

- [x] **Step 5: Document and commit this independent deliverable.** Record actual
counts and byte semantics; say no executor/AI SQL has run. Update the notebook with
complete result, overflow, cap-plus-one, UTF-8 and cost-estimate words. Inspect all
staged changes and the exact Conventional message; verify Kunal author/committer/body.

```powershell
git add src/sqlwarden/config.py src/sqlwarden/executor.py tests/test_limits.py tests/test_executor.py docs/PROGRESS.md docs/DECISIONS.md docs/superpowers/plans/2026-10-04-bounded-sql-executor.md "explaination of project/PROJECT_EXPLAINED.md"
git diff --cached
git diff --cached --check
git commit -m "feat(executor): define complete result and plan budgets"
git log -1 --format=fuller
git log -1 --format=%B
```

---

### Task 2: Internally guarded restricted-pool execution

**Files:** Extend executor.py/test_executor.py; update progress/decisions/notebook.

**Interfaces:** Consume `QueryLimits`, `guard_sql`, `CALIFORNIA_POLICY`,
`QueryResult`, `_ResultBuffer`, `_check_plan`. Produce `QueryExecutor.execute(sql)`
and `open_california_executor(password, limits)` with the signatures in the header.
The constructor's pool is trusted internal/test plumbing, not an API request input.

- [x] **Step 1: Write the driver-contract tests before the executor.** Add a
test-only fake driver; never put injection/debug methods in production. Use actual
asyncpg Attribute/Type objects for prepared metadata, and events for delayed awaits.
The fake must implement this full consumed surface, with each phase recorded:

```python
import asyncio

import asyncpg

from sqlwarden.executor import QueryExecutor


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
            for name in self.conn.columns)

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
        self.identity = ("warden_sandbox_california_schools", "sqlwarden", "on",
                         "pg_catalog, california_schools", 5000, 500, 16384, 65536)
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


@pytest.mark.parametrize("sql", ["DELETE FROM schools", "SELECT pg_sleep(1)",
                                 "SELECT 1; SELECT 2", "SELECT * FROM app.runs"])
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
    assert names == ["begin", "settings", "identity", "plan", "prepare", "cursor",
                     "fetch", "fetch", "rollback"]
    assert not pool.leased


async def test_wrong_identity_never_plans_or_executes():
    pool = FakePool()
    pool.conn.identity = ("warden_owner",) + pool.conn.identity[1:]
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "configuration_error" and result.rows == ()
    assert not any(call[0] in {"plan", "prepare", "cursor"} for call in pool.conn.calls)


@pytest.mark.parametrize("phase", ["begin", "settings", "identity", "plan", "prepare",
                                   "cursor", "fetch", "rollback", "release"])
async def test_total_deadline_discards_connection_in_every_phase(phase):
    pool = FakePool()
    pool.conn.block = phase
    pool.block_release = phase == "release"
    small = QueryLimits(statement_timeout_ms=20, lock_timeout_ms=5,
                        pool_timeout_ms=20, total_timeout_ms=40)
    # This fake reports the small settings too; it models server-observed values.
    pool.conn.identity = pool.conn.identity[:4] + (20, 5, 16384, 65536)
    result = await asyncio.wait_for(QueryExecutor(pool, small).execute("SELECT 1"), 1)
    assert result.reason == "timeout" and result.rows == ()
    assert pool.conn.terminated and not pool.leased


async def test_external_cancellation_is_not_a_successful_result():
    pool = FakePool()
    pool.conn.block = "fetch"
    task = asyncio.create_task(QueryExecutor(pool, QueryLimits()).execute("SELECT 1"))
    await asyncio.wait_for(pool.conn.started.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert pool.conn.terminated and not pool.leased
```

- [x] **Step 2: Observe RED.**

```powershell
uv run pytest tests/test_executor.py -q
```

Expected: QueryExecutor missing first, then meaningful contract failures. The fake
does not prove PostgreSQL enforcement; Task 3 is mandatory before that claim.

- [x] **Step 3: Extend executor.py with the bounded workflow.** Keep Task 1's
contracts. Add the imports/context manager and this small runtime surface:

```python
import asyncio
from contextlib import asynccontextmanager

import asyncpg

from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql

_SETTINGS_SQL = (
    "SELECT pg_catalog.set_config('statement_timeout',$1,true), "
    "pg_catalog.set_config('lock_timeout',$2,true), "
    "pg_catalog.set_config('search_path',$3,true), "
    "pg_catalog.set_config('work_mem','16MB',true)"
)
_IDENTITY_SQL = (
    "SELECT current_user, current_database(), "
    "pg_catalog.current_setting('transaction_read_only'), "
    "pg_catalog.current_setting('search_path'), "
    "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='statement_timeout'), "
    "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='lock_timeout'), "
    "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='work_mem'), "
    "(SELECT setting::int FROM pg_catalog.pg_settings WHERE name='temp_file_limit')"
)


def _discard(conn):
    if conn is not None:
        try:
            conn.terminate()
        except asyncpg.InterfaceError:
            pass  # the public proxy was already released/detached


def _remaining(deadline):
    seconds = deadline - asyncio.get_running_loop().time()
    if seconds <= 0:
        raise TimeoutError
    return seconds


class QueryExecutor:
    def __init__(self, pool, limits: QueryLimits):
        self._pool = pool
        self._limits = limits

    async def execute(self, sql: str) -> QueryResult:
        conn = None
        deadline = asyncio.get_running_loop().time() + self._limits.total_timeout_ms / 1000
        try:
            decision = guard_sql(sql, CALIFORNIA_POLICY)
            if not decision.accepted:
                return QueryResult("blocked", decision.reason)
            async with asyncio.timeout_at(deadline):
                conn = await self._pool.acquire(
                    timeout=min(self._limits.pool_timeout_ms / 1000, _remaining(deadline)))
                result = await self._run(conn, decision.sql, deadline)
                await self._pool.release(conn, timeout=_remaining(deadline))
                conn = None
                return result
        except asyncio.CancelledError:
            raise
        except (TimeoutError, asyncpg.QueryCanceledError, asyncpg.LockNotAvailableError):
            return QueryResult("failed", "timeout")
        except asyncpg.PostgresSyntaxError:
            return QueryResult("failed", "syntax_error")
        except (asyncpg.UndefinedTableError, asyncpg.UndefinedColumnError,
                asyncpg.UndefinedFunctionError, asyncpg.InvalidSchemaNameError):
            return QueryResult("failed", "undefined_object")
        except (asyncpg.InsufficientPrivilegeError, asyncpg.ReadOnlySQLTransactionError):
            return QueryResult("failed", "permission_error")
        except (OSError, asyncpg.PostgresConnectionError,
                asyncpg.InvalidAuthorizationSpecificationError):
            return QueryResult("failed", "connection_error")
        except asyncpg.PostgresError:
            return QueryResult("failed", "database_error")
        except Exception:
            # One top-level boundary: no untrusted driver/parser detail escapes.
            return QueryResult("failed", "internal_error")
        finally:
            _discard(conn)

    async def _run(self, conn, sql, deadline):
        tx = conn.transaction(readonly=True)
        await tx.start()
        await conn.execute(_SETTINGS_SQL,
                           f"{self._limits.statement_timeout_ms}ms",
                           f"{self._limits.lock_timeout_ms}ms",
                           "pg_catalog, california_schools", timeout=_remaining(deadline))
        identity = await conn.fetchrow(_IDENTITY_SQL, timeout=_remaining(deadline))
        expected = ("warden_sandbox_california_schools", "sqlwarden", "on",
                    "pg_catalog, california_schools", self._limits.statement_timeout_ms,
                    self._limits.lock_timeout_ms, 16384)
        if (identity is None or len(identity) != 8 or tuple(identity[:7]) != expected
                or type(identity[7]) is not int or not 0 < identity[7] <= 65536):
            result = QueryResult("failed", "configuration_error")
        else:
            plan = await conn.fetchval("EXPLAIN (FORMAT JSON) " + sql,
                                      timeout=_remaining(deadline))
            reason = _check_plan(plan, self._limits)
            if reason:
                status = "blocked" if reason.endswith("_limit") else "failed"
                result = QueryResult(status, reason)
            else:
                statement = await conn.prepare(sql, timeout=_remaining(deadline))
                buf = _ResultBuffer(tuple(attr.name for attr in statement.get_attributes()),
                                    self._limits)
                result = buf.finish()
                if result.status == "ok":
                    cursor = await statement.cursor(timeout=_remaining(deadline))
                    while True:
                        records = await cursor.fetch(1, timeout=_remaining(deadline))
                        if not records or buf.append(tuple(records[0])):
                            break
                    result = buf.finish()
        await tx.rollback()
        return result


class ExecutorLifecycleError(RuntimeError):
    """A fixed lifecycle category, never a library error message."""


@asynccontextmanager
async def open_california_executor(password: str, limits: QueryLimits = QueryLimits()):
    if type(password) is not str or not password or "\x00" in password:
        raise ValueError("Invalid restricted-reader credential") from None
    try:
        async with asyncio.timeout(limits.pool_timeout_ms / 1000):
            pool = await asyncpg.create_pool(
                host="127.0.0.1", port=55432, database="sqlwarden",
                user="warden_sandbox_california_schools", password=password, ssl=False,
                min_size=0, max_size=1, timeout=limits.pool_timeout_ms / 1000,
                command_timeout=limits.total_timeout_ms / 1000)
    except asyncio.CancelledError:
        raise
    except Exception:
        raise ExecutorLifecycleError("connection_error") from None
    try:
        yield QueryExecutor(pool, limits)
    except BaseException:
        # Preserve the caller's exception/cancellation; do not wait for close here.
        pool.terminate()
        raise
    else:
        try:
            async with asyncio.timeout(limits.pool_timeout_ms / 1000):
                await pool.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            raise ExecutorLifecycleError("connection_error") from None
        finally:
            pool.terminate()
```

The catch-all is only the executor's outer error boundary, never a success fallback;
BaseException/cancellation is not swallowed. _discard terminates an error lease
synchronously; do not inspect asyncpg private fields or await a new cleanup query.
Pool creation/close errors expose only ExecutorLifecycleError("connection_error")
with suppressed chaining. Caller body exceptions/cancellation retain their original
identity and terminate the pool without an awaited close. No runtime secrets loader
is added; these boundaries do not redact a caller's own unrelated exception.

- [x] **Step 4: Add failure/cleanup/opener controls before correcting uncovered paths.**
Extend the fake tests using literal outcomes:

```python
@pytest.mark.parametrize(
    "error, reason",
    [(asyncpg.PostgresSyntaxError("private-canary"), "syntax_error"),
     (asyncpg.UndefinedColumnError("private-canary"), "undefined_object"),
     (asyncpg.InsufficientPrivilegeError("private-canary"), "permission_error"),
     (asyncpg.InvalidPasswordError("private-canary"), "connection_error"),
     (asyncpg.QueryCanceledError("private-canary"), "timeout"),
     (ValueError("private-canary"), "internal_error")],
)
async def test_driver_errors_never_return_or_log_private_details(error, reason, caplog, capsys):
    pool = FakePool()
    pool.conn.error = error
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert (result.status, result.reason, result.rows) == ("failed", reason, ())
    assert pool.conn.terminated and not pool.leased
    assert "private-canary" not in repr(result) + caplog.text + str(capsys.readouterr())


@pytest.mark.parametrize("plan, reason", [("[]", "plan_error"),
    ('[{"Plan":{"Total Cost":100001,"Plan Rows":1}}]', "cost_limit"),
    ('[{"Plan":{"Total Cost":1,"Plan Rows":100001}}]', "plan_row_limit")])
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
        GuardDecision(True, "accepted", "DELETE FROM schools"))
    assert result.reason == "input_invalid" and pool.acquires == 0
```

Add these controls in the same test module. They pin fixed routing, pre-pool
credential rejection, safe errors/settings, first-failure fetching, finite close
and cancellation. A synthetic password can be asserted in fake options; never
assert/print the real environment's credential. This is test-only driver plumbing,
not a runtime injection API.

```python
@pytest.mark.parametrize("index, value", [
    (1, "other"), (2, "off"), (3, "public"),
    (4, 4999), (5, 499), (6, 32768), (7, -1), (7, 65537),
])
async def test_changed_server_settings_fail_before_candidate_planning(index, value):
    pool = FakePool()
    identity = list(pool.conn.identity)
    identity[index] = value
    pool.conn.identity = tuple(identity)
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "configuration_error" and result.rows == ()
    assert not any(call[0] in {"plan", "prepare"} for call in pool.conn.calls)
    assert not pool.leased


@pytest.mark.parametrize("identity", [
    None, (), ("wrong",),
    ("warden_sandbox_california_schools", "sqlwarden", "on",
     "pg_catalog, california_schools", 5000, 500, 16384),
])
async def test_incomplete_identity_metadata_is_configuration_failure(identity):
    pool = FakePool()
    pool.conn.identity = identity
    result = await QueryExecutor(pool, QueryLimits()).execute("SELECT 1")
    assert result.reason == "configuration_error" and not pool.leased


@pytest.mark.parametrize("changes, expected_fetches, reason", [
    ({"max_rows": 2}, 3, "row_limit"),
    ({"max_result_bytes": 30, "max_cell_bytes": 16}, 2, "result_limit"),
    ({"max_result_bytes": 26, "max_cell_bytes": 16}, 0, "result_limit"),
])
async def test_overflow_stops_fetching_at_the_first_proven_failure(changes, expected_fetches, reason):
    pool = FakePool()
    pool.conn.rows = [(1,), (2,), (3,), (4,)]
    result = await QueryExecutor(pool, QueryLimits(**changes)).execute("SELECT 1")
    assert (result.status, result.reason, result.columns, result.rows) == (
        "overflow", reason, (), ())
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
        "host": "127.0.0.1", "port": 55432, "database": "sqlwarden",
        "user": "warden_sandbox_california_schools", "password": "credential-canary",
        "ssl": False, "min_size": 0, "max_size": 1, "timeout": 5.0,
        "command_timeout": 15.0,
    }
    assert pool.closes == 1 and pool.terminated and not pool.leased


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
async def test_lifecycle_errors_are_bounded_and_chain_suppressed(monkeypatch, phase, caplog, capsys):
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
            async with open_california_executor("credential-canary", QueryLimits(pool_timeout_ms=20)):
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
        await asyncio.wait_for(
            (body_started if phase == "body" else pool.close_started).wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 1)
        assert pool.terminated
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
```

```powershell
uv run pytest tests/test_executor.py -q
uv run --env-file .env.setup --env-file .env.california pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Expected: all deterministic/scoped/full tests pass without leaked synthetic canaries;
existing real checks run. Newly constructed fake settings must match their configured
limits, not hard-coded defaults. This step does not establish real executor recovery.

- [x] **Step 5: Document and commit the tested workflow.** Record actual counts,
the one top-level sanitized error boundary and explicit residual allocations/logs.
Notebook explains pool, cursor, read-only transaction, cancellation and rollback.
Inspect staged diff/message, then verify both owner identities and clean body:

```powershell
git add src/sqlwarden/executor.py tests/test_executor.py docs/PROGRESS.md docs/DECISIONS.md docs/superpowers/plans/2026-10-04-bounded-sql-executor.md "explaination of project/PROJECT_EXPLAINED.md"
git diff --cached
git diff --cached --check
git commit -m "feat(executor): guard and bound restricted query execution"
git log -1 --format=fuller
git log -1 --format=%B
```

---

### Task 3: Real restricted-reader bounds and pool recovery

**Files:** Create tests/test_executor_postgres.py; correct executor code only if an
observed RED finds a real defect; update progress/decisions/notebook.

**Interfaces:** Consume `open_california_executor`, `QueryResult`, `QueryLimits`.
Reuse the existing `california_connected()` gate from test_bird_load, including its
fixed local target/port and absence-of-credentials skip. No admin/setup identity
enters the executor; test environments are never runtime configuration.

- [ ] **Step 1: Write the real checks first.** Use module integration marker and
this fixture/pattern. Never log passwords/results or execute generated/gold SQL:

```python
import asyncio
import os

import pytest
from test_bird_load import california_connected

from sqlwarden.config import QueryLimits
from sqlwarden.executor import open_california_executor

pytestmark = pytest.mark.integration


async def ready():
    async with california_connected():
        pass  # skip only when the dedicated target/reader is not supplied


def password():
    return os.environ["WARDEN_CALIFORNIA_PASSWORD"]


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
    async with open_california_executor(password(), QueryLimits(pool_timeout_ms=50)) as executor:
        # White-box test only: occupy its sole slot, never expose a lease to a request.
        async with executor._pool.acquire(timeout=1):
            result = await asyncio.wait_for(executor.execute("SELECT 1"), 1)
            assert result.reason == "timeout" and result.rows == ()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"


async def test_real_query_timeout_discards_then_replaces_connection():
    await ready()
    limits = QueryLimits(statement_timeout_ms=50, lock_timeout_ms=10,
                         pool_timeout_ms=500, total_timeout_ms=1000,
                         max_estimated_cost=1000000000, max_estimated_rows=1000000000)
    async with open_california_executor(password(), limits) as executor:
        result = await asyncio.wait_for(executor.execute(
            "SELECT count(*) FROM schools a CROSS JOIN schools b"), 2)
        assert result.reason == "timeout" and result.rows == ()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"
```

- [ ] **Step 2: Pin actual cancellation and state reset.** Add this observer-based
test without production test hooks. Both connections use the same restricted role;
two is its existing hard limit. The observer query is trusted test-only metadata,
not guard-approved runtime SQL. Always cancel/join the task in finally:

```python
async def test_real_external_cancellation_releases_resources_and_pool_recovers():
    await ready()
    limits = QueryLimits(max_estimated_cost=1000000000, max_estimated_rows=1000000000)
    sql = "SELECT count(*) FROM schools a CROSS JOIN schools b"
    async with california_connected() as observer:
        async with open_california_executor(password(), limits) as executor:
            task = asyncio.create_task(executor.execute(sql))
            try:
                pid = None
                async with asyncio.timeout(2):
                    while pid is None:
                        pid = await observer.fetchval(
                            "SELECT pid FROM pg_catalog.pg_stat_activity "
                            "WHERE usename=current_user AND state='active' AND query=$1",
                            sql, timeout=1)
                        if pid is not None:
                            break
                        if task.done():
                            pytest.fail("The bounded control did not reach active execution", pytrace=False)
                        await asyncio.sleep(0.01)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(task, 1)
                async with asyncio.timeout(1):
                    while await observer.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_stat_activity "
                        "WHERE pid=$1)", pid, timeout=1):
                        await asyncio.sleep(0.01)
                assert (await executor.execute("SELECT 1 AS n")).status == "ok"
            finally:
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
```

Add these independent real identity/reset and error controls. Do not disable the
guard or execute forbidden SQL: existing direct boundary tests already supply that
separate permissions evidence. Never print connection values on failure.

```python
async def test_real_transaction_local_overrides_reset_after_release():
    await ready()
    limits = QueryLimits(statement_timeout_ms=123, lock_timeout_ms=10,
                         pool_timeout_ms=500, total_timeout_ms=1000)
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


@pytest.mark.parametrize("sql", [
    "SELECT missing_column FROM schools", "SELECT lower(1)",
])
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
            repr(result) + caplog.text + str(capsys.readouterr()))


@pytest.mark.parametrize("sql", [
    "DELETE FROM schools", "SELECT * FROM app.runs", "SELECT pg_sleep(1)",
])
async def test_real_guard_denial_never_returns_data(sql):
    await ready()
    async with open_california_executor(password()) as executor:
        result = await executor.execute(sql)
        assert result.status == "blocked" and result.columns == () and result.rows == ()
        assert (await executor.execute("SELECT 1 AS n")).status == "ok"
```

- [ ] **Step 3: Observe real results, investigate failures, then correct only proven defects.**

```powershell
uv run --env-file .env.setup --env-file .env.california pytest tests/test_executor_postgres.py -q
```

Expected: every new real check actually runs and passes. A failure is not proof
the plan is correct: use systematic-debugging, inspect the pinned driver/actual
settings and rule on genuine plan defects. Native count cost should exceed 1;
if actual estimates contradict that assumption, use a known deterministic local
control and record its exact observed estimate without executing gold SQL or
loosening the gate. No sleeps/unbounded query may be introduced to force timing.

- [ ] **Step 4: Verify all modes and record truthful evidence.**

```powershell
uv sync --locked
uv run pytest -q
uv run --env-file .env.setup pytest -q
uv run --env-file .env.setup --env-file .env.california pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Expected: no-env/setup modes pass with correctly gated skips; both private files
run every real check without skips; locked versions unchanged; lint/format/diff
pass. Record actual counts/timings/failures, not forecasts. Recheck native source
fingerprints via the existing full suite, original planning inputs, empty remote,
healthy named-volume PostgreSQL and unloaded Ollama. No grants/data/file resets.

- [ ] **Step 5: Document and commit actual completion.** PROGRESS records this
executor increment only, not completed G0.7a/CLI/EX or universal memory isolation.
DECISIONS records provisional cost knobs, envelope/cancellation contracts, real
results and residual allocation/server-log risks. Update the simple-English
notebook after this completed subtask. Inspect every staged file and message:

```powershell
git add src/sqlwarden/executor.py tests/test_executor_postgres.py docs/PROGRESS.md docs/DECISIONS.md docs/superpowers/plans/2026-10-04-bounded-sql-executor.md "explaination of project/PROJECT_EXPLAINED.md"
git diff --cached
git diff --cached --check
git commit -m "test(executor): verify restricted bounds and pool recovery"
git log -1 --format=fuller
git log -1 --format=%B
```

## Final handoff after approved execution

Follow executing-plans: one fresh read-only whole-branch reviewer, re-grade findings,
one RED-to-GREEN fix pass for Critical/Important issues, and ledger every ruling/
declined-to-judge item with its cost. No per-task reviewers, parallel implementation
or second review. Preserve local feat/foundation and ignored scratch without
deletion approval; no merge/push/publication. Persist rulings before handoff.
Next plan: the pinned official EX comparator, then the one-database model/CLI
slice. No generated SQL until those required components also pass.

## Inline plan self-review (2026-10-04)

Coverage: Task 1 owns complete-result and estimate budgets; Task 2 owns the
internal guard, fixed mapping, readonly setup, guarded JSON EXPLAIN, finite
phases and sanitized lifecycle/query errors; Task 3 verifies those contracts
with the actual restricted PostgreSQL login, restored settings and a disappearing
cancelled backend. All five Review Focus items have concrete controls in their
owning tasks. Parser policy and direct privileges reuse the completed guard and
database evidence; they are not replaced by the fake driver.

Fixed inline: incomplete identity metadata now fails as configuration_error;
creation/close failures have a fixed, chain-suppressed category; caller
cancellation is preserved; named extra controls now contain actual test code;
cancellation observes backend removal before occupying the freed connection.

No executor-scope spec gap identified. Comparator semantics, model/CLI wiring,
other datasets/tenant RLS, development calibration, web admission limits and
full attacks/evaluation remain separately named later tasks. Code fences are
syntax-checked only; proposed executor tests have not run and no runtime code
has been installed. This self-review is not implementation approval.

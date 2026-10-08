"""Complete, typed results and finite budgets for restricted SQL execution."""

import asyncio
import json
import math
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

import asyncpg

from sqlwarden.config import QueryLimits
from sqlwarden.guard import CALIFORNIA_POLICY, DATASET_POLICIES, DatasetPolicy, guard_sql

Cell = str | int | float | bool | Decimal | date | None
Row = tuple[Cell, ...]
MAX_PLAN_BYTES = 64 * 1024
_DEFAULT_LIMITS = QueryLimits()


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Only ok contains complete data; failure never returns a usable prefix."""

    status: Literal["ok", "blocked", "failed", "overflow"]
    reason: str
    columns: tuple[str, ...] = ()
    rows: tuple[Row, ...] = ()
    result_bytes: int = 0


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )


def _budget_cell(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else str(value)
    if type(value) in (Decimal, date):
        return str(value)
    raise ValueError("Unsupported result type")


class _ResultBuffer:
    """Private accumulator; the executor must observe EOF before returning ok."""

    def __init__(self, columns: tuple[str, ...], limits: QueryLimits):
        self._limits = limits
        self._columns = columns
        self._rows: list[Row] = []
        self._reason: str | None = None
        self._bytes = 0
        try:
            if not all(type(name) is str for name in columns):
                raise ValueError("Unsupported column metadata")
            self._bytes = len(_json_bytes({"columns": list(columns), "rows": []}))
        except (ValueError, UnicodeError):
            self._fail("unsupported_result")
        if self._bytes > limits.max_result_bytes:
            self._fail("result_limit")

    def _fail(self, reason: str) -> str:
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
        # The public proxy can already have been released/detached.
        with suppress(asyncpg.InterfaceError):
            conn.terminate()


def _remaining(deadline):
    seconds = deadline - asyncio.get_running_loop().time()
    if seconds <= 0:
        raise TimeoutError
    return seconds


class QueryExecutor:
    def __init__(
        self,
        pool,
        limits: QueryLimits,
        policy: DatasetPolicy = CALIFORNIA_POLICY,
    ):
        self._pool = pool
        self._limits = limits
        self._policy = policy
        self._expected_user = "warden_sandbox_" + policy.schema
        self._search_path = "pg_catalog, " + policy.schema

    async def execute(self, sql: str) -> QueryResult:
        conn = None
        deadline = asyncio.get_running_loop().time() + self._limits.total_timeout_ms / 1000
        try:
            decision = guard_sql(sql, self._policy)
            if not decision.accepted:
                return QueryResult("blocked", decision.reason)
            async with asyncio.timeout_at(deadline):
                conn = await self._pool.acquire(
                    timeout=min(self._limits.pool_timeout_ms / 1000, _remaining(deadline))
                )
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
        except (
            asyncpg.UndefinedTableError,
            asyncpg.UndefinedColumnError,
            asyncpg.UndefinedFunctionError,
            asyncpg.InvalidSchemaNameError,
        ):
            return QueryResult("failed", "undefined_object")
        except (asyncpg.InsufficientPrivilegeError, asyncpg.ReadOnlySQLTransactionError):
            return QueryResult("failed", "permission_error")
        except (
            OSError,
            asyncpg.PostgresConnectionError,
            asyncpg.InvalidAuthorizationSpecificationError,
        ):
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
        await conn.execute(
            _SETTINGS_SQL,
            f"{self._limits.statement_timeout_ms}ms",
            f"{self._limits.lock_timeout_ms}ms",
            self._search_path,
            timeout=_remaining(deadline),
        )
        identity = await conn.fetchrow(_IDENTITY_SQL, timeout=_remaining(deadline))
        expected = (
            self._expected_user,
            "sqlwarden",
            "on",
            self._search_path,
            self._limits.statement_timeout_ms,
            self._limits.lock_timeout_ms,
            16384,
        )
        if (
            identity is None
            or len(identity) != 8
            or tuple(identity[:7]) != expected
            or type(identity[7]) is not int
            or not 0 < identity[7] <= 65536
        ):
            result = QueryResult("failed", "configuration_error")
        else:
            plan = await conn.fetchval("EXPLAIN (FORMAT JSON) " + sql, timeout=_remaining(deadline))
            reason = _check_plan(plan, self._limits)
            if reason:
                status = "blocked" if reason.endswith("_limit") else "failed"
                result = QueryResult(status, reason)
            else:
                statement = await conn.prepare(sql, timeout=_remaining(deadline))
                buf = _ResultBuffer(
                    tuple(attr.name for attr in statement.get_attributes()), self._limits
                )
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


def dataset_password_key(db_id: str) -> str:
    if db_id not in DATASET_POLICIES:
        raise ValueError("Unknown dataset id")
    if db_id == "california_schools":
        return "WARDEN_CALIFORNIA_PASSWORD"
    return "WARDEN_DATASET_" + db_id.upper() + "_PASSWORD"


@asynccontextmanager
async def open_dataset_executor(db_id: str, password: str, limits: QueryLimits = _DEFAULT_LIMITS):
    policy = DATASET_POLICIES.get(db_id)
    if policy is None:
        raise ValueError("Unknown dataset id") from None
    if type(password) is not str or not password or "\x00" in password:
        raise ValueError("Invalid restricted-reader credential") from None
    try:
        async with asyncio.timeout(limits.pool_timeout_ms / 1000):
            pool = await asyncpg.create_pool(
                host="127.0.0.1",
                port=55432,
                database="sqlwarden",
                user="warden_sandbox_" + policy.schema,
                password=password,
                ssl=False,
                min_size=0,
                max_size=1,
                timeout=limits.pool_timeout_ms / 1000,
                command_timeout=limits.total_timeout_ms / 1000,
            )
    except asyncio.CancelledError:
        raise
    except Exception:
        raise ExecutorLifecycleError("connection_error") from None
    try:
        yield QueryExecutor(pool, limits, policy)
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


@asynccontextmanager
async def open_california_executor(password: str, limits: QueryLimits = _DEFAULT_LIMITS):
    async with open_dataset_executor("california_schools", password, limits) as executor:
        yield executor

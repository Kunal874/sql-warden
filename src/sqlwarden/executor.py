"""Complete, typed results and finite budgets for restricted SQL execution."""

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

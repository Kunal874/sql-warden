"""Catch configurations that would disable bounds on untrusted queries."""

import pytest

from sqlwarden.config import QueryLimits


@pytest.mark.parametrize(
    "field",
    [
        "max_rows",
        "max_result_bytes",
        "max_cell_bytes",
        "statement_timeout_ms",
        "lock_timeout_ms",
        "pool_timeout_ms",
        "total_timeout_ms",
    ],
)
@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1000"])
def test_rejects_limits_that_remove_or_misrepresent_a_bound(field, value):
    with pytest.raises(ValueError, match=field):
        QueryLimits(**{field: value})


def test_rejects_a_cell_budget_larger_than_the_total_result_budget():
    with pytest.raises(ValueError, match="max_cell_bytes"):
        QueryLimits(max_result_bytes=128, max_cell_bytes=129)


def test_rejects_a_lock_timeout_longer_than_the_statement_timeout():
    with pytest.raises(ValueError, match="lock_timeout_ms"):
        QueryLimits(statement_timeout_ms=100, lock_timeout_ms=101)


@pytest.mark.parametrize("field", ["statement_timeout_ms", "pool_timeout_ms"])
def test_rejects_an_individual_timeout_longer_than_the_total_budget(field):
    values = {
        "statement_timeout_ms": 500,
        "lock_timeout_ms": 50,
        "pool_timeout_ms": 500,
        "total_timeout_ms": 1000,
    }
    values[field] = 1001
    with pytest.raises(ValueError, match=field):
        QueryLimits(**values)


def test_preserves_valid_small_budgets_for_boundary_checks():
    limits = QueryLimits(
        max_rows=2,
        max_result_bytes=128,
        max_cell_bytes=64,
        statement_timeout_ms=100,
        lock_timeout_ms=20,
        pool_timeout_ms=50,
        total_timeout_ms=200,
    )
    assert limits.max_rows == 2
    assert limits.max_result_bytes == 128
    assert limits.max_cell_bytes == 64
    assert limits.statement_timeout_ms == 100
    assert limits.lock_timeout_ms == 20
    assert limits.pool_timeout_ms == 50
    assert limits.total_timeout_ms == 200

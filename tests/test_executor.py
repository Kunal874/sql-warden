"""Complete results and budgets must not confuse a prefix with an answer."""

import json
import math
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from sqlwarden.config import QueryLimits
from sqlwarden.executor import QueryResult, _check_plan, _ResultBuffer


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

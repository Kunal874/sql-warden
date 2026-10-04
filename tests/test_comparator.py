"""Pinned EX semantics and complete-result boundaries without database I/O."""

import math
from dataclasses import FrozenInstanceError, fields
from datetime import date
from decimal import Decimal

import asyncpg
import pytest

import sqlwarden.executor as executor_module
from sqlwarden.comparator import EXComparison, compare_ex
from sqlwarden.executor import QueryResult


def complete(rows=(), columns=None):
    if columns is None:
        width = len(rows[0]) if rows else 1
        columns = tuple(f"c{i}" for i in range(width))
    return QueryResult("ok", "complete", columns, tuple(rows))


@pytest.mark.parametrize(
    "predicted_rows,reference_rows,score",
    [
        (((2,), (1,)), ((1,), (2,)), 1),
        (((1,), (1,), (2,)), ((2,), (1,)), 1),
        (((1,), (2,)), ((1,),), 0),
        (((1, 2),), ((2, 1),), 0),
        (((1, 2),), ((1,),), 0),
        ((), (), 1),
        (((None,),), ((None,),), 1),
        (((None,),), ((0,),), 0),
        (((None,),), (("None",),), 0),
        (((1,),), ((1.0,),), 1),
        (((1,),), ((Decimal("1.0"),),), 1),
        (((1,),), ((True,),), 1),
        (((0,),), ((False,),), 1),
        (((Decimal("0.1"),),), ((0.1,),), 0),
        (((0.1,),), ((math.nextafter(0.1, math.inf),),), 0),
        (((0.0,),), ((-0.0,),), 1),
        (((math.inf,),), ((math.inf,),), 1),
        (((math.inf,),), ((-math.inf,),), 0),
        (((date(2024, 1, 1),),), ((date(2024, 1, 1),),), 1),
        (((date(2024, 1, 1),),), (("2024-01-01",),), 0),
        ((("1",),), ((1,),), 0),
        ((("é",),), (("é",),), 1),
        ((("é",),), (("e",),), 0),
        (((Decimal("1.00000000000000000001"),),), ((1,),), 0),
    ],
)
def test_literal_row_set_rule(predicted_rows, reference_rows, score):
    outcome = compare_ex(complete(predicted_rows), complete(reference_rows))
    assert outcome == EXComparison(score, "match" if score else "mismatch")
    assert type(outcome.score) is int


def test_column_names_and_byte_metadata_are_not_answer_data():
    predicted = QueryResult("ok", "complete", ("x", "x"), ((1, 2),), 100)
    reference = QueryResult("ok", "complete", ("a", "b"), ((1, 2),), 200)
    assert compare_ex(predicted, reference) == EXComparison(1, "match")


def test_empty_outputs_match_without_column_alignment():
    assert compare_ex(complete(columns=("a",)), complete(columns=("b", "c"))) == (
        EXComparison(1, "match")
    )


def test_distinct_nan_objects_do_not_match():
    assert compare_ex(complete(((float("nan"),),)), complete(((float("nan"),),))) == (
        EXComparison(0, "mismatch")
    )


def test_shared_nan_object_preserves_python_container_identity():
    value = float("nan")
    assert compare_ex(complete(((value,),)), complete(((value,),))) == EXComparison(1, "match")


@pytest.mark.parametrize("status", ["blocked", "failed", "overflow"])
@pytest.mark.parametrize("prefix", [(), ((1,),)])
def test_unsuccessful_predictions_cannot_match_even_a_retained_prefix(status, prefix):
    predicted = QueryResult(status, "private-reason-canary", ("n",), prefix)
    assert compare_ex(predicted, complete(prefix)) == EXComparison(0, "prediction_failed")


@pytest.mark.parametrize("status", ["blocked", "failed", "overflow"])
def test_unsuccessful_reference_is_unscorable_not_a_prediction_failure(status):
    reference = QueryResult(status, "private-reason-canary", ("n",), ((1,),))
    assert compare_ex(complete(((1,),)), reference) == EXComparison(None, "gold_invalid")


def test_reference_failure_has_priority_when_both_sides_fail():
    assert compare_ex(QueryResult("failed", "a"), QueryResult("overflow", "b")) == (
        EXComparison(None, "gold_invalid")
    )


@pytest.mark.parametrize("invalid", [None, {}, object(), "private-result-canary"])
@pytest.mark.parametrize("side", ["prediction", "reference"])
def test_wrong_result_objects_have_fixed_outcomes(invalid, side):
    valid = complete(((1,),))
    predicted, reference = (invalid, valid) if side == "prediction" else (valid, invalid)
    expected = (
        EXComparison(0, "prediction_failed")
        if side == "prediction"
        else EXComparison(None, "gold_invalid")
    )
    assert compare_ex(predicted, reference) == expected


@pytest.mark.parametrize(
    "rows",
    [
        None,
        [(1,)],
        ([1],),
        ("private-row-canary",),
        ((["private-cell-canary"],),),
        ((Decimal("sNaN"),),),
    ],
)
@pytest.mark.parametrize("side", ["prediction", "reference"])
def test_bad_row_containers_or_hashing_do_not_echo_data(rows, side, caplog, capsys):
    invalid = QueryResult("ok", "private-reason-canary", ("private-column-canary",), rows)
    valid = complete(((1,),))
    predicted, reference = (invalid, valid) if side == "prediction" else (valid, invalid)
    outcome = compare_ex(predicted, reference)
    expected = (
        EXComparison(0, "comparison_error")
        if side == "prediction"
        else EXComparison(None, "gold_invalid")
    )
    assert outcome == expected
    assert "private-" not in repr(outcome) + caplog.text + str(capsys.readouterr())


def test_outcome_is_immutable_and_has_no_answer_or_diagnostic_fields():
    outcome = compare_ex(complete(((1,),)), complete(((1,),)))
    assert [field.name for field in fields(outcome)] == ["score", "reason"]
    assert not hasattr(outcome, "__dict__")
    with pytest.raises(FrozenInstanceError):
        outcome.score = 0


def test_comparison_does_not_open_a_pool_connect_or_guard(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Comparison must not perform query I/O")

    monkeypatch.setattr(asyncpg, "connect", forbidden)
    monkeypatch.setattr(asyncpg, "create_pool", forbidden)
    monkeypatch.setattr(executor_module, "guard_sql", forbidden)
    assert compare_ex(complete(((1,),)), complete(((1,),))) == EXComparison(1, "match")

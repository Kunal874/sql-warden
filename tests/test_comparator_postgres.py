"""Handwritten native controls, not BIRD gold execution or a benchmark score."""

import os

import pytest
from test_bird_load import california_connected

from sqlwarden.comparator import EXComparison, compare_ex
from sqlwarden.config import QueryLimits
from sqlwarden.executor import open_california_executor

pytestmark = pytest.mark.integration


async def ready():
    async with california_connected():
        pass


def password():
    return os.environ["WARDEN_CALIFORNIA_PASSWORD"]


@pytest.mark.parametrize(
    "predicted_sql,reference_sql,score",
    [
        ("SELECT count(*) AS n FROM schools", "SELECT 17686 AS reference_count", 1),
        (
            "SELECT n FROM (VALUES (1),(2),(1)) x(n) ORDER BY n",
            "SELECT n FROM (VALUES (2),(1)) x(n) ORDER BY n DESC",
            1,
        ),
        ("SELECT 1 AS a, 2 AS b", "SELECT 2 AS a, 1 AS b", 0),
        (
            "SELECT cdscode FROM schools WHERE false",
            "SELECT NULL AS a, NULL AS b WHERE false",
            1,
        ),
        ("SELECT NULL AS n", "SELECT 0 AS n", 0),
        ("SELECT NULL AS n", "SELECT NULL AS other", 1),
        ("SELECT CAST('1.0' AS numeric) AS n", "SELECT 1 AS n", 1),
        ("SELECT '1' AS n", "SELECT 1 AS n", 0),
        (
            "SELECT CAST('2024-01-01' AS date) AS n",
            "SELECT CAST('2024-01-01' AS date) AS other",
            1,
        ),
        ("SELECT CAST('2024-01-01' AS date) AS n", "SELECT '2024-01-01' AS n", 0),
        (
            "SELECT CAST('NaN' AS double precision) AS n",
            "SELECT CAST('NaN' AS double precision) AS other",
            0,
        ),
        (
            "SELECT CAST('0.1' AS double precision) AS n",
            "SELECT CAST('0.10000000000000002' AS double precision) AS n",
            0,
        ),
    ],
)
async def test_real_native_complete_pairs(predicted_sql, reference_sql, score):
    await ready()
    async with open_california_executor(password()) as executor:
        predicted = await executor.execute(predicted_sql)
        reference = await executor.execute(reference_sql)
        assert predicted.status == reference.status == "ok"
        assert compare_ex(predicted, reference) == EXComparison(
            score, "match" if score else "mismatch"
        )


@pytest.mark.parametrize("invalid_side", ["prediction", "reference"])
async def test_real_overflow_cannot_match_the_complete_prefix(invalid_side):
    await ready()
    async with open_california_executor(password(), QueryLimits(max_rows=2)) as executor:
        valid = await executor.execute("SELECT n FROM (VALUES (1),(2)) x(n) ORDER BY n")
        invalid = await executor.execute("SELECT n FROM (VALUES (1),(2),(3)) x(n) ORDER BY n")
        assert valid.status == "ok" and valid.rows == ((1,), (2,))
        assert (invalid.status, invalid.reason, invalid.rows) == ("overflow", "row_limit", ())
        predicted, reference = (
            (invalid, valid) if invalid_side == "prediction" else (valid, invalid)
        )
        expected = (
            EXComparison(0, "prediction_failed")
            if invalid_side == "prediction"
            else EXComparison(None, "gold_invalid")
        )
        assert compare_ex(predicted, reference) == expected
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)


@pytest.mark.parametrize("invalid_side", ["prediction", "reference"])
async def test_real_engine_failure_is_fixed_and_next_query_recovers(invalid_side, caplog, capsys):
    await ready()
    async with open_california_executor(password()) as executor:
        valid = await executor.execute("SELECT 1 AS n")
        invalid = await executor.execute("SELECT CAST('private-canary' AS int)")
        assert valid.status == "ok"
        assert (invalid.status, invalid.reason, invalid.rows) == ("failed", "database_error", ())
        predicted, reference = (
            (invalid, valid) if invalid_side == "prediction" else (valid, invalid)
        )
        outcome = compare_ex(predicted, reference)
        expected = (
            EXComparison(0, "prediction_failed")
            if invalid_side == "prediction"
            else EXComparison(None, "gold_invalid")
        )
        assert outcome == expected
        assert "private-canary" not in (
            repr(invalid) + repr(outcome) + caplog.text + str(capsys.readouterr())
        )
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)


async def test_real_guard_block_is_a_failure_not_a_correct_empty_answer():
    await ready()
    async with open_california_executor(password()) as executor:
        predicted = await executor.execute("DELETE FROM schools")
        reference = await executor.execute("SELECT 1 AS n")
        assert predicted.status == "blocked" and predicted.columns == () and predicted.rows == ()
        assert reference.status == "ok"
        assert compare_ex(predicted, reference) == EXComparison(0, "prediction_failed")
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)

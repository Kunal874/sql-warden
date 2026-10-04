import os

import pytest

from sqlwarden.cli import ask_once
from sqlwarden.llm import Generation
from tests.test_bird_load import california_connected

pytestmark = pytest.mark.integration


class FixedProvider:
    def __init__(self, sql):
        self.sql = sql

    async def generate(self, question):
        return Generation(self.sql, "ok", calls=1)


async def actual(sql):
    async with california_connected():
        return await ask_once(
            "A fixed test, not a model request.",
            os.environ["WARDEN_CALIFORNIA_PASSWORD"],
            FixedProvider(sql),
        )


@pytest.mark.parametrize(
    "sql,columns,rows",
    [
        ("SELECT count(*) AS n FROM california_schools.schools", ("n",), ((17686,),)),
        ("SELECT 1 AS n WHERE false", ("n",), ()),
        ("SELECT NULL AS n", ("n",), ((None,),)),
    ],
)
async def test_actual_cli_flow_complete_empty_and_null(sql, columns, rows):
    answer = await actual(sql)
    assert answer["status"] == "answered"
    assert answer["sql"] == sql and answer["columns"] == columns and answer["rows"] == rows
    assert answer["model_calls"] == 1 and "confidence" not in answer and "ex_score" not in answer


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM california_schools.schools",
        "SELECT * FROM pg_catalog.pg_class",
        "SELECT * FROM demo_other.canary",
    ],
)
async def test_actual_hostile_candidate_is_blocked(sql):
    answer = await actual(sql)
    assert answer["status"] == "blocked" and "rows" not in answer


async def test_actual_error_and_overflow_are_not_answers_then_next_call_recovers(caplog):
    for sql in ("SELECT 'PRIVATE_CANARY'::int", "SELECT cdscode FROM california_schools.schools"):
        answer = await actual(sql)
        assert answer["status"] == "failed" and "rows" not in answer and "sql" not in answer
        assert "PRIVATE_CANARY" not in repr(answer) + caplog.text
    assert (await actual("SELECT 1 AS n"))["rows"] == ((1,),)

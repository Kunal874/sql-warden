import json

import pytest

from sqlwarden.agent import AgentConfig, run_agent
from sqlwarden.executor import QueryResult
from sqlwarden.guard import CALIFORNIA_POLICY
from sqlwarden.prompts import (
    PROMPT_VERSIONS,
    PromptError,
    build_clarification_prompt,
    build_explanation_prompt,
    build_generation_prompt,
    build_repair_prompt,
    template_sha256,
)
from sqlwarden.schema import SchemaCatalog
from sqlwarden.voting import CandidateResult, vote


def _catalog():
    return SchemaCatalog.from_mapping(
        "california_schools",
        {
            "tables": {
                "schools": {
                    "description": "",
                    "primary_key": ["cdscode"],
                    "foreign_keys": [],
                    "columns": [
                        {"name": "cdscode", "type": "TEXT", "description": "school id"},
                        {"name": "school", "type": "TEXT", "description": "school name"},
                    ],
                }
            }
        },
    )


def test_prompt_builders_are_versioned_json_contracts_without_reference_answers():
    schema = "table schools\ncolumn schools.school TEXT"
    prompts = (
        build_generation_prompt("List schools", schema, candidate_index=1, model="arctic"),
        build_repair_prompt("List schools", schema, sql="SELECT * FROM schools", reason="syntax"),
        build_clarification_prompt("List schools", schema),
        build_explanation_prompt(
            "List schools", "SELECT school FROM schools", columns=("school",), row_count=2
        ),
    )

    for messages in prompts:
        assert [message["role"] for message in messages] == ["system", "user"]
        payload = json.loads(messages[1]["content"])
        assert payload["prompt_version"] in PROMPT_VERSIONS.values()
        rendered = json.dumps(messages).lower()
        assert "expected_answer" not in rendered
        assert "password" not in rendered
        assert "gold" not in rendered
    assert len(template_sha256("generate")) == 64
    with pytest.raises(PromptError):
        build_generation_prompt("", schema)


def test_vote_keeps_failed_denominator_tie_and_single_candidate_rules():
    result_a = QueryResult("ok", "ok", ("x",), ((1,),))
    result_b = QueryResult("ok", "ok", ("x",), ((2,),))

    winner = vote(
        [
            CandidateResult(0, "ok", "ok", "SELECT 1", result_a),
            CandidateResult(1, "ok", "ok", "SELECT 1", result_a),
            CandidateResult(2, "failed", "syntax_error"),
        ],
        requested=3,
    )
    assert winner.status == "answered"
    assert winner.agreement == 2 / 3
    assert winner.high_confidence is True

    tied = vote(
        [
            CandidateResult(0, "ok", "ok", "SELECT 1", result_a),
            CandidateResult(1, "ok", "ok", "SELECT 2", result_b),
        ],
        requested=2,
    )
    assert tied.status == "abstained" and tied.reason == "vote_tie"

    single = vote([CandidateResult(0, "ok", "ok", "SELECT 1", result_a)], requested=1)
    assert single.status == "answered" and single.high_confidence is False


class FakeProvider:
    def __init__(self, contents):
        self.contents = list(contents)
        self.messages = []

    async def complete(self, messages, *, model_config):
        self.messages.append(messages)
        if not self.contents:
            raise ValueError("unexpected call")
        item = self.contents.pop(0)
        if isinstance(item, Exception):
            raise item
        return {"content": item}


class FakeExecutor:
    def __init__(self, results):
        self.results = list(results)
        self.sql = []

    async def execute(self, sql):
        self.sql.append(sql)
        if sql == "SELECT syntax":
            return QueryResult("failed", "syntax_error")
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_agent_answers_repairs_votes_and_explains_with_fake_llm():
    provider = FakeProvider(
        [
            '{"sql":"SELECT syntax"}',
            '{"sql":"SELECT school FROM schools"}',
            '{"sql":"SELECT school FROM schools"}',
            '{"sql":"SELECT count(*) FROM schools"}',
            '{"answer":"Two schools matched."}',
        ]
    )
    executor = FakeExecutor(
        [
            QueryResult("ok", "ok", ("school",), (("A",), ("B",))),
            QueryResult("ok", "ok", ("school",), (("A",), ("B",))),
            QueryResult("ok", "ok", ("count",), ((2,),)),
        ]
    )

    result = await run_agent(
        "List schools",
        catalog=_catalog(),
        provider=provider,
        executor=executor,
        policy=CALIFORNIA_POLICY,
        config=AgentConfig(candidates=3, max_repairs=1, explain=True),
    )

    assert result.status == "answered"
    assert result.vote.agreement == 2 / 3
    assert result.vote.high_confidence is True
    assert result.explanation == "Two schools matched."
    assert any(event.step == "repair" for event in result.trace)


@pytest.mark.asyncio
async def test_agent_abstains_into_bounded_clarification_on_tie():
    provider = FakeProvider(
        [
            '{"sql":"SELECT cdscode FROM schools"}',
            '{"sql":"SELECT school FROM schools"}',
            (
                '{"question":"Which school field?",'
                '"options":[{"id":"A","text":"code"},{"id":"B","text":"name"}]}'
            ),
        ]
    )
    executor = FakeExecutor(
        [
            QueryResult("ok", "ok", ("cdscode",), (("1",),)),
            QueryResult("ok", "ok", ("school",), (("A",),)),
        ]
    )

    result = await run_agent(
        "List schools",
        catalog=_catalog(),
        provider=provider,
        executor=executor,
        policy=CALIFORNIA_POLICY,
        config=AgentConfig(candidates=2, max_repairs=0, explain=False),
    )

    assert result.status == "needs_clarification"
    assert result.reason == "vote_tie"
    assert result.clarification["question"] == "Which school field?"


@pytest.mark.asyncio
async def test_agent_rejects_unbounded_clarification_options():
    provider = FakeProvider(
        [
            '{"sql":"SELECT cdscode FROM schools"}',
            '{"sql":"SELECT school FROM schools"}',
            json.dumps(
                {
                    "question": "Which field?",
                    "options": [{"id": "A", "text": "x" * 500, "extra": "bad"}],
                }
            ),
        ]
    )
    executor = FakeExecutor(
        [
            QueryResult("ok", "ok", ("cdscode",), (("1",),)),
            QueryResult("ok", "ok", ("school",), (("A",),)),
        ]
    )

    result = await run_agent(
        "List schools",
        catalog=_catalog(),
        provider=provider,
        executor=executor,
        policy=CALIFORNIA_POLICY,
        config=AgentConfig(candidates=2, max_repairs=0, explain=False),
    )

    assert result.status == "needs_clarification"
    assert result.clarification == {
        "question": "Please clarify the exact result you want.",
        "options": [],
    }


@pytest.mark.asyncio
async def test_agent_malformed_outputs_and_limits_reach_terminal_state():
    result = await run_agent(
        "List schools",
        catalog=_catalog(),
        provider=FakeProvider(["not json"]),
        executor=FakeExecutor([]),
        policy=CALIFORNIA_POLICY,
        config=AgentConfig(candidates=1, max_repairs=0, clarify_on_abstain=False, explain=False),
    )

    assert result.status == "abstained"
    assert result.reason == "no_valid_candidate"
    assert result.candidates[0].reason == "model output invalid"

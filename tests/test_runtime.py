import asyncio
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal

import pytest

from sqlwarden.api import RunService
from sqlwarden.evaluation import EvaluationError
from sqlwarden.executor import ExecutorLifecycleError, QueryResult
from sqlwarden.runtime import AgentRuntime, runtime_passwords
from sqlwarden.schema import SchemaCatalog

GOOD = "a" * 48
ASK = {"db_id": "california_schools", "question": "List schools"}


def _catalog(_db_id):
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


class FakeProvider:
    def __init__(self, contents):
        self.contents = list(contents)
        self.questions = []

    async def complete(self, messages, *, model_config):
        self.questions.append(messages[-1]["content"])
        item = self.contents.pop(0)
        if isinstance(item, Exception):
            raise item
        return {"content": item}

    def summary(self):
        return {"calls": 9, "live_calls": 9}


def _opener(results, opened=None):
    @asynccontextmanager
    async def open_executor(db_id, password, limits):
        if opened is not None:
            opened.append((db_id, password))

        class Executor:
            async def execute(self, sql):
                return results.pop(0)

        yield Executor()

    return open_executor


def _runtime(provider, results, **kwargs):
    return AgentRuntime(
        {"california_schools": GOOD},
        provider_factory=lambda _catalog: provider,
        open_executor=_opener(results, kwargs.pop("opened", None)),
        catalogs=_catalog,
        **kwargs,
    )


async def _run(runtime, *, clarify_with=None):
    service = RunService(
        runner=runtime.run, continuation_runner=runtime.resume, allowed_dbs=runtime.allowed_dbs
    )
    created = service.create_run(ASK)
    await service.wait(created["run_id"])
    if clarify_with is not None:
        await service.clarify(created["run_id"], created["capability"], clarify_with)
        await service.wait(created["run_id"])
    return service, created


def test_runtime_passwords_accept_only_restricted_runtime_keys():
    assert runtime_passwords({"WARDEN_RUNTIME_CALIFORNIA_SCHOOLS_PASSWORD": GOOD}) == {
        "california_schools": GOOD
    }
    assert runtime_passwords(
        {
            "WARDEN_RUNTIME_CALIFORNIA_SCHOOLS_PASSWORD": GOOD,
            "WARDEN_RUNTIME_TOXICOLOGY_PASSWORD": "b" * 48,
            "PATH": "x",
        }
    ) == {"california_schools": GOOD, "toxicology": "b" * 48}
    refused = [
        {},
        {"WARDEN_RUNTIME_CALIFORNIA_SCHOOLS_PASSWORD": "short"},
        {"WARDEN_RUNTIME_CALIFORNIA_SCHOOLS_PASSWORD": GOOD, "WARDEN_BOOTSTRAP_PASSWORD": GOOD},
        {"WARDEN_RUNTIME_CALIFORNIA_SCHOOLS_PASSWORD": GOOD, "WARDEN_CALIFORNIA_PASSWORD": GOOD},
        {"WARDEN_RUNTIME_UNKNOWN_DB_PASSWORD": GOOD},
        {"WARDEN_RUNTIME_CALIFORNIA_SCHOOLS_PASSWORD": GOOD, "PGPASSWORD": "x"},
    ]
    for values in refused:
        with pytest.raises(ValueError, match="runtime_configuration"):
            runtime_passwords(values)


def test_answered_run_streams_progress_and_returns_bounded_preview():
    rows = tuple((f"S{i}", Decimal("1.50"), date(2026, 1, 2)) for i in range(60))
    provider = FakeProvider(['{"sql":"SELECT school FROM schools"}'])
    opened = []
    runtime = _runtime(
        provider,
        [QueryResult("ok", "ok", ("school", "score", "day"), rows)],
        candidates=1,
        opened=opened,
    )

    service, created = asyncio.run(_run(runtime))

    events = service.events(created["run_id"], created["capability"])
    steps = [event["step"] for event in events]
    assert steps[:3] == ["created", "start", "validate"]
    assert "retrieve" in steps and steps[-1] == "terminal"
    result = service.status(created["run_id"], created["capability"])["result"]
    assert result["status"] == "answered"
    assert result["sql"] == "SELECT school FROM schools"
    assert result["row_count"] == 60
    assert len(result["rows"]) == 50 and result["preview_truncated"] is True
    assert result["rows"][0] == ["S0", "1.50", "2026-01-02"]
    assert result["agreement"] == 1.0
    assert "Returned 60 rows" in result["explanation"]
    assert result["usage"] == {"calls": 9, "live_calls": 9}
    assert opened == [("california_schools", GOOD)]
    assert GOOD not in str(events)


def test_clarification_resumes_with_the_reply_and_never_asks_twice():
    provider = FakeProvider(
        [
            '{"sql":"SELECT cdscode FROM schools"}',
            '{"sql":"SELECT school FROM schools"}',
            '{"question":"Which field?","options":[{"id":"A","text":"school name"}]}',
            '{"sql":"SELECT cdscode FROM schools"}',
            '{"sql":"SELECT school FROM schools"}',
        ]
    )
    results = [
        QueryResult("ok", "ok", ("cdscode",), (("1",),)),
        QueryResult("ok", "ok", ("school",), (("A",),)),
        QueryResult("ok", "ok", ("cdscode",), (("1",),)),
        QueryResult("ok", "ok", ("school",), (("A",),)),
    ]
    runtime = _runtime(provider, results, candidates=2, repairs=0)

    service, created = asyncio.run(_run(runtime, clarify_with={"option_id": "A"}))

    assert "Clarification: school name" in provider.questions[-1]
    status = service.status(created["run_id"], created["capability"])
    assert status["status"] == "abstained"
    assert status["result"]["reason"] == "vote_tie"


def test_model_and_database_outages_are_explicit_failures():
    unavailable = FakeProvider([EvaluationError("model_unavailable")] * 3)
    runtime = _runtime(unavailable, [], candidates=3)
    service, created = asyncio.run(_run(runtime))
    result = service.status(created["run_id"], created["capability"])["result"]
    assert (result["status"], result["reason"]) == ("failed", "model_unavailable")

    @asynccontextmanager
    async def broken(db_id, password, limits):
        raise ExecutorLifecycleError("connection_error")
        yield

    runtime = AgentRuntime(
        {"california_schools": GOOD},
        provider_factory=lambda _catalog: FakeProvider([]),
        open_executor=broken,
        catalogs=_catalog,
    )
    service, created = asyncio.run(_run(runtime))
    result = service.status(created["run_id"], created["capability"])["result"]
    assert (result["status"], result["reason"]) == ("failed", "connection_error")

"""Plain Python G1 agent state machine with fake-LLM friendly seams."""

from __future__ import annotations

import asyncio
import html
import json
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlwarden.evaluation import EvaluationError, extract_sql
from sqlwarden.executor import QueryResult
from sqlwarden.guard import DatasetPolicy, guard_sql
from sqlwarden.prompts import (
    build_clarification_prompt,
    build_explanation_prompt,
    build_generation_prompt,
    build_repair_prompt,
)
from sqlwarden.schema import SchemaCatalog
from sqlwarden.voting import CandidateResult, VoteResult, vote


@dataclass(frozen=True, slots=True)
class AgentConfig:
    candidates: int = 3
    max_repairs: int = 1
    retrieve_columns: int = 24
    clarify_on_abstain: bool = True
    explain: bool = True
    total_timeout_seconds: int = 120

    def __post_init__(self) -> None:
        if not 1 <= self.candidates <= 5:
            raise ValueError("candidate count refused")
        if not 0 <= self.max_repairs <= 2:
            raise ValueError("repair count refused")
        if not 1 <= self.retrieve_columns <= 80:
            raise ValueError("retrieval size refused")
        if type(self.total_timeout_seconds) is not int or self.total_timeout_seconds <= 0:
            raise ValueError("timeout refused")


@dataclass(frozen=True, slots=True)
class AgentEvent:
    step: str
    status: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class AgentResult:
    status: Literal["answered", "needs_clarification", "abstained", "failed"]
    reason: str
    trace: tuple[AgentEvent, ...]
    vote: VoteResult | None = None
    sql: str | None = None
    columns: tuple[str, ...] = ()
    rows: tuple[tuple[Any, ...], ...] = ()
    explanation: str | None = None
    clarification: dict[str, Any] | None = None
    candidates: tuple[CandidateResult, ...] = ()


@dataclass
class _Trace:
    events: list[AgentEvent] = field(default_factory=list)

    def add(self, step: str, status: str, reason: str = "") -> None:
        self.events.append(AgentEvent(step, status, reason))


async def run_agent(
    question: str,
    *,
    catalog: SchemaCatalog,
    provider,
    executor,
    policy: DatasetPolicy,
    config: AgentConfig | None = None,
    model: str = "local",
) -> AgentResult:
    config = config or AgentConfig()
    trace = _Trace()
    try:
        async with asyncio.timeout(config.total_timeout_seconds):
            return await _run(question, catalog, provider, executor, policy, config, model, trace)
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        trace.add("terminal", "failed", "run_timeout")
        return AgentResult("failed", "run_timeout", tuple(trace.events))
    except Exception:
        trace.add("terminal", "failed", "internal_error")
        return AgentResult("failed", "internal_error", tuple(trace.events))


async def _run(question, catalog, provider, executor, policy, config, model, trace):
    trace.add("validate", "ok")
    scope = catalog.retrieve(question, top_k=config.retrieve_columns)
    schema_text = catalog.serialize(scope)
    trace.add("retrieve", "ok", f"{scope.column_count}_columns")
    candidates = []
    for index in range(config.candidates):
        candidate = await _candidate(
            index, question, schema_text, provider, executor, policy, config, model, trace
        )
        candidates.append(candidate)
    voted = vote(candidates, requested=config.candidates)
    trace.add("vote", voted.status, voted.reason)
    if voted.status == "answered" and voted.selected and voted.selected.result:
        result = voted.selected.result
        explanation = None
        if config.explain:
            explanation = await _explain(
                question, voted.selected.sql or "", result, provider, trace
            )
        trace.add("terminal", "answered", voted.reason)
        return AgentResult(
            "answered",
            voted.reason,
            tuple(trace.events),
            voted,
            voted.selected.sql,
            result.columns,
            result.rows,
            explanation,
            candidates=tuple(candidates),
        )
    if config.clarify_on_abstain:
        clarification = await _clarify(question, schema_text, provider, trace)
        trace.add("terminal", "needs_clarification", voted.reason)
        return AgentResult(
            "needs_clarification",
            voted.reason,
            tuple(trace.events),
            voted,
            clarification=clarification,
            candidates=tuple(candidates),
        )
    trace.add("terminal", "abstained", voted.reason)
    return AgentResult(
        "abstained", voted.reason, tuple(trace.events), voted, candidates=tuple(candidates)
    )


async def _candidate(
    index, question, schema_text, provider, executor, policy, config, model, trace
):
    sql, reason = await _sql_from_provider(
        provider,
        build_generation_prompt(question, schema_text, candidate_index=index, model=model),
    )
    if sql is None:
        trace.add("generate", "failed", reason)
        return CandidateResult(index, "failed", reason)
    outcome = await _execute(sql, executor, policy)
    repairs = 0
    while outcome.status != "ok" and repairs < config.max_repairs:
        repairs += 1
        trace.add("repair", "start", outcome.reason)
        repaired, repair_reason = await _sql_from_provider(
            provider,
            build_repair_prompt(question, schema_text, sql=sql, reason=outcome.reason, model=model),
        )
        if repaired is None:
            return CandidateResult(index, "failed", repair_reason, sql, repairs=repairs)
        sql = repaired
        outcome = await _execute(sql, executor, policy)
    if outcome.status == "ok":
        trace.add("candidate", "ok", str(index))
        return CandidateResult(index, "ok", "ok", sql, outcome, repairs)
    status = "blocked" if outcome.status == "blocked" else "failed"
    trace.add("candidate", status, outcome.reason)
    return CandidateResult(index, status, outcome.reason, sql, repairs=repairs)


async def _sql_from_provider(provider, messages) -> tuple[str | None, str]:
    try:
        response = await provider.complete(messages, model_config={})
        return extract_sql(response["content"]), "ok"
    except EvaluationError as error:
        return None, str(error)
    except (KeyError, TypeError, ValueError, TimeoutError):
        return None, "model_response_invalid"


async def _execute(sql: str, executor, policy: DatasetPolicy) -> QueryResult:
    decision = guard_sql(sql, policy)
    if not decision.accepted:
        return QueryResult("blocked", decision.reason)
    return await executor.execute(decision.sql)


async def _clarify(question: str, schema_text: str, provider, trace) -> dict[str, Any]:
    try:
        response = await provider.complete(
            build_clarification_prompt(question, schema_text), model_config={}
        )
        data = json.loads(response["content"])
        options = _clarification_options(data.get("options") if type(data) is dict else None)
        if type(data) is dict and type(data.get("question")) is str and options:
            question_text = data["question"].strip()[:300]
            document = {"question": question_text, "options": options}
            if len(json.dumps(document, ensure_ascii=True).encode("utf-8")) > 2048:
                raise ValueError
            trace.add("clarify", "ok")
            return document
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    trace.add("clarify", "failed", "clarification_unavailable")
    return {"question": "Please clarify the exact result you want.", "options": []}


def _clarification_options(value: Any) -> list[dict[str, str]]:
    if type(value) is not list or not 1 <= len(value) <= 4:
        return []
    options = []
    seen = set()
    for item in value:
        if type(item) is not dict or set(item) != {"id", "text"}:
            return []
        identifier = item["id"].strip() if type(item["id"]) is str else ""
        text = item["text"].strip() if type(item["text"]) is str else ""
        if (
            not identifier
            or identifier in seen
            or len(identifier) > 16
            or not text
            or len(text) > 160
        ):
            return []
        seen.add(identifier)
        options.append({"id": identifier, "text": text})
    return options


async def _explain(question: str, sql: str, result: QueryResult, provider, trace) -> str | None:
    try:
        response = await provider.complete(
            build_explanation_prompt(
                question,
                sql,
                columns=result.columns,
                row_count=len(result.rows),
                rows=result.rows,
            ),
            model_config={},
        )
        data = json.loads(response["content"])
        if type(data) is dict and type(data.get("answer")) is str and data["answer"].strip():
            trace.add("explain", "ok")
            return html.escape(data["answer"].strip()[:1000], quote=False)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    trace.add("explain", "failed", "explanation_unavailable")
    return None

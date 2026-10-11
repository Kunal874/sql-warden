"""Local web runtime: real agent runs behind the G4 API with restricted dataset logins.

Launch (runtime-only credentials, never `.env.setup`):
`uv run --env-file .env.web uvicorn sqlwarden.runtime:create_runtime_app --factory --port 8000`
"""

from __future__ import annotations

import asyncio
import math
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from fastapi import FastAPI

from sqlwarden.agent import AgentConfig, AgentEvent, AgentResult, run_agent
from sqlwarden.api import RunRecord, RunService
from sqlwarden.catalog import AUDIT_SHA, load_catalog
from sqlwarden.config import QueryLimits, database_address, model_url
from sqlwarden.executor import ExecutorLifecycleError, open_dataset_executor
from sqlwarden.guard import DATASET_POLICIES
from sqlwarden.ollama import ARCTIC, OllamaAgentProvider
from sqlwarden.webapp import create_app

PREVIEW_ROWS = 50
DEFAULT_LIMITS = QueryLimits()
LOCAL_ORIGINS = {
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
}
FORBIDDEN_ENV = frozenset(
    {"ADMIN_DATABASE_URL", "APP_DATABASE_URL", "SANDBOX_DATABASE_URL", "PGPASSWORD"}
)
ADDRESS_KEYS = frozenset({"WARDEN_DB_HOST", "WARDEN_DB_PORT", "WARDEN_OLLAMA_URL"})


def runtime_passwords(values: Mapping[str, str]) -> dict[str, str]:
    """Only restricted per-dataset reader credentials; any setup/test key refuses startup."""
    expected = {f"WARDEN_RUNTIME_{db_id.upper()}_PASSWORD": db_id for db_id in DATASET_POLICIES}
    warden = {key for key in values if key.startswith("WARDEN_")} - ADDRESS_KEYS
    passwords = {
        expected[key]: values[key]
        for key in warden
        if key in expected and re.fullmatch(r"[a-f0-9]{48}", values[key])
    }
    if not passwords or len(passwords) != len(warden) or FORBIDDEN_ENV.intersection(values):
        raise ValueError("runtime_configuration")
    database_address(values)
    model_url(values)
    return passwords


class AgentRuntime:
    def __init__(
        self,
        passwords: dict[str, str],
        *,
        provider_factory: Callable[[Any], Any] | None = None,
        open_executor=open_dataset_executor,
        catalogs=load_catalog,
        candidates: int = 3,
        repairs: int = 1,
        retrieve_columns: int = 24,
        limits: QueryLimits = DEFAULT_LIMITS,
    ) -> None:
        self.passwords = dict(passwords)
        self.allowed_dbs = frozenset(passwords)
        self.lock = asyncio.Lock()
        self.provider_factory = provider_factory or (
            lambda catalog: OllamaAgentProvider(
                fingerprints=(catalog.fingerprint(), AUDIT_SHA), lock=self.lock
            )
        )
        self.open_executor = open_executor
        self.catalogs = catalogs
        self.config = AgentConfig(
            candidates=candidates,
            max_repairs=repairs,
            retrieve_columns=retrieve_columns,
            explain=False,
        )
        self.limits = limits

    async def run(self, run: RunRecord) -> None:
        await self._execute(run, run.question, clarify=True)

    async def resume(self, run: RunRecord) -> None:
        question = f"{run.question}\nClarification: {run.clarification['text']}"
        await self._execute(run, question, clarify=False)

    async def readiness(self) -> str | None:
        try:
            async with httpx.AsyncClient(base_url=model_url(), timeout=3, trust_env=False) as c:
                tags = (await c.get("/api/tags")).json().get("models", [])
        except (httpx.HTTPError, ValueError):
            return "model_unavailable"
        pinned = {"name": ARCTIC.alias, "digest": ARCTIC.digest}
        if not any(pinned.items() <= tag.items() for tag in tags):
            return "model_unavailable"
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(*database_address()), 2)
            writer.close()
        except (OSError, TimeoutError):
            return "database_unavailable"
        return None

    async def _execute(self, run: RunRecord, question: str, *, clarify: bool) -> None:
        config = replace(self.config, clarify_on_abstain=clarify)
        catalog = self.catalogs(run.db_id)
        provider = self.provider_factory(catalog)
        await run.event(
            "start",
            "running",
            {
                "candidates": config.candidates,
                "repairs": config.max_repairs,
                "retrieve_columns": config.retrieve_columns,
            },
        )

        def listen(event: AgentEvent) -> None:
            if event.step != "terminal":
                run.emit(event.step, "running", {"detail": event.status, "reason": event.reason})

        try:
            async with self.open_executor(
                run.db_id, self.passwords[run.db_id], self.limits
            ) as executor:
                result = await run_agent(
                    question,
                    catalog=catalog,
                    provider=provider,
                    executor=executor,
                    policy=DATASET_POLICIES[run.db_id],
                    config=config,
                    model=ARCTIC.name,
                    on_event=listen,
                )
        except ExecutorLifecycleError:
            await run.event("terminal", "failed", {"reason": "connection_error"})
            return
        usage = provider.summary() if hasattr(provider, "summary") else None
        await run.event(*_terminal(result, usage))


def _terminal(result: AgentResult, usage: dict | None) -> tuple[str, str, dict[str, Any]]:
    payload: dict[str, Any] = {
        "reason": result.reason,
        "usage": usage,
        "candidates": [
            {"index": c.index, "status": c.status, "reason": c.reason, "repairs": c.repairs}
            for c in result.candidates
        ],
    }
    if result.status == "needs_clarification":
        return "clarify", "needs_clarification", payload | (result.clarification or {})
    if result.status == "answered":
        agreement = result.vote.agreement if result.vote else None
        payload |= {
            "sql": result.sql,
            "columns": list(result.columns),
            "rows": [[_cell(value) for value in row] for row in result.rows[:PREVIEW_ROWS]],
            "row_count": len(result.rows),
            "preview_truncated": len(result.rows) > PREVIEW_ROWS,
            "agreement": agreement,
            "high_confidence": bool(result.vote and result.vote.high_confidence),
            "explanation": _explanation(result, agreement),
        }
    return "terminal", result.status, payload


def _explanation(result: AgentResult, agreement: float | None) -> str:
    """Factual template; no model writes the explanation in the local runtime (D-074)."""
    rows = len(result.rows)
    columns = ", ".join(result.columns) or "no columns"
    noun = "row" if rows == 1 else "rows"
    text = f"Returned {rows} {noun} with columns {columns}."
    if agreement is not None and result.candidates:
        agreeing = round(agreement * len(result.candidates))
        text += f" {agreeing} of {len(result.candidates)} candidates agreed on this result."
    return text


def _cell(value: Any) -> Any:
    if type(value) in (Decimal, date) or (type(value) is float and not math.isfinite(value)):
        return str(value)
    return value


def create_runtime_app() -> FastAPI:
    runtime = AgentRuntime(runtime_passwords(os.environ))
    service = RunService(
        runner=runtime.run,
        continuation_runner=runtime.resume,
        allowed_origins=LOCAL_ORIGINS,
        allowed_dbs=runtime.allowed_dbs,
    )
    return create_app(service, readiness=runtime.readiness)

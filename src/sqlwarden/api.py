"""Framework-free G4 run lifecycle: capabilities, admission, clarification and replay."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

ALLOWED_DBS = frozenset({"california_schools"})
TERMINAL = frozenset(
    {"answered", "failed", "blocked", "abstained", "cancelled", "expired", "interrupted"}
)
MAX_EVENTS_PER_RUN = 256
MAX_QUESTION_CHARS = 500
MAX_CLARIFICATION_CHARS = 200
PRIVATE_KEYS = frozenset({"capability", "credential", "password"})
BOUNDARY_KEYS = frozenset({"db_id", "tenant", "tenant_id", "role"})


class ApiError(ValueError):
    """Stable API refusal reason without private details."""


class EventLimitError(RuntimeError):
    """A runner emitted more events than one run may retain."""


@dataclass
class RunRecord:
    run_id: str
    db_id: str
    question: str
    capability_hash: str
    status: str = "queued"
    events: list[dict[str, Any]] = field(default_factory=list)
    started: bool = False
    interruption_requested: bool = False
    clarification_used: bool = False
    clarification: dict[str, str | None] | None = None
    pending_options: dict[str, str] = field(default_factory=dict)
    pending_since: float | None = None
    finished_at: float | None = None
    task: asyncio.Task | None = None

    async def event(
        self, event_type: str, status: str, payload: dict[str, Any] | None = None
    ) -> None:
        self.emit(event_type, status, payload)

    def emit(self, event_type: str, status: str, payload: dict[str, Any] | None = None) -> None:
        """Synchronous form for callbacks that cannot await."""
        if self.status in TERMINAL:
            return
        if len(self.events) >= MAX_EVENTS_PER_RUN:
            raise EventLimitError
        payload = dict(payload or {})
        payload["status"] = status
        terminal = event_type == "terminal" and status in TERMINAL
        if status == "needs_clarification":
            self.pending_options = _offered_options(payload.get("options"))
            self.pending_since = time.monotonic()
        if terminal or status == "needs_clarification":
            self.status = status
        if terminal:
            self.finished_at = time.monotonic()
        self._append("terminal" if terminal else "progress", event_type, payload)

    def _append(self, kind: str, step: str, payload: dict[str, Any]) -> None:
        self.events.append(
            {"id": len(self.events) + 1, "type": kind, "step": step, "payload": _safe(payload)}
        )


Runner = Callable[[RunRecord], Awaitable[None]]


class RunService:
    def __init__(
        self,
        *,
        runner: Runner,
        continuation_runner: Runner | None = None,
        allowed_origins: set[str] | None = None,
        allowed_dbs: frozenset[str] = ALLOWED_DBS,
        max_active: int = 2,
        max_runs: int = 500,
        retention_seconds: int = 3600,
        rate_limit_per_ip: int = 20,
        rate_window_seconds: int = 60,
        max_rate_buckets: int = 512,
        max_body_bytes: int = 4096,
        run_timeout_seconds: float = 300,
        clarification_ttl_seconds: float = 600,
    ) -> None:
        self.runner = runner
        self.continuation_runner = continuation_runner
        self.allowed_origins = allowed_origins or {"http://localhost:5173"}
        self.allowed_dbs = allowed_dbs
        self.max_active = max_active
        self.max_runs = max_runs
        self.retention_seconds = retention_seconds
        self.rate_limit_per_ip = rate_limit_per_ip
        self.rate_window_seconds = rate_window_seconds
        self.max_rate_buckets = max_rate_buckets
        self.max_body_bytes = max_body_bytes
        self.run_timeout_seconds = run_timeout_seconds
        self.clarification_ttl_seconds = clarification_ttl_seconds
        self.runs: dict[str, RunRecord] = {}
        self.rate_buckets: dict[str, list[float]] = {}

    def create_run(
        self, body: Any, *, origin: str | None = None, client_ip: str = "127.0.0.1"
    ) -> dict[str, str]:
        """Admit a run. A missing Origin is a non-browser client; a wrong one is refused."""
        self._validate_request(body, origin, client_ip)
        if sum(1 for run in self.runs.values() if run.status in {"queued", "running"}) >= (
            self.max_active
        ):
            raise ApiError("overloaded")
        run_id = secrets.token_urlsafe(18)
        capability = secrets.token_urlsafe(32)
        run = RunRecord(run_id, body["db_id"], body["question"], _hash_capability(capability))
        run._append("progress", "created", {"status": "queued"})
        self.runs[run_id] = run
        self._prune()
        return {"status": "created", "run_id": run_id, "capability": capability}

    def authorize(self, run_id: str, capability: str) -> bool:
        run = self.runs.get(run_id)
        return bool(
            run
            and type(capability) is str
            and hmac.compare_digest(run.capability_hash, _hash_capability(capability))
        )

    def events(self, run_id: str, capability: str, *, after_id: int = 0) -> list[dict[str, Any]]:
        run = self._authorized_run(run_id, capability)
        return [event for event in run.events if event["id"] > after_id]

    def status(self, run_id: str, capability: str) -> dict[str, Any]:
        run = self._authorized_run(run_id, capability)
        body: dict[str, Any] = {"status": run.status, "last_event_id": run.events[-1]["id"]}
        if run.status == "needs_clarification":
            body["clarification"] = run.events[-1]["payload"]
        if run.status in TERMINAL:
            body["result"] = next(e for e in reversed(run.events) if e["type"] == "terminal")[
                "payload"
            ]
        return body

    def start(self, run_id: str) -> None:
        run = self.runs[run_id]
        if run.status == "queued" and not run.started:
            run.started = True
            run.task = asyncio.create_task(self._drive_with_runner(run, self.runner))

    async def wait(self, run_id: str) -> dict[str, str]:
        run = self.runs[run_id]
        self.start(run_id)
        if run.task:
            await asyncio.gather(run.task, return_exceptions=True)
        return {"status": run.status}

    def cancel(self, run_id: str, capability: str) -> dict[str, str]:
        run = self._authorized_run(run_id, capability)
        if run.status not in TERMINAL:
            self._terminal(run, "cancelled")
            if run.task:
                run.task.cancel()
        return {"status": run.status}

    async def clarify(self, run_id: str, capability: str, body: Any) -> dict[str, str]:
        run = self._authorized_run(run_id, capability)
        if run.status != "needs_clarification" or run.clarification_used:
            raise ApiError("clarification_not_pending")
        clarification = _validate_clarification(body, run.pending_options)
        run.clarification_used = True
        run.clarification = clarification
        run.status = "running"
        await run.event("clarification", "running")
        if not self.continuation_runner:
            self._terminal(run, "failed", "continuation_unavailable")
            return {"status": run.status}
        run.task = asyncio.create_task(self._drive_with_runner(run, self.continuation_runner))
        return {"status": "running"}

    def mark_interrupted(self) -> None:
        for run in self.runs.values():
            if run.status not in TERMINAL:
                run.interruption_requested = True
                self._terminal(run, "interrupted")
                if run.task:
                    run.task.cancel()

    async def _drive_with_runner(self, run: RunRecord, runner: Runner) -> None:
        run.status = "running"
        try:
            async with asyncio.timeout(self.run_timeout_seconds):
                await runner(run)
            if run.status not in TERMINAL | {"needs_clarification"}:
                self._terminal(run, "failed", "runner_incomplete")
        except asyncio.CancelledError:
            self._terminal(run, "interrupted" if run.interruption_requested else "cancelled")
        except TimeoutError:
            self._terminal(run, "failed", "run_timeout")
        except EventLimitError:
            self._terminal(run, "failed", "event_limit")
        except Exception:
            self._terminal(run, "failed", "internal_error")

    def _validate_request(self, body: Any, origin: str | None, client_ip: str) -> None:
        if origin is not None and origin not in self.allowed_origins:
            raise ApiError("origin_refused")
        if type(body) is not dict:
            raise ApiError("body_invalid")
        try:
            size = len(json.dumps(body, ensure_ascii=True).encode("utf-8"))
        except (TypeError, ValueError):
            raise ApiError("body_invalid") from None
        if size > self.max_body_bytes:
            raise ApiError("body_too_large")
        if set(body) != {"db_id", "question"}:
            raise ApiError("body_invalid")
        if body["db_id"] not in self.allowed_dbs:
            raise ApiError("db_refused")
        if not _bounded_text(body["question"], MAX_QUESTION_CHARS):
            raise ApiError("input_invalid")
        self._rate_limit(client_ip)

    def _rate_limit(self, client_ip: str) -> None:
        now = time.monotonic()
        cutoff = now - self.rate_window_seconds
        if client_ip not in self.rate_buckets and len(self.rate_buckets) >= self.max_rate_buckets:
            self.rate_buckets = {
                key: values for key, values in self.rate_buckets.items() if values[-1] >= cutoff
            }
            if len(self.rate_buckets) >= self.max_rate_buckets:
                raise ApiError("rate_limited")
        bucket = [item for item in self.rate_buckets.get(client_ip, []) if item >= cutoff]
        if len(bucket) >= self.rate_limit_per_ip:
            raise ApiError("rate_limited")
        bucket.append(now)
        self.rate_buckets[client_ip] = bucket

    def _authorized_run(self, run_id: str, capability: str) -> RunRecord:
        if not self.authorize(run_id, capability):
            raise ApiError("unauthorized")
        run = self.runs[run_id]
        if (
            run.status == "needs_clarification"
            and run.pending_since is not None
            and time.monotonic() - run.pending_since >= self.clarification_ttl_seconds
        ):
            self._terminal(run, "expired", "clarification_expired")
        return run

    def _terminal(self, run: RunRecord, status: str, reason: str | None = None) -> None:
        if run.status in TERMINAL:
            return
        run.status = status
        run.finished_at = time.monotonic()
        payload = {"status": status} | ({"reason": reason} if reason else {})
        run._append("terminal", "terminal", payload)

    def _prune(self) -> None:
        now = time.monotonic()
        for run_id, run in list(self.runs.items()):
            if run.finished_at is not None and now - run.finished_at > self.retention_seconds:
                del self.runs[run_id]
        finished = [run_id for run_id, run in self.runs.items() if run.status in TERMINAL]
        while len(self.runs) > self.max_runs and finished:
            del self.runs[finished.pop(0)]


def encode_sse(events: list[dict[str, Any]]) -> str:
    return "".join(
        f"id: {event['id']}\nevent: {event['type']}\ndata: "
        f"{json.dumps(event['payload'] | {'step': event['step']}, sort_keys=True)}\n\n"
        for event in events
    )


def _hash_capability(capability: str) -> str:
    return hashlib.sha256(capability.encode("utf-8")).hexdigest()


def _safe(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in PRIVATE_KEYS}


def _bounded_text(value: Any, limit: int) -> bool:
    return (
        type(value) is str
        and bool(value.strip())
        and len(value) <= limit
        and not any(ord(c) < 32 or 127 <= ord(c) < 160 for c in value)
    )


def _offered_options(value: Any) -> dict[str, str]:
    if type(value) is not list:
        return {}
    return {
        item["id"]: item["text"]
        for item in value
        if type(item) is dict and type(item.get("id")) is str and type(item.get("text")) is str
    }


def _validate_clarification(body: Any, offered: dict[str, str]) -> dict[str, str | None]:
    if type(body) is not dict:
        raise ApiError("clarification_invalid")
    if BOUNDARY_KEYS.intersection(body):
        raise ApiError("clarification_boundary_refused")
    if set(body) == {"option_id"} and body["option_id"] in offered:
        return {"option_id": body["option_id"], "text": offered[body["option_id"]]}
    if set(body) == {"text"} and _bounded_text(body["text"], MAX_CLARIFICATION_CHARS):
        return {"option_id": None, "text": body["text"].strip()}
    raise ApiError("clarification_invalid")

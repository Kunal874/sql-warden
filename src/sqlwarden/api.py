"""Dependency-free G4 API core for run lifecycle, capabilities and SSE replay."""

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


class ApiError(ValueError):
    """Stable API refusal reason without private details."""


@dataclass
class RunRecord:
    run_id: str
    db_id: str
    question: str
    capability_hash: str
    status: str = "queued"
    events: list[dict[str, Any]] = field(default_factory=list)
    started: bool = False
    task: asyncio.Task | None = None

    async def event(
        self, event_type: str, status: str, payload: dict[str, Any] | None = None
    ) -> None:
        payload = dict(payload or {})
        payload.setdefault("status", status)
        self.status = status if event_type == "terminal" else self.status
        self.events.append(
            {
                "id": len(self.events) + 1,
                "type": "terminal" if event_type == "terminal" else "progress",
                "step": event_type,
                "payload": _safe_payload(payload),
            }
        )


Runner = Callable[[RunRecord], Awaitable[None]]


class RunService:
    def __init__(
        self,
        *,
        runner: Runner,
        allowed_origins: set[str] | None = None,
        max_active: int = 2,
        rate_limit_per_ip: int = 20,
        max_body_bytes: int = 4096,
        rate_window_seconds: int = 60,
    ) -> None:
        self.runner = runner
        self.allowed_origins = allowed_origins or {"http://localhost:5173"}
        self.max_active = max_active
        self.rate_limit_per_ip = rate_limit_per_ip
        self.max_body_bytes = max_body_bytes
        self.rate_window_seconds = rate_window_seconds
        self.runs: dict[str, RunRecord] = {}
        self.rate_buckets: dict[str, list[float]] = {}

    def create_run(
        self,
        body: dict[str, Any],
        *,
        origin: str = "http://localhost:5173",
        client_ip: str = "127.0.0.1",
    ) -> dict[str, str]:
        self._validate_request(body, origin, client_ip)
        if (
            sum(1 for run in self.runs.values() if run.status in {"queued", "running"})
            >= self.max_active
        ):
            raise ApiError("overloaded")
        run_id = secrets.token_urlsafe(18)
        capability = secrets.token_urlsafe(32)
        run = RunRecord(
            run_id=run_id,
            db_id=body["db_id"],
            question=body["question"],
            capability_hash=_hash_capability(capability),
        )
        run.events.append(
            {"id": 1, "type": "progress", "step": "created", "payload": {"status": "queued"}}
        )
        self.runs[run_id] = run
        return {"status": "created", "run_id": run_id, "capability": capability}

    def authorize(self, run_id: str, capability: str) -> bool:
        run = self.runs.get(run_id)
        return bool(run and hmac.compare_digest(run.capability_hash, _hash_capability(capability)))

    def events(self, run_id: str, capability: str, *, after_id: int = 0) -> list[dict[str, Any]]:
        run = self._authorized_run(run_id, capability)
        return [event for event in run.events if event["id"] > after_id]

    async def wait(self, run_id: str) -> dict[str, str]:
        run = self.runs[run_id]
        if run.status == "queued" and not run.started:
            run.started = True
            await self._drive(run)
        elif run.task:
            await asyncio.gather(run.task, return_exceptions=True)
        return {"status": run.status}

    def cancel(self, run_id: str, capability: str) -> dict[str, str]:
        run = self._authorized_run(run_id, capability)
        if run.status not in {"cancelled", "answered", "failed", "interrupted"}:
            if run.task:
                run.task.cancel()
            self._terminal(run, "cancelled")
        return {"status": run.status}

    def mark_interrupted(self) -> None:
        for run in self.runs.values():
            if run.status in {"queued", "running"}:
                if run.task:
                    run.task.cancel()
                self._terminal(run, "interrupted")

    async def _drive(self, run: RunRecord) -> None:
        run.status = "running"
        try:
            await self.runner(run)
            if run.status not in {"answered", "failed", "blocked", "interrupted", "cancelled"}:
                self._terminal(run, "failed")
        except asyncio.CancelledError:
            if run.status not in {"cancelled", "interrupted"}:
                self._terminal(run, "cancelled")
        except Exception:
            self._terminal(run, "failed")

    def _validate_request(self, body: dict[str, Any], origin: str, client_ip: str) -> None:
        if origin not in self.allowed_origins:
            raise ApiError("origin_refused")
        try:
            if len(json.dumps(body, ensure_ascii=True).encode("utf-8")) > self.max_body_bytes:
                raise ApiError("body_too_large")
        except ApiError:
            raise
        except (TypeError, ValueError):
            raise ApiError("body_invalid") from None
        if body.get("db_id") not in ALLOWED_DBS:
            raise ApiError("db_refused")
        question = body.get("question")
        if type(question) is not str or not question.strip() or len(question) > 500:
            raise ApiError("input_invalid")
        self._rate_limit(client_ip)

    def _rate_limit(self, client_ip: str) -> None:
        now = time.monotonic()
        cutoff = now - self.rate_window_seconds
        bucket = [item for item in self.rate_buckets.get(client_ip, []) if item >= cutoff]
        if len(bucket) >= self.rate_limit_per_ip:
            raise ApiError("rate_limited")
        bucket.append(now)
        self.rate_buckets[client_ip] = bucket
        if len(self.rate_buckets) > 512:
            self.rate_buckets = {
                key: values
                for key, values in self.rate_buckets.items()
                if values and values[-1] >= cutoff
            }

    def _authorized_run(self, run_id: str, capability: str) -> RunRecord:
        if not self.authorize(run_id, capability):
            raise ApiError("unauthorized")
        return self.runs[run_id]

    def _terminal(self, run: RunRecord, status: str) -> None:
        run.status = status
        run.events.append(
            {
                "id": len(run.events) + 1,
                "type": "terminal",
                "step": "terminal",
                "payload": {"status": status},
            }
        )


def encode_sse(events: list[dict[str, Any]]) -> str:
    return "".join(
        f"id: {event['id']}\nevent: {event['type']}\ndata: "
        f"{json.dumps(event['payload'], sort_keys=True, ensure_ascii=True)}\n\n"
        for event in events
    )


def _hash_capability(capability: str) -> str:
    return hashlib.sha256(capability.encode("utf-8")).hexdigest()


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe = {}
    for key, value in payload.items():
        if key in {"sql", "capability", "credential", "password"}:
            continue
        safe[key] = value
    return safe

"""FastAPI adapter for the G4 run API; serves only the built frontend."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from sqlwarden.api import MAX_EVENTS_PER_RUN, TERMINAL, ApiError, RunService, encode_sse

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"
STATUS_CODES = {
    "unauthorized": 401,
    "origin_refused": 403,
    "body_too_large": 413,
    "rate_limited": 429,
    "overloaded": 503,
}
Readiness = Callable[[], Awaitable[str | None]]


def create_app(
    service: RunService,
    *,
    web_root: Path | None = WEB_DIST,
    readiness: Readiness | None = None,
    heartbeat_seconds: float = 15.0,
    poll_seconds: float = 0.1,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        service.mark_interrupted()

    app = FastAPI(title="SQLWarden local API", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(ApiError)
    async def api_error(_request: Request, error: ApiError) -> JSONResponse:
        reason = str(error)
        headers = {"Retry-After": "10"} if reason in {"overloaded", "rate_limited"} else None
        return JSONResponse(
            {"status": "failed", "reason": reason},
            status_code=STATUS_CODES.get(reason, 400),
            headers=headers,
        )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/ready")
    async def ready() -> JSONResponse:
        reason = await readiness() if readiness else None
        if reason:
            return JSONResponse({"status": "not_ready", "reason": reason}, status_code=503)
        return JSONResponse({"status": "ready"})

    @app.get("/api/databases")
    async def databases() -> dict[str, list[str]]:
        return {"databases": sorted(service.allowed_dbs)}

    @app.post("/api/ask", status_code=202)
    async def ask(request: Request) -> dict[str, str]:
        body = await _json_body(request, service.max_body_bytes)
        created = service.create_run(
            body,
            origin=request.headers.get("origin"),
            client_ip=request.client.host if request.client else "unknown",
        )
        service.start(created["run_id"])
        return created

    @app.get("/api/runs/{run_id}")
    async def run_status(run_id: str, request: Request) -> dict[str, Any]:
        return service.status(run_id, _bearer(request))

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str, request: Request) -> StreamingResponse:
        token = _bearer(request)
        after = _last_event_id(request.headers.get("last-event-id"))
        service.events(run_id, token, after_id=after)

        async def stream():
            nonlocal after
            beat = time.monotonic()
            deadline = beat + service.run_timeout_seconds + 30
            while time.monotonic() < deadline:
                try:
                    events = service.events(run_id, token, after_id=after)
                    status = service.runs[run_id].status
                except (ApiError, KeyError):
                    return
                if events:
                    yield encode_sse(events)
                    after = events[-1]["id"]
                    beat = time.monotonic()
                if status in TERMINAL or status == "needs_clarification":
                    return
                if await request.is_disconnected():
                    return
                if time.monotonic() - beat >= heartbeat_seconds:
                    yield ": heartbeat\n\n"
                    beat = time.monotonic()
                await asyncio.sleep(poll_seconds)

        return StreamingResponse(
            stream(), media_type="text/event-stream", headers={"Cache-Control": "no-store"}
        )

    @app.post("/api/runs/{run_id}/cancel")
    async def cancel_run(run_id: str, request: Request) -> dict[str, str]:
        return service.cancel(run_id, _bearer(request))

    @app.post("/api/runs/{run_id}/clarification", status_code=202)
    async def clarify_run(run_id: str, request: Request) -> dict[str, str]:
        token = _bearer(request)
        body = await _json_body(request, service.max_body_bytes)
        return await service.clarify(run_id, token, body)

    @app.get("/api/attacks")
    async def attacks() -> dict[str, Any]:
        manifest = _load_json(ROOT / "docs/attack-suite-manifest.json")
        return {
            "mode": "all_layers_on",
            "attacks": [
                {key: item[key] for key in ("id", "threat_id", "observed_layer", "outcome")}
                | {"predicate": item["success_predicate"], "config": item["seed_configuration"]}
                for item in manifest["attacks"]
            ],
            "false_blocks": manifest["false_block_measurement"],
            "layer_off": manifest["e5_layer_off_policy"]["status"],
        }

    @app.get("/api/benchmark")
    async def benchmark() -> dict[str, Any]:
        dashboard = _load_json(ROOT / "results/E0_smoke/dashboard.json")
        return {
            "status": "ok",
            "models": dashboard["models"],
            "paired": dashboard["paired"],
            "excludes": dashboard["excludes"],
            "claim": "local_development_slice_not_official_benchmark",
        }

    if web_root is not None and web_root.is_dir():
        app.mount("/", StaticFiles(directory=web_root, html=True), name="web")
    return app


async def _json_body(request: Request, limit: int) -> Any:
    declared = request.headers.get("content-length")
    if declared is not None and (not declared.isdigit() or int(declared) > limit):
        raise ApiError("body_too_large")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > limit:
            raise ApiError("body_too_large")
    try:
        return json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise ApiError("body_invalid") from None


def _bearer(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise ApiError("unauthorized")
    return header.removeprefix("Bearer ").strip()


def _last_event_id(value: str | None) -> int:
    if value and value.isdigit() and int(value) <= MAX_EVENTS_PER_RUN + 1:
        return int(value)
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

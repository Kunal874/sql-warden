"""Scripted local G4 smoke without starting a network server."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlwarden.api import RunService

ROOT = Path(__file__).resolve().parents[1]


async def _runner(run):
    await run.event("validate", "ok")
    await run.event("terminal", "answered", {"rows": [[1]], "preview_truncated": False})


async def _clarification_runner(run):
    await run.event(
        "clarify",
        "needs_clarification",
        {"question": "Which field?", "options": [{"id": "name", "text": "Name"}]},
    )


async def _continuation_runner(run):
    await run.event("terminal", "answered", {"rows": [["School name"]], "preview_truncated": False})


async def _flows() -> tuple[str, str]:
    service = RunService(runner=_runner)
    created = service.create_run({"db_id": "california_schools", "question": "How many rows?"})
    result = await service.wait(created["run_id"])
    clarification_service = RunService(
        runner=_clarification_runner,
        continuation_runner=_continuation_runner,
    )
    pending = clarification_service.create_run(
        {"db_id": "california_schools", "question": "Which school?"}
    )
    await clarification_service.wait(pending["run_id"])
    await clarification_service.clarify(
        pending["run_id"], pending["capability"], {"option_id": "name"}
    )
    clarified = await clarification_service.wait(pending["run_id"])
    return result["status"], clarified["status"]


def main() -> int:
    pages = sorted(path.name for path in (ROOT / "web").glob("*.html"))
    run_status, clarification_status = asyncio.run(_flows())
    print("pages=" + ",".join(pages))
    print("api_run_status=" + run_status)
    print("api_clarification_status=" + clarification_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

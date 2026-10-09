"""Scripted local G4 smoke without starting a network server."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlwarden.api import RunService

ROOT = Path(__file__).resolve().parents[1]


async def _runner(run):
    await run.event("validate", "ok")
    await run.event("terminal", "answered", {"rows": [[1]], "preview_truncated": False})


def main() -> int:
    pages = sorted(path.name for path in (ROOT / "web").glob("*.html"))
    service = RunService(runner=_runner)
    created = service.create_run({"db_id": "california_schools", "question": "How many rows?"})
    result = asyncio.run(service.wait(created["run_id"]))
    print("pages=" + ",".join(pages))
    print("api_run_status=" + result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

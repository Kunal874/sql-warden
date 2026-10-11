import json
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.smoke_g4_local import run_smoke
from sqlwarden.api import RunService
from sqlwarden.webapp import create_app

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("main.tsx", "api.ts", "Ask.tsx", "AttackLab.tsx", "Benchmark.tsx")


def test_react_pages_cover_required_states_without_raw_html_or_url_tokens():
    sources = {name: (ROOT / "web/src" / name).read_text(encoding="utf-8") for name in SOURCES}
    text = "\n".join(sources.values())

    assert "dangerouslySetInnerHTML" not in text and "innerHTML" not in text
    assert "EventSource" not in text
    assert "Authorization: `Bearer ${" in sources["api.ts"]
    for state in (
        "loading",
        "overload",
        "model-unavailable",
        "interrupted",
        "empty",
        "truncated",
        "blocked",
        "abstained",
    ):
        assert state in sources["Ask.tsx"], state
    assert "not a probability" in sources["Ask.tsx"]
    assert "Not an official BIRD score" in sources["Benchmark.tsx"]
    assert "observed" in sources["AttackLab.tsx"]


def test_vite_react_package_is_locked_to_approved_stack():
    package = json.loads((ROOT / "web/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "web/package-lock.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["scripts"] == {"typecheck": "tsc --noEmit", "build": "vite build"}
    assert set(package["dependencies"]) == {"react", "react-dom", "recharts"}
    assert set(package["devDependencies"]) == {
        "@types/react",
        "@types/react-dom",
        "typescript",
        "vite",
    }
    assert lock["packages"][""]["dependencies"] == package["dependencies"]


async def _clarifying(run):
    await run.event(
        "clarify",
        "needs_clarification",
        {"question": "Which?", "options": [{"id": "A", "text": "the count"}]},
    )


async def _answer(run):
    await run.event("terminal", "answered", {"rows": [[3]], "row_count": 1, "agreement": 1.0})


def test_smoke_flow_covers_ask_clarification_result_and_cancel(tmp_path):
    (tmp_path / "index.html").write_text('<div id="root"></div>', encoding="utf-8")
    service = RunService(runner=_clarifying, continuation_runner=_answer)
    with TestClient(create_app(service, web_root=tmp_path)) as client:
        report = run_smoke(
            client, db_id="california_schools", question="How many?", origin="http://localhost:5173"
        )

    assert report["index_served"] and report["source_hidden"]
    assert report["ask_status_code"] == 202
    assert report["clarification"] == {"options": 1, "reply": ["option_id"], "status_code": 202}
    assert report["run"]["status"] == "answered"
    assert report["run"]["steps"][-1] == "terminal"
    assert report["cancel_status"] == "cancelled"

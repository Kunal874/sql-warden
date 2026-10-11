import asyncio

from fastapi.testclient import TestClient

from sqlwarden.api import RunService
from sqlwarden.webapp import create_app

ASK = {"db_id": "california_schools", "question": "How many rows?"}
ORIGIN = {"origin": "http://localhost:5173"}


async def answered_runner(run):
    await run.event("validate", "ok")
    await run.event("terminal", "answered", {"rows": [[1]], "preview_truncated": False})


async def waiting_runner(run):
    await run.event("validate", "ok")
    await asyncio.Event().wait()


async def clarification_runner(run):
    await run.event(
        "clarify",
        "needs_clarification",
        {"question": "Which field?", "options": [{"id": "name", "text": "Name"}]},
    )


async def continuation_runner(run):
    await run.event("terminal", "answered", {"rows": [["School name"]], "preview_truncated": False})


def _client(service, **kwargs):
    return TestClient(create_app(service, web_root=None, **kwargs))


def _bearer(created):
    return {"authorization": "Bearer " + created["capability"]}


def _stream(client, url, headers):
    with client.stream("GET", url, headers=headers) as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-store"
        return "".join(response.iter_text())


def test_ask_returns_202_and_streams_events_until_terminal():
    with _client(RunService(runner=answered_runner)) as client:
        created = client.post("/api/ask", json=ASK, headers=ORIGIN)
        assert created.status_code == 202
        body = created.json()
        assert body["run_id"] and body["capability"]

        text = _stream(client, f"/api/runs/{body['run_id']}/events", _bearer(body))
        assert "event: terminal" in text
        assert '"answered"' in text
        assert body["capability"] not in text

        status = client.get(f"/api/runs/{body['run_id']}", headers=_bearer(body)).json()
        assert status["status"] == "answered"
        assert status["result"]["rows"] == [[1]]

        replay = _stream(
            client,
            f"/api/runs/{body['run_id']}/events",
            _bearer(body) | {"last-event-id": "2"},
        )
        assert "id: 2\n" not in replay
        assert "id: 3\n" in replay

        cancel = client.post(f"/api/runs/{body['run_id']}/cancel", headers=_bearer(body))
        assert cancel.json()["status"] == "answered"


def test_stream_sends_heartbeats_and_ends_with_run_timeout():
    service = RunService(runner=waiting_runner, run_timeout_seconds=0.3)
    with _client(service, heartbeat_seconds=0.05, poll_seconds=0.01) as client:
        created = client.post("/api/ask", json=ASK).json()
        text = _stream(client, f"/api/runs/{created['run_id']}/events", _bearer(created))
        assert ": heartbeat" in text
        assert '"run_timeout"' in text


def test_requests_fail_closed_before_any_work():
    calls = []

    async def counting_runner(run):
        calls.append(run.run_id)
        await answered_runner(run)

    service = RunService(runner=counting_runner, max_body_bytes=90)
    with _client(service) as client:
        bad_origin = client.post("/api/ask", json=ASK, headers={"origin": "http://evil.example"})
        assert (bad_origin.status_code, bad_origin.json()["reason"]) == (403, "origin_refused")

        too_large = client.post(
            "/api/ask",
            content=b'{"db_id":"california_schools","question":"' + b"x" * 200 + b'"}',
            headers={"content-type": "application/json"},
        )
        assert too_large.status_code == 413

        not_object = client.post("/api/ask", json=["california_schools"])
        assert (not_object.status_code, not_object.json()["reason"]) == (400, "body_invalid")
        not_json = client.post("/api/ask", content=b"{", headers={"content-type": "text/plain"})
        assert (not_json.status_code, not_json.json()["reason"]) == (400, "body_invalid")

        created = client.post("/api/ask", json=ASK).json()
        for url in (
            f"/api/runs/{created['run_id']}",
            f"/api/runs/{created['run_id']}/events",
        ):
            assert client.get(url).status_code == 401
            assert client.get(url, headers={"authorization": "Bearer wrong"}).status_code == 401
        unknown = client.get("/api/runs/unknown", headers=_bearer(created))
        assert unknown.status_code == 401
    assert calls == [created["run_id"]]


def test_overload_is_rejected_promptly_with_retry_hint():
    service = RunService(runner=waiting_runner, max_active=1)
    with _client(service) as client:
        assert client.post("/api/ask", json=ASK).status_code == 202
        overloaded = client.post("/api/ask", json=ASK)
        assert overloaded.status_code == 503
        assert overloaded.headers["retry-after"]


def test_shutdown_marks_unfinished_runs_interrupted():
    service = RunService(runner=waiting_runner)
    with _client(service) as client:
        created = client.post("/api/ask", json=ASK).json()
    assert service.runs[created["run_id"]].status == "interrupted"


def test_clarification_endpoint_resumes_once_and_cancels_cleanly():
    service = RunService(runner=clarification_runner, continuation_runner=continuation_runner)
    with _client(service) as client:
        created = client.post("/api/ask", json=ASK).json()
        url = f"/api/runs/{created['run_id']}"
        text = _stream(client, url + "/events", _bearer(created))
        assert '"needs_clarification"' in text

        pending = client.get(url, headers=_bearer(created)).json()
        assert pending["clarification"]["options"] == [{"id": "name", "text": "Name"}]
        refused = client.post(
            url + "/clarification",
            json={"option_id": "name", "db_id": "toxicology"},
            headers=_bearer(created),
        )
        assert refused.json()["reason"] == "clarification_boundary_refused"

        accepted = client.post(
            url + "/clarification", json={"option_id": "name"}, headers=_bearer(created)
        )
        assert (accepted.status_code, accepted.json()["status"]) == (202, "running")
        duplicate = client.post(
            url + "/clarification", json={"option_id": "name"}, headers=_bearer(created)
        )
        assert duplicate.json()["reason"] == "clarification_not_pending"

        resumed = _stream(client, url + "/events", _bearer(created) | {"last-event-id": "3"})
        assert '"answered"' in resumed


def test_info_routes_are_sanitized_and_static_serves_only_the_build(tmp_path):
    (tmp_path / "index.html").write_text("<div id=root></div>", encoding="utf-8")
    with TestClient(create_app(RunService(runner=answered_runner), web_root=tmp_path)) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.get("/api/ready").json()["status"] == "ready"
        assert client.get("/api/databases").json()["databases"] == ["california_schools"]
        attacks = client.get("/api/attacks").json()
        assert attacks["mode"] == "all_layers_on"
        assert attacks["attacks"]
        assert all("sql" not in item for item in attacks["attacks"])
        benchmark = client.get("/api/benchmark").json()
        assert benchmark["models"]["arctic"]["ex"] == 0.22
        assert "credentials" in benchmark["excludes"]
        assert client.get("/").text == "<div id=root></div>"
        assert client.get("/package.json").status_code == 404


def test_readiness_reports_unavailable_dependencies():
    async def not_ready():
        return "model_unavailable"

    with TestClient(
        create_app(RunService(runner=answered_runner), web_root=None, readiness=not_ready)
    ) as client:
        ready = client.get("/api/ready")
        assert (ready.status_code, ready.json()) == (
            503,
            {"status": "not_ready", "reason": "model_unavailable"},
        )

import asyncio

import pytest

from sqlwarden import api


async def answered_runner(run):
    await run.event("validate", "ok")
    await run.event("terminal", "answered", {"rows": [[1]], "preview_truncated": False})


async def waiting_runner(run):
    await run.event("validate", "ok")
    await asyncio.Event().wait()


def test_run_creation_uses_capability_hashes_and_sanitized_events():
    service = api.RunService(runner=answered_runner, allowed_origins={"http://localhost:5173"})
    created = service.create_run(
        {"db_id": "california_schools", "question": "How many schools?"},
        origin="http://localhost:5173",
        client_ip="127.0.0.1",
    )

    assert created["status"] == "created"
    assert created["run_id"]
    assert created["capability"]
    assert created["capability"] not in repr(service)
    assert service.authorize(created["run_id"], created["capability"]) is True
    assert service.authorize(created["run_id"], "wrong") is False

    result = asyncio.run(service.wait(created["run_id"]))
    assert result["status"] == "answered"
    replay = service.events(created["run_id"], created["capability"], after_id=0)
    assert [event["id"] for event in replay] == [1, 2, 3]
    assert replay[-1]["type"] == "terminal"
    assert "capability" not in str(replay)


def test_request_limits_cors_db_allowlist_and_rate_limit_are_fail_closed():
    service = api.RunService(
        runner=answered_runner,
        allowed_origins={"http://localhost:5173"},
        rate_limit_per_ip=2,
        max_body_bytes=80,
    )

    with pytest.raises(api.ApiError, match="origin_refused"):
        service.create_run({"db_id": "california_schools", "question": "x"}, origin="bad")

    with pytest.raises(api.ApiError, match="db_refused"):
        service.create_run({"db_id": "other", "question": "x"}, origin="http://localhost:5173")

    with pytest.raises(api.ApiError, match="body_too_large"):
        service.create_run(
            {"db_id": "california_schools", "question": "x" * 100},
            origin="http://localhost:5173",
            client_ip="1.1.1.1",
        )

    for _ in range(2):
        service.create_run(
            {"db_id": "california_schools", "question": "x"},
            origin="http://localhost:5173",
            client_ip="2.2.2.2",
        )
    with pytest.raises(api.ApiError, match="rate_limited"):
        service.create_run(
            {"db_id": "california_schools", "question": "x"},
            origin="http://localhost:5173",
            client_ip="2.2.2.2",
        )


def test_admission_cancel_replay_and_restart_interrupt_unfinished_runs():
    service = api.RunService(runner=waiting_runner, max_active=1)
    first = service.create_run({"db_id": "california_schools", "question": "x"})
    with pytest.raises(api.ApiError, match="overloaded"):
        service.create_run({"db_id": "california_schools", "question": "y"})

    assert service.cancel(first["run_id"], first["capability"])["status"] == "cancelled"
    assert (
        service.events(first["run_id"], first["capability"], after_id=1)[-1]["type"] == "terminal"
    )

    second = service.create_run({"db_id": "california_schools", "question": "z"})
    service.mark_interrupted()
    interrupted = service.events(second["run_id"], second["capability"], after_id=0)[-1]
    assert interrupted["type"] == "terminal"
    assert interrupted["payload"]["status"] == "interrupted"


def test_sse_encoding_is_header_token_friendly_and_replayable():
    service = api.RunService(runner=answered_runner)
    created = service.create_run({"db_id": "california_schools", "question": "x"})
    asyncio.run(service.wait(created["run_id"]))

    text = api.encode_sse(service.events(created["run_id"], created["capability"], after_id=1))

    assert "id: 2" in text
    assert "event: progress" in text
    assert created["capability"] not in text

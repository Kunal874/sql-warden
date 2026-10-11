import asyncio

import pytest

from sqlwarden import api

ASK = {"db_id": "california_schools", "question": "How many schools?"}


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
        {"question": "Which school field?", "options": [{"id": "name", "text": "Name"}]},
    )


async def continuation_runner(run):
    assert run.clarification == {"option_id": "name", "text": "Name"}
    await run.event("terminal", "answered", {"rows": [["School name"]], "preview_truncated": False})


async def chatty_runner(run):
    for _ in range(api.MAX_EVENTS_PER_RUN + 5):
        await run.event("progress", "running")


def test_run_creation_uses_capability_hashes_and_sanitized_events():
    service = api.RunService(runner=answered_runner, allowed_origins={"http://localhost:5173"})
    created = service.create_run(ASK, origin="http://localhost:5173", client_ip="127.0.0.1")

    assert created["status"] == "created"
    assert created["run_id"]
    assert created["capability"]
    assert created["capability"] not in repr(service)
    assert service.authorize(created["run_id"], created["capability"]) is True
    assert service.authorize(created["run_id"], "wrong") is False
    assert service.authorize("unknown", created["capability"]) is False

    result = asyncio.run(service.wait(created["run_id"]))
    assert result["status"] == "answered"
    replay = service.events(created["run_id"], created["capability"], after_id=0)
    assert [event["id"] for event in replay] == [1, 2, 3]
    assert replay[-1]["type"] == "terminal"
    assert "capability" not in str(replay)


def test_request_limits_origin_db_allowlist_and_rate_limit_are_fail_closed():
    service = api.RunService(
        runner=answered_runner,
        allowed_origins={"http://localhost:5173"},
        rate_limit_per_ip=2,
        max_body_bytes=80,
    )

    with pytest.raises(api.ApiError, match="origin_refused"):
        service.create_run({"db_id": "california_schools", "question": "x"}, origin="bad")
    with pytest.raises(api.ApiError, match="body_invalid"):
        service.create_run(["california_schools"], origin=None)
    with pytest.raises(api.ApiError, match="db_refused"):
        service.create_run({"db_id": "other", "question": "x"}, origin="http://localhost:5173")
    with pytest.raises(api.ApiError, match="input_invalid"):
        service.create_run({"db_id": "california_schools", "question": " "})
    with pytest.raises(api.ApiError, match="body_too_large"):
        service.create_run(
            {"db_id": "california_schools", "question": "x" * 100},
            origin="http://localhost:5173",
            client_ip="1.1.1.1",
        )

    for _ in range(2):
        service.create_run(
            {"db_id": "california_schools", "question": "x"},
            origin=None,
            client_ip="2.2.2.2",
        )
    with pytest.raises(api.ApiError, match="rate_limited"):
        service.create_run({"db_id": "california_schools", "question": "x"}, client_ip="2.2.2.2")


def test_rate_limit_buckets_are_capped_and_fail_closed_when_full():
    service = api.RunService(runner=answered_runner, max_active=10_000, max_rate_buckets=3)
    for index in range(3):
        service.create_run(ASK, client_ip=f"10.0.0.{index}")
    with pytest.raises(api.ApiError, match="rate_limited"):
        service.create_run(ASK, client_ip="10.0.0.99")
    assert len(service.rate_buckets) == 3


def test_admission_cancel_replay_and_restart_interrupt_unfinished_runs():
    async def scenario():
        service = api.RunService(runner=waiting_runner, max_active=1)
        first = service.create_run(ASK)
        service.start(first["run_id"])
        await asyncio.sleep(0)
        with pytest.raises(api.ApiError, match="overloaded"):
            service.create_run(ASK)

        assert service.cancel(first["run_id"], first["capability"])["status"] == "cancelled"
        await service.wait(first["run_id"])
        cancelled = service.events(first["run_id"], first["capability"], after_id=0)
        assert cancelled[-1]["type"] == "terminal"
        assert [event["payload"]["status"] for event in cancelled].count("cancelled") == 1

        second = service.create_run(ASK)
        service.start(second["run_id"])
        await asyncio.sleep(0)
        service.mark_interrupted()
        await service.wait(second["run_id"])
        interrupted = service.events(second["run_id"], second["capability"], after_id=0)
        assert interrupted[-1]["type"] == "terminal"
        assert interrupted[-1]["payload"]["status"] == "interrupted"
        assert service.cancel(second["run_id"], second["capability"])["status"] == "interrupted"

    asyncio.run(scenario())


def test_start_is_idempotent_and_never_duplicates_work():
    calls = []

    async def counting_runner(run):
        calls.append(run.run_id)
        await run.event("terminal", "answered")

    async def scenario():
        service = api.RunService(runner=counting_runner)
        created = service.create_run(ASK)
        service.start(created["run_id"])
        service.start(created["run_id"])
        await service.wait(created["run_id"])
        await service.wait(created["run_id"])
        assert calls == [created["run_id"]]

    asyncio.run(scenario())


def test_total_run_timeout_and_event_cap_end_runs_as_failed():
    async def scenario():
        slow = api.RunService(runner=waiting_runner, run_timeout_seconds=0.01)
        created = slow.create_run(ASK)
        assert (await slow.wait(created["run_id"]))["status"] == "failed"
        last = slow.events(created["run_id"], created["capability"])[-1]
        assert last["payload"] == {"status": "failed", "reason": "run_timeout"}

        chatty = api.RunService(runner=chatty_runner)
        created = chatty.create_run(ASK)
        assert (await chatty.wait(created["run_id"]))["status"] == "failed"
        events = chatty.events(created["run_id"], created["capability"])
        assert len(events) <= api.MAX_EVENTS_PER_RUN + 1
        assert events[-1]["payload"]["reason"] == "event_limit"

    asyncio.run(scenario())


def test_terminal_runs_are_retained_with_a_finite_count():
    async def scenario():
        service = api.RunService(runner=answered_runner, max_runs=3, max_active=10)
        created = []
        for _ in range(5):
            run = service.create_run(ASK)
            await service.wait(run["run_id"])
            created.append(run)
        assert len(service.runs) == 3
        assert service.authorize(created[0]["run_id"], created[0]["capability"]) is False
        assert service.authorize(created[-1]["run_id"], created[-1]["capability"]) is True

    asyncio.run(scenario())


def test_sse_encoding_is_header_token_friendly_and_replayable():
    service = api.RunService(runner=answered_runner)
    created = service.create_run(ASK)
    asyncio.run(service.wait(created["run_id"]))

    text = api.encode_sse(service.events(created["run_id"], created["capability"], after_id=1))

    assert "id: 2" in text
    assert "event: progress" in text
    assert '"step": "validate"' in text
    assert created["capability"] not in text


def test_clarification_accepts_one_offered_option_and_rejects_boundary_changes():
    async def scenario():
        service = api.RunService(
            runner=clarification_runner, continuation_runner=continuation_runner
        )
        created = service.create_run(ASK)
        run_id, token = created["run_id"], created["capability"]
        assert (await service.wait(run_id))["status"] == "needs_clarification"

        with pytest.raises(api.ApiError, match="clarification_boundary_refused"):
            await service.clarify(run_id, token, {"option_id": "name", "db_id": "other"})
        with pytest.raises(api.ApiError, match="clarification_invalid"):
            await service.clarify(run_id, token, {"option_id": "not-offered"})
        with pytest.raises(api.ApiError, match="clarification_invalid"):
            await service.clarify(run_id, token, {"option_id": "name", "text": "both"})

        assert (await service.clarify(run_id, token, {"option_id": "name"}))["status"] == (
            "running"
        )
        with pytest.raises(api.ApiError, match="clarification_not_pending"):
            await service.clarify(run_id, token, {"text": "school name"})
        assert (await service.wait(run_id))["status"] == "answered"

    asyncio.run(scenario())


def test_clarification_expires_and_cannot_resume():
    async def scenario():
        service = api.RunService(
            runner=clarification_runner,
            continuation_runner=continuation_runner,
            clarification_ttl_seconds=0,
        )
        created = service.create_run(ASK)
        await service.wait(created["run_id"])
        with pytest.raises(api.ApiError, match="clarification_not_pending"):
            await service.clarify(created["run_id"], created["capability"], {"option_id": "name"})
        assert service.status(created["run_id"], created["capability"])["status"] == "expired"

    asyncio.run(scenario())


def test_free_text_clarification_is_bounded_and_passed_to_continuation():
    seen = {}

    async def text_continuation(run):
        seen.update(run.clarification)
        await run.event("terminal", "abstained", {"reason": "no_majority"})

    async def scenario():
        service = api.RunService(runner=clarification_runner, continuation_runner=text_continuation)
        created = service.create_run(ASK)
        await service.wait(created["run_id"])
        with pytest.raises(api.ApiError, match="clarification_invalid"):
            await service.clarify(created["run_id"], created["capability"], {"text": "x" * 201})
        await service.clarify(created["run_id"], created["capability"], {"text": "school name"})
        assert (await service.wait(created["run_id"]))["status"] == "abstained"
        assert seen == {"option_id": None, "text": "school name"}

    asyncio.run(scenario())


def test_status_reports_terminal_result_without_private_fields():
    async def scenario():
        async def runner(run):
            await run.event(
                "terminal",
                "answered",
                {"sql": "SELECT 1", "rows": [[1]], "capability": "leak", "password": "leak"},
            )

        service = api.RunService(runner=runner)
        created = service.create_run(ASK)
        await service.wait(created["run_id"])
        status = service.status(created["run_id"], created["capability"])
        assert status["status"] == "answered"
        assert status["result"]["sql"] == "SELECT 1"
        assert "leak" not in str(status)

    asyncio.run(scenario())

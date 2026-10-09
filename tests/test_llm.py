import asyncio
import gzip
import json

import httpx
import pytest

from sqlwarden import cli, llm
from sqlwarden.llm import ALIAS, DIGEST, Generation, LocalQwen, _LocalTransport


def payload(content='{"sql":"SELECT 1"}', finish="stop", usage=None):
    return {
        "id": "local-test",
        "object": "chat.completion",
        "created": 0,
        "model": ALIAS,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish,
            }
        ],
        "usage": usage,
    }


def fake_handler(reply, seen, models=None, digest=DIGEST):
    def handle(request):
        seen.append(request)
        path = request.url.path
        if path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": ALIAS, "digest": digest}]})
        if path == "/api/ps":
            current = [{"name": ALIAS, "digest": DIGEST, "context_length": 2048}]
            return httpx.Response(200, json={"models": current if models is None else models})
        if path == "/api/generate":
            return httpx.Response(200, json={"done": True})
        return httpx.Response(200, json=reply)

    return handle


async def test_one_generation_uses_only_fixed_local_transport_and_reports_usage():
    seen = []
    usage = {"prompt_tokens": 80, "completion_tokens": 10, "total_tokens": 90}
    provider = LocalQwen(httpx.MockTransport(fake_handler(payload(usage=usage), seen)))
    result = await provider.generate("Give one constant.")
    assert provider.cleanup_confirmed is True
    assert result == Generation("SELECT 1", "ok", 80, 10, 1, 0)
    requests = [r for r in seen if r.url.path == "/v1/chat/completions"]
    assert len(requests) == 1
    request = requests[0]
    body = json.loads(request.content)
    assert (request.url.host, request.url.port) == ("127.0.0.1", 11434)
    assert body["model"] == ALIAS
    assert (body["max_tokens"], body["temperature"], body["stream"]) == (128, 0, False)
    assert body["response_format"] == {"type": "json_object"}
    assert "tools" not in body and "gold" not in body


async def test_loop_complete_uses_supplied_messages_and_local_contract():
    seen = []
    usage = {"prompt_tokens": 90, "completion_tokens": 12, "total_tokens": 102}
    provider = LocalQwen(httpx.MockTransport(fake_handler(payload(usage=usage), seen)))
    messages = [
        {"role": "system", "content": "Return JSON."},
        {"role": "user", "content": '{"question":"List schools"}'},
    ]

    result = await provider.complete(messages, model_config={"max_tokens": 64})

    assert result["content"] == '{"sql":"SELECT 1"}'
    assert result["usage"] == {"prompt_tokens": 90, "completion_tokens": 12}
    request = [r for r in seen if r.url.path == "/v1/chat/completions"][0]
    body = json.loads(request.content)
    assert body["messages"] == messages
    assert body["max_tokens"] == 64


@pytest.mark.parametrize(
    "content,finish",
    [
        ("not JSON", "stop"),
        ('{"sql":"SELECT 1","extra":1}', "stop"),
        ('{"sql":"SELECT 2","sql":"SELECT 1"}', "stop"),
        ('{"sql":1}', "stop"),
        ('{"sql":""}', "stop"),
        ('{"sql":"SELECT 1"}', "length"),
        ('{"sql":"SELECT 1"}', None),
    ],
)
async def test_malformed_or_incomplete_output_has_no_sql(content, finish):
    seen = []
    result = await LocalQwen(
        httpx.MockTransport(fake_handler(payload(content, finish), seen))
    ).generate("One.")
    assert result.sql is None and result.calls == 1
    assert result.reason in {"model_output_invalid", "model_output_incomplete"}


@pytest.mark.parametrize("change", ["choices", "tool_calls", "function_call", "refusal", "model"])
async def test_wrong_shape_or_model_never_produces_sql(change):
    reply, seen = payload(), []
    if change == "choices":
        reply["choices"] *= 2
    elif change == "tool_calls":
        reply["choices"][0]["message"]["tool_calls"] = [{"id": "x"}]
    elif change == "function_call":
        reply["choices"][0]["message"]["function_call"] = {"name": "x", "arguments": "{}"}
    elif change == "refusal":
        reply["choices"][0]["message"]["refusal"] = "Refused."
    else:
        reply["model"] = "another-model"
    assert (
        await LocalQwen(httpx.MockTransport(fake_handler(reply, seen))).generate("One.")
    ).sql is None


@pytest.mark.parametrize("usage", [None, {}, {"prompt_tokens": True, "completion_tokens": -1}])
async def test_unknown_or_malformed_usage_is_unavailable_not_zero(usage):
    result = await LocalQwen(httpx.MockTransport(fake_handler(payload(usage=usage), []))).generate(
        "One."
    )
    assert result.reason == "ok"
    assert result.prompt_tokens is None and result.completion_tokens is None


async def test_changed_pin_or_other_loaded_model_refuses_before_chat():
    for kwargs in ({"digest": "changed"}, {"models": [{"name": "other"}]}):
        seen = []
        result = await LocalQwen(
            httpx.MockTransport(fake_handler(payload(), seen, **kwargs))
        ).generate("One.")
        assert result.reason == "model_configuration" and result.calls == 0
        assert all(r.url.path != "/v1/chat/completions" for r in seen)


async def test_prompt_limit_refuses_without_network():
    async def no_network(request):
        raise AssertionError("Prompt overflow reached transport")

    result = await LocalQwen(httpx.MockTransport(no_network)).generate("x" * 2000)
    assert result == Generation(None, "prompt_limit")


@pytest.mark.parametrize("status", [429, 500, 302])
async def test_failed_chat_is_not_retried_or_redirected_and_does_not_echo_body(status, caplog):
    seen = []
    normal = fake_handler(payload(), seen)

    def handle(request):
        if request.url.path == "/v1/chat/completions":
            seen.append(request)
            return httpx.Response(
                status,
                headers={"Location": "https://example.com"},
                json={"error": {"message": "PRIVATE_CANARY"}},
            )
        return normal(request)

    result = await LocalQwen(httpx.MockTransport(handle)).generate("One.")
    assert result.sql is None and result.calls == 1
    assert len([r for r in seen if r.url.path == "/v1/chat/completions"]) == 1
    assert "PRIVATE_CANARY" not in repr(result) + caplog.text


async def test_transport_rejects_nonlocal_oversize_and_compressed_bodies():
    for url, headers, body in [
        ("https://example.com/v1/chat/completions", {}, b"x"),
        ("http://127.0.0.1:11434/api/ps", {}, b"x" * 65537),
        ("http://127.0.0.1:11434/api/ps", {"Content-Encoding": "gzip"}, gzip.compress(b"x")),
    ]:
        transport = _LocalTransport(
            httpx.MockTransport(
                lambda r, headers=headers, body=body: httpx.Response(
                    200, headers=headers, content=body
                )
            )
        )
        async with httpx.AsyncClient(transport=transport, trust_env=False) as client:
            with pytest.raises(ValueError):
                await client.get(url)


async def test_cancellation_propagates_instead_of_becoming_a_failed_generation():
    entered = asyncio.Event()

    async def wait(request):
        entered.set()
        await asyncio.Event().wait()

    task = asyncio.create_task(LocalQwen(httpx.MockTransport(wait)).generate("One."))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_empty_server_has_exactly_one_preload_before_one_chat():
    seen, ps_calls = [], 0
    normal = fake_handler(payload(), seen)

    def handle(request):
        nonlocal ps_calls
        if request.url.path == "/api/ps":
            ps_calls += 1
            if ps_calls == 1:
                seen.append(request)
                return httpx.Response(200, json={"models": []})
        return normal(request)

    result = await LocalQwen(httpx.MockTransport(handle)).generate("One.")
    assert (result.calls, result.warmups, result.reason) == (1, 1, "ok")
    loads = [r for r in seen if r.url.path == "/api/generate"]
    assert len(loads) == 1
    assert json.loads(loads[0].content)["prompt"] == ""


async def test_transport_timeout_is_fixed_and_not_retried():
    seen = []
    normal = fake_handler(payload(), seen)

    def handle(request):
        if request.url.path == "/v1/chat/completions":
            seen.append(request)
            raise httpx.ReadTimeout("PRIVATE_CANARY", request=request)
        return normal(request)

    result = await LocalQwen(httpx.MockTransport(handle)).generate("One.")
    assert result.sql is None and result.calls == 1
    assert "PRIVATE_CANARY" not in repr(result)
    assert result.reason == "model_timeout"


async def test_missing_pin_and_wrong_running_context_fail_before_generation():
    for current in ([], [{"name": ALIAS, "digest": DIGEST, "context_length": 4096}]):
        seen = []
        normal = fake_handler(payload(), seen)

        def handle(request, current=current, seen=seen, normal=normal):
            if request.url.path == "/api/tags" and not current:
                seen.append(request)
                return httpx.Response(200, json={"models": []})
            if request.url.path == "/api/ps":
                seen.append(request)
                return httpx.Response(200, json={"models": current})
            return normal(request)

        result = await LocalQwen(httpx.MockTransport(handle)).generate("One.")
        assert result.reason == "model_configuration" and result.calls == 0


async def test_default_factories_disable_proxies_redirects_and_transport_retries(monkeypatch):
    recorded, seen = {}, []
    original_client = httpx.AsyncClient

    def transport(**kwargs):
        recorded["transport"] = kwargs
        return httpx.MockTransport(fake_handler(payload(), seen))

    class RecordedClient(original_client):
        def __init__(self, **kwargs):
            recorded["client"] = kwargs
            super().__init__(**kwargs)

    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:8888")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:8888")
    monkeypatch.setattr(llm.httpx, "AsyncHTTPTransport", transport)
    monkeypatch.setattr(llm.httpx, "AsyncClient", RecordedClient)
    assert (await LocalQwen().generate("One.")).reason == "ok"
    assert recorded["transport"] == {"retries": 0, "trust_env": False}
    assert recorded["client"]["trust_env"] is False
    assert recorded["client"]["follow_redirects"] is False
    assert all(r.headers["accept-encoding"] == "identity" for r in seen)


async def test_streamed_response_cap_closes_before_consuming_the_remainder():
    class Chunks(httpx.AsyncByteStream):
        def __init__(self):
            self.chunks = 0
            self.closed = False

        async def __aiter__(self):
            for chunk in (b"x" * 65536, b"x", b"never-consumed"):
                self.chunks += 1
                yield chunk

        async def aclose(self):
            self.closed = True

    stream = Chunks()
    transport = _LocalTransport(httpx.MockTransport(lambda r: httpx.Response(200, stream=stream)))
    async with httpx.AsyncClient(transport=transport, trust_env=False) as client:
        with pytest.raises(ValueError, match="response_limit"):
            await client.get("http://127.0.0.1:11434/api/ps")
    assert stream.chunks == 2 and stream.closed is True


@pytest.mark.parametrize(
    "path,deadline,calls", [("/api/tags", 90, 0), ("/v1/chat/completions", 60, 1)]
)
async def test_readiness_and_generation_deadlines_are_finite_and_not_retried(
    path, deadline, calls, monkeypatch
):
    seen = []
    entered = asyncio.Event()
    normal = fake_handler(payload(), seen)
    original_timeout = asyncio.timeout

    async def handle(request):
        if request.url.path == path:
            seen.append(request)
            entered.set()
            await asyncio.Event().wait()
        return normal(request)

    monkeypatch.setattr(
        llm.asyncio, "timeout", lambda delay: original_timeout(0.05 if delay == deadline else delay)
    )
    provider = LocalQwen(httpx.MockTransport(handle))
    result = await provider.generate("One.")
    assert entered.is_set() and result.reason == "model_timeout"
    assert result.calls == calls and result.sql is None
    assert len([r for r in seen if r.url.path == path]) == 1
    assert provider.cleanup_confirmed is True


async def test_cancellation_during_client_cleanup_propagates():
    entered = asyncio.Event()

    class WaitingClose(httpx.MockTransport):
        async def aclose(self):
            entered.set()
            await asyncio.Event().wait()

    provider = LocalQwen(WaitingClose(fake_handler(payload(), [])))
    task = asyncio.create_task(provider.generate("One."))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert provider.cleanup_confirmed is False


async def test_failed_client_cleanup_is_not_reported_as_confirmed():
    class BrokenClose(httpx.MockTransport):
        async def aclose(self):
            raise RuntimeError("PRIVATE_CANARY")

    provider = LocalQwen(BrokenClose(fake_handler(payload(), [])))
    result = await provider.generate("One.")
    assert result.reason == "ok" and provider.cleanup_confirmed is False
    assert "PRIVATE_CANARY" not in repr(result)


@pytest.mark.parametrize("prompt,output", [(1921, 1), (80, 129)])
async def test_reported_context_or_output_overflow_never_produces_sql(prompt, output):
    usage = {"prompt_tokens": prompt, "completion_tokens": output, "total_tokens": prompt + output}
    provider = LocalQwen(httpx.MockTransport(fake_handler(payload(usage=usage), [])))
    result = await provider.generate("One.")
    assert result.reason == "model_output_invalid" and result.sql is None
    assert (result.prompt_tokens, result.completion_tokens, result.calls) == (prompt, output, 1)


@pytest.mark.parametrize(
    "key,value",
    [
        ("OPENAI_CUSTOM_HEADERS", "X-Private: PRIVATE_CANARY"),
        ("OPENAI_ADMIN_KEY", "PRIVATE_CANARY"),
        ("OPENAI_WEBHOOK_SECRET", "PRIVATE_CANARY"),
    ],
)
async def test_inherited_sdk_private_settings_refuse_before_network(key, value, monkeypatch):
    monkeypatch.setenv(key, value)

    async def no_network(request):
        pytest.fail("Inherited private settings reached transport")

    provider = LocalQwen(httpx.MockTransport(no_network))
    result = await provider.generate("One.")
    assert result == Generation(None, "model_configuration")
    assert provider.cleanup_confirmed is None


@pytest.mark.parametrize(
    "usage,prompt,output",
    [
        ({"prompt_tokens": 1921}, 1921, None),
        ({"completion_tokens": 129}, None, 129),
        ({"prompt_tokens": 1921, "completion_tokens": -1}, 1921, None),
        ({"prompt_tokens": 1921, "completion_tokens": False}, 1921, None),
        ({"prompt_tokens": 1921, "completion_tokens": "bad"}, 1921, None),
        ({"prompt_tokens": -1, "completion_tokens": 129}, None, 129),
        ({"prompt_tokens": True, "completion_tokens": 129}, None, 129),
        ({"prompt_tokens": "bad", "completion_tokens": 129}, None, 129),
    ],
)
async def test_reported_overflow_with_unavailable_counter_never_opens_executor(
    usage, prompt, output, monkeypatch
):
    seen = []
    provider = LocalQwen(httpx.MockTransport(fake_handler(payload(usage=usage), seen)))
    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    answer = await cli.ask_once("One.", "a" * 48, provider)
    assert answer["status"] == "failed" and answer["reason"] == "model_output_invalid"
    assert answer["usage"] == {"prompt_tokens": prompt, "completion_tokens": output}
    assert "sql" not in answer and "rows" not in answer
    assert len([r for r in seen if r.url.path == "/v1/chat/completions"]) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("role", "user"),
        ("role", "system"),
        ("role", "tool"),
        ("role", None),
        ("role", "MISSING"),
        ("tool_calls", {}),
        ("tool_calls", ""),
        ("tool_calls", False),
        ("tool_calls", 0),
        ("function_call", {}),
        ("function_call", ""),
        ("function_call", False),
        ("refusal", 0),
        ("refusal", False),
        ("refusal", {}),
        ("refusal", []),
    ],
)
async def test_malformed_message_envelope_never_opens_executor(field, value, monkeypatch):
    reply, seen = payload(), []
    message = reply["choices"][0]["message"]
    if value == "MISSING":
        message.pop(field)
    else:
        message[field] = value
    provider = LocalQwen(httpx.MockTransport(fake_handler(reply, seen)))
    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    answer = await cli.ask_once("One.", "a" * 48, provider)
    assert answer["status"] == "failed" and answer["reason"] == "model_output_invalid"
    assert "sql" not in answer and "rows" not in answer and answer["model_calls"] == 1


@pytest.mark.parametrize(
    "usage,prompt,output",
    [
        ({"prompt_tokens": 80}, 80, None),
        ({"completion_tokens": 10}, None, 10),
        ({"prompt_tokens": "bad", "completion_tokens": 10}, None, 10),
        ({"prompt_tokens": 80, "completion_tokens": -1}, 80, None),
    ],
)
async def test_partial_usage_keeps_valid_counter_without_inventing_missing_one(
    usage, prompt, output
):
    provider = LocalQwen(httpx.MockTransport(fake_handler(payload(usage=usage), [])))
    assert await provider.generate("One.") == Generation("SELECT 1", "ok", prompt, output, 1, 0)


@pytest.mark.parametrize("field,value", [("tool_calls", []), ("refusal", "")])
async def test_empty_valid_optional_message_fields_still_allow_sql(field, value):
    reply = payload()
    reply["choices"][0]["message"][field] = value
    provider = LocalQwen(httpx.MockTransport(fake_handler(reply, [])))
    assert (await provider.generate("One.")).sql == "SELECT 1"

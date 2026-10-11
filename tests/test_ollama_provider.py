import json

import httpx
import pytest

from sqlwarden.cache import JsonDiskCache
from sqlwarden.evaluation import EvaluationError
from sqlwarden.ollama import ARCTIC, QWEN, OllamaAgentProvider

MESSAGES = [{"role": "system", "content": "s"}, {"role": "user", "content": "q"}]


class FakeOllama:
    def __init__(self, *, loaded=(), digest=None, status=200):
        self.loaded = list(loaded)
        self.digests = {ARCTIC.alias: ARCTIC.digest, QWEN.alias: QWEN.digest}
        if digest:
            self.digests[ARCTIC.alias] = digest
        self.status = status
        self.chats = []
        self.unloads = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            models = [{"name": name, "digest": digest} for name, digest in self.digests.items()]
            return httpx.Response(200, json={"models": models})
        if request.url.path == "/api/ps":
            models = [{"name": name, "size_vram": 5_000_000_000} for name in self.loaded]
            return httpx.Response(200, json={"models": models})
        body = json.loads(request.content)
        if request.url.path == "/api/generate":
            assert body["keep_alive"] == 0
            self.unloads.append(body["model"])
            self.loaded.remove(body["model"])
            return httpx.Response(200, json={"done": True})
        assert request.url.path == "/v1/chat/completions"
        self.chats.append(body)
        if body["model"] not in self.loaded:
            self.loaded.append(body["model"])
        return httpx.Response(
            self.status,
            json={
                "choices": [{"message": {"content": '{"sql":"SELECT 1"}'}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
        )


def _provider(fake, **kwargs):
    return OllamaAgentProvider(transport=httpx.MockTransport(fake.handler), **kwargs)


@pytest.mark.asyncio
async def test_roles_route_to_pinned_models_with_per_candidate_sampling():
    fake = FakeOllama()
    provider = _provider(fake)

    await provider.complete(MESSAGES, model_config={"role": "generate", "candidate_index": 0})
    await provider.complete(MESSAGES, model_config={"role": "generate", "candidate_index": 2})
    await provider.complete(MESSAGES, model_config={"role": "repair", "candidate_index": 2})

    assert [chat["model"] for chat in fake.chats] == [ARCTIC.alias] * 3
    assert [(chat["temperature"], chat["seed"]) for chat in fake.chats] == [
        (0.0, 42),
        (0.7, 44),
        (0.0, 44),
    ]
    assert all("response_format" not in chat for chat in fake.chats)
    assert all(chat["max_tokens"] == ARCTIC.max_output_tokens for chat in fake.chats)
    assert provider.summary()["calls"] == 3
    assert provider.summary()["prompt_tokens"] == 33
    assert provider.summary()["completion_tokens"] == 21


@pytest.mark.asyncio
async def test_helper_role_unloads_the_generator_first_and_records_swap():
    fake = FakeOllama(loaded=[ARCTIC.alias])
    provider = _provider(fake)

    await provider.complete(MESSAGES, model_config={"role": "clarify"})

    assert fake.unloads == [ARCTIC.alias]
    assert fake.chats[0]["model"] == QWEN.alias
    assert fake.chats[0]["response_format"] == {"type": "json_object"}
    assert provider.calls[0]["model"] == "qwen"
    assert provider.calls[0]["swap_seconds"] is not None
    assert fake.loaded == [QWEN.alias]


@pytest.mark.asyncio
async def test_missing_helper_and_wrong_digest_are_refused_without_a_chat_call():
    fake = FakeOllama(digest="0" * 64)
    with pytest.raises(EvaluationError, match="model_configuration"):
        await _provider(fake).complete(MESSAGES, model_config={"role": "generate"})
    with pytest.raises(EvaluationError, match="helper_unavailable"):
        await _provider(FakeOllama(), helper=None).complete(
            MESSAGES, model_config={"role": "clarify"}
        )
    assert fake.chats == []


@pytest.mark.asyncio
async def test_prompt_budget_is_checked_before_sending():
    fake = FakeOllama()
    provider = _provider(fake)
    huge = [{"role": "user", "content": "x" * (ARCTIC.context_tokens * 4)}]

    with pytest.raises(EvaluationError, match="prompt_budget"):
        await provider.complete(huge, model_config={"role": "generate"})

    assert fake.chats == []
    assert provider.calls == [
        {"role": "generate", "model": "arctic", "status": "prompt_budget", "cache_hit": False}
    ]


@pytest.mark.asyncio
async def test_unavailable_model_is_a_stable_reason():
    with pytest.raises(EvaluationError, match="model_unavailable"):
        await _provider(FakeOllama(status=500)).complete(
            MESSAGES, model_config={"role": "generate"}
        )


@pytest.mark.asyncio
async def test_cache_replays_only_the_same_sample(tmp_path):
    fake = FakeOllama()
    cache = JsonDiskCache(tmp_path)
    first = _provider(fake, cache=cache, fingerprints=("a" * 64, "b" * 64))
    await first.complete(MESSAGES, model_config={"role": "generate", "candidate_index": 0})

    replay = _provider(fake, cache=cache, fingerprints=("a" * 64, "b" * 64))
    hit = await replay.complete(MESSAGES, model_config={"role": "generate", "candidate_index": 0})
    await replay.complete(MESSAGES, model_config={"role": "generate", "candidate_index": 1})

    assert hit["content"] == '{"sql":"SELECT 1"}'
    assert [call["cache_hit"] for call in replay.calls] == [True, False]
    assert len(fake.chats) == 2
    assert replay.summary()["cache_hits"] == 1
    assert replay.summary()["live_calls"] == 1

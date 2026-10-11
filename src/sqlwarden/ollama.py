"""Pinned local Ollama models for agent roles, one GPU model loaded at a time."""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import suppress
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

import httpx

from sqlwarden.cache import CacheKey, JsonDiskCache
from sqlwarden.evaluation import EvaluationError, _conservative_token_estimate
from sqlwarden.provider import LOCAL_BASE_URL

SAMPLE_TEMPERATURE = 0.7
BASE_SEED = 42
HELPER_ROLES = frozenset({"clarify", "explain"})


@dataclass(frozen=True, slots=True)
class LocalModel:
    name: str
    alias: str
    digest: str
    context_tokens: int
    max_output_tokens: int


ARCTIC = LocalModel(
    "arctic",
    "sqlwarden-arctic-text2sql-r1-7b-q4km-ctx8192:smoke-v1",
    "d4e34b35065d29da2566b3b201d9e6bd54d005c565e1e182a9e318086168b19d",
    8192,
    3072,
)
# Arctic reasons before its final SQL block (D-075), so it gets a 3072-token output cap.
# Helper output is a short JSON object; a small cap keeps clarification inside ctx2048.
QWEN = LocalModel(
    "qwen",
    "sqlwarden-qwen2.5-coder-7b-ctx2048:smoke-v1",
    "b00066f4a0af314f23919f5644e49e37f8ec7210ecd9cc2ae4236f43ef1d9c2b",
    2048,
    256,
)


class OllamaAgentProvider:
    """Agent provider: generate/repair use the generator, clarify/explain the helper.

    Candidate 0 is greedy; later candidates sample with distinct seeds, so a cached
    candidate can never stand in for another candidate's vote.
    """

    def __init__(
        self,
        *,
        generator: LocalModel = ARCTIC,
        helper: LocalModel | None = QWEN,
        cache: JsonDiskCache | None = None,
        fingerprints: tuple[str, str] = ("unfingerprinted", "unfingerprinted"),
        transport: httpx.AsyncBaseTransport | None = None,
        lock: asyncio.Lock | None = None,
        timeout_seconds: float = 120,
    ) -> None:
        self.generator = generator
        self.helper = helper
        self.cache = cache
        self.schema_sha256, self.data_sha256 = fingerprints
        self.transport = transport
        self.lock = lock or asyncio.Lock()
        self.timeout_seconds = timeout_seconds
        self.calls: list[dict[str, Any]] = []
        self._verified: set[str] = set()

    async def complete(self, messages, *, model_config) -> dict[str, Any]:
        role = model_config.get("role", "generate")
        index = model_config.get("candidate_index", 0)
        model = self.helper if role in HELPER_ROLES else self.generator
        if model is None:
            raise EvaluationError("helper_unavailable")
        call = {"role": role, "model": model.name}
        prompt = json.dumps(messages, ensure_ascii=False)
        if _conservative_token_estimate(prompt) + model.max_output_tokens > model.context_tokens:
            self.calls.append(call | {"status": "prompt_budget", "cache_hit": False})
            raise EvaluationError("prompt_budget")
        seed = BASE_SEED + index
        params = {
            "temperature": SAMPLE_TEMPERATURE if role == "generate" and index > 0 else 0.0,
            "seed": seed,
            "max_tokens": model.max_output_tokens,
        }
        if role in HELPER_ROLES:
            params["response_format"] = {"type": "json_object"}
        key = self._cache_key(model, messages, params, f"{role}:{index}", seed)
        cached = self._cached(key)
        if cached is not None:
            self.calls.append(call | {"status": "ok", "cache_hit": True} | cached["usage"])
            return {"content": cached["content"], "usage": cached["usage"], "cache_hit": True}
        async with self.lock, self._client() as client:
            swap_seconds = await self._prepare(client, model)
            started = time.perf_counter()
            response = await client.post(
                "/v1/chat/completions",
                json={"model": model.alias, "messages": messages, "stream": False} | params,
            )
            seconds = round(time.perf_counter() - started, 3)
            if response.status_code != 200:
                self.calls.append(call | {"status": "model_unavailable", "cache_hit": False})
                raise EvaluationError("model_unavailable")
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            usage = _usage(payload.get("usage"))
            vram = await self._vram(client, model)
        self.calls.append(
            call
            | {"status": "ok", "cache_hit": False, "seconds": seconds}
            | {"swap_seconds": swap_seconds, "vram_bytes": vram}
            | usage
        )
        if self.cache is not None and type(content) is str:
            with suppress(ValueError, FileExistsError):
                self.cache.write(key, {"content": content, "usage": usage})
        return {"content": content, "usage": usage, "seconds": seconds, "cache_hit": False}

    def summary(self) -> dict[str, Any]:
        live = [call for call in self.calls if call["status"] == "ok" and not call["cache_hit"]]

        def total(name: str, rows: list[dict[str, Any]]) -> int | None:
            values = [row.get(name) for row in rows]
            return None if any(value is None for value in values) else sum(values)

        answered = [call for call in self.calls if call["status"] == "ok"]
        return {
            "calls": len(self.calls),
            "live_calls": len(live),
            "cache_hits": sum(1 for call in self.calls if call["cache_hit"]),
            "prompt_tokens": total("prompt_tokens", answered),
            "completion_tokens": total("completion_tokens", answered),
            "live_seconds": round(sum(call["seconds"] for call in live), 3),
            "swap_seconds": round(sum(call.get("swap_seconds") or 0 for call in live), 3),
            "peak_vram_bytes": max((call.get("vram_bytes") or 0 for call in live), default=None),
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=LOCAL_BASE_URL,
            transport=self.transport,
            timeout=httpx.Timeout(self.timeout_seconds, connect=3, pool=3),
            trust_env=False,
            follow_redirects=False,
            headers={"Accept-Encoding": "identity"},
        )

    async def _prepare(self, client: httpx.AsyncClient, model: LocalModel) -> float | None:
        if model.alias not in self._verified:
            tags = (await client.get("/api/tags", timeout=5)).json().get("models", [])
            matches = [item for item in tags if item.get("name") == model.alias]
            if len(matches) != 1 or matches[0].get("digest") != model.digest:
                raise EvaluationError("model_configuration")
            self._verified.add(model.alias)
        others = await self._other_loaded(client, model)
        if not others:
            return None
        started = time.perf_counter()
        for name in others:
            await client.post(
                "/api/generate",
                json={"model": name, "prompt": "", "stream": False, "keep_alive": 0},
            )
        for _ in range(40):
            if not await self._other_loaded(client, model):
                return round(time.perf_counter() - started, 3)
            await asyncio.sleep(0.25)
        raise EvaluationError("another_model_loaded")

    async def _other_loaded(self, client: httpx.AsyncClient, model: LocalModel) -> list[str]:
        loaded = (await client.get("/api/ps", timeout=5)).json().get("models", [])
        return [item["name"] for item in loaded if item.get("name") != model.alias]

    async def _vram(self, client: httpx.AsyncClient, model: LocalModel) -> int | None:
        loaded = (await client.get("/api/ps", timeout=5)).json().get("models", [])
        sizes = [item.get("size_vram") for item in loaded if item.get("name") == model.alias]
        return sizes[0] if sizes and type(sizes[0]) is int else None

    def _cache_key(self, model, messages, params, sample_id, seed) -> CacheKey:
        return CacheKey(
            provider="ollama",
            model=model.alias,
            revision=model.name,
            digest=model.digest,
            template_sha256=_sha(messages[0]["content"] if messages else ""),
            schema_sha256=self.schema_sha256,
            data_sha256=self.data_sha256,
            messages_sha256=_sha(messages),
            params_sha256=_sha(params),
            sample_id=sample_id,
            seed=seed,
        )

    def _cached(self, key: CacheKey) -> dict[str, Any] | None:
        if self.cache is None:
            return None
        try:
            payload = self.cache.read(key)
        except (FileNotFoundError, ValueError):
            return None
        if type(payload.get("content")) is not str or type(payload.get("usage")) is not dict:
            return None
        return payload


def _usage(value: Any) -> dict[str, int | None]:
    value = value if type(value) is dict else {}
    return {
        name: value.get(name) if type(value.get(name)) is int and value.get(name) >= 0 else None
        for name in ("prompt_tokens", "completion_tokens")
    }


def _sha(value: Any) -> str:
    text = value if type(value) is str else json.dumps(value, sort_keys=True, ensure_ascii=False)
    return sha256(text.encode("utf-8")).hexdigest()

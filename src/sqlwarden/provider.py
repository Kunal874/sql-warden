"""Typed local-provider contracts for G1.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

LOCAL_BASE_URL = "http://127.0.0.1:11434"


def local_ollama_config() -> dict[str, Any]:
    return {
        "base_url": LOCAL_BASE_URL,
        "http_retries": 0,
        "sdk_retries": 0,
        "follow_redirects": False,
        "trust_env": False,
    }


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    provider: str
    base_url: str
    model: str
    revision: str
    digest: str
    template_sha256: str
    messages: tuple[tuple[str, str], ...]
    params: dict[str, Any]
    seed: int
    sample_id: str
    retries: int = 0
    http_retries: int = 0
    _params_view: MappingProxyType = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.base_url != LOCAL_BASE_URL or self.retries != 0 or self.http_retries != 0:
            raise ValueError("local provider configuration refused")
        if not all(
            isinstance(value, str) and value
            for value in (
                self.provider,
                self.model,
                self.revision,
                self.digest,
                self.template_sha256,
                self.sample_id,
            )
        ):
            raise ValueError("provider request metadata refused")
        if (
            not isinstance(self.seed, int)
            or not isinstance(self.messages, tuple)
            or not all(
                isinstance(item, tuple)
                and len(item) == 2
                and all(isinstance(part, str) for part in item)
                for item in self.messages
            )
        ):
            raise ValueError("provider request payload refused")
        object.__setattr__(self, "_params_view", MappingProxyType(dict(self.params)))

    def to_cache_material(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "revision": self.revision,
            "digest": self.digest,
            "template_sha256": self.template_sha256,
            "messages": list(self.messages),
            "params": dict(self._params_view),
            "sample_id": self.sample_id,
            "seed": self.seed,
            "retries": self.retries,
            "http_retries": self.http_retries,
        }


@dataclass(frozen=True, slots=True)
class ProviderOutcome:
    status: str
    content_sha256: str
    prompt_tokens: int | None
    completion_tokens: int | None
    provider_calls: int
    cache_hit: bool

    def to_json(self) -> dict[str, Any]:
        if (
            not self.status
            or len(self.content_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.content_sha256)
            or not isinstance(self.provider_calls, int)
            or self.provider_calls < 0
            or not isinstance(self.cache_hit, bool)
        ):
            raise ValueError("provider outcome refused")
        for value in (self.prompt_tokens, self.completion_tokens):
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError("provider outcome refused")
        return {
            "status": self.status,
            "content_sha256": self.content_sha256,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "provider_calls": self.provider_calls,
            "cache_hit": self.cache_hit,
        }

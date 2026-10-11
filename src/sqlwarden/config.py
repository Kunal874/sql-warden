"""Validated execution limits for the early safe slice."""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, fields

# Inference stays on the laptop until a hosted model is approved (D-077).
LOCAL_MODEL_URLS = frozenset(
    {"http://127.0.0.1:11434", "http://localhost:11434", "http://host.docker.internal:11434"}
)
HOST_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}")


def database_address(env: Mapping[str, str] = os.environ) -> tuple[str, int]:
    """Where restricted logins connect: the laptop port, or the compose service name."""
    host = env.get("WARDEN_DB_HOST", "127.0.0.1")
    port = env.get("WARDEN_DB_PORT", "55432")
    if not HOST_NAME.fullmatch(host) or not port.isdigit() or not 0 < int(port) < 65536:
        raise ValueError("database address refused")
    return host, int(port)


def model_url(env: Mapping[str, str] = os.environ) -> str:
    url = env.get("WARDEN_OLLAMA_URL", "http://127.0.0.1:11434")
    if url not in LOCAL_MODEL_URLS:
        raise ValueError("model url refused")
    return url


@dataclass(frozen=True, slots=True)
class QueryLimits:
    """Finite server-owned budgets; bad configuration must fail before a query."""

    max_rows: int = 1000
    max_result_bytes: int = 2 * 1024 * 1024
    max_cell_bytes: int = 64 * 1024
    statement_timeout_ms: int = 5000
    lock_timeout_ms: int = 500
    pool_timeout_ms: int = 5000
    total_timeout_ms: int = 15000
    max_estimated_cost: int = 100000
    max_estimated_rows: int = 100000

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{field.name} must be a positive integer")
        if self.max_cell_bytes > self.max_result_bytes:
            raise ValueError("max_cell_bytes cannot exceed max_result_bytes")
        if self.lock_timeout_ms > self.statement_timeout_ms:
            raise ValueError("lock_timeout_ms cannot exceed statement_timeout_ms")
        for name in ("statement_timeout_ms", "pool_timeout_ms"):
            if getattr(self, name) > self.total_timeout_ms:
                raise ValueError(f"{name} cannot exceed total_timeout_ms")

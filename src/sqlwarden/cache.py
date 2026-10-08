"""Small JSON disk cache for sample-safe provider responses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

FORBIDDEN_TERMS = ("password", "credential", "secret", "gold", "expected_answer")


@dataclass(frozen=True, slots=True)
class CacheKey:
    provider: str
    model: str
    revision: str
    digest: str
    template_sha256: str
    schema_sha256: str
    data_sha256: str
    messages_sha256: str
    params_sha256: str
    sample_id: str
    seed: int

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        if any(
            not isinstance(value, str) or not value for key, value in data.items() if key != "seed"
        ):
            raise ValueError("cache key metadata refused")
        if not isinstance(self.seed, int):
            raise ValueError("cache key seed refused")
        _refuse_forbidden(data)
        return data

    def cache_digest(self) -> str:
        payload = json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class JsonDiskCache:
    def __init__(self, root: Path, *, max_bytes: int = 64 * 1024):
        self.root = root
        self.max_bytes = max_bytes

    def path_for(self, key: CacheKey) -> Path:
        digest = key.cache_digest()
        return self.root / digest[:2] / f"{digest}.json"

    def write(self, key: CacheKey, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ValueError("cache payload refused")
        _refuse_forbidden(payload)
        document = {"key": key.to_json(), "payload": payload}
        encoded = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
        if len(encoded.encode()) > self.max_bytes:
            raise ValueError("cache oversize")
        path = self.path_for(key)
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        if temporary.exists() or temporary.is_symlink():
            raise FileExistsError(temporary)
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise ValueError("cache write failed") from None

    def read(self, key: CacheKey) -> dict[str, Any]:
        path = self.path_for(key)
        if path.is_symlink():
            raise ValueError("cache symlink refused")
        try:
            raw = path.read_bytes()
        except OSError:
            raise FileNotFoundError(path) from None
        if len(raw) > self.max_bytes:
            raise ValueError("cache oversize")
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("cache corrupt") from None
        if document.get("key") != key.to_json() or type(document.get("payload")) is not dict:
            raise ValueError("cache corrupt")
        _refuse_forbidden(document["payload"])
        return document["payload"]


def _refuse_forbidden(value: Any) -> None:
    text = json.dumps(value, sort_keys=True, ensure_ascii=True).lower()
    if any(term in text for term in FORBIDDEN_TERMS):
        raise ValueError("cache secret/gold storage refused")

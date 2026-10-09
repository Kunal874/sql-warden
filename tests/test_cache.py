import json
from dataclasses import replace

import pytest

from sqlwarden.cache import CacheKey, JsonDiskCache


def _key():
    return CacheKey(
        provider="ollama",
        model="model",
        revision="revision",
        digest="digest",
        template_sha256="template",
        schema_sha256="schema",
        data_sha256="data",
        messages_sha256="messages",
        params_sha256="params",
        sample_id="sample",
        seed=42,
    )


def test_cache_key_covers_every_replay_input_and_is_stable():
    key = _key()
    changed = replace(key, seed=43)

    assert key.cache_digest() == _key().cache_digest()
    assert key.cache_digest() != changed.cache_digest()
    assert set(key.to_json()) == {
        "provider",
        "model",
        "revision",
        "digest",
        "template_sha256",
        "schema_sha256",
        "data_sha256",
        "messages_sha256",
        "params_sha256",
        "sample_id",
        "seed",
    }


def test_cache_atomic_no_overwrite_and_exact_replay(tmp_path):
    cache = JsonDiskCache(tmp_path)
    key = _key()
    payload = {"status": "ok", "usage": {"prompt_tokens": 1}}

    cache.write(key, payload)

    assert cache.read(key) == payload
    with pytest.raises(FileExistsError):
        cache.write(key, payload)


def test_cache_refuses_corruption_symlink_oversize_and_secret_gold_storage(tmp_path):
    cache = JsonDiskCache(tmp_path, max_bytes=64)
    key = _key()

    path = cache.path_for(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt"):
        cache.read(key)
    path.unlink()

    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt"):
        cache.read(key)
    path.unlink()

    with pytest.raises(ValueError, match="oversize"):
        cache.write(key, {"content": "x" * 100})
    with pytest.raises(ValueError, match="secret"):
        cache.write(replace(_key(), sample_id="secret"), {"status": "ok"})
    with pytest.raises(ValueError, match="secret"):
        cache.write(_key(), {"gold_sql": "SELECT 1"})

    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    try:
        path.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this host: {exc}")
    with pytest.raises(ValueError, match="symlink"):
        cache.read(key)
    path.unlink()


def test_cache_reads_are_bounded_before_loading_full_file(tmp_path):
    cache = JsonDiskCache(tmp_path, max_bytes=8)
    key = _key()
    path = cache.path_for(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * 128)

    with pytest.raises(ValueError, match="oversize"):
        cache.read(key)


def test_cache_file_contains_no_unbounded_prompt_material(tmp_path):
    cache = JsonDiskCache(tmp_path)
    key = _key()
    cache.write(key, {"status": "ok", "content_sha256": "a" * 64})

    raw = json.loads(cache.path_for(key).read_text(encoding="utf-8"))

    assert "prompt" not in json.dumps(raw).lower()
    assert raw["payload"] == {"status": "ok", "content_sha256": "a" * 64}

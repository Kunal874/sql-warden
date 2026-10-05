import hashlib

import httpx
import pytest

from scripts import fetch_descriptions as fetch
from scripts.inspect_labels import REVISION


def fixture_pins(raw=b"fixture"):
    path = "data/schemas/db/database_description/table.csv"
    return {
        "corrected_revision": REVISION,
        "corrected_description_sources": [
            {
                "path": path,
                "url": fetch.BASE + REVISION + "/" + path,
                "output": "db/table.csv",
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        ],
    }


def test_pinned_download_no_auth_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    requests = []

    def handler(request):
        requests.append(request)
        assert "authorization" not in request.headers
        assert request.headers["accept-encoding"] == "identity"
        return httpx.Response(200, stream=httpx.ByteStream(b"fixture"))

    destination = tmp_path / "release"
    transport = httpx.MockTransport(handler)
    fetch.fetch_descriptions(destination, transport=transport, pins=fixture_pins())
    assert len(requests) == 1
    assert (destination / "db/table.csv").read_bytes() == b"fixture"
    with pytest.raises(ValueError, match="already exists"):
        fetch.fetch_descriptions(destination, transport=transport, pins=fixture_pins())
    assert len(requests) == 1


@pytest.mark.parametrize("mode", ["redirect", "gzip", "overflow", "truncated", "hash", "timeout"])
def test_rejected_body_leaves_no_published_files(tmp_path, mode):
    def handler(request):
        if mode == "redirect":
            return httpx.Response(302, headers={"location": "https://example.invalid"})
        if mode == "gzip":
            return httpx.Response(
                200, headers={"content-encoding": "gzip"}, stream=httpx.ByteStream(b"fixture")
            )
        if mode == "timeout":
            raise httpx.ReadTimeout("test-only", request=request)
        bodies = {"overflow": b"fixture!", "truncated": b"fix", "hash": b"changed"}
        return httpx.Response(200, stream=httpx.ByteStream(bodies[mode]))

    with pytest.raises((ValueError, httpx.HTTPError)):
        fetch.fetch_descriptions(
            tmp_path / "release", transport=httpx.MockTransport(handler), pins=fixture_pins()
        )
    assert not (tmp_path / "release").exists()
    assert not list(tmp_path.glob(".description-intake-*"))


def test_each_unbuffered_raw_chunk_checks_deadline(tmp_path, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(fetch, "monotonic", lambda: clock[0])

    class LateBody(httpx.SyncByteStream):
        def __iter__(self):
            yield b"f"
            clock[0] = 181.0
            yield b"i"
            clock[0] = 1000.0
            yield b"xture"

    transport = httpx.MockTransport(lambda _: httpx.Response(200, stream=LateBody()))
    with pytest.raises(ValueError, match="deadline"):
        fetch.fetch_descriptions(tmp_path / "release", transport=transport, pins=fixture_pins())
    assert not (tmp_path / "release").exists()

    assert clock[0] == 181.0


def test_late_failure_is_atomic_and_old_artifacts_remain(tmp_path):
    pins = fixture_pins()
    second = dict(pins["corrected_description_sources"][0], output="db/other.csv", sha256="0" * 64)
    pins["corrected_description_sources"].append(second)
    old = tmp_path / "old"
    old.mkdir()
    (old / "keep").write_bytes(b"unchanged")
    with pytest.raises(ValueError, match="pin mismatch"):
        fetch.fetch_descriptions(
            tmp_path / "release",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, stream=httpx.ByteStream(b"fixture"))
            ),
            pins=pins,
        )
    assert (old / "keep").read_bytes() == b"unchanged"
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("output", "../escape"),
        ("url", "https://example.invalid/file"),
        ("bytes", 32769),
        ("bytes", True),
    ],
)
def test_invalid_fixed_source_fails_before_network(tmp_path, field, value):
    pins = fixture_pins()
    pins["corrected_description_sources"][0][field] = value

    def handler(_):
        pytest.fail("network must not be reached")

    with pytest.raises(ValueError):
        fetch.fetch_descriptions(
            tmp_path / "release", transport=httpx.MockTransport(handler), pins=pins
        )

import hashlib

import httpx
import pytest

import scripts.fetch_labels as module


def fake_resources(monkeypatch):
    resources = {
        "data/arcwise_plat_sql_only_with_diff.json": (b"sql", "sql.json"),
        "data/arcwise_plat_full_with_diff.json": (b"full", "full.json"),
        "README.md": (b"readme", "README.md"),
        "LICENSE": (b"license", "LICENSE"),
    }
    monkeypatch.setattr(
        module,
        "RESOURCES",
        {
            path: (filename, len(raw), hashlib.sha256(raw).hexdigest())
            for path, (raw, filename) in resources.items()
        },
    )
    return resources


def transport_for(resources, *, bad=None, calls=None):
    def handle(request):
        if calls is not None:
            calls.append(str(request.url))
        path = request.url.path.split(module.REVISION + "/", 1)[1]
        raw, _ = resources[path]
        assert request.url.scheme == "https"
        assert request.url.host == "raw.githubusercontent.com"
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        if path == "LICENSE" and bad == "redirect":
            return httpx.Response(302, headers={"Location": "https://example.invalid/"})
        headers = {}
        if path == "LICENSE" and bad == "compressed":
            headers["Content-Encoding"] = "gzip"
        if path == "LICENSE" and bad == "oversize":
            raw += b"x"
        if path == "LICENSE" and bad == "hash":
            raw = b"x" * len(raw)
        if path == "LICENSE" and bad == "truncated":
            raw = raw[:-1]
        return httpx.Response(200, headers=headers, stream=httpx.ByteStream(raw))

    return httpx.MockTransport(handle)


def test_exact_release_is_published_once(tmp_path, monkeypatch):
    resources = fake_resources(monkeypatch)
    destination = tmp_path / "release"
    calls = []
    module.fetch_sources(destination, transport=transport_for(resources, calls=calls))
    assert len(calls) == 4
    for raw, filename in resources.values():
        assert (destination / filename).read_bytes() == raw
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=transport_for(resources, calls=calls))
    assert len(calls) == 4


@pytest.mark.parametrize("bad", ["redirect", "compressed", "oversize", "hash", "truncated"])
def test_failed_last_file_never_publishes_partial_release(tmp_path, monkeypatch, bad):
    resources = fake_resources(monkeypatch)
    destination = tmp_path / "release"
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=transport_for(resources, bad=bad))
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_timeout_leaves_no_published_release(tmp_path, monkeypatch):
    fake_resources(monkeypatch)

    def fail(request):
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    destination = tmp_path / "release"
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=httpx.MockTransport(fail))
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_command_deadline_is_checked_during_stream(tmp_path, monkeypatch):
    resources = fake_resources(monkeypatch)
    ticks = iter([0.0, 0.0, 121.0])
    monkeypatch.setattr(module, "monotonic", lambda: next(ticks, 121.0))
    destination = tmp_path / "release"
    calls = []
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=transport_for(resources, calls=calls))
    assert len(calls) == 1
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_trickling_body_checks_deadline_without_buffering(tmp_path, monkeypatch):
    raw = b"x" * 1000
    source = "data/arcwise_plat_sql_only_with_diff.json"
    monkeypatch.setattr(
        module, "RESOURCES", {source: ("sql.json", len(raw), hashlib.sha256(raw).hexdigest())}
    )
    elapsed = [0.0]
    monkeypatch.setattr(module, "monotonic", lambda: elapsed[0])

    class Trickle(httpx.SyncByteStream):
        def __iter__(self):
            for value in raw:
                elapsed[0] += 1.0
                yield bytes([value])

    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=Trickle()))
    destination = tmp_path / "release"
    with pytest.raises(module.IntakeError, match="acquisition deadline exceeded"):
        module.fetch_sources(destination, transport=transport)
    assert elapsed[0] == 120.0
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []

import hashlib

import httpx
import pytest

from scripts import fetch_arctic


def response(body: bytes, *, request, status=200, headers=None):
    return httpx.Response(
        status, stream=httpx.ByteStream(body), headers=headers or {}, request=request
    )


def test_fixed_model_pin_is_revision_addressed_and_exact():
    assert fetch_arctic.REVISION == "8e1a51188952afa8021bce6c8b3e5b495b3e85cd"
    assert fetch_arctic.EXPECTED_BYTES == 4_683_074_144
    assert fetch_arctic.EXPECTED_SHA256 == (
        "9c005244e3ab7fada2c53a9511999f4d22fbbd4f76a4416416a6d41d82702255"
    )
    assert fetch_arctic.REVISION in fetch_arctic.URL
    assert fetch_arctic.FILENAME in fetch_arctic.URL


def test_download_uses_identity_encoding_and_atomic_staging(tmp_path, monkeypatch):
    body = b"fixed model"
    monkeypatch.setattr(fetch_arctic, "EXPECTED_BYTES", len(body))
    monkeypatch.setattr(fetch_arctic, "EXPECTED_SHA256", hashlib.sha256(body).hexdigest())
    seen = []

    def handler(request):
        seen.append(request)
        return response(body, request=request, headers={"Content-Length": str(len(body))})

    target = tmp_path / fetch_arctic.FILENAME
    with httpx.Client(transport=httpx.MockTransport(handler), trust_env=False) as client:
        result = fetch_arctic.download(client, target, free_bytes=20 * 1024**3)

    assert result == target
    assert target.read_bytes() == body
    assert not target.with_suffix(target.suffix + ".part").exists()
    assert seen[0].headers["Accept-Encoding"] == "identity"


def test_download_resumes_only_an_exact_range(tmp_path, monkeypatch):
    body = b"fixed model"
    monkeypatch.setattr(fetch_arctic, "EXPECTED_BYTES", len(body))
    monkeypatch.setattr(fetch_arctic, "EXPECTED_SHA256", hashlib.sha256(body).hexdigest())
    target = tmp_path / fetch_arctic.FILENAME
    stage = target.with_suffix(target.suffix + ".part")
    stage.write_bytes(body[:5])

    def handler(request):
        assert request.headers["Range"] == "bytes=5-"
        return response(
            body[5:],
            request=request,
            status=206,
            headers={
                "Content-Length": str(len(body) - 5),
                "Content-Range": f"bytes 5-{len(body) - 1}/{len(body)}",
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler), trust_env=False) as client:
        fetch_arctic.download(client, target, free_bytes=20 * 1024**3)

    assert target.read_bytes() == body


@pytest.mark.parametrize(
    ("status", "headers"),
    [
        (206, {"Content-Length": "6", "Content-Range": "bytes 4-9/10"}),
        (200, {"Content-Length": "5", "Content-Encoding": "gzip"}),
    ],
)
def test_download_refuses_changed_range_or_encoding(tmp_path, monkeypatch, status, headers):
    body = b"0123456789"
    monkeypatch.setattr(fetch_arctic, "EXPECTED_BYTES", len(body))
    target = tmp_path / fetch_arctic.FILENAME
    target.with_suffix(target.suffix + ".part").write_bytes(body[:5])

    def handler(request):
        return response(body[5:], request=request, status=status, headers=headers)

    with (
        httpx.Client(transport=httpx.MockTransport(handler), trust_env=False) as client,
        pytest.raises(fetch_arctic.FetchError),
    ):
        fetch_arctic.download(client, target, free_bytes=20 * 1024**3)

    assert not target.exists()


def test_download_refuses_low_reserve_existing_mismatch_and_symlink(tmp_path, monkeypatch):
    body = b"fixed model"
    monkeypatch.setattr(fetch_arctic, "EXPECTED_BYTES", len(body))
    target = tmp_path / fetch_arctic.FILENAME
    target.write_bytes(b"wrong")
    with pytest.raises(fetch_arctic.FetchError, match="existing target mismatch"):
        fetch_arctic.download(None, target, free_bytes=20 * 1024**3)

    target.unlink()
    with pytest.raises(fetch_arctic.FetchError, match="disk reserve"):
        fetch_arctic.download(None, target, free_bytes=fetch_arctic.RESERVE_BYTES)

    real = tmp_path / "real"
    real.write_bytes(body)
    try:
        target.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(fetch_arctic.FetchError, match="symlink"):
        fetch_arctic.download(None, target, free_bytes=20 * 1024**3)

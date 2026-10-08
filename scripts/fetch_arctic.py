"""Download exactly the reviewed Arctic GGUF to ignored local storage."""

import hashlib
import json
import os
import shutil
from pathlib import Path

import httpx

REVISION = "8e1a51188952afa8021bce6c8b3e5b495b3e85cd"
FILENAME = "Arctic-Text2SQL-R1-7B.Q4_K_M.gguf"
URL = (
    "https://huggingface.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF/resolve/"
    + REVISION
    + "/"
    + FILENAME
    + "?download=true"
)
EXPECTED_BYTES = 4_683_074_144
EXPECTED_SHA256 = "9c005244e3ab7fada2c53a9511999f4d22fbbd4f76a4416416a6d41d82702255"
RESERVE_BYTES = 12 * 1024**3
ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / ".tools/models" / FILENAME


class FetchError(ValueError):
    """A fixed download refusal without response bodies or signed URLs."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checked_existing(target: Path) -> bool:
    if target.is_symlink():
        raise FetchError("target is a symlink")
    if not target.exists():
        return False
    if target.stat().st_size != EXPECTED_BYTES or file_sha256(target) != EXPECTED_SHA256:
        raise FetchError("existing target mismatch")
    return True


def download(client, target: Path, *, free_bytes: int | None = None) -> Path:
    if _checked_existing(target):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.with_suffix(target.suffix + ".part")
    if stage.is_symlink():
        raise FetchError("staging target is a symlink")
    offset = stage.stat().st_size if stage.exists() else 0
    if offset > EXPECTED_BYTES:
        raise FetchError("staging target exceeds pin")
    available = shutil.disk_usage(target.parent).free if free_bytes is None else free_bytes
    remaining = EXPECTED_BYTES - offset
    if available - remaining < RESERVE_BYTES:
        raise FetchError("insufficient disk reserve")
    if client is None:
        raise FetchError("download client unavailable")

    headers = {"Accept-Encoding": "identity"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    with client.stream("GET", URL, headers=headers) as response:
        expected_status = 206 if offset else 200
        if response.status_code != expected_status:
            raise FetchError("download status refused")
        encoding = response.headers.get("Content-Encoding", "identity").lower()
        if encoding != "identity":
            raise FetchError("download encoding refused")
        try:
            length = int(response.headers["Content-Length"])
        except (KeyError, ValueError):
            raise FetchError("download length unavailable") from None
        if length != remaining:
            raise FetchError("download length mismatch")
        if offset:
            wanted = f"bytes {offset}-{EXPECTED_BYTES - 1}/{EXPECTED_BYTES}"
            if response.headers.get("Content-Range") != wanted:
                raise FetchError("download range mismatch")
        mode = "ab" if offset else "xb"
        written = offset
        next_progress = ((written // (256 * 1024**2)) + 1) * (256 * 1024**2)
        with stage.open(mode) as stream:
            for chunk in response.iter_bytes(1024 * 1024):
                written += len(chunk)
                if written > EXPECTED_BYTES:
                    raise FetchError("download exceeded pin")
                stream.write(chunk)
                if written >= next_progress:
                    print(json.dumps({"status": "downloading", "bytes": written}))
                    next_progress += 256 * 1024**2
            stream.flush()
            os.fsync(stream.fileno())
    if written != EXPECTED_BYTES:
        raise FetchError("download incomplete")
    if file_sha256(stage) != EXPECTED_SHA256:
        raise FetchError("download hash mismatch")
    if target.exists() or target.is_symlink():
        raise FetchError("target appeared during download")
    stage.replace(target)
    return target


def main() -> int:
    timeout = httpx.Timeout(connect=30, read=60, write=60, pool=5)
    try:
        with httpx.Client(
            timeout=timeout,
            trust_env=False,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            path = download(client, TARGET)
    except (FetchError, OSError, httpx.HTTPError) as error:
        reason = str(error) if isinstance(error, FetchError) else "download transport error"
        print(json.dumps({"status": "failed", "reason": reason}))
        return 1
    print(
        json.dumps(
            {
                "status": "complete",
                "path": str(path.relative_to(ROOT)),
                "bytes": EXPECTED_BYTES,
                "sha256": EXPECTED_SHA256,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

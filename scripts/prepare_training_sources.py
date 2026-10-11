"""Acquire tiny pinned BIRD training inputs without downloading the database archive."""

from __future__ import annotations

import hashlib
import io
import json
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_URL = "https://bird-bench.oss-cn-beijing.aliyuncs.com/train.zip"
ARCHIVE_LENGTH = 8919543554
ARCHIVE_ETAG = '"1FBA2891BD215A42CE1004736AB7F47F-400"'
DATA_REVISION = "4068469807b255fcfc0816bdd520946fe460d256"
DATA_URL = (
    "https://huggingface.co/datasets/birdsql/bird23-train-filtered/resolve/"
    + DATA_REVISION
    + "/data/train-00000-of-00001.jsonl"
)


class RangeReader(io.RawIOBase):
    def __init__(self, size: int, fetch: Callable[[int, int], bytes], *, budget=32 * 2**20):
        self.size, self.fetch, self.budget = size, fetch, budget
        self.position = 0
        self.downloaded = 0

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset + (0 if whence == 0 else self.position if whence == 1 else self.size)
        if whence not in (0, 1, 2) or not 0 <= position <= self.size:
            raise ValueError("invalid archive seek")
        self.position = position
        return position

    def read(self, size=-1):
        count = self.size - self.position if size == -1 else min(size, self.size - self.position)
        if count < 0 or count > 8 * 2**20:
            raise ValueError("archive range cap exceeded")
        if self.downloaded + count > self.budget:
            raise ValueError("archive network budget exceeded")
        if not count:
            return b""
        content = self.fetch(self.position, self.position + count - 1)
        if len(content) != count:
            raise ValueError("short range response")
        self.position += count
        self.downloaded += count
        return content


def fetch_range(start: int, end: int) -> bytes:
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
        },
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=30) as response:
        if (
            response.status != 206
            or response.headers.get("Content-Range") != f"bytes {start}-{end}/{ARCHIVE_LENGTH}"
            or response.headers.get("ETag") != ARCHIVE_ETAG
        ):
            raise ValueError("archive identity/range refused")
        return response.read(end - start + 2)


def main() -> None:
    import shutil

    from scripts.run_training_pilot import check_disk, disk_used

    check_disk(shutil.disk_usage(ROOT).free, disk_used())
    directory = ROOT / "data/training/source"
    if directory.exists():
        raise FileExistsError("training source output already exists")
    reader = RangeReader(ARCHIVE_LENGTH, fetch_range)
    with zipfile.ZipFile(reader) as archive:
        matches = [
            info
            for info in archive.infolist()
            if info.filename.endswith("/train_tables.json") or info.filename == "train_tables.json"
        ]
        if len(matches) != 1 or matches[0].file_size > 8 * 2**20:
            raise ValueError("training schema member refused")
        tables = archive.read(matches[0])  # ZipFile verifies the member's CRC.
        member = matches[0].filename
    with urllib.request.urlopen(DATA_URL, timeout=30) as response:
        labels = response.read(4 * 2**20 + 1)
    if len(labels) != 2654294:
        raise ValueError("filtered annotation size refused")
    schemas = json.loads(tables)
    annotations = [json.loads(line) for line in labels.splitlines() if line.strip()]
    if len(annotations) != 6601:
        raise ValueError("filtered annotation count refused")
    report = {
        "archive_url": ARCHIVE_URL,
        "archive_length": ARCHIVE_LENGTH,
        "archive_etag": ARCHIVE_ETAG,
        "archive_member": member,
        "archive_bytes_fetched": reader.downloaded,
        "archive_integrity": "pinned length/ETag, extracted member CRC; full archive not hashed",
        "dataset": "birdsql/bird23-train-filtered",
        "revision": DATA_REVISION,
        "license": "CC-BY-SA-4.0",
        "annotation_count": len(annotations),
        "schema_count": len(schemas),
        "schema_sha256": hashlib.sha256(tables).hexdigest(),
        "annotation_sha256": hashlib.sha256(labels).hexdigest(),
        "labels": "SQLite source; not yet PostgreSQL converted or execution verified",
    }
    directory.mkdir(parents=True)
    (directory / "train-tables.json").write_bytes(tables)
    (directory / "filtered-train.jsonl").write_bytes(labels)
    with (ROOT / "docs/training-source-manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

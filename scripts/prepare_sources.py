"""Fixed, offline source extraction; no source SQL execution."""

import hashlib
import json
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from time import monotonic

from sqlwarden.data import file_sha256

PINS_PATH = Path("docs/source-release-pins.json")
SOURCE_DIR = Path("data/source-release/minidev-0703")
ARCHIVE = Path("data/raw/minidev_0703.zip")


def load_pins() -> dict:
    return json.loads(PINS_PATH.read_text(encoding="utf-8"))


def relative_path(value: str) -> Path:
    if not isinstance(value, str) or "\\" in value or ":" in value:
        raise ValueError("unsupported output path")
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or any(part in {".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise ValueError("unsupported output path")
    return Path(*path.parts)


def checked_file(path: Path, pin: dict) -> None:
    if (
        type(pin["bytes"]) is not int
        or pin["bytes"] < 0
        or re.fullmatch(r"[a-f0-9]{64}", pin["sha256"]) is None
    ):
        raise ValueError("invalid source pin")
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size != pin["bytes"]
        or file_sha256(path) != pin["sha256"]
    ):
        raise ValueError("source pin mismatch")


def new_destination(destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination already exists")


def unique_outputs(entries: list[dict]) -> None:
    outputs = [relative_path(entry["output"]).as_posix().casefold() for entry in entries]
    if len(set(outputs)) != len(outputs):
        raise ValueError("output path collision")


def selected_member(archive: zipfile.ZipFile, pin: dict) -> zipfile.ZipInfo:
    matches = [item for item in archive.infolist() if item.filename == pin["member"]]
    if len(matches) != 1:
        raise ValueError("archive member missing or duplicated")
    item = matches[0]
    if (
        item.is_dir()
        or stat.S_ISLNK(item.external_attr >> 16)
        or item.flag_bits & 1
        or item.file_size != pin["bytes"]
    ):
        raise ValueError("archive member rejected")
    return item


def extract_sources(archive_path: Path, destination: Path, *, pins: dict | None = None) -> None:
    pins = load_pins() if pins is None else pins
    entries = [pins["metadata"], *pins["sqlite_sources"], *pins["original_description_sources"]]
    unique_outputs(entries)
    if len({entry["member"] for entry in entries}) != len(entries):
        raise ValueError("source member collision")
    new_destination(destination)
    checked_file(archive_path, pins["archive"])
    deadline = monotonic() + 900
    destination.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(destination.parent).free < sum(e["bytes"] for e in entries) + 2**30:
        raise ValueError("insufficient disk reserve")
    with TemporaryDirectory(prefix=".source-prep-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for entry in entries:
                item = selected_member(archive, entry)
                output = staging / relative_path(entry["output"])
                output.parent.mkdir(parents=True, exist_ok=True)
                count = 0
                digest = hashlib.sha256()
                with archive.open(item) as source, output.open("xb") as target:
                    while chunk := source.read(1024 * 1024):
                        if monotonic() >= deadline:
                            raise ValueError("extraction deadline exceeded")
                        count += len(chunk)
                        if count > entry["bytes"]:
                            raise ValueError("member byte limit exceeded")
                        digest.update(chunk)
                        target.write(chunk)
                if count != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                    raise ValueError("member pin mismatch")
        if monotonic() >= deadline:
            raise ValueError("extraction deadline exceeded")
        new_destination(destination)
        staging.rename(destination)


def main() -> int:
    try:
        extract_sources(ARCHIVE, SOURCE_DIR)
    except (ValueError, OSError, zipfile.BadZipFile):
        print(json.dumps({"status": "failed", "stage": "source extraction"}))
        return 1
    print(json.dumps({"status": "extracted", "files": 87}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

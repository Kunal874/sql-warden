"""Acquire only the 75 reviewed, revision-pinned description CSVs."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import httpx

from scripts.inspect_labels import REVISION
from scripts.prepare_sources import load_pins, new_destination, relative_path, unique_outputs

BASE = "https://raw.githubusercontent.com/uiuc-kang-lab/text_to_sql_benchmarks/"
DESCRIPTION_DIR = Path("data/description-corrections/arcwise-fe766045")


def fetch_descriptions(
    destination: Path, *, transport: httpx.BaseTransport | None = None, pins: dict | None = None
) -> None:
    pins = load_pins() if pins is None else pins
    if pins["corrected_revision"] != REVISION:
        raise ValueError("unapproved revision")
    entries = pins["corrected_description_sources"]
    unique_outputs(entries)
    for entry in entries:
        if (
            entry["url"] != BASE + REVISION + "/" + entry["path"]
            or type(entry["bytes"]) is not int
            or not 0 < entry["bytes"] <= 32768
        ):
            raise ValueError("unapproved description source")
    new_destination(destination)
    deadline = monotonic() + 180
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".description-intake-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        with httpx.Client(
            trust_env=False,
            follow_redirects=False,
            transport=transport or httpx.HTTPTransport(retries=0, trust_env=False),
            headers={"Accept-Encoding": "identity"},
        ) as client:
            for entry in entries:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise ValueError("description deadline exceeded")
                raw = bytearray()
                with client.stream("GET", entry["url"], timeout=min(20.0, remaining)) as response:
                    if response.status_code != 200:
                        raise ValueError("description HTTP status rejected")
                    if response.headers.get("content-encoding", "identity").lower() != "identity":
                        raise ValueError("description encoding rejected")
                    for chunk in response.iter_raw():
                        if monotonic() >= deadline:
                            raise ValueError("description deadline exceeded")
                        if len(raw) + len(chunk) > entry["bytes"]:
                            raise ValueError("description byte limit exceeded")
                        raw.extend(chunk)
                if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                    raise ValueError("description pin mismatch")
                output = staging / relative_path(entry["output"])
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as target:
                    target.write(raw)
        if monotonic() >= deadline:
            raise ValueError("description deadline exceeded")
        new_destination(destination)
        staging.rename(destination)


def main() -> int:
    try:
        fetch_descriptions(DESCRIPTION_DIR)
    except (ValueError, OSError, httpx.HTTPError):
        print(json.dumps({"status": "failed", "stage": "description acquisition"}))
        return 1
    print(json.dumps({"status": "acquired", "files": 75, "revision": REVISION}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

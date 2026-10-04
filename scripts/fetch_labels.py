"""Acquire only the approved pinned correction labels and license context."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import httpx

from scripts.inspect_labels import CORRECTION_DIR, REVISION

BASE = "https://raw.githubusercontent.com/uiuc-kang-lab/text_to_sql_benchmarks/"
RESOURCES = {
    "data/arcwise_plat_sql_only_with_diff.json": (
        "arcwise_plat_sql_only_with_diff.json",
        287718,
        "e7bf76408f99266506ea558d84982c69422e5db3dfecab5f08a3a8d3900e8395",
    ),
    "data/arcwise_plat_full_with_diff.json": (
        "arcwise_plat_full_with_diff.json",
        332246,
        "baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8",
    ),
    "README.md": (
        "README.md",
        5038,
        "7aefaba8da2792a8edde1cb534dde1f89c3228e87ac5b923838ba68bb56cf0f5",
    ),
    "LICENSE": (
        "LICENSE",
        20138,
        "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5",
    ),
}


class IntakeError(ValueError):
    """Stable fixed-source acquisition failure."""


def fetch_sources(destination: Path, *, transport: httpx.BaseTransport | None = None) -> None:
    if destination.exists() or destination.is_symlink():
        raise IntakeError("destination already exists")
    deadline = monotonic() + 120
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".label-intake-", dir=destination.parent) as temporary:
            staging = Path(temporary) / "release"
            staging.mkdir()
            with httpx.Client(
                trust_env=False,
                follow_redirects=False,
                transport=transport or httpx.HTTPTransport(retries=0, trust_env=False),
                headers={"Accept-Encoding": "identity"},
            ) as client:
                for source, (filename, size, digest) in RESOURCES.items():
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise IntakeError("acquisition deadline exceeded")
                    raw = bytearray()
                    url = BASE + REVISION + "/" + source
                    with client.stream("GET", url, timeout=min(20.0, remaining)) as response:
                        if response.status_code != 200:
                            raise IntakeError("source HTTP status rejected")
                        if (
                            response.headers.get("content-encoding", "identity").lower()
                            != "identity"
                        ):
                            raise IntakeError("source encoding rejected")
                        for chunk in response.iter_raw():
                            if monotonic() >= deadline:
                                raise IntakeError("acquisition deadline exceeded")
                            if len(raw) + len(chunk) > size:
                                raise IntakeError("source byte limit exceeded")
                            raw.extend(chunk)
                    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
                        raise IntakeError("source pin mismatch")
                    with (staging / filename).open("xb") as output:
                        output.write(raw)
            if monotonic() >= deadline:
                raise IntakeError("acquisition deadline exceeded")
            if destination.exists() or destination.is_symlink():
                raise IntakeError("destination appeared during acquisition")
            staging.rename(destination)
    except (OSError, httpx.HTTPError):
        raise IntakeError("acquisition failed") from None


def main() -> int:
    try:
        fetch_sources(Path("data") / CORRECTION_DIR)
    except IntakeError as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1
    print(json.dumps({"status": "acquired", "revision": REVISION, "files": len(RESOURCES)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Setup-only copy of the existing restricted reader credential; never runtime."""

import re
from pathlib import Path


def prepare(root: Path) -> None:
    target = root / ".env.runtime"
    if target.exists():
        raise FileExistsError("Runtime credential file already exists")
    source = (root / ".env.california").read_text(encoding="utf-8")
    match = re.fullmatch(r"WARDEN_CALIFORNIA_PASSWORD=([a-f0-9]{48})\n?", source)
    if match is None:
        raise ValueError("Restricted credential source is invalid")
    with target.open("x", encoding="utf-8", newline="\n") as file:
        file.write("WARDEN_RUNTIME_CALIFORNIA_PASSWORD=" + match[1] + "\n")


if __name__ == "__main__":
    try:
        prepare(Path(__file__).resolve().parents[1])
    except (OSError, ValueError):
        raise SystemExit("Runtime setup refused; no private values are printed") from None
    print("Created ignored .env.runtime with only the restricted California credential.")

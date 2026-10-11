"""Setup-only: copy the existing restricted reader credentials into ignored `.env.web`.

The web runtime loads only these per-dataset reader keys; setup and test keys stay out.
"""

import re
from pathlib import Path

from sqlwarden.guard import DATASET_POLICIES

SECRET = re.compile(r"[a-f0-9]{48}")


def _read(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if line
    )


def prepare(root: Path) -> None:
    target = root / ".env.web"
    if target.exists():
        raise FileExistsError("Runtime credential file already exists")
    sources = _read(root / ".env.california") | _read(root / ".env.datasets")
    lines = []
    for db_id in sorted(DATASET_POLICIES):
        source_key = (
            "WARDEN_CALIFORNIA_PASSWORD"
            if db_id == "california_schools"
            else f"WARDEN_DATASET_{db_id.upper()}_PASSWORD"
        )
        value = sources.get(source_key, "")
        if not SECRET.fullmatch(value):
            raise ValueError("Restricted credential source is invalid")
        lines.append(f"WARDEN_RUNTIME_{db_id.upper()}_PASSWORD={value}\n")
    with target.open("x", encoding="utf-8", newline="\n") as file:
        file.writelines(lines)


if __name__ == "__main__":
    try:
        prepare(Path(__file__).resolve().parents[1])
    except (OSError, ValueError):
        raise SystemExit("Runtime setup refused; no private values are printed") from None
    print("Created ignored .env.web with restricted dataset reader credentials only.")

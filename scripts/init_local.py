"""Create local-only credentials without printing them or overwriting files."""

import argparse
from pathlib import Path
from secrets import token_hex


def initialize(root: Path) -> None:
    """Create setup-only and runtime environment files."""
    paths = (root / ".env.setup", root / ".env")
    if any(path.exists() for path in paths):
        raise FileExistsError("Local credential files already exist; leaving them untouched")
    passwords = {
        key: token_hex(24)
        for key in (
            "WARDEN_BOOTSTRAP_PASSWORD",
            "WARDEN_APP_PASSWORD",
            "WARDEN_SCHOOLS_PASSWORD",
            "WARDEN_OTHER_PASSWORD",
            "WARDEN_TENANT_A_PASSWORD",
            "WARDEN_TENANT_B_PASSWORD",
        )
    }
    setup = {"WARDEN_PG_PORT": "55432", "WARDEN_TEST_TARGET": "sqlwarden-local", **passwords}
    runtime = {
        key: value
        for key, value in setup.items()
        if key not in {"WARDEN_BOOTSTRAP_PASSWORD", "WARDEN_TEST_TARGET"}
    }
    for path, values in zip(paths, (setup, runtime), strict=True):
        with path.open("x", encoding="utf-8", newline="\n") as file:
            file.write("".join(f"{key}={value}\n" for key, value in values.items()))


def initialize_bird(root: Path) -> None:
    with (root / ".env.california").open("x", encoding="utf-8", newline="\n") as file:
        file.write(f"WARDEN_CALIFORNIA_PASSWORD={token_hex(24)}\n")
    print("Created .env.california. Values are private and will not be printed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bird", action="store_true", help="Create only the separate California credential"
    )
    args = parser.parse_args()
    try:
        if args.bird:
            initialize_bird(Path(__file__).resolve().parents[1])
        else:
            initialize(Path(__file__).resolve().parents[1])
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from None
    if not args.bird:
        print("Created .env.setup and .env. Values are private and will not be printed.")

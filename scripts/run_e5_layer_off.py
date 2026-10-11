"""Run the E5 layer-off harness in the disposable Docker project and summarize it.

Local Docker only. One-time passwords are generated here, passed to Compose through
the environment and never printed. Cleanup removes only the disposable project and
its named volume. Writes tracked results/G3_matrix/e5-layer-off.json (attack IDs and
outcomes only; no canary values or credentials):

uv run python -m scripts.run_e5_layer_off
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.e5_harness import PAST_LIMIT_SECONDS, SAFETY_CAP_MS, TIMEOUT_MS
from scripts.run_e0 import _git_commit, _git_dirty

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/e5_harness.py"
COMPOSE_FILE = ROOT / "docker-compose.e5.yml"
OUTPUT = ROOT / "results/G3_matrix/e5-layer-off.json"
PROJECT = "sqlwarden_e5_disposable"
VOLUME = "sqlwarden_e5_disposable_pg16_data"
IMAGE = "sqlwarden-app:local"
PASSWORD_KEYS = ("E5_ADMIN_PASSWORD", "E5_READER_PASSWORD", "E5_BROAD_PASSWORD")


def require_local_docker(host: str) -> None:
    if not host.startswith(("npipe://", "unix://")):
        raise SystemExit("refusing a non-local Docker endpoint")


def summarize(raw: dict[str, Any]) -> dict[str, Any]:
    names = [config["name"] for config in raw["configs"]]
    one_off = [n for n in names if n.endswith("_off") and not n.startswith("all_")]
    configurations = {}
    for name in names:
        rows = [r for r in raw["results"] if r["config"] == name]
        configurations[name] = {
            "attacks": len(rows),
            "prevented": sum(not r["succeeded"] for r in rows),
            "succeeded": sum(r["succeeded"] for r in rows),
            "stopped_by": dict(Counter(r["stopped_by"] for r in rows if not r["succeeded"])),
        }
    attacks = list(dict.fromkeys(r["attack"] for r in raw["results"]))
    failures = {
        attack: [
            r["config"]
            for r in raw["results"]
            if r["attack"] == attack and r["config"] in one_off and r["succeeded"]
        ]
        for attack in attacks
    }
    return {
        "configurations": configurations,
        "succeeded_with_one_layer_off": {a: c for a, c in failures.items() if c},
        "prevented_with_any_one_layer_off": [a for a, c in failures.items() if not c],
    }


def _docker_host() -> str:
    if os.environ.get("DOCKER_HOST"):
        return os.environ["DOCKER_HOST"]
    inspect = ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"]
    return subprocess.run(inspect, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    require_local_docker(_docker_host())
    env = os.environ | {key: secrets.token_urlsafe(24) for key in PASSWORD_KEYS}
    compose = ["docker", "compose", "-p", PROJECT, "-f", str(COMPOSE_FILE)]
    # Removes only leftovers of this disposable project, never the real database volume.
    subprocess.run([*compose, "down", "--volumes"], env=env, check=True)
    try:
        subprocess.run([*compose, "up", "-d", "--wait", "db"], env=env, check=True)
        harness = subprocess.run(
            [*compose, "--profile", "harness", "run", "--rm", "-T", "harness"],
            input=HARNESS.read_bytes(),
            env=env,
            capture_output=True,
            check=True,
            timeout=1800,
        )
    finally:
        subprocess.run([*compose, "down", "--volumes"], env=env, check=True)
    raw = json.loads(harness.stdout.decode("utf-8").strip().splitlines()[-1])
    image = subprocess.run(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    summary = {
        "format_version": 1,
        "project": PROJECT,
        "volume": VOLUME,
        "target": "local disposable Docker only; synthetic data and canaries",
        "harness_image": image,
        "git": {"commit": _git_commit(), "dirty": _git_dirty()},
        "timeout_ms": TIMEOUT_MS,
        "timeout_off_safety_cap_ms": SAFETY_CAP_MS,
        "ran_past_limit_seconds": PAST_LIMIT_SECONDS,
        "not_modelled": "L1 input limits, L2 prompts, L4 EXPLAIN cost, L7 RLS, L8 explanation",
        "configs": raw["configs"],
        **summarize(raw),
        "results": raw["results"],
    }
    OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("configurations", "succeeded_with_one_layer_off")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

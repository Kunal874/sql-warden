"""Source and resource checks for local G6 serving, without ML imports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from training.full import choose_checkpoint
from training.pilot import MODEL, REVISION

GIB = 2**30


def check_serving_budget(
    ram_bytes: int,
    free_d: int,
    used_d: int,
    added_c: int,
    *,
    planned_d: int = 0,
    loading: bool = True,
) -> None:
    if min(ram_bytes, free_d, used_d, added_c, planned_d) < 0:
        raise ValueError("negative serving resource count")
    floor = 4 if loading else 1
    if ram_bytes < floor * GIB:
        raise RuntimeError(f"available RAM below {floor} GiB")
    if free_d - planned_d < 20 * GIB:
        raise RuntimeError("planned output would breach 20 GiB D reserve")
    if used_d + added_c + planned_d > 24 * GIB:
        raise RuntimeError("combined G6 artifacts exceed 24 GiB")


def cache_snapshot(directory: Path) -> dict[str, int]:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("Ollama cache directory unavailable or redirected")
    return {
        path.relative_to(directory).as_posix(): path.stat().st_size
        for path in directory.rglob("*")
        if path.is_file()
    }


def cache_growth(directory: Path, baseline: dict[str, int]) -> int:
    current = cache_snapshot(directory)
    if any(current.get(name) != size for name, size in baseline.items()):
        raise ValueError("existing Ollama cache membership/size changed")
    return sum(size for name, size in current.items() if name not in baseline)


def file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def merge_inputs(root: Path) -> tuple[Path, Path]:
    pin = json.loads((root / "docs/g6-serving-inputs.json").read_text(encoding="utf-8"))
    report = json.loads((root / "results/G6_training/summary.json").read_text(encoding="utf-8"))
    selected = pin["selected_adapter"]
    if not (
        pin["model"] == report["model"] == MODEL
        and pin["revision"] == report["revision"] == REVISION
        and report["status"] == "completed"
        and report["git_dirty"] is False
        and choose_checkpoint(report["checkpoints"])
        == report["chosen_checkpoint"]
        == selected["step"]
        and selected["sha256"] == report["adapter_sha256"]
    ):
        raise ValueError("merge selection/provenance refused")
    base = root / f"models/g6/cache/models--Qwen--Qwen2.5-Coder-1.5B-Instruct/snapshots/{REVISION}"
    adapter = root / f"models/g6/full-adapters/step-{selected['step']}"
    weight = base / "model.safetensors"
    checks = [
        (weight, pin["base_weights"]["sha256"]),
        (adapter / "adapter_model.safetensors", selected["sha256"]),
        (adapter / "adapter_config.json", selected["config_sha256"]),
    ]
    if weight.stat().st_size != pin["base_weights"]["bytes"] or any(
        path.is_symlink() or file_hash(path) != digest for path, digest in checks
    ):
        raise ValueError("merge input fingerprint refused")
    return base, adapter

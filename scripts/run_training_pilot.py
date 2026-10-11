"""Supervise local GPU training without importing training dependencies."""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_resources(ram_bytes: int, disk_free: int, disk_used: int) -> None:
    if ram_bytes < 4 * 2**30:
        raise RuntimeError("available RAM below 4 GiB")
    check_disk(disk_free, disk_used)


def check_disk(disk_free: int, disk_used: int) -> None:
    if disk_free < 20 * 2**30:
        raise RuntimeError("disk reserve below 20 GiB")
    if disk_used > 12 * 2**30:
        raise RuntimeError("training disk budget exceeds 12 GiB")


def available_ram() -> int:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong)
            for name in (
                "total_phys",
                "avail_phys",
                "total_page",
                "avail_page",
                "total_virtual",
                "avail_virtual",
                "avail_extended",
            )
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("cannot inspect available RAM")
    return status.avail_phys


def disk_used() -> int:
    directories = [ROOT / "training/.venv", ROOT / "models/g6", ROOT / ".tools/g6"]
    return sum(
        path.stat().st_size
        for directory in directories
        if directory.exists()
        for path in directory.rglob("*")
        if path.is_file()
    )


def supervise(
    command: list[str],
    summary: Path,
    *,
    timeout: float = 2700,
    monitor: Callable[[], None] | None = None,
) -> None:
    evidence = summary.with_suffix(".evidence.json")
    if summary.exists() or evidence.exists():
        raise FileExistsError("run output already exists")
    started = time.monotonic()
    with subprocess.Popen(command) as process:
        try:
            while True:
                if monitor is not None:
                    monitor()
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, timeout)
                try:
                    code = process.wait(timeout=min(5, remaining))
                    if code:
                        raise subprocess.CalledProcessError(code, command)
                    break
                except subprocess.TimeoutExpired:
                    continue
        except BaseException:
            process.kill()
            process.wait()
            raise
    if not evidence.is_file():
        raise RuntimeError("training evidence is missing")
    report = json.loads(evidence.read_text(encoding="utf-8"))
    allowed = {
        "status",
        "device",
        "model",
        "revision",
        "seed",
        "steps",
        "gpu_name",
        "elapsed_seconds",
        "peak_allocated_bytes",
        "peak_reserved_bytes",
        "trainable_parameters",
        "total_parameters",
        "losses",
        "adapter_changed",
        "adapter_reloaded",
        "adapter_sha256",
        "packages",
        "git_commit",
        "git_dirty",
        "cuda_probe",
        "generation_nonempty",
        "generation_sha256",
    }
    if not isinstance(report, dict) or set(report) - allowed:
        raise RuntimeError("unapproved evidence fields")
    from training.pilot import validate_losses

    validate_losses(report.get("losses", []), expected_steps=20)
    if not (
        report.get("status") == "completed"
        and report.get("device") == "cuda"
        and report.get("adapter_changed") is True
        and report.get("adapter_reloaded") is True
    ):
        raise RuntimeError("training evidence is incomplete")
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    with summary.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=ROOT / "results/G6_pilot/summary.json")
    args = parser.parse_args()
    check_resources(available_ram(), shutil.disk_usage(ROOT).free, disk_used())
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    env_updates = {
        "HF_HOME": str(ROOT / "models/g6/cache"),
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
    }
    os.environ.update(env_updates)
    python = ROOT / "training/.venv/Scripts/python.exe"
    supervise(
        [
            str(python),
            str(ROOT / "training/pilot.py"),
            "--evidence",
            str(args.summary.with_suffix(".evidence.json")),
        ],
        args.summary,
        monitor=lambda: check_disk(shutil.disk_usage(ROOT).free, disk_used()),
    )


if __name__ == "__main__":
    main()

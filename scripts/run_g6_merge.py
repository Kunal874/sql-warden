"""Supervise the approved local merge; preserve existing Ollama cache files."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from contextlib import suppress
from pathlib import Path

from scripts.prepare_g6_serving import cache_growth, cache_snapshot, check_serving_budget, file_hash
from scripts.run_training_pilot import available_ram, disk_used

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".tools/g6/ollama-cache-baseline.json"


def serving_storage() -> tuple[int, int]:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    added = cache_growth(Path(baseline["models_directory"]), baseline["files"])
    added += sum(cache_snapshot(Path(baseline["conversion_directory"])).values())
    evaluation = sum(
        path.stat().st_size for path in (ROOT / "results/G6_e9").rglob("*") if path.is_file()
    )
    return disk_used() + evaluation, added


def publish_merge(summary: Path) -> None:
    if summary.exists():
        raise FileExistsError("merge summary already exists")
    report = json.loads(summary.with_suffix(".evidence.json").read_text(encoding="utf-8"))
    fields = {
        "status",
        "model",
        "revision",
        "selected_checkpoint",
        "adapter_sha256",
        "device",
        "dtype",
        "preload_ram_bytes",
        "elapsed_seconds",
        "peak_reserved_bytes",
        "changed_weights",
        "saved_tensors_equal",
        "reload_logits_equal",
        "generation_nonempty",
        "generation_sha256",
        "artifact_files",
        "git_commit",
        "git_dirty",
    }
    pin = json.loads((ROOT / "docs/g6-serving-inputs.json").read_text(encoding="utf-8"))
    if (
        not isinstance(report, dict)
        or set(report) != fields
        or not (
            report["status"] == "completed"
            and report["device"] == "cuda"
            and report["dtype"] == "float16"
            and report["git_dirty"] is False
            and report["git_commit"]
            == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
            and report["model"] == pin["model"]
            and report["revision"] == pin["revision"]
            and report["selected_checkpoint"] == pin["selected_adapter"]["step"]
            and report["adapter_sha256"] == pin["selected_adapter"]["sha256"]
            and all(
                report[name] is True
                for name in (
                    "changed_weights",
                    "saved_tensors_equal",
                    "reload_logits_equal",
                    "generation_nonempty",
                )
            )
        )
    ):
        raise RuntimeError("merge evidence incomplete or provenance changed")
    output = ROOT / "models/g6/merged"
    files = report["artifact_files"]
    if not files or set(files) != {path.name for path in output.iterdir() if path.is_file()}:
        raise RuntimeError("merge artifact membership changed")
    for name, metadata in files.items():
        if Path(name).name != name:
            raise ValueError("merge artifact path refused")
        path = output / name
        if (
            path.is_symlink()
            or path.stat().st_size != metadata["bytes"]
            or file_hash(path) != metadata["sha256"]
        ):
            raise RuntimeError("merge artifact fingerprint changed")
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    with summary.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def main() -> None:
    output = ROOT / "models/g6/merged"
    evidence = ROOT / "results/G6_training/merge.evidence.json"
    summary = ROOT / "results/G6_training/merge.json"
    if output.exists() or evidence.exists() or summary.exists():
        raise FileExistsError("merge output already exists; refusing overwrite")
    if not BASELINE.exists():
        cache = Path(
            os.environ.get("OLLAMA_MODELS") or Path(os.environ["USERPROFILE"]) / ".ollama/models"
        )
        conversion = cache.parent / "sqlwarden-g6"
        if conversion.exists():
            raise FileExistsError("conversion workspace already exists")
        files = cache_snapshot(cache)
        conversion.mkdir()
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        with BASELINE.open("x", encoding="utf-8") as handle:
            json.dump(
                {
                    "models_directory": str(cache),
                    "conversion_directory": str(conversion),
                    "files": files,
                },
                handle,
                indent=2,
            )
    used, added = serving_storage()
    check_serving_budget(
        available_ram(), shutil.disk_usage(ROOT).free, used, added, planned_d=3 * 2**30
    )
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
        raise RuntimeError("merge requires clean Git provenance")
    started = time.monotonic()
    environment = os.environ | {
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
    }
    command = [str(ROOT / "training/.venv/Scripts/python.exe"), str(ROOT / "training/merge.py")]
    with subprocess.Popen(command, cwd=ROOT, env=environment) as process:
        try:
            while process.poll() is None:
                used, added = serving_storage()
                check_serving_budget(
                    available_ram(), shutil.disk_usage(ROOT).free, used, added, loading=False
                )
                if time.monotonic() - started > 1200:
                    raise subprocess.TimeoutExpired(command, 1200)
                with suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5)
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, command)
        except BaseException:
            process.kill()
            process.wait()
            raise
    publish_merge(summary)
    print("full merge verified; compact evidence saved", flush=True)


if __name__ == "__main__":
    main()

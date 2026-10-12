"""Bounded pinned Qwen2 conversion; all large intermediates stay on C:."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from contextlib import suppress

from scripts.prepare_g6_serving import check_serving_budget, file_hash, merge_inputs
from scripts.run_g6_merge import BASELINE, ROOT, serving_storage
from scripts.run_training_pilot import available_ram


def monitor(*, planned_c: int = 0, loading: bool = True) -> None:
    used, added = serving_storage()
    check_serving_budget(
        available_ram(), shutil.disk_usage(ROOT).free, used, added + planned_c, loading=loading
    )


def run_tool(command: list[str], *, planned_c: int) -> float:
    monitor(planned_c=planned_c)
    environment = os.environ | {
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "OLLAMA_HOST": "127.0.0.1:11434",
    }
    started = time.monotonic()
    with subprocess.Popen(command, cwd=ROOT, env=environment) as process:
        try:
            while process.poll() is None:
                monitor(loading=False)
                if time.monotonic() - started > 900:
                    raise subprocess.TimeoutExpired(command, 900)
                with suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5)
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, command)
        except BaseException:
            process.kill()
            process.wait()
            raise
    monitor(loading=False)
    return round(time.monotonic() - started, 3)


def main() -> None:
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
        raise RuntimeError("conversion requires clean Git provenance")
    summary = ROOT / "results/G6_training/conversion.json"
    if summary.exists():
        raise FileExistsError("conversion summary exists")
    tools = json.loads((ROOT / "docs/g6-conversion-tools.json").read_text())
    cpp = tools["llama_cpp"]
    quantizer = ROOT / ".tools/g6/llama-bin-b11429/llama-quantize.exe"
    if file_hash(quantizer) != cpp["quantizer_sha256"]:
        raise ValueError("quantizer fingerprint changed")
    converter = ROOT / f".tools/g6/llama-source/llama.cpp-{cpp['commit']}/convert_hf_to_gguf.py"
    base, _ = merge_inputs(ROOT)
    merged = ROOT / "models/g6/merged"
    merge = json.loads((ROOT / "results/G6_training/merge.json").read_text())
    if merge["status"] != "completed":
        raise ValueError("merge evidence incomplete")
    for name, metadata in merge["artifact_files"].items():
        if file_hash(merged / name) != metadata["sha256"]:
            raise ValueError("merged artifact changed")
    directory = json.loads(BASELINE.read_text())["conversion_directory"]
    from pathlib import Path

    directory = Path(directory)
    report = {
        "status": "completed",
        "quantization": "Q4_K_M",
        "threads": 4,
        "llama_cpp_commit": cpp["commit"],
        "models": {},
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    for name, source in [("base", base), ("tuned", merged)]:
        f16 = directory / f"{name}-f16.gguf"
        q4 = directory / f"{name}-q4km.gguf"
        if f16.exists() or q4.exists():
            raise FileExistsError("conversion output exists; preserve and investigate")
        print(f"{name}: F16 GGUF conversion", flush=True)
        seconds_f16 = run_tool(
            [
                str(ROOT / "training/.venv/Scripts/python.exe"),
                str(converter),
                str(source),
                "--outfile",
                str(f16),
                "--outtype",
                "f16",
            ],
            planned_c=3 * 2**30,
        )
        print(f"{name}: Q4_K_M quantization", flush=True)
        seconds_q4 = run_tool(
            [
                str(quantizer),
                str(f16),
                str(q4),
                "Q4_K_M",
                "4",
            ],
            planned_c=1200 * 2**20,
        )
        report["models"][name] = {
            "f16": {"bytes": f16.stat().st_size, "sha256": file_hash(f16)},
            "q4km": {"bytes": q4.stat().st_size, "sha256": file_hash(q4)},
            "f16_seconds": seconds_f16,
            "quantize_seconds": seconds_q4,
        }
    with summary.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print("both Q4_K_M artifacts ready; Ollama imports still pending", flush=True)


if __name__ == "__main__":
    main()

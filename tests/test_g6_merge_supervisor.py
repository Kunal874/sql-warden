import hashlib
import json
import subprocess

import pytest

from scripts import run_g6_merge as merge


def test_serving_storage_counts_e9_evidence_as_well_as_weights(tmp_path, monkeypatch):
    monkeypatch.setattr(merge, "ROOT", tmp_path)
    cache = tmp_path / "cache"
    conversion = tmp_path / "conversion"
    cache.mkdir()
    conversion.mkdir()
    (cache / "new-model").write_bytes(b"cache")
    (conversion / "base.gguf").write_bytes(b"gguf")
    raw = tmp_path / "results/G6_e9/raw"
    raw.mkdir(parents=True)
    (raw / "base.jsonl").write_bytes(b"evaluation")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {"models_directory": str(cache), "conversion_directory": str(conversion), "files": {}}
        )
    )
    monkeypatch.setattr(merge, "BASELINE", baseline)
    monkeypatch.setattr(merge, "disk_used", lambda: 100)
    assert merge.serving_storage() == (110, 9)


@pytest.fixture
def merge_report(tmp_path, monkeypatch):
    monkeypatch.setattr(merge, "ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    output = tmp_path / "models/g6/merged"
    output.mkdir(parents=True)
    artifact = output / "model.safetensors"
    artifact.write_bytes(b"merged")
    pin = {
        "model": "pinned-model",
        "revision": "pinned-revision",
        "selected_adapter": {"step": 400, "sha256": "a" * 64},
    }
    (tmp_path / "docs/g6-serving-inputs.json").write_text(json.dumps(pin))
    report = {
        "status": "completed",
        "model": pin["model"],
        "revision": pin["revision"],
        "selected_checkpoint": 400,
        "adapter_sha256": "a" * 64,
        "device": "cuda",
        "dtype": "float16",
        "preload_ram_bytes": 5 * 2**30,
        "elapsed_seconds": 10.0,
        "peak_reserved_bytes": 4 * 2**30,
        "changed_weights": True,
        "saved_tensors_equal": True,
        "reload_logits_equal": True,
        "generation_nonempty": True,
        "generation_sha256": "b" * 64,
        "artifact_files": {
            artifact.name: {"bytes": 6, "sha256": hashlib.sha256(b"merged").hexdigest()}
        },
        "git_commit": "c" * 40,
        "git_dirty": False,
    }
    monkeypatch.setattr(merge.subprocess, "check_output", lambda *a, **k: "c" * 40)
    summary = tmp_path / "merge.json"
    return report, summary, artifact


def test_publish_merge_checks_real_artifacts_and_preserves_evidence(merge_report):
    report, summary, _ = merge_report
    evidence = summary.with_suffix(".evidence.json")
    evidence.write_text(json.dumps(report))
    merge.publish_merge(summary)
    assert json.loads(summary.read_text()) == report
    assert evidence.exists()
    with pytest.raises(FileExistsError):
        merge.publish_merge(summary)


@pytest.mark.parametrize(
    "problem", ["incomplete", "extra", "dirty", "commit", "step", "artifact", "nan", "path"]
)
def test_publish_merge_refuses_invalid_or_changed_evidence(merge_report, problem):
    report, summary, artifact = merge_report
    if problem == "incomplete":
        report["reload_logits_equal"] = False
    elif problem == "extra":
        report["prompt"] = "must not be published"
    elif problem == "dirty":
        report["git_dirty"] = True
    elif problem == "commit":
        report["git_commit"] = "d" * 40
    elif problem == "step":
        report["selected_checkpoint"] = 500
    elif problem == "artifact":
        artifact.write_bytes(b"broken")
    elif problem == "nan":
        report["elapsed_seconds"] = float("nan")
    else:
        report["artifact_files"] = {"../outside": {"bytes": 0, "sha256": "a" * 64}}
    summary.with_suffix(".evidence.json").write_text(json.dumps(report))
    with pytest.raises((ValueError, RuntimeError)):
        merge.publish_merge(summary)
    assert not summary.exists()


@pytest.mark.parametrize("failure", ["resource", "timeout", "exit"])
def test_supervisor_kills_only_owned_child_and_does_not_publish(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(merge, "ROOT", tmp_path)
    baseline = tmp_path / "baseline.json"
    baseline.write_text("{}")
    monkeypatch.setattr(merge, "BASELINE", baseline)
    monkeypatch.setattr(merge, "serving_storage", lambda: (0, 0))
    monkeypatch.setattr(merge, "available_ram", lambda: 6 * 2**30)
    monkeypatch.setattr(
        merge.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 30 * 2**30})()
    )
    monkeypatch.setattr(merge.subprocess, "check_output", lambda *a, **k: b"")
    calls = []

    class Process:
        returncode = 1 if failure == "exit" else None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def poll(self):
            return self.returncode

        def wait(self, **kwargs):
            calls.append("wait")
            return self.returncode

        def kill(self):
            calls.append("kill")

    monkeypatch.setattr(merge.subprocess, "Popen", lambda *a, **k: Process())
    times = iter([0, 1201])
    monkeypatch.setattr(merge.time, "monotonic", lambda: next(times))

    def budget(*args, **kwargs):
        if failure == "resource" and kwargs.get("loading") is False:
            raise RuntimeError("resource limit")

    monkeypatch.setattr(merge, "check_serving_budget", budget)
    with pytest.raises((RuntimeError, subprocess.TimeoutExpired, subprocess.CalledProcessError)):
        merge.main()
    assert calls == ["kill", "wait"]
    assert not (tmp_path / "results/G6_training/merge.json").exists()

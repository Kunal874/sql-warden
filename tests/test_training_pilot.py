import json
import math
import subprocess
import sys

import pytest

from scripts.run_training_pilot import check_resources, supervise
from training.pilot import response_example, validate_losses


@pytest.mark.parametrize(
    ("ram", "disk", "used", "reason"),
    [(3, 30, 0, "RAM"), (8, 19, 0, "disk reserve"), (8, 30, 13, "disk budget")],
)
def test_resource_floor_refuses_loading(ram, disk, used, reason):
    with pytest.raises(RuntimeError, match=reason):
        check_resources(ram * 2**30, disk * 2**30, used * 2**30)


def test_resource_floor_allows_exact_boundary():
    check_resources(4 * 2**30, 20 * 2**30, 12 * 2**30)


def test_timeout_does_not_publish_summary(tmp_path):
    summary = tmp_path / "summary.json"
    with pytest.raises(subprocess.TimeoutExpired):
        supervise([sys.executable, "-c", "import time; time.sleep(10)"], summary, timeout=0.05)
    assert not summary.exists()


def test_failed_child_does_not_publish_summary(tmp_path):
    summary = tmp_path / "summary.json"
    with pytest.raises(subprocess.CalledProcessError):
        supervise([sys.executable, "-c", "raise SystemExit(2)"], summary, timeout=10)
    assert not summary.exists()


def test_supervisor_publishes_only_validated_evidence(tmp_path):
    summary = tmp_path / "summary.json"
    command = [sys.executable, "-c", "print(123)"]
    with pytest.raises(RuntimeError, match="evidence"):
        supervise(command, summary, timeout=10)
    assert not summary.exists()


def test_response_labels_mask_prompt_and_padding():
    example = response_example([10, 11], [20, 21], max_length=6, pad_id=0)
    assert example == {
        "input_ids": [10, 11, 20, 21, 0, 0],
        "attention_mask": [1, 1, 1, 1, 0, 0],
        "labels": [-100, -100, 20, 21, -100, -100],
    }


def test_overlong_example_is_refused_instead_of_truncated():
    with pytest.raises(ValueError, match="token limit"):
        response_example([10, 11, 12], [20, 21], max_length=4, pad_id=0)


@pytest.mark.parametrize("losses", [[], [math.nan], [math.inf], [1.0, -math.inf]])
def test_nonfinite_or_missing_loss_refuses_completion(losses):
    with pytest.raises(ValueError, match="loss"):
        validate_losses(losses, expected_steps=20)


def test_incomplete_steps_refuse_completion():
    with pytest.raises(ValueError, match="steps"):
        validate_losses([1.0] * 19, expected_steps=20)


def test_finite_complete_losses_are_serializable():
    losses = [1.0] * 20
    validate_losses(losses, expected_steps=20)
    assert len(json.loads(json.dumps(losses, allow_nan=False))) == 20


def test_evidence_with_raw_sql_is_never_published(tmp_path):
    summary = tmp_path / "summary.json"
    evidence = summary.with_suffix(".evidence.json")
    report = {
        "status": "completed",
        "device": "cuda",
        "adapter_changed": True,
        "adapter_reloaded": True,
        "losses": [1.0] * 20,
        "sql": "SELECT secret FROM users",
    }
    command = [
        sys.executable,
        "-c",
        "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(sys.argv[2])",
        str(evidence),
        json.dumps(report),
    ]
    with pytest.raises(RuntimeError, match="fields"):
        supervise(command, summary, timeout=10)
    assert not summary.exists()


def test_disk_monitor_stops_child_without_publishing(tmp_path):
    def limit_exceeded():
        raise RuntimeError("disk budget exceeded")

    summary = tmp_path / "summary.json"
    with pytest.raises(RuntimeError, match="disk budget"):
        supervise(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            summary,
            timeout=10,
            monitor=limit_exceeded,
        )
    assert not summary.exists()

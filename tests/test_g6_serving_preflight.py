import hashlib
import json

import pytest

from scripts.prepare_g6_serving import (
    cache_growth,
    cache_snapshot,
    check_serving_budget,
    merge_inputs,
)
from training.pilot import MODEL, REVISION

GIB = 2**30


def test_serving_budget_counts_both_drives_and_planned_output():
    check_serving_budget(6 * GIB, 24 * GIB, 10 * GIB, 5 * GIB, planned_d=3 * GIB)
    with pytest.raises(RuntimeError, match="24 GiB"):
        check_serving_budget(6 * GIB, 24 * GIB, 10 * GIB, 12 * GIB, planned_d=3 * GIB)


def test_serving_keeps_disk_reserve_after_planned_merge():
    with pytest.raises(RuntimeError, match="20 GiB"):
        check_serving_budget(6 * GIB, 22 * GIB, 10 * GIB, 0, planned_d=3 * GIB)


def test_full_merge_requires_the_existing_ram_floor():
    with pytest.raises(RuntimeError, match="4 GiB"):
        check_serving_budget(3 * GIB, 24 * GIB, 10 * GIB, 0)


def test_live_monitor_keeps_one_gib_without_reapplying_the_loading_floor():
    check_serving_budget(2 * GIB, 24 * GIB, 13 * GIB, 0, loading=False)
    with pytest.raises(RuntimeError, match="1 GiB"):
        check_serving_budget(GIB - 1, 24 * GIB, 13 * GIB, 0, loading=False)


def test_cache_growth_counts_only_new_files_and_refuses_old_cache_change(tmp_path):
    old = tmp_path / "old-blob"
    old.write_bytes(b"old")
    baseline = cache_snapshot(tmp_path)
    (tmp_path / "new-blob").write_bytes(b"new-model")
    assert cache_growth(tmp_path, baseline) == 9
    old.write_bytes(b"changed")
    with pytest.raises(ValueError, match="existing Ollama cache"):
        cache_growth(tmp_path, baseline)


def test_missing_cache_directory_cannot_be_counted_as_zero(tmp_path):
    with pytest.raises(ValueError, match="cache directory"):
        cache_snapshot(tmp_path / "missing")


def test_serving_budget_refuses_negative_measurements():
    with pytest.raises(ValueError, match="negative"):
        check_serving_budget(6 * GIB, 24 * GIB, 10 * GIB, -1)


@pytest.fixture
def pinned_inputs(tmp_path):
    base = (
        tmp_path / f"models/g6/cache/models--Qwen--Qwen2.5-Coder-1.5B-Instruct/snapshots/{REVISION}"
    )
    adapter = tmp_path / "models/g6/full-adapters/step-400"
    base.mkdir(parents=True)
    adapter.mkdir(parents=True)
    (base / "model.safetensors").write_bytes(b"base")
    (adapter / "adapter_model.safetensors").write_bytes(b"adapter")
    (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")

    def sha(value):
        return hashlib.sha256(value).hexdigest()

    pin = {
        "model": MODEL,
        "revision": REVISION,
        "base_weights": {"bytes": 4, "sha256": sha(b"base")},
        "selected_adapter": {"step": 400, "sha256": sha(b"adapter"), "config_sha256": sha(b"{}")},
    }
    report = {
        "status": "completed",
        "model": MODEL,
        "revision": REVISION,
        "git_dirty": False,
        "chosen_checkpoint": 400,
        "adapter_sha256": sha(b"adapter"),
        "checkpoints": [{"step": 400, "loss": 0.1}, {"step": 500, "loss": 0.2}],
    }
    (tmp_path / "docs").mkdir()
    (tmp_path / "results/G6_training").mkdir(parents=True)
    (tmp_path / "docs/g6-serving-inputs.json").write_text(json.dumps(pin), encoding="utf-8")
    (tmp_path / "results/G6_training/summary.json").write_text(json.dumps(report), encoding="utf-8")
    return tmp_path, base, adapter


def test_merge_uses_the_validation_selected_checkpoint(pinned_inputs):
    root, base, adapter = pinned_inputs
    assert merge_inputs(root) == (base, adapter)


@pytest.mark.parametrize("name", ["base", "adapter", "config", "selection"])
def test_merge_refuses_changed_inputs_or_nonselected_checkpoint(pinned_inputs, name):
    root, base, adapter = pinned_inputs
    if name == "selection":
        path = root / "docs/g6-serving-inputs.json"
        pin = json.loads(path.read_text())
        pin["selected_adapter"]["step"] = 500
        path.write_text(json.dumps(pin), encoding="utf-8")
    else:
        path = {
            "base": base / "model.safetensors",
            "adapter": adapter / "adapter_model.safetensors",
            "config": adapter / "adapter_config.json",
        }[name]
        path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="merge"):
        merge_inputs(root)

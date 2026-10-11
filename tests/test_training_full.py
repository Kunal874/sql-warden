import hashlib
import json

import pytest

from training.full import choose_checkpoint, load_tokenized


def test_checkpoint_choice_uses_validation_loss_and_earlier_tie():
    checkpoints = [
        {"step": 100, "loss": 1.2},
        {"step": 200, "loss": 0.8},
        {"step": 300, "loss": 0.8},
    ]
    assert choose_checkpoint(checkpoints) == 200


def test_nonfinite_checkpoint_metric_refuses_selection():
    with pytest.raises(ValueError, match="validation"):
        choose_checkpoint([{"step": 100, "loss": float("nan")}])


def test_corrupt_token_file_refuses_loading(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint"):
        load_tokenized(path, "0" * 64, max_length=4)


def test_all_masked_answer_refuses_training(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(
        json.dumps(
            {
                "source_index": 1,
                "db_id": "toy",
                "input_ids": [1, 2, 3, 0],
                "attention_mask": [1, 1, 1, 0],
                "labels": [-100] * 4,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="labels"):
        load_tokenized(path, digest, max_length=4)


def test_answer_labels_must_match_input_tokens(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(
        json.dumps(
            {
                "source_index": 1,
                "db_id": "toy",
                "input_ids": [1, 2, 3, 0],
                "attention_mask": [1, 1, 1, 0],
                "labels": [-100, -100, 99, -100],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="labels"):
        load_tokenized(path, digest, max_length=4)

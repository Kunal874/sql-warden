import hashlib
import json

import pytest

from scripts.build_e9_report import summarize_pair


def record(qid, correct, model):
    return {
        "question_id": qid,
        "generator": model,
        "gold_corrected_valid": True,
        "final_ex_corrected": correct,
        "status": "answered" if correct else "abstained",
        "reason": "single_candidate" if correct else "no_valid_candidate",
        "seconds": qid,
        "calls": [],
        "candidates": [],
    }


def test_report_pairs_by_id_and_keeps_failures_in_denominator():
    base = [record(1, 0, "base"), record(2, 1, "base")]
    tuned = [record(2, 0, "tuned"), record(1, 1, "tuned")]
    report = summarize_pair(base, tuned, [1, 2])
    assert report["base"]["accuracy"]["ex"]["rate"] == 0.5
    assert report["tuned_vs_base"]["difference"] == 0
    assert report["tuned_vs_base"]["left_only"] == 1
    assert report["tuned_vs_base"]["right_only"] == 1
    assert report["base"]["latency"]["peak_vram_bytes"] is None
    assert report["base"]["failures"] == {"no_valid_candidate": 1}


@pytest.mark.parametrize("bad", ["missing", "duplicate", "gold", "score", "cache", "generator"])
def test_report_refuses_incomplete_or_incomparable_records(bad):
    base = [record(1, 0, "base"), record(2, 1, "base")]
    tuned = [record(1, 1, "tuned"), record(2, 1, "tuned")]
    if bad == "missing":
        tuned.pop()
    elif bad == "duplicate":
        tuned[1]["question_id"] = 1
    elif bad == "gold":
        tuned[0]["gold_corrected_valid"] = False
    elif bad == "score":
        tuned[0]["final_ex_corrected"] = None
    elif bad == "cache":
        tuned[0]["calls"] = [{"cache_hit": True}]
    else:
        tuned[0]["generator"] = "base"
    with pytest.raises(ValueError, match="E9"):
        summarize_pair(base, tuned, [1, 2])


@pytest.fixture
def report_files(tmp_path, monkeypatch):
    from scripts import build_e9_report

    serving = {
        name: {
            "name": name,
            "alias": f"sqlwarden-{name}:e9-v1",
            "digest": digit * 64,
            "context_tokens": 8192,
            "max_output_tokens": 3072,
            "quantization": "Q4_K_M",
        }
        for name, digit in [("base", "a"), ("tuned", "b")]
    }
    (tmp_path / "docs").mkdir()
    serving_path = tmp_path / "docs/g6-serving-manifest.json"
    serving_path.write_text(json.dumps(serving), encoding="utf-8")
    for split in ["dev", "held_out"]:
        directory = tmp_path / "raw" / split
        directory.mkdir(parents=True)
        for name in ["base", "tuned"]:
            row = record(1, name == "tuned", name) | {"sql": "private-test-sql"}
            row["final_ex_corrected"] = int(row["final_ex_corrected"])
            (directory / f"{name}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
            manifest = {
                "experiment": "E9",
                "split": split,
                "git": {"dirty": False, "commit": "clean"},
                "generator": {
                    key: value for key, value in serving[name].items() if key != "quantization"
                },
                "serving_sha256": hashlib.sha256(serving_path.read_bytes()).hexdigest(),
            }
            manifest["fingerprint"] = hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode()
            ).hexdigest()
            (directory / f"{name}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(build_e9_report, "ROOT", tmp_path)
    monkeypatch.setattr(build_e9_report, "RAW", tmp_path / "raw")
    monkeypatch.setattr(build_e9_report, "build_items", lambda split: [{"question_id": 1}])
    return tmp_path


def test_report_writer_contains_metrics_not_raw_sql(report_files):
    from scripts.build_e9_report import main

    main()
    output = report_files / "results/G6_e9/summary.json"
    assert "private-test-sql" not in output.read_text()
    report = json.loads(output.read_text())
    assert report["splits"]["held_out"]["tuned_vs_base"]["difference"] == 1


def test_report_refuses_altered_generator_even_with_matching_digest(report_files):
    from scripts.build_e9_report import main

    path = report_files / "raw/dev/tuned.manifest.json"
    manifest = json.loads(path.read_text())
    manifest.pop("fingerprint")
    manifest["generator"]["alias"] = "sqlwarden-unmatched:e9-v1"
    manifest["fingerprint"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()
    ).hexdigest()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="provenance"):
        main()
    assert not (report_files / "results/G6_e9/summary.json").exists()

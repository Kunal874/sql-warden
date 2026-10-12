import copy
import hashlib
import json

import pytest


def row(qid, score, repairs):
    return {
        "question_id": qid,
        "generator": "tuned",
        "experiment": "E10-dev-repair",
        "condition": "full_n1_k1" if repairs else "full_n1",
        "gold_corrected_valid": True,
        "final_ex_corrected": score,
        "status": "answered" if score else "abstained",
        "reason": "single_candidate" if score else "no_valid_candidate",
        "calls": [],
        "seconds": 2 if repairs else 1,
        "candidates": [{"status": "ok", "repairs": repairs, "attempts": [{"sql": "private"}]}],
    }


def test_repair_report_measures_paired_gain_and_cost_without_private_sql():
    from scripts.build_repair_report import summarize

    baseline = [row(1, 0, 0), row(2, 1, 0)]
    repaired = [row(2, 1, 1), row(1, 1, 1)]
    before = copy.deepcopy(repaired)
    report = summarize(baseline, repaired, [1, 2])
    assert report["k0"]["accuracy"]["ex"]["count"] == 1
    assert report["k1_vs_k0"]["difference"] == 0.5
    assert report["k1"]["latency"]["median_item_seconds"] == 2
    assert report["repair_attempts"] == 2
    assert "private" not in json.dumps(report)
    assert repaired == before


@pytest.mark.parametrize("bad", ["condition", "experiment", "generator", "repairs", "calls"])
def test_repair_report_refuses_wrong_or_over_budget_records(bad):
    from scripts.build_repair_report import summarize

    baseline, repaired = [row(1, 0, 0)], [row(1, 1, 1)]
    if bad == "repairs":
        repaired[0]["candidates"][0]["repairs"] = 2
    elif bad == "calls":
        repaired[0]["calls"] = [{"role": "generate"}] * 3
    else:
        repaired[0][bad] = "wrong"
    with pytest.raises(ValueError, match="repair"):
        summarize(baseline, repaired, [1])


@pytest.mark.parametrize("changed", [None, "git", "prompt", "config", "tail"])
def test_report_writer_checks_matching_provenance(tmp_path, monkeypatch, changed):
    from scripts import build_repair_report as report
    from scripts.run_e9 import load_generators
    from tests.test_run_e9 import serving_manifest

    (tmp_path / "docs").mkdir()
    serving = tmp_path / "docs/g6-serving-manifest.json"
    serving.write_text(json.dumps(serving_manifest()))
    from dataclasses import asdict

    generator = asdict(load_generators(serving)["tuned"])
    directory = tmp_path / "raw/repair/dev"
    directory.mkdir(parents=True)
    for repairs in (0, 1):
        manifest = {
            "experiment": "E10-dev-repair",
            "split": "dev",
            "condition": "full_n1_k1" if repairs else "full_n1",
            "config": {"max_repairs": repairs, "candidates": 1},
            "git": {"dirty": False, "commit": "clean"},
            "generator": generator,
            "prompts": "fixed",
            "serving_sha256": hashlib.sha256(serving.read_bytes()).hexdigest(),
        }
        if repairs and changed == "git":
            manifest["git"]["commit"] = "different"
        if repairs and changed == "prompt":
            manifest["prompts"] = "different"
        if repairs and changed == "config":
            manifest["config"]["candidates"] = 3
        manifest["fingerprint"] = hashlib.sha256(
            json.dumps(manifest, sort_keys=True).encode()
        ).hexdigest()
        (directory / f"k{repairs}.manifest.json").write_text(json.dumps(manifest))
        (directory / f"k{repairs}.jsonl").write_text(
            json.dumps(row(1, repairs, repairs)) + ("" if changed == "tail" else "\n")
        )
    monkeypatch.setattr(report, "ROOT", tmp_path)
    monkeypatch.setattr(report, "RAW", tmp_path / "raw")
    monkeypatch.setattr(report, "build_items", lambda split: [{"question_id": 1}])
    monkeypatch.setattr(report, "check_e9_resources", lambda **kwargs: None)
    if changed:
        with pytest.raises(ValueError, match="repair"):
            report.main()
    else:
        report.main()
        result = json.loads((tmp_path / "results/G6_e9/repair/summary.json").read_text())
        assert result["k1_vs_k0"]["difference"] == 1

import json

from scripts import build_evaluation_artifacts


def test_builds_compact_dashboard_matrix_and_failure_labels_without_raw_text():
    protocol = {
        "split": {"dev_ids": [1, 2, 3], "dev_id_sha256": "abc"},
        "metrics": {"bootstrap": {"seed": 5, "samples": 200}},
    }
    records = {
        "arctic": [
            {"question_id": 1, "db_id": "financial", "model": "arctic", "status": "correct"},
            {
                "question_id": 2,
                "db_id": "financial",
                "model": "arctic",
                "status": "incorrect",
                "reason": "result_mismatch",
                "sql": "SELECT raw",
                "messages": [{"content": "prompt"}],
            },
            {
                "question_id": 3,
                "db_id": "financial",
                "model": "arctic",
                "status": "blocked",
                "reason": "table_not_allowed",
            },
        ],
        "qwen": [
            {"question_id": 1, "db_id": "financial", "model": "qwen", "status": "incorrect"},
            {
                "question_id": 2,
                "db_id": "financial",
                "model": "qwen",
                "status": "generation_failed",
                "reason": "prompt_budget",
            },
            {"question_id": 3, "db_id": "financial", "model": "qwen", "status": "correct"},
        ],
    }

    artifacts = build_evaluation_artifacts.build_artifacts(protocol, records)
    rendered = json.dumps(artifacts, sort_keys=True)

    assert artifacts["summary"]["models"]["arctic"]["phase_metrics"]["guard"]["count"] == 2
    assert artifacts["summary"]["paired"]["arctic_vs_qwen"]["paired_count"] == 3
    assert artifacts["dashboard"]["models"]["qwen"]["answered_only_ex"] == 0.5
    assert artifacts["failures"]["label_count"] == 4
    assert len(artifacts["failures"]["labels"]) == 4
    assert "Arctic measured 1/3 exact matches" in artifacts["resume"]
    assert "not an official benchmark" in artifacts["resume"]
    assert {item["id"] for item in artifacts["matrix"]["experiments"]} == {
        "E1",
        "E2",
        "E3",
        "E4",
        "E6",
        "E7",
        "E8",
    }
    assert artifacts["matrix"]["time_budget"]["weekly_hours"] == "15-20"
    assert "SELECT raw" not in rendered
    assert '"content": "prompt"' not in rendered

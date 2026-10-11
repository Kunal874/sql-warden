from scripts.update_evaluation_matrix import matrix

FROZEN = {"format_version": 1, "protocol": {"dev_count": 100}, "rules": ["r"], "deferred": {}}


def _records(n, seconds=36.0):
    return [{"question_id": i, "seconds": seconds} for i in range(n)]


def test_status_comes_from_complete_runs_and_frozen_fields_are_kept():
    runs = {("dev", "messy_n1"): _records(100), ("held_out", "ret_n3_k1"): _records(10)}

    result = matrix(FROZEN, runs, e5_done=True)
    by_id = {e["id"]: e for e in result["experiments"]}

    assert by_id["E4"]["status"] == "complete"
    assert by_id["E8"]["status"] == "pending"
    assert by_id["E8"]["runs"] == [
        {"run": "held_out/ret_n3_k1", "items": 10, "expected": 324, "hours": 0.1}
    ]
    assert by_id["E5"]["status"] == "complete"
    assert by_id["E9"]["status"] == "not_run"
    assert result["protocol"] == FROZEN["protocol"] and result["rules"] == ["r"]
    assert "deferred" not in result


def test_hours_count_clarification_and_resume_time_once_per_run():
    record = {"question_id": 1, "ask_seconds": 1800, "resume_seconds": 1800}
    runs = {("dev", "clarify_oracle"): [record], ("dev", "ret_n3_k1"): _records(100)}

    result = matrix(FROZEN, runs, e5_done=False)

    assert result["measured_run_hours"]["dev/clarify_oracle"] == 1.0
    assert result["measured_run_hours"]["total"] == 2.0
    assert {e["id"]: e["status"] for e in result["experiments"]}["E5"] == "pending"

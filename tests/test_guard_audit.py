import json

from scripts import audit_guard_gold


def test_guard_case_inventory_has_at_least_forty_meaningful_cases():
    inventory = audit_guard_gold.guard_case_inventory()

    assert inventory["safe_cases"] >= 40
    assert inventory["unsafe_cases"] >= 40
    assert inventory["total_cases"] >= 80


def test_guard_audit_summary_is_compact_and_excludes_sql_text():
    records = [
        {"question_id": 1, "db_id": "california_schools", "status": "accepted"},
        {
            "question_id": 2,
            "db_id": "financial",
            "status": "blocked",
            "reason": "function_not_allowed",
        },
        {"question_id": 3, "db_id": "financial", "status": "transpile_failed"},
    ]

    summary = audit_guard_gold.summarize(records, source_sha256="a" * 64)
    rendered = json.dumps(summary, sort_keys=True)

    assert summary["items"] == 3
    assert summary["status_counts"] == {"accepted": 1, "blocked": 1, "transpile_failed": 1}
    assert summary["blocked_reason_counts"] == {"function_not_allowed": 1}
    assert summary["by_db"]["financial"] == {
        "accepted": 0,
        "blocked": 1,
        "transpile_failed": 1,
    }
    assert "SELECT" not in rendered.upper()
    assert "password" not in rendered.lower()

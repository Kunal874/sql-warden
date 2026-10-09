import json
from pathlib import Path

from sqlwarden.config import QueryLimits
from sqlwarden.guard import CALIFORNIA_POLICY, CAST_TYPES, FUNCTION_NAMES, guard_sql
from sqlwarden.security_contract import (
    DEFAULT_QUERY_LIMITS,
    EXECUTOR_REASON_STATUS,
    REVIEWED_CAST_TYPES,
    REVIEWED_FUNCTIONS,
    TENANT_AUTHORIZATION_DESIGN,
)


def test_reviewed_function_contract_is_exactly_the_runtime_allowlist():
    reviewed = {item["sqlglot_class"] for item in REVIEWED_FUNCTIONS}

    assert reviewed == FUNCTION_NAMES
    assert reviewed == {
        "Abs",
        "Avg",
        "Coalesce",
        "Count",
        "Length",
        "Lower",
        "Max",
        "Min",
        "Nullif",
        "Round",
        "RowNumber",
        "Sum",
        "Upper",
    }
    assert guard_sql("SELECT lower('ABC')", CALIFORNIA_POLICY).accepted
    assert not guard_sql("SELECT pg_catalog.lower('ABC')", CALIFORNIA_POLICY).accepted
    assert not guard_sql("SELECT set_config('search_path','app',false)", CALIFORNIA_POLICY).accepted


def test_reviewed_cast_and_limit_contracts_are_exact_runtime_values():
    reviewed = {item["type"] for item in REVIEWED_CAST_TYPES}

    assert reviewed == CAST_TYPES
    assert reviewed == {"BIGINT", "BOOLEAN", "DATE", "DECIMAL", "DOUBLE", "FLOAT", "INT", "TEXT"}
    assert QueryLimits() == DEFAULT_QUERY_LIMITS
    assert DEFAULT_QUERY_LIMITS.total_timeout_ms == 15000
    assert DEFAULT_QUERY_LIMITS.max_estimated_cost == 100000
    assert DEFAULT_QUERY_LIMITS.max_estimated_rows == 100000


def test_c4_tenant_design_rejects_mutable_session_setting_boundary():
    assert TENANT_AUTHORIZATION_DESIGN == {
        "tenant_selector": "server_chosen_database_role",
        "rls": "force_role_specific_policies_in_g2_6",
        "mutable_session_setting_boundary": "rejected",
        "client_supplied_tenant_id": "rejected",
    }


def test_executor_reason_contract_documents_stable_status_categories():
    assert EXECUTOR_REASON_STATUS == {
        "accepted": "blocked",
        "cell_limit": "overflow",
        "configuration_error": "failed",
        "connection_error": "failed",
        "cost_limit": "blocked",
        "database_error": "failed",
        "identifier_invalid": "blocked",
        "input_invalid": "blocked",
        "input_limit": "blocked",
        "internal_error": "failed",
        "ok": "ok",
        "parse_error": "blocked",
        "permission_error": "failed",
        "plan_error": "failed",
        "plan_limit": "failed",
        "plan_row_limit": "blocked",
        "result_limit": "overflow",
        "row_limit": "overflow",
        "schema_not_allowed": "blocked",
        "statement_not_allowed": "blocked",
        "syntax_error": "failed",
        "table_not_allowed": "blocked",
        "timeout": "failed",
        "undefined_object": "failed",
        "unsupported_node": "blocked",
        "unsupported_relation": "blocked",
        "unsupported_result": "failed",
    }
    assert set(EXECUTOR_REASON_STATUS.values()) == {"ok", "blocked", "failed", "overflow"}


def test_executor_cost_calibration_manifest_matches_query_limit_defaults():
    manifest = json.loads(Path("docs/executor-cost-calibration-manifest.json").read_text())

    assert manifest["default_limits"] == {
        "max_estimated_cost": QueryLimits().max_estimated_cost,
        "max_estimated_rows": QueryLimits().max_estimated_rows,
        "statement_timeout_ms": QueryLimits().statement_timeout_ms,
        "lock_timeout_ms": QueryLimits().lock_timeout_ms,
        "total_timeout_ms": QueryLimits().total_timeout_ms,
    }
    assert manifest["explain_policy"] == {
        "guard_before_explain": True,
        "format": "EXPLAIN (FORMAT JSON)",
        "analyze": False,
        "identity": "same_restricted_dataset_identity_as_execution",
    }

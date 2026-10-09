from sqlwarden.config import QueryLimits
from sqlwarden.guard import CALIFORNIA_POLICY, CAST_TYPES, FUNCTION_NAMES, guard_sql
from sqlwarden.security_contract import (
    DEFAULT_QUERY_LIMITS,
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

"""Reviewed local security choices for G2/C4."""

from __future__ import annotations

from types import MappingProxyType

from sqlwarden.config import QueryLimits

REVIEWED_FUNCTIONS = (
    {"sqlglot_class": "Abs", "sql_names": ("abs",), "reason": "numeric magnitude only"},
    {"sqlglot_class": "Avg", "sql_names": ("avg",), "reason": "aggregate only"},
    {"sqlglot_class": "Coalesce", "sql_names": ("coalesce",), "reason": "null handling only"},
    {"sqlglot_class": "Count", "sql_names": ("count",), "reason": "aggregate only"},
    {"sqlglot_class": "Length", "sql_names": ("length",), "reason": "string length only"},
    {"sqlglot_class": "Lower", "sql_names": ("lower",), "reason": "string case only"},
    {"sqlglot_class": "Max", "sql_names": ("max",), "reason": "aggregate only"},
    {"sqlglot_class": "Min", "sql_names": ("min",), "reason": "aggregate only"},
    {"sqlglot_class": "Nullif", "sql_names": ("nullif",), "reason": "null handling only"},
    {"sqlglot_class": "Round", "sql_names": ("round",), "reason": "numeric rounding only"},
    {"sqlglot_class": "RowNumber", "sql_names": ("row_number",), "reason": "window ordinal only"},
    {"sqlglot_class": "Sum", "sql_names": ("sum",), "reason": "aggregate only"},
    {"sqlglot_class": "Upper", "sql_names": ("upper",), "reason": "string case only"},
)
REVIEWED_CAST_TYPES = (
    {"type": "BIGINT", "reason": "scalar numeric display/conversion"},
    {"type": "BOOLEAN", "reason": "scalar boolean display/conversion"},
    {"type": "DATE", "reason": "scalar date display/conversion"},
    {"type": "DECIMAL", "reason": "scalar numeric display/conversion"},
    {"type": "DOUBLE", "reason": "scalar numeric display/conversion"},
    {"type": "FLOAT", "reason": "scalar numeric display/conversion"},
    {"type": "INT", "reason": "scalar numeric display/conversion"},
    {"type": "TEXT", "reason": "scalar text display/conversion"},
)
DEFAULT_QUERY_LIMITS = QueryLimits()
TENANT_AUTHORIZATION_DESIGN = MappingProxyType(
    {
        "tenant_selector": "server_chosen_database_role",
        "rls": "force_role_specific_policies_in_g2_6",
        "mutable_session_setting_boundary": "rejected",
        "client_supplied_tenant_id": "rejected",
    }
)
EXECUTOR_REASON_STATUS = MappingProxyType(
    {
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
)


def allowed_function_classes() -> frozenset[str]:
    return frozenset(item["sqlglot_class"] for item in REVIEWED_FUNCTIONS)


def allowed_cast_type_names() -> frozenset[str]:
    return frozenset(item["type"] for item in REVIEWED_CAST_TYPES)

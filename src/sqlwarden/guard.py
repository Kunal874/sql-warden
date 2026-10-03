"""Pure, fail-closed checks; acceptance is not permission to execute a query."""

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, OptimizeError, ParseError, TokenError
from sqlglot.optimizer.scope import Scope, traverse_scope

MAX_SQL_BYTES = 8192
MAX_AST_NODES = 1000
MAX_AST_DEPTH = 64
ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

STRUCTURAL_NAMES = frozenset(
    [
        "Select",
        "Union",
        "Intersect",
        "Except",
        "With",
        "CTE",
        "Subquery",
        "Table",
        "TableAlias",
        "Identifier",
        "Column",
        "Star",
        "Literal",
        "Null",
        "Boolean",
        "Alias",
        "From",
        "Join",
        "Where",
        "Group",
        "Having",
        "Order",
        "Ordered",
        "Limit",
        "Offset",
        "Distinct",
        "Paren",
        "And",
        "Or",
        "Not",
        "EQ",
        "NEQ",
        "GT",
        "GTE",
        "LT",
        "LTE",
        "Is",
        "In",
        "Between",
        "Exists",
        "Like",
        "ILike",
        "Add",
        "Sub",
        "Mul",
        "Div",
        "Mod",
        "Neg",
        "Case",
        "If",
        "Cast",
        "DataType",
        "Tuple",
        "Values",
        "Filter",
        "Window",
        "WindowSpec",
    ]
)
FUNCTION_NAMES = frozenset(
    [
        "Count",
        "Sum",
        "Avg",
        "Min",
        "Max",
        "Abs",
        "Round",
        "Length",
        "Lower",
        "Upper",
        "Coalesce",
        "Nullif",
        "RowNumber",
    ]
)
CAST_TYPES = frozenset(["INT", "BIGINT", "FLOAT", "DOUBLE", "DECIMAL", "TEXT", "DATE", "BOOLEAN"])
ALLOWED_NODES = frozenset(getattr(exp, name) for name in STRUCTURAL_NAMES | FUNCTION_NAMES)
QUERY_ROOTS = frozenset({exp.Select, exp.Union, exp.Intersect, exp.Except})


def _valid_name(name: str) -> bool:
    if not isinstance(name, str) or not name or "\x00" in name:
        return False
    try:
        return len(name.encode("utf-8")) <= 63
    except UnicodeEncodeError:
        return False


@dataclass(frozen=True, slots=True)
class DatasetPolicy:
    """Exact physical names supplied by trusted server configuration."""

    schema: str
    tables: frozenset[str]

    def __post_init__(self) -> None:
        if not _valid_name(self.schema):
            raise ValueError("Invalid dataset schema name")
        if (
            not isinstance(self.tables, frozenset)
            or not self.tables
            or not all(_valid_name(table) for table in self.tables)
        ):
            raise ValueError("Invalid dataset table allowlist")


CALIFORNIA_POLICY = DatasetPolicy("california_schools", frozenset({"schools", "frpm", "satscores"}))


@dataclass(frozen=True, slots=True)
class GuardDecision:
    accepted: bool
    reason: str
    sql: str | None


def _check_nodes(tree: exp.Expression) -> str | None:
    reasons = set()
    for node in tree.walk():
        kind = type(node)
        if isinstance(node, (exp.DDL, exp.DML, exp.Into, exp.Lock, exp.Copy, exp.Set, exp.Command)):
            reasons.add("modifying_node")
        if isinstance(node, exp.Func) and kind not in ALLOWED_NODES:
            reasons.add("function_not_allowed")
        if kind is exp.If and (
            type(node.parent) is not exp.Case or node not in node.parent.args.get("ifs", [])
        ):
            reasons.add("function_not_allowed")
        if isinstance(node, exp.Cast) and (
            kind is not exp.Cast
            or type(node.args.get("to")) is not exp.DataType
            or any(value for key, value in node.args.items() if key not in {"this", "to"})
        ):
            reasons.add("cast_not_allowed")
        if kind is exp.DataType and (
            getattr(node.this, "name", None) not in CAST_TYPES
            or any(value for key, value in node.args.items() if key != "this")
            or type(node.parent) is not exp.Cast
            or node.parent.args.get("to") is not node
        ):
            reasons.add("cast_not_allowed")
        if kind is exp.Join and (
            node.side not in ("", "LEFT", "RIGHT", "FULL")
            or node.kind not in ("", "INNER", "OUTER", "CROSS")
            or node.method not in ("", "NATURAL")
            or any(
                value
                for key, value in node.args.items()
                if key not in {"this", "on", "side", "kind", "using", "method"}
            )
        ):
            reasons.add("unsupported_node")
        if kind not in ALLOWED_NODES:
            reasons.add("unsupported_node")
    return next(
        (
            reason
            for reason in (
                "modifying_node",
                "function_not_allowed",
                "cast_not_allowed",
                "unsupported_node",
            )
            if reason in reasons
        ),
        None,
    )


def _check_tables(tree: exp.Expression, policy: DatasetPolicy) -> str | None:
    # Unsupported CTE bodies can make SQLGlot log raw SQL during scope traversal.
    for cte in tree.find_all(exp.CTE):
        body = cte.this.unnest() if isinstance(cte.this, exp.Expression) else None
        if type(body) not in QUERY_ROOTS | {exp.Values}:
            return "unsupported_relation"
    seen_tables = set()
    try:
        scopes = traverse_scope(tree)
        if not scopes:
            return "unsupported_relation"
        for scope in scopes:
            for node, source in scope.selected_sources.values():
                if isinstance(node, exp.Table):
                    seen_tables.add(id(node))
                    if isinstance(source, Scope) and (node.catalog or node.db):
                        return "schema_not_allowed"
                if isinstance(source, exp.Table):
                    seen_tables.add(id(source))
                    if not isinstance(source.this, exp.Identifier):
                        return "unsupported_relation"
                    if source.catalog or source.db not in ("", policy.schema):
                        return "schema_not_allowed"
                    if source.name not in policy.tables:
                        return "table_not_allowed"
                elif not isinstance(source, Scope):
                    return "unsupported_relation"
        if any(id(table) not in seen_tables for table in tree.find_all(exp.Table)):
            return "unsupported_relation"
    except (OptimizeError, RecursionError):
        return "unsupported_relation"
    return None


def guard_sql(sql: str, policy: DatasetPolicy) -> GuardDecision:
    """Inspect an analysis tree without rewriting SQL or accessing external systems."""
    if not isinstance(sql, str) or not sql.strip() or "\x00" in sql:
        return GuardDecision(False, "input_invalid", None)
    try:
        sql_bytes = sql.encode("utf-8")
    except UnicodeEncodeError:
        return GuardDecision(False, "input_invalid", None)
    if len(sql_bytes) > MAX_SQL_BYTES:
        return GuardDecision(False, "input_limit", None)
    try:
        statements = sqlglot.parse(
            sql, read="postgres", error_level=ErrorLevel.RAISE, error_message_context=0
        )
    except (ParseError, TokenError, RecursionError, IndexError):
        return GuardDecision(False, "parse_error", None)
    if len(statements) != 1 or statements[0] is None:
        return GuardDecision(False, "statement_not_allowed", None)
    tree = statements[0]
    root = tree
    while type(root) in (exp.Subquery, exp.Paren) and not any(
        value for key, value in root.args.items() if key != "this"
    ):
        root = root.this
    if type(root) not in QUERY_ROOTS:
        return GuardDecision(False, "statement_not_allowed", None)

    nodes = []
    pending = [(tree, 0)]
    while pending:
        node, depth = pending.pop()
        nodes.append(node)
        if len(nodes) > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            return GuardDecision(False, "ast_limit", None)
        pending.extend((child, depth + 1) for child in node.iter_expressions())
    for node in nodes:
        if isinstance(node, exp.Identifier):
            if not _valid_name(node.this):
                return GuardDecision(False, "identifier_invalid", None)
            if not node.args.get("quoted"):
                node.set("this", node.this.translate(ASCII_LOWER))

    reason = _check_nodes(tree) or _check_tables(tree, policy)
    if reason:
        return GuardDecision(False, reason, None)
    return GuardDecision(True, "accepted", sql)

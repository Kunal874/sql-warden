"""A read guard must understand every relation and never return rejected SQL."""

import subprocess
import sys
from dataclasses import FrozenInstanceError

import pytest
from sqlglot import exp
from sqlglot.errors import OptimizeError, ParseError, TokenError

from sqlwarden.guard import CALIFORNIA_POLICY, DATASET_POLICIES, DatasetPolicy, guard_sql

SAFE = [
    "SELECT 1",
    "SELECT '; DROP TABLE schools'",
    "SELECT count(*) FROM schools",
    'SELECT "School Name" FROM schools WHERE "County" = \'Alameda\'',
    "SELECT s.cdscode FROM schools AS s",
    "SELECT cdscode FROM california_schools.schools",
    'SELECT cdscode FROM "california_schools"."schools"',
    "SELECT cdscode FROM SCHOOLS",
    "SELECT cdscode FROM SCHOOLS /* sqlglot.meta case_sensitive */",
    "SELECT cdscode FROM schools -- DROP is a harmless comment",
    "WITH x AS (SELECT cdscode FROM schools) SELECT * FROM x",
    "WITH schools AS (SELECT 1 AS x) SELECT x FROM schools",
    "WITH x AS (SELECT cdscode FROM schools), y AS (SELECT * FROM x) SELECT * FROM y",
    "WITH X AS (SELECT 1) SELECT * FROM X /* sqlglot.meta case_sensitive */",
    "SELECT * FROM (SELECT cdscode FROM schools) AS x",
    "SELECT s.cdscode FROM schools s WHERE EXISTS (SELECT 1 FROM frpm f WHERE f.cdscode=s.cdscode)",
    "SELECT cdscode FROM schools UNION SELECT cdscode FROM frpm",
    "SELECT cdscode FROM schools INTERSECT SELECT cdscode FROM frpm",
    "SELECT cdscode FROM schools EXCEPT SELECT cdscode FROM frpm",
    "SELECT count(DISTINCT cdscode) FROM schools",
    'SELECT "County", count(*) FROM schools GROUP BY "County" HAVING count(*) > 1',
    "SELECT cdscode FROM schools ORDER BY cdscode DESC NULLS LAST LIMIT 2 OFFSET 1",
    "SELECT CASE WHEN 1=1 THEN coalesce(NULL, 2) ELSE 3 END",
    "SELECT CAST(1 AS bigint), CAST('2020-01-01' AS date)",
    "SELECT row_number() OVER (ORDER BY cdscode) FROM schools",
]
UNSAFE = [
    "SELECT 1; SELECT 2",
    "SELECT 1; DROP TABLE schools",
    "INSERT INTO schools(cdscode) VALUES ('x')",
    "UPDATE schools SET cdscode='x'",
    "DELETE FROM schools",
    "CREATE TABLE x(a int)",
    "ALTER TABLE schools ADD x int",
    "TRUNCATE schools",
    "COPY schools TO STDOUT",
    "SET search_path=app",
    "CALL x()",
    "DO $$BEGIN NULL; END$$",
    "WITH x AS (DELETE FROM schools RETURNING *) SELECT * FROM x",
    "WITH x AS (UPDATE schools SET cdscode='x' RETURNING *) SELECT * FROM x",
    "SELECT * INTO x FROM schools",
    "SELECT * FROM schools FOR UPDATE",
    "SELECT * FROM schools FOR SHARE",
    "SELECT * FROM pg_catalog.pg_roles",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM app.runs",
    "SELECT * FROM demo_other.accounts",
    'SELECT * FROM "Schools"',
    "SELECT * FROM unknown_table",
    "WITH x AS (SELECT * FROM app.runs) SELECT 1",
    "WITH x AS (SELECT 1) SELECT * FROM app.x",
    'WITH "X" AS (SELECT 1) SELECT * FROM x',
    "SELECT * FROM schools x JOIN frpm x ON true",
    "WITH x AS (SELECT 1) SELECT * FROM (WITH y AS (SELECT * FROM app.x) SELECT * FROM y) z",
    "SELECT pg_read_file('/not-a-real-target')",
    "SELECT pg_sleep(1)",
    "SELECT set_config('search_path', 'app', false)",
    "SELECT nextval('not-a-real-sequence')",
    "SELECT * FROM generate_series(1, 3)",
    "SELECT * FROM unnest(ARRAY[1, 2])",
    "SELECT public.count(*) FROM schools",
    "SELECT 1 OPERATOR(public.+) 2",
    "SELECT CAST('schools' AS regclass)",
    "SELECT CAST(1 AS public.custom_type)",
    "SELECT CAST(1 AS numeric(1000000, 2))",
    "EXPLAIN SELECT 1",
]


@pytest.mark.parametrize("sql", SAFE)
def test_supported_reads_keep_exact_sql(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.reason == "accepted"
    assert decision.sql == sql


@pytest.mark.parametrize("sql", UNSAFE)
def test_unsafe_or_unreviewed_sql_never_returns_executable_text(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted
    assert decision.sql is None


@pytest.mark.parametrize(
    "sql, reason",
    [
        ("SELECT 1; SELECT 2", "statement_not_allowed"),
        ("DELETE FROM schools", "statement_not_allowed"),
        ("WITH x AS (DELETE FROM schools RETURNING *) SELECT 1", "modifying_node"),
        ("SELECT * INTO x FROM schools", "modifying_node"),
        ("SELECT * FROM schools FOR UPDATE", "modifying_node"),
        ("SELECT pg_read_file('/not-a-real-target')", "function_not_allowed"),
        ("SELECT public.count(*) FROM schools", "function_not_allowed"),
        ("SELECT CAST('schools' AS regclass)", "cast_not_allowed"),
        ("SELECT 1 OPERATOR(public.+) 2", "unsupported_node"),
        ("SELECT ARRAY[1, 2]", "function_not_allowed"),
        ("SELECT * FROM app.runs", "schema_not_allowed"),
        ("SELECT * FROM unknown_table", "table_not_allowed"),
        ("SELECT * FROM schools x JOIN frpm x ON true", "unsupported_relation"),
        ("SELECT (", "parse_error"),
    ],
)
def test_rejection_has_stable_non_secret_category(sql, reason):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == reason


@pytest.mark.parametrize(
    "sql",
    [
        'WITH "X" AS (SELECT 1) SELECT * FROM "X"',
        'SELECT "S".cdscode FROM schools AS "S"',
        'SELECT * FROM schools AS "X" JOIN frpm AS x ON true',
        "SELECT * FROM schools X JOIN frpm y ON true",
        "SELECT * FROM schools JOIN frpm USING (cdscode)",
        "SELECT * FROM schools NATURAL LEFT JOIN frpm",
        "SELECT * FROM schools CROSS JOIN frpm",
        "SELECT * FROM schools LEFT OUTER JOIN frpm USING (cdscode)",
        "SELECT * FROM schools RIGHT JOIN frpm USING (cdscode)",
        "SELECT * FROM schools FULL JOIN frpm USING (cdscode)",
        "SELECT * FROM schools INNER JOIN frpm ON schools.cdscode=frpm.cdscode",
        "SELECT 1 UNION (SELECT 2 INTERSECT SELECT 2)",
        "(SELECT 1)",
        "((SELECT 1))",
        "WITH x AS (SELECT 1) SELECT * FROM (WITH x AS (SELECT 2) SELECT * FROM x) z",
        "SELECT count(*) FILTER (WHERE cdscode IS NOT NULL) FROM schools",
        "SELECT * FROM (VALUES (1)) AS x(n)",
        "WITH x(n) AS (VALUES (1)) SELECT * FROM x",
        "WITH x AS ((SELECT 1)) SELECT * FROM x",
        "SELECT 1;",
        ' \n/* keep all bytes */ SELECT "School Name" FROM "schools" '
        "WHERE cdscode = 'x; -- y' -- final comment\n",
    ],
)
def test_supported_scopes_joins_and_query_parens_are_not_rewritten(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted, decision.reason
    assert decision.sql == sql


@pytest.mark.parametrize(
    "sql",
    [
        "WITH x AS (SELECT 1) SELECT * FROM (SELECT * FROM app.x) AS x",
        "SELECT * FROM (WITH x AS (SELECT 1) SELECT * FROM x) z JOIN x ON true",
        "WITH x AS (SELECT 1) SELECT 1 UNION SELECT * FROM app.x",
        "WITH x AS (SELECT 1) SELECT 1 UNION (SELECT 2 EXCEPT SELECT * FROM app.x)",
        "WITH x AS (SELECT * FROM pg_catalog.pg_roles) SELECT 1",
        "SELECT 1 WHERE EXISTS (SELECT 1 FROM information_schema.tables)",
        "SELECT 1 FROM schools WHERE cdscode IN (SELECT cdscode FROM demo_other.accounts)",
        "WITH x AS (SELECT 1) SELECT * FROM california_schools.x",
        "SELECT * FROM otherdb.california_schools.schools",
        "SELECT * FROM schools X JOIN frpm x ON true",
        'SELECT * FROM schools AS "X" JOIN frpm AS "X" ON true',
        "SELECT * FROM schools X /* sqlglot.meta case_sensitive */ JOIN frpm x ON true",
        "SELECT * FROM schools SEMI JOIN frpm USING (cdscode)",
        "SELECT * FROM schools ANTI JOIN frpm USING (cdscode)",
        "SELECT * FROM schools ASOF JOIN frpm ON true",
        "SELECT * FROM schools TABLESAMPLE SYSTEM (1)",
        "SELECT * FROM LATERAL (SELECT 1) AS x",
    ],
)
def test_scope_leakage_and_unreviewed_relations_fail_closed(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None


@pytest.mark.parametrize(
    "sql, accepted",
    [
        ('SELECT * FROM "MixedCase"', True),
        ('SELECT * FROM "SchemaCase"."MixedCase"', True),
        ("SELECT * FROM MixedCase", False),
        ('SELECT * FROM schemacase."MixedCase"', False),
        ('SELECT * FROM "SchemaCase"."mixedcase"', False),
    ],
)
def test_trusted_policy_matches_exact_quoted_physical_names(sql, accepted):
    policy = DatasetPolicy("SchemaCase", frozenset({"MixedCase"}))
    decision = guard_sql(sql, policy)
    assert decision.accepted is accepted
    assert decision.sql == (sql if accepted else None)


@pytest.mark.parametrize("name", ["ÉCOLE", "école"])
def test_unquoted_postgres_folding_only_changes_ascii(name):
    policy = DatasetPolicy("school_data", frozenset({"École"}))
    sql = f"SELECT * FROM {name}"
    assert guard_sql(sql, policy).accepted is (name == "ÉCOLE")


@pytest.mark.parametrize("name", [None, 5, "", "a\x00b", "\ud800", "a" * 64, "é" * 32])
@pytest.mark.parametrize("field", ["schema", "table"])
def test_policy_rejects_missing_or_ambiguous_physical_names(field, name):
    schema, tables = "dataset", frozenset({"schools"})
    if field == "schema":
        schema = name
    else:
        tables = frozenset({name})
    with pytest.raises(ValueError):
        DatasetPolicy(schema, tables)


@pytest.mark.parametrize("tables", [None, "schools", {"schools"}, frozenset()])
def test_policy_requires_nonempty_immutable_table_allowlist(tables):
    with pytest.raises(ValueError):
        DatasetPolicy("dataset", tables)


def test_policy_and_decision_cannot_be_mutated_after_a_check():
    with pytest.raises(FrozenInstanceError):
        CALIFORNIA_POLICY.schema = "app"
    decision = guard_sql("SELECT 1", CALIFORNIA_POLICY)
    with pytest.raises(FrozenInstanceError):
        decision.sql = "DELETE FROM schools"


def test_dataset_policies_are_fixed_for_all_loaded_release_databases():
    assert DATASET_POLICIES["california_schools"] is CALIFORNIA_POLICY
    assert {policy.schema for policy in DATASET_POLICIES.values()} == set(DATASET_POLICIES)
    assert {name: policy.tables for name, policy in DATASET_POLICIES.items()} == {
        "california_schools": frozenset({"frpm", "satscores", "schools"}),
        "card_games": frozenset(
            {"cards", "foreign_data", "legalities", "rulings", "set_translations", "sets"}
        ),
        "codebase_community": frozenset(
            {"badges", "comments", "posthistory", "postlinks", "posts", "tags", "users", "votes"}
        ),
        "debit_card_specializing": frozenset(
            {"customers", "gasstations", "products", "transactions_1k", "yearmonth"}
        ),
        "european_football_2": frozenset(
            {"country", "league", "match", "player", "player_attributes", "team", "team_attributes"}
        ),
        "financial": frozenset(
            {"account", "card", "client", "disp", "district", "loan", "order", "trans"}
        ),
        "formula_1": frozenset(
            {
                "circuits",
                "constructorresults",
                "constructors",
                "constructorstandings",
                "drivers",
                "driverstandings",
                "laptimes",
                "pitstops",
                "qualifying",
                "races",
                "results",
                "seasons",
                "status",
            }
        ),
        "student_club": frozenset(
            {"attendance", "budget", "event", "expense", "income", "major", "member", "zip_code"}
        ),
        "superhero": frozenset(
            {
                "alignment",
                "attribute",
                "colour",
                "gender",
                "hero_attribute",
                "hero_power",
                "publisher",
                "race",
                "superhero",
                "superpower",
            }
        ),
        "thrombosis_prediction": frozenset({"examination", "laboratory", "patient"}),
        "toxicology": frozenset({"atom", "bond", "connected", "molecule"}),
    }


def test_dataset_policy_map_cannot_be_mutated():
    with pytest.raises(TypeError):
        DATASET_POLICIES["app"] = DatasetPolicy("app", frozenset({"runs"}))


def test_non_california_dataset_policy_accepts_only_its_own_schema_and_tables():
    financial = DATASET_POLICIES["financial"]
    assert guard_sql('SELECT count(*) FROM "order"', financial).accepted
    assert guard_sql("SELECT count(*) FROM financial.account", financial).accepted
    assert guard_sql("SELECT count(*) FROM schools", financial).reason == "table_not_allowed"
    assert guard_sql("SELECT count(*) FROM california_schools.schools", financial).reason == (
        "schema_not_allowed"
    )


@pytest.mark.parametrize("sql", [None, 4, b"SELECT 1", "", " ", "SELECT '\x00'", "\ud800"])
def test_invalid_input_is_a_sanitized_rejection(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "input_invalid"


def test_sql_byte_budget_rejects_before_parser(monkeypatch):
    def forbidden_parse(*args, **kwargs):
        pytest.fail("Oversized SQL reached parser")

    monkeypatch.setattr("sqlwarden.guard.sqlglot.parse", forbidden_parse)
    sql = "SELECT '" + "x" * 8193 + "'"
    assert guard_sql(sql, CALIFORNIA_POLICY).reason == "input_limit"


@pytest.mark.parametrize("byte_count, accepted", [(8192, True), (8193, False)])
def test_sql_bytes_at_the_exact_boundary(byte_count, accepted):
    sql = "SELECT '" + "x" * (byte_count - 9) + "'"
    assert guard_sql(sql, CALIFORNIA_POLICY).accepted is accepted


def test_sql_budget_counts_multibyte_text_in_bytes():
    sql = "SELECT '" + "é" * 4092 + "'"
    assert len(sql) < 8192
    assert guard_sql(sql, CALIFORNIA_POLICY).reason == "input_limit"


@pytest.mark.parametrize("count, accepted", [(999, True), (1000, False)])
def test_ast_node_boundary(count, accepted):
    sql = "SELECT " + ",".join("1" for _ in range(count))
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted is accepted
    if not accepted:
        assert decision.reason == "ast_limit"


@pytest.mark.parametrize("depth, accepted", [(64, True), (65, False)])
def test_ast_depth_boundary_counts_root_as_zero(monkeypatch, depth, accepted):
    expression = exp.Literal.number(1)
    for _ in range(depth - 1):
        expression = exp.Paren(this=expression)
    tree = exp.Select(expressions=[expression])
    monkeypatch.setattr("sqlwarden.guard.sqlglot.parse", lambda *a, **k: [tree])
    decision = guard_sql("SELECT 1", CALIFORNIA_POLICY)
    assert decision.accepted is accepted
    if not accepted:
        assert decision.reason == "ast_limit"


@pytest.mark.parametrize("byte_count, accepted", [(63, True), (64, False)])
def test_identifier_byte_boundary(byte_count, accepted):
    name = "a" * byte_count
    assert guard_sql(f'SELECT 1 AS "{name}"', CALIFORNIA_POLICY).accepted is accepted


@pytest.mark.parametrize("name, accepted", [("é" * 31 + "a", True), ("é" * 32, False)])
@pytest.mark.parametrize("quoted", [False, True])
def test_identifier_limit_counts_utf8_bytes(name, accepted, quoted):
    alias = f'"{name}"' if quoted else name
    decision = guard_sql(f"SELECT 1 AS {alias}", CALIFORNIA_POLICY)
    assert decision.accepted is accepted
    if not accepted:
        assert decision.reason == "identifier_invalid"


@pytest.mark.parametrize("sql", ["SELECT (", "SELECT 'unclosed", "SELECT 1) ", "SELECT FROM"])
def test_malformed_input_never_returns_executable_sql(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None


@pytest.mark.parametrize("error", [ParseError, TokenError, RecursionError, IndexError])
def test_parser_failures_are_sanitized(monkeypatch, error):
    def failed_parse(*args, **kwargs):
        raise error("not-a-real-secret")

    monkeypatch.setattr("sqlwarden.guard.sqlglot.parse", failed_parse)
    decision = guard_sql("SELECT 1", CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "parse_error"


@pytest.mark.parametrize("sql", ["SELECT VAR_MAP(1)", "SELECT LEVENSHTEIN_LESS_EQUAL()"])
def test_parser_builder_index_errors_are_sanitized(sql, caplog):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "parse_error"
    assert sql not in caplog.text


def test_unsupported_command_does_not_log_input_literals(caplog):
    decision = guard_sql("CALL not_a_real_secret('not-a-real-secret')", CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert "not-a-real-secret" not in caplog.text
    assert "not_a_real_secret" not in caplog.text


@pytest.mark.parametrize(
    "sql",
    [
        "WITH x AS ('review-canary') SELECT 1",
        "WITH x AS ('review-canary') SELECT * FROM x",
        "WITH x AS (('review-canary')) SELECT 1",
        "WITH x AS (CASE WHEN true THEN 'review-canary' ELSE NULL END) SELECT * FROM x",
    ],
)
def test_unsupported_cte_bodies_reject_without_logging_sql(sql, caplog):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert "review-canary" not in caplog.text
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "unsupported_relation"


def test_empty_scope_traversal_cannot_skip_a_physical_table(monkeypatch):
    monkeypatch.setattr("sqlwarden.guard.traverse_scope", lambda tree: [])
    decision = guard_sql("SELECT * FROM schools", CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "unsupported_relation"


def test_incomplete_scope_traversal_cannot_skip_an_unused_cte(monkeypatch):
    from sqlwarden import guard

    real_traverse = guard.traverse_scope
    monkeypatch.setattr("sqlwarden.guard.traverse_scope", lambda tree: real_traverse(tree)[-1:])
    decision = guard_sql("WITH x AS (SELECT * FROM app.runs) SELECT 1", CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "unsupported_relation"


def test_scope_construction_errors_fail_closed(monkeypatch):
    def failed_scope(tree):
        raise OptimizeError("not-a-real-secret")

    monkeypatch.setattr("sqlwarden.guard.traverse_scope", failed_scope)
    decision = guard_sql("SELECT * FROM schools", CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "unsupported_relation"


def test_new_node_subclass_is_not_implicitly_allowed(monkeypatch):
    class NewLiteral(exp.Literal):
        pass

    tree = exp.Select(expressions=[NewLiteral(this="1", is_string=False)])
    monkeypatch.setattr("sqlwarden.guard.sqlglot.parse", lambda *a, **k: [tree])
    decision = guard_sql("SELECT 1", CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None
    assert decision.reason == "unsupported_node"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT IF(true, 1, 2)",
        "SELECT CAST(1 AS numeric(10, 2))",
        "SELECT CAST(1 AS int[])",
        "SELECT CAST(1 AS timestamptz)",
        "SELECT pg_catalog.to_char(CAST('2020-01-01' AS timestamp), 'YYYY')",
        "SELECT date_trunc('year', CAST('2020-01-01' AS timestamp))",
        "SELECT clock_timestamp()",
        "SELECT EXTRACT(EPOCH_UNREVIEWED FROM CAST('2020-01-01' AS date))",
        "SELECT CAST(1 AS pg_catalog.int8)",
        "SELECT pg_catalog.abs(-1)",
        "SELECT app.lower('x')",
        'SELECT "pg_sleep"(1)',
        "SELECT anonymous_unreviewed(1)",
    ],
)
def test_unreviewed_functions_and_cast_forms_fail_closed(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None


def test_guard_import_and_usage_need_no_database_or_model_package():
    code = (
        "import sys; from sqlwarden.guard import guard_sql, CALIFORNIA_POLICY; "
        "assert guard_sql('SELECT 1', CALIFORNIA_POLICY).accepted; "
        "assert not any(n.split('.')[0] in {'asyncpg', 'openai', 'ollama', 'httpx'} "
        "for n in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT to_char(CAST('2020-01-01 10:00' AS timestamp), 'YYYY-MM')",
        "SELECT substring('abcdef', 2, 3)",
        "SELECT substr('abcdef', 2, 3)",
        "SELECT strpos('abcdef', 'cd')",
        "SELECT EXTRACT(YEAR FROM CAST('2020-01-01' AS date))",
        "SELECT date(CAST('2020-01-01 10:00' AS timestamp))",
        "SELECT CURRENT_TIMESTAMP",
        "SELECT rank() OVER (ORDER BY school) FROM schools",
        "SELECT dense_rank() OVER (ORDER BY school) FROM schools",
        "SELECT CAST('2020-01-01 10:00' AS timestamp)",
    ],
)
def test_reviewed_date_text_and_rank_functions_from_gold_audit_are_accepted(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql

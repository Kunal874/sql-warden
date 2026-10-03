"""Handwritten acceptance controls and catalog review, not an AI SQL executor."""

import datetime
from decimal import Decimal

import pytest
from test_bird_load import california_connected

from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql

pytestmark = pytest.mark.integration


@pytest.fixture
async def restricted_reader():
    async with california_connected() as conn, conn.transaction(readonly=True):
        await conn.execute("SET LOCAL statement_timeout='5s'")
        await conn.execute("SET LOCAL lock_timeout='500ms'")
        await conn.execute("SET LOCAL search_path=pg_catalog,california_schools")
        assert await conn.fetchval("SELECT current_user") == "warden_sandbox_california_schools"
        assert await conn.fetchval("SHOW transaction_read_only") == "on"
        assert await conn.fetchval("SHOW statement_timeout") == "5s"
        assert await conn.fetchval("SHOW lock_timeout") == "500ms"
        assert await conn.fetchval("SHOW search_path") == "pg_catalog, california_schools"
        yield conn


async def test_guarded_handwritten_count_uses_restricted_reader(restricted_reader):
    sql = "SELECT count(*) FROM california_schools.schools"
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql
    assert await restricted_reader.fetchval(decision.sql) == 17686


@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT count(cdscode) FROM schools", 17686),
        ("SELECT count(DISTINCT cdscode) FROM schools", 17686),
        ("SELECT sum(n) FROM (VALUES (CAST(1 AS bigint)), (CAST(2 AS bigint))) x(n)", Decimal(3)),
        ("SELECT sum(n) FROM (VALUES (CAST(1 AS real)), (CAST(2 AS real))) x(n)", 3.0),
        (
            "SELECT avg(n) FROM (VALUES (CAST(1 AS bigint)), (CAST(2 AS bigint))) x(n)",
            Decimal("1.5"),
        ),
        ("SELECT avg(n) FROM (VALUES (CAST(1 AS real)), (CAST(2 AS real))) x(n)", 1.5),
        ("SELECT min(n) FROM (VALUES ('b'), ('a')) x(n)", "a"),
        ("SELECT max(n) FROM (VALUES ('b'), ('a')) x(n)", "b"),
        ("SELECT min(n) FROM (VALUES (CAST(1 AS bigint)), (CAST(2 AS bigint))) x(n)", 1),
        ("SELECT max(n) FROM (VALUES (CAST(1 AS bigint)), (CAST(2 AS bigint))) x(n)", 2),
        ("SELECT min(n) FROM (VALUES (CAST(1 AS real)), (CAST(2 AS real))) x(n)", 1.0),
        ("SELECT max(n) FROM (VALUES (CAST(1 AS real)), (CAST(2 AS real))) x(n)", 2.0),
        (
            "SELECT min(n) FROM (VALUES (CAST('2020-01-01' AS date)), "
            "(CAST('2020-01-02' AS date))) x(n)",
            datetime.date(2020, 1, 1),
        ),
        (
            "SELECT max(n) FROM (VALUES (CAST('2020-01-01' AS date)), "
            "(CAST('2020-01-02' AS date))) x(n)",
            datetime.date(2020, 1, 2),
        ),
        ("SELECT abs(CAST(-2 AS bigint))", 2),
        ("SELECT abs(CAST('-2.5' AS real))", 2.5),
        ("SELECT round(CAST('2.25' AS double precision))", 2.0),
        ("SELECT round(CAST('2.25' AS decimal), 1)", Decimal("2.3")),
        ("SELECT length('é')", 1),
        ("SELECT lower('AbC')", "abc"),
        ("SELECT upper('AbC')", "ABC"),
        ("SELECT coalesce(NULL, CAST(3 AS bigint))", 3),
        ("SELECT nullif('same', 'same')", None),
        ("SELECT row_number() OVER (ORDER BY n) FROM (VALUES (2), (1)) x(n) LIMIT 1", 1),
        ("SELECT CASE WHEN 1=1 THEN coalesce(NULL, 2) ELSE 3 END", 2),
        ("SELECT count(*) FILTER (WHERE cdscode IS NOT NULL) FROM schools", 17686),
    ],
)
async def test_every_admitted_function_has_a_small_real_control(restricted_reader, sql, expected):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql, decision.reason
    result = await restricted_reader.fetchval(decision.sql)
    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT CAST('42' AS int)", 42),
        ("SELECT CAST('42' AS bigint)", 42),
        ("SELECT CAST('1.5' AS real)", 1.5),
        ("SELECT CAST('1.5' AS float)", 1.5),
        ("SELECT CAST('1.5' AS double precision)", 1.5),
        ("SELECT CAST('1.5' AS decimal)", Decimal("1.5")),
        ("SELECT CAST(CAST(42 AS bigint) AS decimal)", Decimal(42)),
        ("SELECT CAST(42 AS text)", "42"),
        ("SELECT CAST('2020-01-01' AS date)", datetime.date(2020, 1, 1)),
        ("SELECT CAST('true' AS boolean)", True),
    ],
)
async def test_every_admitted_cast_type_has_a_real_control(restricted_reader, sql, expected):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql, decision.reason
    result = await restricted_reader.fetchval(decision.sql)
    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT CAST(6 AS bigint) + CAST(2 AS bigint)", 8),
        ("SELECT CAST(6 AS bigint) - CAST(2 AS bigint)", 4),
        ("SELECT CAST(6 AS bigint) * CAST(2 AS bigint)", 12),
        ("SELECT CAST(6 AS bigint) / CAST(2 AS bigint)", 3),
        ("SELECT CAST(5 AS bigint) % CAST(2 AS bigint)", 1),
        ("SELECT CAST('1.5' AS real) + CAST('2.5' AS real)", 4.0),
        ("SELECT CAST('1.5' AS real) < CAST('2.5' AS real)", True),
        ("SELECT CAST('2020-01-01' AS date) < CAST('2020-01-02' AS date)", True),
        ("SELECT 'same' = CAST('same' AS text)", True),
        ("SELECT 'school' LIKE 'sch%'", True),
        ("SELECT 'School' ILIKE 'sch%'", True),
        ("SELECT nullif(CAST(1 AS bigint), CAST(1 AS bigint))", None),
    ],
)
async def test_reviewed_native_operators_execute_under_the_same_login(
    restricted_reader, sql, expected
):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql, decision.reason
    assert await restricted_reader.fetchval(decision.sql) == expected


@pytest.mark.parametrize(
    "sql, expected",
    [
        (
            "SELECT 1 FROM schools s JOIN frpm f USING (cdscode) "
            "LEFT JOIN satscores t ON s.cdscode=t.cds ORDER BY s.cdscode LIMIT 3",
            [(1,), (1,), (1,)],
        ),
        (
            "WITH small AS (SELECT cdscode FROM schools ORDER BY cdscode LIMIT 2) "
            "SELECT count(*) FROM small",
            [(2,)],
        ),
        ("WITH schools AS (SELECT 1 AS n) SELECT sum(n) FROM schools", [(1,)]),
        ("WITH X AS (SELECT 1) SELECT * FROM X /* sqlglot.meta case_sensitive */", [(1,)]),
        ("SELECT count(*) FROM SCHOOLS /* sqlglot.meta case_sensitive */", [(17686,)]),
        ('SELECT count(*) FROM "california_schools"."schools"', [(17686,)]),
    ],
)
async def test_bounded_native_join_and_scopes_match_postgres(restricted_reader, sql, expected):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql, decision.reason
    rows = await restricted_reader.fetch(decision.sql)
    assert [tuple(row) for row in rows] == expected


# These catalog queries are trusted test inspection, never guard-approved runtime SQL.
# CASE/COALESCE/NULLIF are SQL forms, not invented pg_proc grants.
FUNCTION_SIGNATURES = [
    ("count()", "bigint", "a"),
    ('count("any")', "bigint", "a"),
    ("sum(bigint)", "numeric", "a"),
    ("sum(real)", "real", "a"),
    ("avg(bigint)", "numeric", "a"),
    ("avg(real)", "double precision", "a"),
    ("min(text)", "text", "a"),
    ("max(text)", "text", "a"),
    ("min(bigint)", "bigint", "a"),
    ("max(bigint)", "bigint", "a"),
    ("min(real)", "real", "a"),
    ("max(real)", "real", "a"),
    ("min(date)", "date", "a"),
    ("max(date)", "date", "a"),
    ("abs(bigint)", "bigint", "f"),
    ("abs(real)", "real", "f"),
    ("round(double precision)", "double precision", "f"),
    ("round(numeric,integer)", "numeric", "f"),
    ("length(text)", "integer", "f"),
    ("lower(text)", "text", "f"),
    ("upper(text)", "text", "f"),
    ("row_number()", "bigint", "w"),
]
OPERATOR_SIGNATURES = [
    "+(bigint,bigint)",
    "-(bigint,bigint)",
    "*(bigint,bigint)",
    "/(bigint,bigint)",
    "%(bigint,bigint)",
    "=(bigint,bigint)",
    "+(real,real)",
    "<(real,real)",
    "<(date,date)",
    "=(text,text)",
    "~~(text,text)",
    "~~*(text,text)",
]


async def test_actual_builtin_function_operator_and_type_inventory(restricted_reader):
    conn = restricted_reader
    for signature, result_type, kind in FUNCTION_SIGNATURES:
        row = await conn.fetchrow(
            "SELECT p.prokind::text AS kind, p.provolatile::text AS volatility, "
            "p.prosecdef, l.lanname, n.nspname, format_type(p.prorettype,NULL) AS result_type, "
            "has_function_privilege(current_user,p.oid,'EXECUTE') AS executable "
            "FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace "
            "JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE p.oid=to_regprocedure($1)",
            f"pg_catalog.{signature}",
        )
        assert row is not None, signature
        assert row["kind"] == kind and row["result_type"] == result_type, signature
        assert row["nspname"] == "pg_catalog" and row["lanname"] in {"internal", "c"}, signature
        assert row["volatility"] in {"i", "s"} and not row["prosecdef"], signature
        assert row["executable"], signature
        if kind == "a":
            routines = await conn.fetch(
                "SELECT n.nspname,l.lanname,p.prosecdef,p.provolatile::text AS volatility "
                "FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON p.oid=ANY(ARRAY["
                "a.aggtransfn,a.aggfinalfn,a.aggcombinefn,a.aggserialfn,a.aggdeserialfn,"
                "a.aggmtransfn,a.aggminvtransfn,a.aggmfinalfn]) "
                "JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace "
                "JOIN pg_catalog.pg_language l ON l.oid=p.prolang "
                "WHERE a.aggfnoid=to_regprocedure($1)",
                f"pg_catalog.{signature}",
            )
            assert routines, signature
            assert all(
                r["nspname"] == "pg_catalog"
                and r["lanname"] in {"internal", "c"}
                and not r["prosecdef"]
                and r["volatility"] in {"i", "s"}
                for r in routines
            ), signature
    for signature in OPERATOR_SIGNATURES:
        row = await conn.fetchrow(
            "SELECT n.nspname,pn.nspname AS proc_schema,l.lanname,p.prosecdef,"
            "p.provolatile::text AS volatility,p.oid::regprocedure::text AS implementation "
            "FROM pg_catalog.pg_operator o JOIN pg_catalog.pg_proc p ON p.oid=o.oprcode "
            "JOIN pg_catalog.pg_namespace n ON n.oid=o.oprnamespace "
            "JOIN pg_catalog.pg_namespace pn ON pn.oid=p.pronamespace "
            "JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE o.oid=to_regoperator($1)",
            f"pg_catalog.{signature}",
        )
        assert row is not None, signature
        assert row["nspname"] == row["proc_schema"] == "pg_catalog", signature
        assert row["lanname"] in {"internal", "c"} and not row["prosecdef"], signature
        assert row["volatility"] in {"i", "s"}, signature
        print(f"Operator {signature}: {row['implementation']}")
    for type_name in ("int4", "int8", "float4", "float8", "numeric", "text", "date", "bool"):
        row = await conn.fetchrow(
            "SELECT n.nspname,t.typtype::text AS kind,t.typbasetype,t.typrelid,"
            "t.typinput::regprocedure::text AS input,t.typoutput::regprocedure::text AS output "
            "FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace "
            "WHERE t.oid=to_regtype($1)",
            f"pg_catalog.{type_name}",
        )
        assert row is not None and row["nspname"] == "pg_catalog", type_name
        assert row["kind"] == "b" and row["typbasetype"] == row["typrelid"] == 0, type_name
        routines = await conn.fetch(
            "SELECT n.nspname,l.lanname,p.prosecdef,p.provolatile::text AS volatility "
            "FROM pg_catalog.pg_type t JOIN pg_catalog.pg_proc p "
            "ON p.oid IN (t.typinput,t.typoutput) "
            "JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace "
            "JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE t.oid=to_regtype($1)",
            f"pg_catalog.{type_name}",
        )
        assert len(routines) == 2, type_name
        assert all(
            r["nspname"] == "pg_catalog"
            and r["lanname"] in {"internal", "c"}
            and not r["prosecdef"]
            and r["volatility"] in {"i", "s"}
            for r in routines
        ), type_name
        print(f"Type {type_name}: {row['input']}, {row['output']}")
    cast = await conn.fetchrow(
        "SELECT c.castmethod::text AS method,p.oid::regprocedure::text AS implementation,"
        "n.nspname,l.lanname,p.prosecdef FROM pg_catalog.pg_cast c "
        "JOIN pg_catalog.pg_proc p ON p.oid=c.castfunc "
        "JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace "
        "JOIN pg_catalog.pg_language l ON l.oid=p.prolang "
        "WHERE c.castsource=to_regtype('bigint') AND c.casttarget=to_regtype('numeric')"
    )
    assert cast is not None and cast["method"] == "f"
    assert cast["nspname"] == "pg_catalog" and cast["lanname"] in {"internal", "c"}
    assert not cast["prosecdef"]
    print(f"Cast bigint -> numeric: {cast['implementation']}")
    for sql in (
        "SELECT pg_catalog.abs(1)",
        "SELECT app.lower('x')",
        "SELECT 1 OPERATOR(public.+) 2",
        "SELECT CAST(1 AS public.custom_type)",
    ):
        # Check rejection only: no unsafe SQL is ever sent to this connection.
        decision = guard_sql(sql, CALIFORNIA_POLICY)
        assert not decision.accepted and decision.sql is None

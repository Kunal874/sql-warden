# Minimum SQL Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Native execution is preserved; AGENTS.md forbids parallel implementation without Kunal's request. Steps use checkbox syntax for tracking.

**Goal:** Implement and verify G0.7a's first prerequisite: a fail-closed, scope-aware PostgreSQL SQL guard for the existing California dataset, without executing model output.

**Architecture:** Keep a pure Python guard separate from database connections. Parse the original SQL, inspect every supported tree node and relation scope, and return either unchanged SQL or a stable rejection category. The future executor must call the guard itself; a returned dataclass is not an authorization capability.

**Tech Stack:** Python 3.12, uv, pure-Python sqlglot 30.21.0, existing asyncpg/pytest and standard-library dataclasses. Kunal approved its direct addition with this plan on 2026-10-04. No SDK, model loading or other dependency is needed here.

**Spec:** [BUILD_SPEC](../../BUILD_SPEC.md), sections 2, 5–6 and 11; [AGENTS](../../../AGENTS.md); [DATA](../../DATA.md). These existing approved contracts supply the design; this plan does not replace them.

**Status:** Prepared and self-reviewed on 2026-10-03; Kunal approved the plan and dependency on 2026-10-04. Tasks 1–2 are verified (184 guard unit tests, 56 new real PostgreSQL checks; full suite 398 passed). One final read-only review remains. Execution baseline: clean feat/foundation at 83ac96a, 158 tests passed with both private test environments.

## Global Constraints

- Workspace: `D:/PROJECTS/SQLWARDEN`. Use the current workspace; do not create a nested `sqlwarden` directory.
- Python 3.12 with uv; PostgreSQL 16 in Docker; native Ollama; React 18/TypeScript later.
- Keep inference local until a hosted configuration is explicitly approved.
- No remote addition or push before the G7 release approval.
- Kunal is the sole author and committer of new project commits.
- Never commit secrets, data downloads, model weights, caches, raw run output or unrelated user changes.
- Real PostgreSQL integration tests must run before database security claims.
- Use tests first for security boundaries, result comparison, voting, budgets and state transitions.
- Preserve the existing named volume, credentials, imported rows and PostgreSQL 17 service.
- No generated SQL executes before the minimum guard, bounded executor and comparator pass.
- After each completed group/subtask, update explaination of project/PROJECT_EXPLAINED.md in simple English.

## Scope and alternatives

G0.7a has dependent guard, executor, comparator and CLI parts. This plan covers
only the guard; completing it does not complete G0.7a. Separate subsequent plans
will consume the interfaces below instead of creating another guard. The source
investigation for the comparator is preserved in [EX_COMPARATOR](../../EX_COMPARATOR.md).

Use a reusable pure guard now. Combining its checks with a single CLI file would
mean fewer initial files, but couple security tests to connection/model behavior.
The reusable boundary fits the existing plan and can be tested without GPU memory.
No full agent, repair/voting/retrieval, website, hosted service or benchmark run is
included in this increment.

## Files and responsibility

- Create `src/sqlwarden/guard.py`: immutable dataset policy, guard decision,
  fixed syntax/function/type policy and pure validation.
- Create `tests/test_guard.py`: deterministic accepted/rejected SQL, scope,
  input limits and unchanged-text tests.
- Create `tests/test_guard_postgres.py`: narrowly bounded, handwritten acceptance
  checks through the existing restricted California test connection.
- Modify `pyproject.toml` and `uv.lock` only to add the approved pinned SQLGlot.
- Update `docs/PROGRESS.md`, `docs/DECISIONS.md`, this plan's checkboxes and the
  learning notebook after actual completed tasks. Preserve historical inputs.

## Reviewed parser reference

- [PyPI release](https://pypi.org/project/sqlglot/30.21.0/): Python >=3.9; pure wheel
  sqlglot-30.21.0-py3-none-any.whl, 763892 bytes, published SHA-256
  816d1a4815b7562b3976efcc0b561c928a743f976efd0fb8ad6db7a5b96c069e.
  Originally registry metadata; independently downloaded/verified on 2026-10-04
  with matching size/hash, under ignored .tools/parser (not committed).
- Tag v30.21.0 points to commit 5d16fa83bfb8f3582eaffa4b99c7d05a061d8a76.
  [License](https://github.com/tobymao/sqlglot/blob/5d16fa83bfb8f3582eaffa4b99c7d05a061d8a76/LICENSE): MIT.
- [Scope source](https://github.com/tobymao/sqlglot/blob/5d16fa83bfb8f3582eaffa4b99c7d05a061d8a76/sqlglot/optimizer/scope.py):
  selected sources resolve to a physical Table or another Scope. Inspect every
  descendant scope, including unused CTEs; account for every Table node.
- [Identifier normalization source](https://github.com/tobymao/sqlglot/blob/5d16fa83bfb8f3582eaffa4b99c7d05a061d8a76/sqlglot/optimizer/normalize_identifiers.py)
  honors comment-supplied metadata. Do not let input comments configure the guard.
  Normalize unquoted identifiers with ASCII-only PostgreSQL folding; preserve quoted
  identifiers. Do not serialize the analysis tree back into executed SQL.
- SQLGlot describes its parser as lenient, not an engine validator. Accepted SQL
  may still fail PostgreSQL syntax/type checks. The guard never claims otherwise.

## Review Focus

1. A forbidden relation is hidden inside an unused/nested CTE, alias or correlated subquery: inspect its actual scope, not a global list of CTE names.
2. A SELECT contains an executable side effect through a nested write, function, qualified operator or cast: reject unreviewed structure before any connection.
3. Quoting, case, long identifiers or SQLGlot metadata comments change name resolution: match PostgreSQL semantics and reject ambiguous overlength identifiers.
4. Empty, non-string, invalid Unicode or oversized input exhausts/parses unexpectedly: reject with bounded, non-secret categories and no parser traceback.
5. Unknown nodes, table functions or partially resolved sources appear after a parser change: fail closed and require complete Table-node accounting.

---

### Task 1: Pure scope-aware SQL guard

**Files:** Create guard.py/test_guard.py; modify pyproject.toml/uv.lock; update progress/decisions/notebook.

**Interfaces:**
- `DatasetPolicy(schema: str, tables: frozenset[str])`: frozen/slotted dataclass;
  validate nonempty PostgreSQL identifiers, <=63 UTF-8 bytes, no NUL. Tables are
  exact physical names; the policy is constructed by trusted code, not a model.
- `CALIFORNIA_POLICY = DatasetPolicy("california_schools", frozenset({"schools", "frpm", "satscores"}))`.
- `GuardDecision(accepted: bool, reason: str, sql: str | None)`: frozen/slotted;
  accepted means reason="accepted" and sql is the unchanged input. Rejected
  decisions have sql=None. No raw error, literal, credential or traceback field.
- `guard_sql(sql: str, policy: DatasetPolicy) -> GuardDecision`: pure function,
  no file/network/database/model calls and no SQL rewriting.
- Internal checks consume a parsed normalized tree and return a reason string
  or None: `_check_nodes(tree: exp.Expression) -> str | None`,
  `_check_tables(tree: exp.Expression, policy: DatasetPolicy) -> str | None`.

- [x] **Step 1: Add the approved parser after plan approval.**

```powershell
uv add "sqlglot==30.21.0"
uv sync --locked
```

Use the explicit uv path from PROGRESS if PATH is missing. Inspect resolved
dependencies, default extras and wheel identity; do not add compiled extras or
change Python. The selected version must be locked, not resolved again each run.

- [x] **Step 2: Write failing accept/reject tests with these exact cases.**

```python
import pytest
from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql

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
```

Add focused tests for rejection categories, missing policy names, quoted aliases
versus unquoted aliases, duplicate aliases, CTE scope leakage, input comments
`/* sqlglot.meta case_sensitive */`, all Table nodes in unused CTEs, and nested
set operations. Check a quoted mixed-case table under a synthetic trusted policy:
quoted exact name passes and its unquoted spelling fails. These tests cover Review
Focus 1, 3 and 5; do not use an actual forbidden file or execute UNSAFE cases.

- [x] **Step 3: Observe RED.**

```powershell
uv run pytest tests/test_guard.py -q
```

Expected initial failure: missing sqlwarden.guard; after its interface exists,
assertion failures must identify incomplete protection. Preserve each observed
RED result. Do not replace meaningful failure cases with parser-only tests.

- [x] **Step 4: Implement immutable policy/results and bounded parsing.**

```python
from sqlglot import exp

MAX_SQL_BYTES = 8192
MAX_AST_NODES = 1000
MAX_AST_DEPTH = 64
ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

def fold_identifier(identifier: exp.Identifier) -> None:
    if not identifier.args.get("quoted"):
        identifier.set("this", identifier.this.translate(ASCII_LOWER))
```

Validate policy names at construction. For SQL, reject non-string, empty/NUL,
unencodable Unicode and input exceeding MAX_SQL_BYTES before parsing. Use
sqlglot.parse(read="postgres", error_level=ErrorLevel.RAISE); require exactly one
nonempty parsed statement and a Select/Union/Intersect/Except root (unwrap plain
query parentheses). Catch ParseError/TokenError/RecursionError without echoing
their text. Reject over-budget AST count/depth and identifiers exceeding 63 UTF-8
bytes. Normalize only analysis-tree Identifiers with fold_identifier, disregarding
comment metadata; accepted text remains byte-for-byte unchanged.

- [x] **Step 5: Implement the explicit structural/function/type policy.**

```python
STRUCTURAL_NAMES = frozenset("""
Select Union Intersect Except With CTE Subquery Table TableAlias Identifier Column
Star Literal Null Boolean Alias From Join Where Group Having Order Ordered Limit
Offset Distinct Paren And Or Not EQ NEQ GT GTE LT LTE Is In Between Exists Like ILike
Add Sub Mul Div Mod Neg Case If Cast DataType Tuple Values Filter Window WindowSpec
""".split())
FUNCTION_NAMES = frozenset("""
Count Sum Avg Min Max Abs Round Length Lower Upper Coalesce Nullif RowNumber
""".split())
CAST_TYPES = frozenset("INT BIGINT FLOAT DOUBLE DECIMAL TEXT DATE BOOLEAN".split())
```

Resolve these names against the pinned expression API and fail configuration if
one is absent. Check exact concrete node classes, not every subclass of a broad
base. Reject write/INTO/lock nodes anywhere; unknown nodes/functions fail closed.
If is allowed only as a CASE branch, not a standalone function call. Allow only
plain builtin cast targets above without precision, array, nested or custom-type
arguments. Reject function qualification and qualified/custom operators in this
initial policy. Permit ordinary INNER/LEFT/RIGHT/FULL/CROSS joins, including USING
and NATURAL; reject unreviewed join modifiers. Do not add name-based exceptions
for arbitrary Anonymous functions, unsupported parser Commands or table functions.

Use stable categories in deterministic order: input_invalid/input_limit,
parse_error/statement_not_allowed, ast_limit, identifier_invalid,
modifying_node/function_not_allowed/cast_not_allowed/unsupported_node,
schema_not_allowed/table_not_allowed/unsupported_relation, accepted.
No expression literal is returned in rejection details. This covers Review Focus 2.

- [x] **Step 6: Resolve actual table scopes and require full coverage.**

```python
from sqlglot import exp
from sqlglot.errors import OptimizeError
from sqlglot.optimizer.scope import Scope, traverse_scope

def _check_tables(tree: exp.Expression, policy: DatasetPolicy) -> str | None:
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
    except OptimizeError:
        return "unsupported_relation"
    return None
```

In this loop, physical sources must use an Identifier, no catalog, either no schema
or the exact policy schema, and an exact approved table name. Scope sources may
represent CTE/derived relations, but a CTE reference cannot carry a schema/catalog.
Then require every Table found by tree.find_all(exp.Table) to appear in seen_tables;
unaccounted nodes reject. Inspect all descendant/unused CTE scopes. Catch
OptimizeError/unsupported scope construction with a sanitized rejection. A CTE
name is never a global exemption. No rewriting, qualification injection or LIMIT
injection is permitted. These checks finish Review Focus 1 and 5.

- [x] **Step 7: Add boundary and invariance tests, then observe GREEN.**

```python
@pytest.mark.parametrize("sql", [None, 4, b"SELECT 1", "", " ", "SELECT '\x00'", "\ud800"])
def test_invalid_input_is_a_sanitized_rejection(sql):
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert not decision.accepted and decision.sql is None

def test_sql_byte_budget_rejects_before_parser(monkeypatch):
    def forbidden_parse(*args, **kwargs):
        pytest.fail("Oversized SQL reached parser")
    monkeypatch.setattr("sqlwarden.guard.sqlglot.parse", forbidden_parse)
    sql = "SELECT '" + "x" * 8193 + "'"
    assert guard_sql(sql, CALIFORNIA_POLICY).reason == "input_limit"

@pytest.mark.parametrize("count, accepted", [(999, True), (1000, False)])
def test_ast_node_boundary(count, accepted):
    sql = "SELECT " + ",".join("1" for _ in range(count))
    assert guard_sql(sql, CALIFORNIA_POLICY).accepted is accepted

@pytest.mark.parametrize("byte_count, accepted", [(63, True), (64, False)])
def test_identifier_byte_boundary(byte_count, accepted):
    name = "a" * byte_count
    assert guard_sql(f'SELECT 1 AS "{name}"', CALIFORNIA_POLICY).accepted is accepted

@pytest.mark.parametrize("name, accepted", [("é" * 31 + "a", True), ("é" * 32, False)])
def test_identifier_limit_counts_utf8_bytes(name, accepted):
    assert guard_sql(f'SELECT 1 AS "{name}"', CALIFORNIA_POLICY).accepted is accepted
```

Exercise max AST count/depth at the exact boundary and one over; long quoted and
unquoted multibyte names; malformed parentheses; an unsupported table expression;
qualified builtin functions (initially rejected); and equal guarded input/output
with comments, whitespace, literals and quoted names intact. Directly assert no
database or model import/call is needed. Run test_guard.py, the full existing suite,
ruff check/format and diff checks. Record actual counts, not predicted counts.
Define root depth as zero; use constructed Paren chains under a Select and a
monkeypatched parser for deterministic depth 64/65 checks. Also monkeypatch scope
traversal to return no scope for a real Table tree and require unsupported_relation;
no unaccounted physical source may be accepted after an API change.

- [x] **Step 8: Document and commit the working pure guard.** Update the notebook
with AST, scope, allowlist and fail-closed in simple language. PROGRESS must say
the guard is unit-tested, not yet an execution boundary or completed G0.7a. Record
strict-policy false blocks and the pending PostgreSQL checks. Inspect all staged
files and exact message, commit only this task and verify owner-only attribution.

```powershell
git add src/sqlwarden/guard.py tests/test_guard.py pyproject.toml uv.lock docs/PROGRESS.md docs/DECISIONS.md docs/superpowers/plans/2026-10-03-minimum-sql-guard.md "explaination of project/PROJECT_EXPLAINED.md"
git diff --cached
git diff --cached --check
git commit -m "feat(guard): add fail-closed PostgreSQL SQL validation"
git log -1 --format=fuller
git log -1 --format=%B
```

### Task 2: Real PostgreSQL acceptance and policy checks

**Files:** Create tests/test_guard_postgres.py; update progress/decisions/notebook/plan.

**Interfaces:** Consume guard_sql/CALIFORNIA_POLICY from Task 1 and the existing
`test_bird_load.california_connected()` async context manager. No production pool,
executor, admin credential loader or model client is produced in this task.

- [x] **Step 1: Write integration checks before broadening any policy.**

```python
import pytest
from test_bird_load import california_connected
from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql

@pytest.mark.integration
async def test_guarded_handwritten_count_uses_restricted_reader():
    sql = "SELECT count(*) FROM california_schools.schools"
    decision = guard_sql(sql, CALIFORNIA_POLICY)
    assert decision.accepted and decision.sql == sql
    async with california_connected() as conn:
        async with conn.transaction(readonly=True):
            await conn.execute("SET LOCAL statement_timeout='5s'")
            await conn.execute("SET LOCAL lock_timeout='500ms'")
            await conn.execute("SET LOCAL search_path=pg_catalog,california_schools")
            assert await conn.fetchval("SELECT current_user") == "warden_sandbox_california_schools"
            assert await conn.fetchval("SHOW transaction_read_only") == "on"
            assert await conn.fetchval(decision.sql) == 17686
```

Add small scalar aggregate/function/cast cases for every admitted function and
type, a bounded native-key join and CTE (explicit handwritten LIMIT where needed).
Inspect builtin pg_catalog overloads/operators/casts actually used with the native
text/bigint/real/date types; record signatures and findings without raw rows or
credentials. Verify no untrusted function/type/operator qualification is admitted.
These are static authored tests, not AI queries or benchmark gold. Never execute
Task 1's UNSAFE inputs here. Reuse the existing connection gate so no-env runs skip
and explicitly supplied missing California setup fails.

- [x] **Step 2: Run real acceptance checks and investigate failures.**

```powershell
uv run --env-file .env.setup --env-file .env.california pytest tests/test_guard_postgres.py -q
```

Expect actual PostgreSQL success, not mocks/skips. If an accepted structure behaves
differently in PostgreSQL, first pin that case in test_guard.py, observe RED, then
tighten the policy and verify GREEN. Do not silently broaden the allowlist, change
grants/data or use setup credentials for guarded queries to make a test pass.

- [x] **Step 3: Verify all modes and the safe-slice handoff.**

```powershell
uv sync --locked
uv run pytest -q
uv run --env-file .env.setup pytest -q
uv run --env-file .env.setup --env-file .env.california pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Report exact pass/skip counts for each mode. Check original planning files remain
unchanged, no secret/raw data is staged, no remote exists and Ollama remains
unloaded. Passing this guard plan still permits no AI SQL execution. G0.7a's
bounded executor/comparator/CLI must be planned, implemented and verified first.
The native executor follows executing-plans and requests one final read-only review
of this completed implementation; resolve findings with tests rather than claims.

- [x] **Step 4: Update explanations and commit verified acceptance evidence.**
Explain how a guard differs from database privileges and why both are needed.
Record the real checks, initial false-block limitations and exact next task in
PROGRESS/DECISIONS. Inspect staged diff/message and verify identity after commit.

```powershell
git add tests/test_guard_postgres.py src/sqlwarden/guard.py tests/test_guard.py docs/PROGRESS.md docs/DECISIONS.md docs/superpowers/plans/2026-10-03-minimum-sql-guard.md "explaination of project/PROJECT_EXPLAINED.md"
git diff --cached
git diff --cached --check
git commit -m "test(guard): verify restricted PostgreSQL acceptance"
git log -1 --format=fuller
git log -1 --format=%B
```

## Self-review and execution handoff

This plan covers the minimum guard and tests, not the whole product specification.
All five Review Focus conditions are assigned to Task 1; Task 2 checks real-engine
compatibility without claiming exhaustive security. Input and AST limits are
finite, but do not establish a hard wall-clock parser deadline. Strict unsupported
nodes, qualified functions and parameterized/custom casts can reject benign SQL;
G2's acceptance audit must report that rather than hide exclusions.

After Kunal approves the plan and direct SQLGlot addition, execute Tasks 1–2
natively in the current checkout. Do not start work from an earlier continue
message alone: this written plan did not exist when that message was sent. Keep
the same guard for subsequent G0.7a executor/comparator/CLI work; do not run the
old native-import plan, download another model or start a benchmark.

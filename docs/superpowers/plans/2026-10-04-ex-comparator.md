# Pinned EX Comparator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Preserve native sequential execution in the current checkout; AGENTS.md forbids parallel implementation without Kunal's request. Steps use checkbox syntax for tracking.

**Goal:** Complete G0.7a's answer-checker prerequisite by reproducing the pinned BIRD EX rule for complete typed results, with explicit prediction-failure and invalid-reference outcomes.

**Architecture:** One pure function consumes the existing QueryResult objects and compares sets of row tuples without sorting, rounding or converting cells to strings. A small immutable outcome contains only a score and fixed reason; it never returns reference rows or runs SQL. Restricted PostgreSQL controls then verify the native-result and failure handoff; voting, benchmark orchestration and model/CLI wiring remain separate.

**Tech Stack:** Python 3.12, standard-library dataclasses/datetime/decimal/math/typing, existing locked asyncpg 0.31.0 and SQLGlot 30.21.0 through the executor, pytest and pytest-asyncio. No dependency addition or upgrade.

**Spec:** [BUILD_SPEC](../../BUILD_SPEC.md), sections 2, 4, 6–8 and 11; [AGENTS](../../../AGENTS.md); [EX source record](../../EX_COMPARATOR.md); [DECISIONS](../../DECISIONS.md), D-003/D-022/D-023. Reuse the approved architectural design; this plan is only its comparator subsystem, not a new benchmark definition.

**Status:** Complete under Kunal's "yes do it" approval on 2026-10-04. Task 1 at a7be998 and Task 2 at 7d26e77 have passing task-done gates (60 units / 17 actual checks). The sole final read-only review found no actionable findings. Latest implementer full suite: 606 passed, zero skips, including 158 actual PostgreSQL checks (17.51s). Reviewer independently passed 60 units (0.20s). D-024/D-026 record every ruling and cost. Native execution stays selected; no generated SQL or benchmark score. G0.7a still needs the separately planned model/CLI flow.

## Global Constraints

- Workspace: `D:/PROJECTS/SQLWARDEN`. Use the current workspace; do not create a nested `sqlwarden` directory.
- Python 3.12 with uv; PostgreSQL 16 in Docker; native Ollama; React 18/TypeScript later.
- Kunal is the sole author and committer of new project commits.
- Keep legitimate third-party citations and required dataset, model and software license notices. Those are distinct from project contributor credits.
- No remote addition or push before the G7 release approval.
- Budget: INR 0 recurring. Any one-time spend, at most INR 1,500, needs explicit approval. Never assume a credit card, paid fallback or service signup is authorized.
- Keep inference local until a hosted configuration is explicitly approved.
- Use the approved dependency list in the plan. Ask before adding direct dependencies, spending money, accounts, benchmark changes, publication, destructive work or history edits.
- Keep the original exclusions: no user accounts, uploaded databases, write-query feature, semantic-layer DSL, UCI Online Retail, runtime multi-agent system, LangChain, LlamaIndex, LiteLLM, vector database service, Redis/queues, Kubernetes, or Project 2 work.
- Never commit secrets, data downloads, model weights, caches, raw run output or unrelated user changes.
- Use tests first for security boundaries, result comparison, voting, budgets and state transitions.
- Real PostgreSQL integration tests must run before database security claims.
- Implement only files needed by the current task. Do not generate the entire directory tree, empty abstractions, trivial tests or optional features in advance.
- Preserve the three original planning files as historical inputs.
- Gold SQL/results are accessible only to offline scoring, conversion validation and explicitly labelled analysis, never to retrieval, generation, repair, voting or inference-time decisions.
- Preserve the current named volume, imported data, credentials and PostgreSQL 17 service. Private .env.setup/.env.california files are tests-only; never use them to launch a runtime or prompt a model.
- After each fully completed task, update explaination of project/PROJECT_EXPLAINED.md in simple English, preserving earlier entries.
- No AI-generated SQL, model load, new download, benchmark gold execution, split freeze, exclusion decision, CLI/API or voting implementation in this increment.

## Review Focus

1. Matching prefixes, failed/blocked/overflowed predictions and bad references must not become correct answers; a bad reference must not silently change a benchmark denominator. Task 1 status/priority tests and Task 2 real overflow/error tests own this.
2. Row order, duplicate counts, column positions, column names and empty results must follow the pinned row-set rule, not a new semantic or voting comparator. Task 1 literal pairs/metadata tests and Task 2 native pairs own this.
3. NULL, native numeric equality, precise decimals, dates, adjacent floats, infinity and NaN identity must use Python value semantics, not the executor's JSON sizing representation. Task 1 native-cell/NaN tests and Task 2 casts own this.
4. Malformed row containers, unhashable values and signaling Decimal NaN must produce fixed outcomes without exposing rows, raw exceptions or reasons. Task 1 malformed/canary/immutable-record tests own this; Task 2 checks engine-error redaction and recovery.
5. Comparison must perform no database/model I/O and leak no reference data into an inference path; the real handoff must still use the existing guard and fixed restricted reader. Task 1 no-I/O test and Task 2 restricted controls own this. Source review checks imports/call sites; these tests are not formal information-flow proof.

## Scope and exact rule

Pinned upstream revision: `abd11b6db92a1c9f809b32f7564c7c71b34d67f0`.
The [official rule](https://github.com/bird-bench/mini_dev/blob/abd11b6db92a1c9f809b32f7564c7c71b34d67f0/evaluation/evaluation_ex.py#L18-L22)
uses equality of sets of complete row tuples. The [helper](https://github.com/bird-bench/mini_dev/blob/abd11b6db92a1c9f809b32f7564c7c71b34d67f0/evaluation/evaluation_utils.py#L57-L67)
fetches complete outputs first. Both exact source hashes were rechecked in memory
on 2026-10-04 and match EX_COMPARATOR.md; no upstream code was run or vendored.

The rule ignores row order, duplicate counts and column names, but not positions
within each row. It adds no tolerance or extra type tags. Thus 1, 1.0,
Decimal('1.0') and True can compare equal; date objects and matching date text do
not. Empty sets match even when column metadata has different widths. Distinct
NaN objects compare unequal, while sharing the same NaN object can match through
Python container identity semantics. Reproduce this rather than correcting it.
This is not a claim that PostgreSQL adaptation produces an official BIRD score.

The wrapper enforces the project's complete-result boundary:

| Condition, in priority order | score | reason |
| --- | --- | --- |
| Reference is not a complete usable QueryResult | None | gold_invalid |
| Prediction is not an ok QueryResult | 0 | prediction_failed |
| Prediction rows cannot be compared under the typed contract | 0 | comparison_error |
| Complete row sets match | 1 | match |
| Complete row sets differ | 0 | mismatch |

None means the reference cannot support scoring; it is NOT an instruction to drop
the question. C1/G0.7's frozen validity manifest owns gold failures and counts.
A pending/interrupted job is not a terminal QueryResult and remains pending in
the future job runner. Failed predictions remain failures in end-to-end EX; this
function computes no denominator or aggregate metric. No gold result enters the
future online agent's voting or repair path. Future duplicate-preserving voting
must use its own comparator, not this one.

QueryResult is a trusted internal container, not an unforgeable proof of EOF.
The executor creates ok only after completing its bounded fetch. Synthetic unit
fixtures deliberately construct complete or malformed results. The helper checks
the tuple container contract and catches normal hashing/equality failures; it
does not sandbox arbitrary Python objects, validate cache files, or establish a
hard memory/CPU deadline. Keep future request input away from these constructors.
Sets allocate additional memory over the already bounded results. No stricter
cell normalization, new result authority token, registry, cache or result-type
refactor is needed here.

## File map and interfaces

- Create `src/sqlwarden/comparator.py`: pure complete-result EX wrapper.
- Create `tests/test_comparator.py`: literal, no-I/O unit controls.
- Create `tests/test_comparator_postgres.py`: handwritten restricted native controls.
- Update `docs/EX_COMPARATOR.md`: implementation contract, actual checks and residuals.
- Update `docs/PROGRESS.md`, `docs/DECISIONS.md`, and `explaination of project/PROJECT_EXPLAINED.md` after each completed task and final review.
- Keep executor/guard/config, dependency files, original plans and data unchanged.

Consumes the existing frozen/slotted QueryResult with status in
ok/blocked/failed/overflow, reason: str, columns: tuple[str, ...],
rows: tuple[Row, ...], and result_bytes: int. Row is
tuple[str | int | float | bool | Decimal | date | None, ...].

Produces `compare_ex(predicted: QueryResult, reference: QueryResult) -> EXComparison`.
EXComparison is frozen/slotted with exactly `score: Literal[0, 1] | None` and
`reason: Literal['match', 'mismatch', 'prediction_failed', 'gold_invalid', 'comparison_error']`.
The record contains no rows, SQL or raw diagnostic details.

Task 2 consumes `open_california_executor(password: str, limits: QueryLimits)`,
an async context manager yielding QueryExecutor; limits may be omitted for current
defaults. `await executor.execute(sql: str) -> QueryResult` guards SQL internally.
Do not add a caller-supplied policy, host, role or successful-result shortcut.

## Commands and private diagnostics

Run PowerShell commands from the repository root. If uv is not on PATH, replace
`uv` with `& 'C:/Users/Kunal/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uv.exe'`.
Use `--tb=line` for every private database test command; never use `--showlocals`.
No raw connection arguments, setup values or server logs enter documentation.
The rotated reader password stays private; do not rerun credential initialization
or the ignored rotation probe.

## Task 1: Pure complete-result EX comparison

**Files:** Create `src/sqlwarden/comparator.py` and `tests/test_comparator.py`;
update the four evidence/notebook files listed above. No existing runtime edit.

**Interfaces:** Consumes QueryResult/Row from sqlwarden.executor. Produces the
EXComparison record and compare_ex signature defined in File map; no SQL execution,
gold-file loading, environment read, rounding, log listener or model call.

- [x] **Step 1: Write the complete unit controls before creating the module.**

Add `tests/test_comparator.py`:

```python
"""Pinned EX semantics and complete-result boundaries without database I/O."""

import math
from dataclasses import FrozenInstanceError, fields
from datetime import date
from decimal import Decimal

import asyncpg
import pytest

import sqlwarden.executor as executor_module
from sqlwarden.comparator import EXComparison, compare_ex
from sqlwarden.executor import QueryResult


def complete(rows=(), columns=None):
    if columns is None:
        width = len(rows[0]) if rows else 1
        columns = tuple(f"c{i}" for i in range(width))
    return QueryResult("ok", "complete", columns, tuple(rows))


@pytest.mark.parametrize(
    "predicted_rows,reference_rows,score",
    [
        (((2,), (1,)), ((1,), (2,)), 1),
        (((1,), (1,), (2,)), ((2,), (1,)), 1),
        (((1,), (2,)), ((1,),), 0),
        (((1, 2),), ((2, 1),), 0),
        (((1, 2),), ((1,),), 0),
        ((), (), 1),
        (((None,),), ((None,),), 1),
        (((None,),), ((0,),), 0),
        (((None,),), (("None",),), 0),
        (((1,),), ((1.0,),), 1),
        (((1,),), ((Decimal("1.0"),),), 1),
        (((1,),), ((True,),), 1),
        (((0,),), ((False,),), 1),
        (((Decimal("0.1"),),), ((0.1,),), 0),
        (((0.1,),), ((math.nextafter(0.1, math.inf),),), 0),
        (((0.0,),), ((-0.0,),), 1),
        (((math.inf,),), ((math.inf,),), 1),
        (((math.inf,),), ((-math.inf,),), 0),
        (((date(2024, 1, 1),),), ((date(2024, 1, 1),),), 1),
        (((date(2024, 1, 1),),), (("2024-01-01",),), 0),
        ((("1",),), ((1,),), 0),
        ((("é",),), (("é",),), 1),
        ((("é",),), (("e",),), 0),
        (((Decimal("1.00000000000000000001"),),), ((1,),), 0),
    ],
)
def test_literal_row_set_rule(predicted_rows, reference_rows, score):
    outcome = compare_ex(complete(predicted_rows), complete(reference_rows))
    assert outcome == EXComparison(score, "match" if score else "mismatch")
    assert type(outcome.score) is int


def test_column_names_and_byte_metadata_are_not_answer_data():
    predicted = QueryResult("ok", "complete", ("x", "x"), ((1, 2),), 100)
    reference = QueryResult("ok", "complete", ("a", "b"), ((1, 2),), 200)
    assert compare_ex(predicted, reference) == EXComparison(1, "match")


def test_empty_outputs_match_without_column_alignment():
    assert compare_ex(complete(columns=("a",)), complete(columns=("b", "c"))) == (
        EXComparison(1, "match")
    )


def test_distinct_nan_objects_do_not_match():
    assert compare_ex(complete(((float("nan"),),)), complete(((float("nan"),),))) == (
        EXComparison(0, "mismatch")
    )


def test_shared_nan_object_preserves_python_container_identity():
    value = float("nan")
    assert compare_ex(complete(((value,),)), complete(((value,),))) == EXComparison(1, "match")


@pytest.mark.parametrize("status", ["blocked", "failed", "overflow"])
@pytest.mark.parametrize("prefix", [(), ((1,),)])
def test_unsuccessful_predictions_cannot_match_even_a_retained_prefix(status, prefix):
    predicted = QueryResult(status, "private-reason-canary", ("n",), prefix)
    assert compare_ex(predicted, complete(prefix)) == EXComparison(0, "prediction_failed")


@pytest.mark.parametrize("status", ["blocked", "failed", "overflow"])
def test_unsuccessful_reference_is_unscorable_not_a_prediction_failure(status):
    reference = QueryResult(status, "private-reason-canary", ("n",), ((1,),))
    assert compare_ex(complete(((1,),)), reference) == EXComparison(None, "gold_invalid")


def test_reference_failure_has_priority_when_both_sides_fail():
    assert compare_ex(QueryResult("failed", "a"), QueryResult("overflow", "b")) == (
        EXComparison(None, "gold_invalid")
    )


@pytest.mark.parametrize("invalid", [None, {}, object(), "private-result-canary"])
@pytest.mark.parametrize("side", ["prediction", "reference"])
def test_wrong_result_objects_have_fixed_outcomes(invalid, side):
    valid = complete(((1,),))
    predicted, reference = (invalid, valid) if side == "prediction" else (valid, invalid)
    expected = (
        EXComparison(0, "prediction_failed")
        if side == "prediction"
        else EXComparison(None, "gold_invalid")
    )
    assert compare_ex(predicted, reference) == expected


@pytest.mark.parametrize(
    "rows",
    [
        None,
        [(1,)],
        ([1],),
        ("private-row-canary",),
        ((["private-cell-canary"],),),
        ((Decimal("sNaN"),),),
    ],
)
@pytest.mark.parametrize("side", ["prediction", "reference"])
def test_bad_row_containers_or_hashing_do_not_echo_data(rows, side, caplog, capsys):
    invalid = QueryResult("ok", "private-reason-canary", ("private-column-canary",), rows)
    valid = complete(((1,),))
    predicted, reference = (invalid, valid) if side == "prediction" else (valid, invalid)
    outcome = compare_ex(predicted, reference)
    expected = (
        EXComparison(0, "comparison_error")
        if side == "prediction"
        else EXComparison(None, "gold_invalid")
    )
    assert outcome == expected
    assert "private-" not in repr(outcome) + caplog.text + str(capsys.readouterr())


def test_outcome_is_immutable_and_has_no_answer_or_diagnostic_fields():
    outcome = compare_ex(complete(((1,),)), complete(((1,),)))
    assert [field.name for field in fields(outcome)] == ["score", "reason"]
    assert not hasattr(outcome, "__dict__")
    with pytest.raises(FrozenInstanceError):
        outcome.score = 0


def test_comparison_does_not_open_a_pool_connect_or_guard(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Comparison must not perform query I/O")

    monkeypatch.setattr(asyncpg, "connect", forbidden)
    monkeypatch.setattr(asyncpg, "create_pool", forbidden)
    monkeypatch.setattr(executor_module, "guard_sql", forbidden)
    assert compare_ex(complete(((1,),)), complete(((1,),))) == EXComparison(1, "match")
```

- [x] **Step 2: Observe real RED before implementation.**

Run `uv run pytest tests/test_comparator.py -q --tb=line`.
Expected: collection fails because sqlwarden.comparator does not exist. If the
file already exists, reconcile Git/Handoff rather than overwriting or treating a
different import/environment failure as the intended RED.

- [x] **Step 3: Add the small independent implementation.**

Create `src/sqlwarden/comparator.py`:

```python
"""Offline row-set EX for complete results, not the future voting comparator.

Rule independently reproduced from bird-bench/mini_dev evaluation_ex.py,
revision abd11b6db92a1c9f809b32f7564c7c71b34d67f0, lines 18-22.
See docs/EX_COMPARATOR.md for the primary-source link and fingerprints.
"""

from dataclasses import dataclass
from typing import Literal

from sqlwarden.executor import QueryResult, Row


@dataclass(frozen=True, slots=True)
class EXComparison:
    score: Literal[0, 1] | None
    reason: Literal["match", "mismatch", "prediction_failed", "gold_invalid", "comparison_error"]


def _row_set(result: QueryResult) -> set[Row]:
    if type(result.rows) is not tuple or any(type(row) is not tuple for row in result.rows):
        raise TypeError("Invalid result row container")
    return set(result.rows)


def compare_ex(predicted: QueryResult, reference: QueryResult) -> EXComparison:
    """Score a terminal prediction; invalid gold does not select a denominator."""
    if type(reference) is not QueryResult or reference.status != "ok":
        return EXComparison(None, "gold_invalid")
    try:
        reference_rows = _row_set(reference)
    except (TypeError, ValueError, ArithmeticError):
        return EXComparison(None, "gold_invalid")
    if type(predicted) is not QueryResult or predicted.status != "ok":
        return EXComparison(0, "prediction_failed")
    try:
        matches = _row_set(predicted) == reference_rows
    except (TypeError, ValueError, ArithmeticError):
        return EXComparison(0, "comparison_error")
    return EXComparison(1, "match") if matches else EXComparison(0, "mismatch")
```

Catch only ordinary container/value/arithmetic errors, never BaseException or
external cancellation. Do not stringify, log or return the caught exception.
The accepted Cell union contains no user-defined hashing/equality code; adversarial
Python objects are outside the trusted constructor contract. No executor change.

- [x] **Step 4: Verify GREEN and the existing deterministic suite.**

Run `uv run pytest tests/test_comparator.py -q --tb=line`, then
`uv run pytest -q --tb=line`, `uv run ruff check .`,
`uv run ruff format --check .`, and `git diff --check`.
Expected: all comparator units pass; existing deterministic tests pass; real
database tests skip without private configuration; lint/format/whitespace pass.
Record actual counts, skips and timings. Fix a real new failure test-first, not
by relaxing expected semantics. No PostgreSQL acceptance claim from this step.

- [x] **Step 5: Save evidence and the learning entry, then commit Task 1.**

Update EX_COMPARATOR with the exact five outcomes, pending-denominator boundary
and remaining native verification. Add a dated PROGRESS entry with RED/GREEN,
actual counts and next Task 2. Record any deviation and its concrete cost in
DECISIONS; do not fabricate a decision if no deviation occurred. Add a notebook
entry: "The checker is built for complete answers. It ignores row order and repeated
rows because that is the saved BIRD rule; it does not round close numbers. A failed
answer is not correct, and a broken reference needs separate handling. Real database
checks come next." Explain EX, reference, set, float and NaN in simple English.

Stage only the two new Python files and updated evidence/notebook files:

```powershell
git add src/sqlwarden/comparator.py tests/test_comparator.py docs/EX_COMPARATOR.md docs/PROGRESS.md docs/DECISIONS.md 'explaination of project/PROJECT_EXPLAINED.md'
git diff --cached --check
git diff --cached
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
git commit -m 'feat(comparator): preserve pinned complete-result EX semantics'
git log -1 --format=fuller
git log -1 --format=%B
git status --short
```

Inspect the entire staged change and exact message before committing; both
identities must be Kunal <kunalchandrakar2005@gmail.com>, with no trailers or
assistant credit. Update the next progress record with this actual commit hash.

## Task 2: Restricted PostgreSQL handoff and actual native semantics

**Files:** Create `tests/test_comparator_postgres.py`; update
`docs/EX_COMPARATOR.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`, and
`explaination of project/PROJECT_EXPLAINED.md`. No database, grant, data, guard,
executor or dependency change is planned.

**Interfaces:** Consumes compare_ex/EXComparison from Task 1, QueryLimits from
sqlwarden.config and open_california_executor from sqlwarden.executor. The existing
test-only california_connected context gates the dedicated target/reader. Runtime
code still cannot read either test environment file. All SQL below is handwritten
test control input, not generated SQL or a benchmark question/reference pair.

- [x] **Step 1: Write these real controls before considering any corrective code.**

Create `tests/test_comparator_postgres.py`:

```python
"""Handwritten native controls, not BIRD gold execution or a benchmark score."""

import os

import pytest
from test_bird_load import california_connected

from sqlwarden.comparator import EXComparison, compare_ex
from sqlwarden.config import QueryLimits
from sqlwarden.executor import open_california_executor

pytestmark = pytest.mark.integration


async def ready():
    async with california_connected():
        pass


def password():
    return os.environ["WARDEN_CALIFORNIA_PASSWORD"]


@pytest.mark.parametrize(
    "predicted_sql,reference_sql,score",
    [
        ("SELECT count(*) AS n FROM schools", "SELECT 17686 AS reference_count", 1),
        (
            "SELECT n FROM (VALUES (1),(2),(1)) x(n) ORDER BY n",
            "SELECT n FROM (VALUES (2),(1)) x(n) ORDER BY n DESC",
            1,
        ),
        ("SELECT 1 AS a, 2 AS b", "SELECT 2 AS a, 1 AS b", 0),
        (
            "SELECT cdscode FROM schools WHERE false",
            "SELECT NULL AS a, NULL AS b WHERE false",
            1,
        ),
        ("SELECT NULL AS n", "SELECT 0 AS n", 0),
        ("SELECT NULL AS n", "SELECT NULL AS other", 1),
        ("SELECT CAST('1.0' AS numeric) AS n", "SELECT 1 AS n", 1),
        ("SELECT '1' AS n", "SELECT 1 AS n", 0),
        (
            "SELECT CAST('2024-01-01' AS date) AS n",
            "SELECT CAST('2024-01-01' AS date) AS other",
            1,
        ),
        ("SELECT CAST('2024-01-01' AS date) AS n", "SELECT '2024-01-01' AS n", 0),
        (
            "SELECT CAST('NaN' AS double precision) AS n",
            "SELECT CAST('NaN' AS double precision) AS other",
            0,
        ),
        (
            "SELECT CAST('0.1' AS double precision) AS n",
            "SELECT CAST('0.10000000000000002' AS double precision) AS n",
            0,
        ),
    ],
)
async def test_real_native_complete_pairs(predicted_sql, reference_sql, score):
    await ready()
    async with open_california_executor(password()) as executor:
        predicted = await executor.execute(predicted_sql)
        reference = await executor.execute(reference_sql)
        assert predicted.status == reference.status == "ok"
        assert compare_ex(predicted, reference) == EXComparison(
            score, "match" if score else "mismatch"
        )


@pytest.mark.parametrize("invalid_side", ["prediction", "reference"])
async def test_real_overflow_cannot_match_the_complete_prefix(invalid_side):
    await ready()
    async with open_california_executor(password(), QueryLimits(max_rows=2)) as executor:
        valid = await executor.execute("SELECT n FROM (VALUES (1),(2)) x(n) ORDER BY n")
        invalid = await executor.execute("SELECT n FROM (VALUES (1),(2),(3)) x(n) ORDER BY n")
        assert valid.status == "ok" and valid.rows == ((1,), (2,))
        assert (invalid.status, invalid.reason, invalid.rows) == ("overflow", "row_limit", ())
        predicted, reference = (
            (invalid, valid) if invalid_side == "prediction" else (valid, invalid)
        )
        expected = (
            EXComparison(0, "prediction_failed")
            if invalid_side == "prediction"
            else EXComparison(None, "gold_invalid")
        )
        assert compare_ex(predicted, reference) == expected
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)


@pytest.mark.parametrize("invalid_side", ["prediction", "reference"])
async def test_real_engine_failure_is_fixed_and_next_query_recovers(invalid_side, caplog, capsys):
    await ready()
    async with open_california_executor(password()) as executor:
        valid = await executor.execute("SELECT 1 AS n")
        invalid = await executor.execute("SELECT CAST('private-canary' AS int)")
        assert valid.status == "ok"
        assert (invalid.status, invalid.reason, invalid.rows) == ("failed", "database_error", ())
        predicted, reference = (
            (invalid, valid) if invalid_side == "prediction" else (valid, invalid)
        )
        outcome = compare_ex(predicted, reference)
        expected = (
            EXComparison(0, "prediction_failed")
            if invalid_side == "prediction"
            else EXComparison(None, "gold_invalid")
        )
        assert outcome == expected
        assert "private-canary" not in (
            repr(invalid) + repr(outcome) + caplog.text + str(capsys.readouterr())
        )
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)


async def test_real_guard_block_is_a_failure_not_a_correct_empty_answer():
    await ready()
    async with open_california_executor(password()) as executor:
        predicted = await executor.execute("DELETE FROM schools")
        reference = await executor.execute("SELECT 1 AS n")
        assert predicted.status == "blocked" and predicted.columns == () and predicted.rows == ()
        assert reference.status == "ok"
        assert compare_ex(predicted, reference) == EXComparison(0, "prediction_failed")
        assert (await executor.execute("SELECT 1 AS n")).rows == ((1,),)
```

All 24 SQL inputs in the twelve successful pair controls were accepted by the
pure guard during preparation. That is not evidence that these new database tests ran.
The 17 integration cases test the production handoff, not a new algorithm; Task 1
owns the required initial RED. Do not alter working production code or loosen
the database boundary merely to manufacture an integration RED.

- [x] **Step 2: Run the actual restricted controls.**

Run `uv run --env-file .env.setup --env-file .env.california pytest tests/test_comparator_postgres.py -q --tb=line`.
Expected: 17 pass, zero skips on the existing dedicated target. A skipped run is
not acceptance. No admin connection, write, import, privilege/credential change
or model output is needed. If native behavior differs, inspect sanitized type and
fixed-category evidence before changing code; preserve the pinned rule. Write a
unit regression before any necessary correction and record its rationale/cost.

- [x] **Step 3: Recheck the whole increment and unchanged boundaries.**

Run, as separate commands with each exit code captured:

```powershell
uv sync --locked
uv run pytest -q --tb=line
uv run --env-file .env.setup pytest -q --tb=line
uv run --env-file .env.setup --env-file .env.california pytest -q --tb=line
uv run ruff check .
uv run ruff format --check .
git diff --check
git diff -- sqlwarden-plan.md SQLWARDEN_EXECUTION_PROMPT.md SQLWARDEN_PLAN_REVIEW.md pyproject.toml uv.lock src/sqlwarden/guard.py src/sqlwarden/executor.py src/sqlwarden/config.py
git remote -v
& 'C:/Users/Kunal/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe' inspect sqlwarden-postgres-1 --format '{{.State.Health.Status}} {{json .HostConfig.PortBindings}} {{range .Mounts}}{{.Name}} {{end}}'
& 'C:/Users/Kunal/AppData/Local/Programs/Ollama/ollama.exe' ps
```

Expected: full configured suite has zero skips and includes the actual new 17
PostgreSQL cases; unconfigured/setup-only runs skip only unsupplied reader tests.
Lint/format/whitespace pass; original plans/runtime/dependency diff and remotes
empty; Docker healthy on 127.0.0.1:55432 with sqlwarden_pg16_data preserved; no
loaded model. Record actual counts/timings, not the expectation as a result.
These tests do not establish a hard Python memory/time cap, exhaustive SQL safety,
benchmark validity, inference leakage prevention or end-to-end question answering.

- [x] **Step 4: Save real evidence and commit Task 2.**

Update EX_COMPARATOR with actual unit/native/full results, exact source revision,
unchanged equality rule, invalid-gold manifest boundary and residual limits.
PROGRESS marks only the comparator implementation/native checks complete, with
one final read-only review next. DECISIONS records any runtime deviations in order.
Notebook entry: "The answer checker now passes small handwritten checks on the real
database. Repeated rows and order are ignored, swapped columns do not match, and
failed or oversized answers cannot be called correct. The close-number and missing-
value checks pass too. These are checks of the code, not an AI accuracy score; the
AI command-line demonstration is still next." Include actual counts and explain
reference failures without promising an automatic exclusion or benchmark score.

```powershell
git add tests/test_comparator_postgres.py docs/EX_COMPARATOR.md docs/PROGRESS.md docs/DECISIONS.md 'explaination of project/PROJECT_EXPLAINED.md'
git diff --cached --check
git diff --cached
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
git commit -m 'test(comparator): verify native result and failure boundaries'
git log -1 --format=fuller
git log -1 --format=%B
git status --short
```

Inspect all staged files/message first and verify sole owner identity/body after.
If corrective production/unit files changed, include only those demonstrated fixes
and record them; never stage private env files or raw results.

## Single final review and handoff

After both tasks, use the executing-plans native final-review gate: one fresh
read-only reviewer of this complete comparator increment against the recorded
pre-implementation HEAD. Do not redo the completed executor, guard or import
reviews and do not dispatch a second review. Required review inputs include this
plan, BUILD_SPEC, all five Review Focus conditions, exact source record and every
execution ruling. Apply the skill's bounded correction gate for actionable
findings; record every declined-to-judge ruling and concrete cost, deferred minors
and actual final checks in DECISIONS/PROGRESS/notebook. Do not delete retained
scratch without approval or offer a prohibited remote/push/merge action.

Once the whole comparator increment actually passes, mark only its G0.7a child
complete. G0.7a still needs the separately planned safe one-database model/CLI flow;
C1, frozen benchmark runs, broader agent/voting/UI/release remain unfinished.
Do not execute model-generated SQL during this plan or report a benchmark score.

Completion record (2026-10-04): both planned tasks and task-done gates complete;
sole fresh read-only review covered 1ffb81d..7d26e77. No Critical/Important/Minor
findings or deferred minors; no correction pass or second reviewer. Final checks
and independently repeated versus implementer evidence are recorded above and
in PROGRESS/EX_COMPARATOR. All six declined-to-judge boundaries and the ordered
final rulings/costs are persisted in D-026, continuing D-024's setup ruling.
Notebook updated. Current local branch and ignored scratch retained without
merge/remote/push/publication/deletion under owner rules; no CLI implementation.

## Preparation self-review record

This is the pre-approval preparation snapshot; current execution status is above.

- Spec coverage: complete-only result use, pinned duplicates/order/NULL/floats/empty/error semantics, fixed private outcomes, local restricted acceptance, test-first workflow and notebook are owned by Tasks 1–2. Voting, validity manifest, aggregate/resumable evaluation, model/CLI, tenant RLS and release are explicit separate milestones, not missing comparator steps.
- Placeholder scan: every code step has complete source/tests; commands, paths, outcomes and commit messages are concrete. Checkboxes are unchecked because implementation has not run.
- Type consistency: both tasks use existing QueryResult/Row and the same compare_ex/EXComparison interface; no sizing-string conversion, nonexistent type, new credential loader or guard shortcut.
- Review Focus: all five conditions map to named literal/status/malformed/no-I/O unit controls and bounded real pair/overflow/error/guard controls. No claim of proof beyond those checks.
- Syntax-only preparation checks parse the three Python fences without executing them. Snippet lint/format checks classify the proposed sqlwarden module as first-party explicitly because it does not exist yet; production configuration is unchanged. AST inspection counts 60 planned unit cases and 17 planned integration cases, not test passes. Native semantics probes use synthetic Python values, and guard preflight performs no database I/O. Actual comparator RED/GREEN and the 17 new integration tests await plan approval.

**Review approval:** Kunal's "yes do it" approves this artifact. Preserve native
sequential execution; do not ask again about the execution method or previously
approved dependencies. Both tasks, completion gates and the sole final review
are now complete; do not repeat them or dispatch another comparator reviewer.

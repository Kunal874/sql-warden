# G2/C4 Guardrail Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make G2.1/C4 explicit and checked: reviewed SQL function/cast policy,
fixed execution-limit defaults, cost-threshold rationale and role-specific tenant
design.

**Architecture:** Keep the runtime guard/executor small. Add an explicit security
contract module that the existing guard/config code consumes, then record C4 in
docs. Do not add dependencies, change database objects, or run live inference.

**Tech Stack:** Python 3.12, stdlib dataclasses, existing sqlglot/asyncpg code,
pytest and uv.

**Spec:** `docs/BUILD_SPEC.md` sections 5-7 and `docs/PROGRESS.md` G2.1/C4.

## Global Constraints

- Work in `D:/PROJECTS/SQLWARDEN`; keep inference local.
- No new direct dependencies, spending, accounts, remote, push, publication,
  benchmark changes, destructive work or history edits.
- Kunal is sole author/committer: `Kunal <kunalchandrakar2005@gmail.com>`.
- Never commit secrets, downloads, model weights, caches or raw runs.
- Use tests first for security boundaries and state/limit transitions.
- Real PostgreSQL integration tests must run before database security claims.

## Review Focus

- Qualified built-in functions such as `pg_catalog.lower(...)` must not bypass the
  reviewed-function policy.
- Session-mutating functions such as `set_config(...)` and risky functions such as
  `pg_read_file(...)` must remain blocked.
- Execution default limits must be explicit and finite; malformed limits still fail
  before a query.
- Tenant design must use role-specific identities, not a mutable SQL setting, and
  must be recorded before G2.6 implements it.
- C4 docs must not claim hosted/public security or unimplemented RLS behavior.

---

### Task 1: Explicit guardrail contract

**Files:**
- Create: `src/sqlwarden/security_contract.py`
- Modify: `src/sqlwarden/guard.py`
- Modify: `src/sqlwarden/config.py`
- Test: `tests/test_security_contract.py`

**Interfaces:**
- Produces: `REVIEWED_FUNCTIONS`, `REVIEWED_CAST_TYPES`,
  `DEFAULT_QUERY_LIMITS`, `TENANT_AUTHORIZATION_DESIGN`,
  `allowed_function_classes()`, `allowed_cast_type_names()`.
- Consumes: existing `sqlwarden.guard.FUNCTION_NAMES`,
  `sqlwarden.guard.CAST_TYPES`, `sqlwarden.config.QueryLimits`.

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```python
from sqlwarden.config import QueryLimits
from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql
from sqlwarden.security_contract import (
    DEFAULT_QUERY_LIMITS,
    REVIEWED_CAST_TYPES,
    REVIEWED_FUNCTIONS,
    TENANT_AUTHORIZATION_DESIGN,
)

def test_reviewed_function_contract_is_exactly_the_runtime_allowlist():
    assert {item["sqlglot_class"] for item in REVIEWED_FUNCTIONS} == {...}
    assert guard_sql("SELECT lower('ABC')", CALIFORNIA_POLICY).accepted
    assert not guard_sql("SELECT pg_catalog.lower('ABC')", CALIFORNIA_POLICY).accepted
    assert not guard_sql("SELECT set_config('search_path','app',false)", CALIFORNIA_POLICY).accepted

def test_reviewed_cast_and_limit_contracts_are_exact_runtime_values():
    assert {item["type"] for item in REVIEWED_CAST_TYPES} == {...}
    assert DEFAULT_QUERY_LIMITS == QueryLimits()

def test_c4_tenant_design_rejects_mutable_session_setting_boundary():
    assert TENANT_AUTHORIZATION_DESIGN["tenant_selector"] == "server_chosen_database_role"
    assert TENANT_AUTHORIZATION_DESIGN["mutable_session_setting_boundary"] == "rejected"
```

Run:

```powershell
uv run pytest tests/test_security_contract.py -q --tb=line
```

Expected: fail because `sqlwarden.security_contract` does not exist.

- [ ] **Step 2: Implement minimal contract module and wire constants**

Create `src/sqlwarden/security_contract.py` with the reviewed data. Import
`allowed_function_classes()` and `allowed_cast_type_names()` from `guard.py` instead
of duplicating the lists there. Import `DEFAULT_QUERY_LIMITS` as the defaults in
`QueryLimits` tests.

- [ ] **Step 3: Verify focused tests pass**

Run:

```powershell
uv run pytest tests/test_security_contract.py tests/test_guard.py tests/test_executor.py -q --tb=line
```

Expected: pass.

### Task 2: C4 docs and progress

**Files:**
- Modify: `docs/DECISIONS.md`
- Modify: `docs/PROGRESS.md`
- Modify: `explaination of project/PROJECT_EXPLAINED.md`

**Interfaces:**
- Consumes: `src/sqlwarden/security_contract.py` values.
- Produces: D-060 C4 decision and updated G2.1 checklist/handoff.

- [ ] **Step 1: Document the C4 decision**

Record:

- exact reviewed function/cast policy;
- current default cost/row/byte/time limits;
- tenant design: server chooses separate tenant database roles, forced RLS later,
  mutable `app.tenant_id` alone rejected.

- [ ] **Step 2: Run verification**

Run:

```powershell
uv run pytest tests/test_security_contract.py tests/test_guard.py tests/test_executor.py -q --tb=line
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Expected: all pass.

### Task 3: Commit checked G2.1 slice

**Files:**
- Stage only Task 1-2 files and this plan.

**Steps:**

- [ ] Inspect staged diff and exact commit message.
- [ ] Commit as `feat(security): record c4 guardrail contract`.
- [ ] Verify `git log -1 --format=fuller` and `git log -1 --format=%B` show Kunal only.

## Done criteria

- G2.1 is checked in `docs/PROGRESS.md`.
- C4 is recorded in `docs/DECISIONS.md`.
- The simple-English notebook explains the new terms.
- Focused tests, Ruff and diff whitespace pass.
- No live model call, source/gold mutation, raw run, remote or push.

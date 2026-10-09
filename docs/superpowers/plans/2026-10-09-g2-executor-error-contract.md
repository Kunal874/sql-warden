# G2 Executor Error Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete G2.3 by making executor caps/deadlines/error categories explicit
and checked against existing executor behavior.

**Architecture:** Extend the existing security contract with the stable executor
reason/status map. Add tests that exercise current fake-executor paths and verify
all observed reasons are documented. Do not change database schema or credentials.

**Spec:** `docs/BUILD_SPEC.md` G2.3 and executor-boundary sections.

## Tasks

### Task 1: Executor reason contract

**Files:**
- Modify: `src/sqlwarden/security_contract.py`
- Modify: `tests/test_security_contract.py`
- Test: `tests/test_executor.py`

**Checks:**
- every documented reason maps to `ok`, `blocked`, `failed` or `overflow`;
- representative executor outcomes use only documented reasons;
- existing executor tests continue to pass.

### Task 2: Docs and commit

**Files:**
- Modify: `docs/PROGRESS.md`
- Modify: `docs/DECISIONS.md`
- Modify: `explaination of project/PROJECT_EXPLAINED.md`

**Checks:**
- focused security/executor tests pass;
- Ruff and diff whitespace pass;
- commit as `feat(security): record executor error contract`.

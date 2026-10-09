# G2 Guard Coverage Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete G2.2 by proving the guard has at least 40 meaningful cases and
recording a compact safe-gold guard acceptance audit.

**Architecture:** Keep runtime behavior unchanged. Add a read-only script that
loads the corrected usable pool, transpiles corrected SQL using existing helpers,
runs the pure guard, and writes compact counts/reasons only.

**Tech Stack:** Python 3.12, existing scripts/validate_gold helpers, pytest, uv.

**Spec:** `docs/BUILD_SPEC.md` G2.2 and `docs/PROGRESS.md` G2 checklist.

## Global Constraints

- No raw SQL, result rows, credentials, downloads, model calls, hosted calls,
  remote, push, publication or benchmark-definition change.
- Compact tracked audit outputs may contain IDs/counts/reasons only.
- Use tests first.

## Tasks

### Task 1: Guard audit helper and script

**Files:**
- Create: `scripts/audit_guard_gold.py`
- Test: `tests/test_guard_audit.py`

**Checks:**
- helper summarizes accepted/blocked/transpile failures without SQL text;
- script writes `docs/guard-gold-audit-manifest.json`;
- guard test corpus has at least 40 case strings.

### Task 2: Run audit, docs and commit

**Files:**
- Create: `docs/guard-gold-audit-manifest.json`
- Modify: `docs/PROGRESS.md`
- Modify: `docs/DECISIONS.md`
- Modify: `explaination of project/PROJECT_EXPLAINED.md`

**Checks:**
- focused guard audit tests pass;
- script runs;
- focused guard tests pass;
- Ruff and diff whitespace pass.

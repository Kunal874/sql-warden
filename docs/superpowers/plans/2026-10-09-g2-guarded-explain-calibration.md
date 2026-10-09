# G2 Guarded EXPLAIN Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete G2.4 by recording guarded EXPLAIN ordering, same identity/settings
evidence and calibrated cost thresholds.

**Architecture:** Runtime already performs guarded EXPLAIN under the restricted
identity. Add a compact manifest and test it against `QueryLimits`, then run the
unit and real PostgreSQL checks that prove the behavior.

**Spec:** `docs/BUILD_SPEC.md` G2.4.

## Tasks

1. Add a compact `docs/executor-cost-calibration-manifest.json`.
2. Add a test that the manifest matches current `QueryLimits`.
3. Run focused executor and real PostgreSQL cost/identity checks.
4. Update progress/decisions/notebook and commit.

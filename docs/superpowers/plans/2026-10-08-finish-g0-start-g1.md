# Finish G0 and start G1 — implementation plan

> Owner direction: Kunal's 2026-10-08 instruction explicitly selects sequential
> inline execution of the remaining G0 checklist and the first G1 slice. Do not
> pause for routine plan review. Ask only if observed C1 evidence creates a real
> choice that the active spec says must not be inferred, or for a genuine blocker.

**Spec:** `docs/BUILD_SPEC.md` sections 5–8 and 11; original task IDs in
`sqlwarden-plan.md`; current state in `docs/PROGRESS.md`.

**Goal:** finish G0 with a truthful PostgreSQL-adapted validity manifest, frozen
protocol, second local model smoke and measured E0, then complete G1.1's first
provider/cache slice. Keep all inference local, one GPU model at a time.

**Non-goals:** no hosted service, publication, remote/push, new direct dependency,
source/gold mutation, benchmark cherry-picking, G1.2+ implementation, G2 claim,
or official BIRD leaderboard equivalence.

## Fixed design choices

- Use the already pinned `bird_sqlite`, `bird_pg`, `arcwise_sql`, and
  `arcwise_full` files, aligned by integer question ID and database—not list order.
- Treat `bird_pg` as the proposed PostgreSQL conversion for original labels.
  Transpile corrected SQLite SQL with pinned SQLGlot 30.21.0. Never edit a gold SQL
  string to make it pass; classify failure instead.
- Cross-dialect validation compares complete results with typed, lossless
  canonicalization: null tag; booleans; exact integers/decimals; finite floats via
  their exact decimal text (no tolerance/rounding); text unchanged; byte hex;
  date/time ISO. Result row order is ignored and duplicates are preserved for
  conversion validity. Official EX remains the separately pinned set comparator.
- Read SQLite immutable/query-only and PostgreSQL through each dataset's restricted
  login in a read-only transaction. Fixed limits: 10 seconds/query, 100,000 rows,
  16 MiB result bytes, 1 MiB/cell, 30 minutes per track. A limit/failure is an
  explicit exclusion reason, never silently removed.
- C1 default if at least 95% of aligned `arcwise_full` items verify: primary labels
  are `arcwise_full`; IDs 119/120 remain missing; corrected descriptions are primary;
  text-difference IDs are candidate ambiguity labels (`needs_review`), not automatic
  positives. Clear unchanged matched items are negatives. If survival is below 95%,
  stop only then with measured options as BUILD_SPEC requires.
- Freeze a seeded 100-item development split after validity, stratified by database
  and difficulty with variant families kept together. Seed `20261008`; the remaining
  usable IDs are held out. Never tune from held-out results.
- Second model: official Snowflake revision
  `2d73facaf7e15831d0b918d219e0d565f113f592`, Apache-2.0; community GGUF revision
  `8e1a51188952afa8021bce6c8b3e5b495b3e85cd`, Q4_K_M file size 4,683,074,144,
  SHA-256 `9c005244e3ab7fada2c53a9511999f4d22fbbd4f76a4416416a6d41d82702255`.
  Create a context-8192 Ollama alias only after hash verification. One model loaded.
- E0 is single-shot, temperature zero, no repair/voting/retrieval/clarification.
  Full schema really means every table/column/key/selected description for that
  question's database. Guard and restricted execution stay enabled. Fixed per-item
  generation 120 seconds, total request 150 seconds, max output 1024 tokens; record
  failures. Report exact n, EX, 10,000-resample seeded 95% bootstrap interval,
  median/p95 seconds, token availability and peak VRAM. No hidden retries.
- C2 default is evidence-based: retain both 7B models only if both complete the smoke
  and E0 within local limits; otherwise retain the working model and record the other
  as unavailable/too slow. Development slice stays 100; helper remains Qwen only
  because Arctic's model card excludes general non-SQL text.
- G1.1 starts by extracting the bounded local provider contract and adding a
  sample-safe atomic disk cache. No hosted configuration and no automatic retries.

## Task 1 — Gold validation engine (G0.5)

**Files:** create `scripts/validate_gold.py`, `tests/test_gold_validation.py`.

1. Write failing tests for pinned-input refusal, ID/database alignment, safe SQLite
   URI/query-only mode, corrected SQLite→Postgres transpilation, statement refusal,
   typed canonicalization (including duplicates/order/null/decimal/float/date/bytes),
   row/byte/cell/time limits, sanitized classifications, aggregate counts and atomic
   manifest publication. No raw SQL/results in the report.
2. Run `uv run pytest tests/test_gold_validation.py -q --tb=line` and observe RED.
3. Implement the smallest offline validator. PostgreSQL connection mapping is fixed
   from approved IDs to `warden_sandbox_<db_id>` and private environment keys.
4. Run the new tests GREEN, then no-env regression and Ruff/format/diff.
5. Update notebook and commit `feat(data): add bounded gold validation` after staged
   diff/message/identity inspection.

## Task 2 — Actual validity, descriptions and C1 freeze (G0.5/G0.5b)

**Files:** create ignored detailed evidence; create
`docs/gold-validity-manifest.json`; update `docs/DATA.md`, `docs/DECISIONS.md`,
`docs/PROGRESS.md`, notebook.

1. Confirm all 11 restricted logins, pins, database fingerprints and no loaded model.
2. Run all four label tracks under the fixed limits. Save only per-ID status/reason,
   hashes and aggregate counts locally; no result cells/SQL/question prose.
3. Verify the manifest totals against evidence and source alignment. Apply the C1
   default only when `arcwise_full` survival is >=95%; otherwise present measured
   options because this is the one threshold choice the spec reserves.
4. Select corrected descriptions with the existing exact unique mapping; preserve
   originals as an alternate. Freeze candidate ambiguity IDs and unchanged negative
   controls without claiming semantic human review.
5. Run validator tests, full configured regression, Ruff/format/diff. Commit
   `docs(data): freeze postgres gold validity and c1 policy`.

## Task 3 — Freeze protocol and split (G0.7 preparation)

**Files:** create `src/sqlwarden/protocol.py`, `tests/test_protocol.py`,
`docs/e0-protocol.json`.

1. Write RED tests for deterministic family grouping, stratification, exactly 100
   development IDs when usable n permits, disjoint held-out IDs, full coverage,
   stable hash, invalid manifest refusal, and seeded bootstrap interval edge cases.
2. Implement deterministic split/metrics using stdlib only; gold is offline-only.
3. Generate and validate the tracked protocol manifest with IDs and hashes but no
   question/SQL/result text. Run tests and regressions.
4. Update records/notebook and commit `feat(eval): freeze g0 evaluation protocol`.

## Task 4 — General restricted dataset execution for E0

**Files:** modify `src/sqlwarden/executor.py`, `src/sqlwarden/guard.py` only where
needed; create/extend executor/guard tests.

1. Write RED unit and real PostgreSQL tests for fixed dataset policies, credential
   mapping, identity/search-path verification, own-schema reads, cross-schema/SET ROLE/
   write denial, complete-result limits and preserved California wrapper behavior.
2. Generalize the existing executor without a broad login or client-supplied role.
   Runtime opens only a server-approved db_id/password pair.
3. Run pure and actual tests plus full configured suite. Commit
   `feat(executor): support fixed restricted datasets`.

## Task 5 — Arctic acquisition and bounded local smoke (G0.6)

**Files:** create a fixed ignored model download/Modelfile helper only if needed;
update `docs/MODELS.md`, create `docs/arctic-smoke-manifest.json`, tests for any
new helper.

1. Recheck free disk/RAM/GPU, model unloaded, fixed revisions/size/hash/license.
2. Download exactly the pinned Q4_K_M file with identity encoding, no proxy/redirect
   inheritance, bounded progress, 12 GiB disk reserve and staging rename. Refuse an
   existing mismatched target. Verify SHA-256 before Ollama creation.
3. Create fixed context-8192 alias and record Ollama digest/template/parameters.
4. Run tiny local schema→SQL capability probes: deterministic output parsing,
   context/output limits, usage availability, seed behavior, one model loaded, and
   unload confirmation. No database credentials/data or gold SQL in prompts.
5. Update records/notebook and commit `docs(models): record bounded arctic smoke`.

## Task 6 — Minimal E0 runner and actual two-model E0 (G0.7)

**Files:** create `src/sqlwarden/evaluation.py`, `scripts/run_e0.py`,
`tests/test_evaluation.py`; write ignored raw runs and tracked
`results/E0_smoke/summary.json` plus compact protocol-safe manifest.

1. Write RED tests for full-schema serialization/no truncation, prompt separation,
   strict SQL extraction per model, no gold in inference, one call/item/no retry,
   guard/execution outcome categories, resumable atomic records, usage/latency/VRAM
   accounting, interrupted=pending, EX denominator and seeded confidence interval.
2. Implement the minimal single-shot runner. Cache is not yet used; fresh calls are
   labelled live. Raw predictions remain ignored and exclude credentials/gold results.
3. Run deterministic tests and a two-item safe local canary per model. Unload between.
4. Run the frozen 100 IDs for Qwen then Arctic, one model at a time, resuming only
   completed atomic items. Execute candidate SQL only after guard under the matching
   restricted login. Score offline against frozen gold results.
5. Build `summary.json` from raw records, verify exact denominator and hashes, run full
   configured suite/Ruff/format/diff. Update records/notebook and commit
   `feat(eval): record local two-model e0`.

## Task 7 — C2, finish G0, begin G1.1 cache

**Files:** create `src/sqlwarden/provider.py`, `src/sqlwarden/cache.py`,
`tests/test_provider.py`, `tests/test_cache.py`; adapt `src/sqlwarden/llm.py`
without breaking the safe CLI; update docs/notebook.

1. Record C2 from measured smoke/E0 evidence using the fixed rule above. Mark G0.5,
   G0.5b/C1, G0.6, G0.7 and G0.8/C2 complete only when their artifacts pass. Offer
   the interview drill in the final report; user may skip later.
2. Write RED tests for typed provider request/usage/outcome, zero hidden retries,
   local-only URL/model pinning, cache key coverage (provider/model/revision/digest/
   template/schema/data/messages/params/sample/seed), atomic no-overwrite writes,
   corruption/symlink/oversize refusal, exact replay and no secret/gold storage.
3. Implement the smallest provider/cache slice with stdlib hashing/JSON/filesystem.
   Existing `LocalQwen` delegates without changing its public safe-CLI contract.
4. Run provider/cache/LLM/CLI tests, full configured suite, lint/format/diff. Update
   PROGRESS/DECISIONS/notebook and commit `feat(agent): add bounded provider cache`.
5. Dispatch one fresh read-only review of this complete plan range. One test-first
   fix pass for Critical/Important only; record every set-aside/ruling and Minor.
   Keep branch local; no merge, remote or push.

## Completion evidence

- G0 checklist truthfully complete or stopped only at the explicit <95% C1 choice.
- `docs/gold-validity-manifest.json`, `docs/e0-protocol.json`, both model manifests,
  and `results/E0_smoke/summary.json` reconcile to ignored evidence and fixed pins.
- Real PostgreSQL tests support every dataset-boundary claim.
- No model is left loaded; setup credentials never enter prompts/runtime/cache.
- G1 has started with G1.1 provider/cache behavior, not merely a planning document.

# G6 Full Training Implementation Plan

> Use superpowers:executing-plans sequentially. Kunal approves plans and routine execution without further review stops; ask only for new consequential choices or authority.

**Goal:** Train Qwen Coder 1.5B on real PostgreSQL-converted BIRD examples and
produce an evidence-backed E9 comparison and resume entry.

**Architecture:** Reuse the isolated CUDA stack and tested pilot engine. Keep
training records, adapters and raw runs ignored. Reuse SQLWarden's frozen prompts,
guard, restricted executor and EX comparator; publish compact metadata only.

**Spec:** BUILD_SPEC section 10, D-084/D-087, and the successful G6 pilot.

## Constraints and recipe

- Same pinned Qwen Coder 1.5B Instruct and installed six-package training stack.
- Training labels structurally qualified, guard accepted, execution-unverified:
  this limitation was explicitly chosen by Kunal.
- Exclude European Football and Codebase evaluation families and shared physical
  table schemas; screen exact normalized evaluation question/SQL duplicates.
- Keep related database variants on one side of train/validation. No training
  examples from the 11 evaluation databases. Content-level database identity and
  unknown pretraining contamination remain limitations.
- Frozen sample: 2000 training examples from 57 databases, 128 validation examples
  from 6 separate databases; context 2048, no truncation. Source and token hashes
  in the three training manifests. Seed 42; response-only loss.
- NF4 QLoRA, rank8/alpha16, q/v projections, microbatch1, accumulation4, constant
  learning rate0.0002, dropout0, AdamW, gradient clipping1.0 and checkpointing.
- One pass: 500 optimizer steps. Validate and save adapters at steps100/200/300/
  400/500; choose lowest validation loss (tie: earlier step), never evaluation EX.
- A 2-step 2048-token probe precedes the full run; 10-minute probe cap. Full run
  cap2 hours, still at most12 GiB total training disk and20 GiB free reserve.
  No money, cloud, push, runtime replacement or weight publication.

## Review focus

Corrupted token files/hash mismatches, all-masked labels, crossed database
families, interrupted training publishing success, and checkpoint selection
using evaluation outcomes must be caught by checks.

## Task 1 — data freeze (G6.3)

- [x] Add tests first for name-family overlap, shared table schema, mixed-case
  identifier restoration, unsafe/non-query labels and deterministic sampling.
- [x] Prepare and hash structural PostgreSQL labels, separate databases, token
  limits, balanced samples. Preserve initial pre-family-fix records ignored.
- [x] Sample audit: 50 seeded records structurally screened, eight complex
  source/converted pairs inspected for quoting, casts, CASE/IIF and division.
  SQLGlot adds NULLIF denominators; numeric/date/type equivalence still unverified.
- [x] Run relevant/full checks, update notes and commit the frozen artifacts.

## Task 2 — full QLoRA training (G6.4)

- [x] Extend the tested pilot engine to consume fingerprinted token records and
  the frozen recipe; test step validation, corrupted/masked tokens and checkpoint
  choice independently of GPU packages.
- [x] Commit checked code and run the 2-step long-context probe from clean Git.
- [ ] Run 500 steps from base weights with logged finite losses/validation,
  checkpoint hashes, timing and peak memory; interrupt safely at resource caps.
- [ ] Reload the chosen adapter, check weights/generation, record compact summary,
  run checks, update progress/decisions/notebook and commit.

## Task 3 — serving, matched E9 and resume (G6.5/G6.6)

- [ ] Verify adapter merge/GGUF conversion resource requirements and exact tools
  before adding conversion dependencies; choose a local path within budget.
- [ ] Freeze matched prompt/schema/quantization/context/output/loop settings for
  base and tuned models; Arctic comparison must name any contract differences.
  Existing held-out outcomes are already known, so E9 is a repeat comparison,
  not a claim of a new untouched test set. Tune only on training validation/dev.
- [ ] Run development then all324 existing verified held-out questions for base
  and tuned under restricted logins; compute EX, paired intervals, latency/memory
  and failure counts. A larger model comparison uses comparable settings or is
  explicitly a reference result.
- [ ] Update EVAL/README/RESUME/notebook using actual evidence, including a null
  or negative improvement. Keep existing G3 summaries and headlines intact.
- [ ] Review the complete change and run applicable local release checks. Commit
  under Kunal's identity. Leave publication/push/weights to separate approval.

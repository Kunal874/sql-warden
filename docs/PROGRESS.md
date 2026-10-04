# SQLWarden progress

Active spec: [BUILD_SPEC.md](BUILD_SPEC.md). Detailed product plan:
[sqlwarden-plan.md](../sqlwarden-plan.md). Preserve task IDs; the active spec
amends their order and checks.

Current group: G0. G0.7a's first thin slice is complete: guard, bounded executor,
pinned comparator and safe local single-candidate CLI. Tasks saved at 227f869,
f8b8150 and 3e1f72e; sole final read-only review found two Important parsing gaps,
both fixed in one TDD pass. Latest full suite 719/719, zero skips, including 165
actual PostgreSQL checks; provider 67/CLI 39 checks. No Critical/deferred Minor.
The sole approved live question matched 17686 in 11.387s, one preload/generation,
89/18 reported tokens. Runtime-only copy is private/ignored; automatic model
unload observed after tool-blocked explicit stop. CLI_SMOKE preserves exact
pre-fix live checkpoint, D-031 all 18 rulings/costs. No inference repeated.
Progress snapshot: 7 of 12 numbered top-level G0 items complete, excluding the
interview drill. This is checklist coverage, not overall project effort.
G0 data/validity/models/evaluation and G1–G5/G7 remain unfinished. No benchmark score.
Release order: G0 → G1 → G2 → G3 → G4 → G5 → G7; G6 is optional after release.

2026-10-05 continuation: completed remaining-G0.5 read-only preparation and
prepared the two-task corrected-label intake plan for required artifact review.
Fresh unchanged suite: 719 passes, zero skips (165 actual PostgreSQL, 19.64s).
No new runtime/data-import/model step executed; G0 remains 7/12. D-032/DATA hold
new source pins and baseline text drift; intake implementation awaits approval.

## Preflight evidence (2026-10-03)

- Workspace initially contained only the three planning documents; no Git repo or implementation.
- GitHub repository has no refs (read-only `git ls-remote`).
- Confirmed Git name/email: Kunal <kunalchandrakar2005@gmail.com>.
- RTX 4060 Laptop GPU: 8188 MiB VRAM; 16 GB system RAM; roughly 66 GB free on D:.
- Node 24.18.0/npm 11.16.0, uv 0.12.22, Docker Desktop 4.83.0, WSL 2.7.11.0.
- uv/Docker are installed per-user and not on this session's PATH.
- Python 3.14.0 existed; managed Python 3.12.15 now runs successfully.
- Ollama 0.35.1 installed successfully (installer hash verified by winget).
- PostgreSQL 17 service owns 5432. API 8000, Vite 5173, Ollama 11434 had no listeners.
- No active Git hook path, commit template or author/committer environment override was found.
- At preflight no model inference or BIRD import had run; see the current session log below.

## Task checklist

### G0 — foundation and data

- [x] G0.1 / C0: inspect tools, GPU/disk/ports, identity and time; record owner answers.
- [x] G0.2: initialize local repo; instructions/spec/memory/ignore files; verified owner-only foundation commit.
- [x] G0.3: minimal locked Python 3.12 src project; ruff/pytest; meaningful behavior check.
- [x] G0.4: isolated Docker PostgreSQL 16, restricted dataset/app logins; direct denial tests.
- [x] G0.5a (early): inspect/fetch one small pinned dataset; provenance, safe import and data checks.
- [x] G0.6a (early): Qwen endpoint smoke; availability, digest/template/capabilities and measured memory.
- [x] G0.7a (early): tested minimum guard, bounded executor, EX comparator and one-database CLI smoke.
  - [x] Inspect/pin official EX source and prepare the first SQL-guard plan.
  - [x] Review/approve the written guard plan and direct SQLGlot addition.
  - [x] Implement/verify the pure scope-aware guard (193 unit checks after review fixes).
  - [x] Verify guard acceptance on real restricted PostgreSQL (56 real checks).
  - [x] Complete final read-only guard-plan review and resolve its findings.
  - [x] Prepare/self-review the bounded executor implementation plan.
  - [x] Review/approve that new executor plan; preserve native execution.
  - [x] Implement/verify the bounded executor against real PostgreSQL.
  - [x] Complete the single final executor review; no actionable findings.
  - [x] Prepare/self-review the pinned EX comparator implementation plan.
  - [x] Review/approve that new comparator plan; preserve native execution.
  - [x] Implement/verify the pure complete-result comparator (60 unit checks).
  - [x] Verify comparator acceptance with actual restricted PostgreSQL (17 checks).
  - [x] Complete the single final comparator review; no actionable findings.
  - [x] Implement/verify the pinned EX comparator.
  - [x] Prepare/self-review the separate safe local model/CLI plan.
  - [x] Review/approve that new artifact, openai/httpx additions and bounded acceptance operations.
  - [x] Build/test the pinned bounded local provider (67 deterministic checks after final fixes).
  - [x] Build/test the safe one-database model/CLI flow (39 deterministic flow checks).
  - [x] Actual CLI controls, exclusive runtime copy, one bounded live question and confirmed unload.
  - [x] Sole final CLI review and one test-first parsing correction pass; 719 full checks pass.
- [ ] G0.5: remaining datasets/descriptions/corrections; ID alignment and conversion validity manifest; DATA.
- [ ] G0.5b / C1: confirm layout, labels, conversion survival and ambiguity-label policy.
- [ ] G0.6: second model smoke, recorded availability, one GPU model at a time.
- [ ] G0.7: freeze split; E0 on the development slice; measured summaries with exact n.
- [ ] G0.8 / C2: model/slice/helper choices from speed and memory evidence.
- [ ] G0 interview drill (may be skipped by Kunal).

### G1 — agent core

- [ ] G1.1: LLM providers, bounded retries/timeouts, usage and sample-safe atomic cache.
- [ ] G1.2: schema extraction/serializer, keys/descriptions and bounded untrusted samples.
- [ ] G1.3 / C3: BM25, scope-aware recall; choose retrieval size, n/k and helper strategy.
- [ ] G1.4: versioned generation/repair/clarify/explain prompts and per-model output formats.
- [ ] G1.5: typed state machine/events, quality ablations and explicit terminal states.
- [ ] G1.6: complete-result voting, ties/failed denominator/n=1, agreement and abstention.
- [ ] G1.7: bounded clarification and labelled simulated/oracle assistance.
- [ ] G1.8: fake-LLM limits, errors, malformed output, ties and abstention tests.
- [ ] G1.9: extend the early CLI with loop settings and trace summary.
- [ ] G1 interview drill.

### G2 — guardrails and sandbox

- [ ] G2.1 / C4: reviewed functions, limits, cost thresholds and role-specific tenant design.
- [ ] G2.2: expand guard to at least 40 meaningful cases plus safe-gold acceptance audit.
- [ ] G2.3: expand executor settings/caps/deadlines/cancellation and sanitized error categories.
- [ ] G2.4: guarded EXPLAIN, same identity/settings and calibrated cost checks.
- [ ] G2.5: effective grants/default grants; real direct-connection permission tests.
- [ ] G2.6: forced tenant RLS, separate tenant identities and boundary tests.
- [ ] G2.7: untrusted data and explanation isolation tests with benign controls.
- [ ] G2.8: at least 40 attacks, threat-specific success predicates; disposable-only E5 and false blocks.
- [ ] G2.9: SECURITY with evidence and residual limitations.
- [ ] G2 interview drill.

### G3 — evaluation

- [ ] G3.1: extend E0 runner: fingerprinted config/metadata, durable JSONL and safe resume.
- [ ] G3.2: separately report parse/guard/execution/EX, coverage and answered-only metrics; tests.
- [ ] G3.3: seeded bootstrap/paired comparisons, boundary-rate intervals and exact n.
- [ ] G3.4 / C5: freeze protocol, experiment matrix and time budget before tuning.
- [ ] G3.5: agreed E1–E4 and E6–E8, unchanged-input rescoring versus separate reruns.
- [ ] G3.6: label 50 observed failures if available; otherwise all; taxonomy/examples.
- [ ] G3.7: EVAL, compact dashboard export and result-driven README/resume generation.
- [ ] G3 interview drill.

### G4 — API and web

- [ ] G4.1: API, capabilities, atomic lifecycle, SSE replay, admission/budgets/rate limits and CORS.
- [ ] G4.2: API lifecycle/races/restart/disconnect/cancellation tests.
- [ ] G4.3 / C6: confirm existing three-page scope and polish level.
- [ ] G4.4: Ask, Attack Lab, Benchmark with real artifacts and complete failure/loading states.
- [ ] G4.5: clean local full-stack run and scripted request/clarification/result flow.
- [ ] G4 interview drill.

### G5 — deployment preparation only

- [ ] G5.1 / C7: verify current free tiers and suitable grants/RLS/resources; hosting recommendation.
- [ ] G5.2: non-root multistage image, health/readiness, pinned locks and local runbook.
- [ ] G5.3: prepare hosted dataset/role scripts; actual provisioning deferred to approved G7.
- [ ] G5.4: prepare deployment instructions; publication deferred to approved G7.
- [ ] G5.5: prepare bounded public checks; execute only after approved G7 deployment.
- [ ] G5.6: minimal-permission CI: lint, Python tests, web typecheck/build, disposable Postgres job.
- [ ] G5.7: complete README with actual results, citations, licenses and limitations.
- [ ] G5 interview drill.

### G7 — release

- [ ] G7.1: clean local clone/install/runbook verification.
- [ ] G7.2: full-history author/committer/body and verified secret scan; license checks.
- [ ] G7.3 / C9: concrete release preview; approve exact repo/visibility, push and hosting actions.
- [ ] G7.4: approved remote/push/provision/deploy; actual CI and bounded public smoke/abuse checks.
- [ ] G7.5: result-derived resume bullets and 12 evidence-backed interview questions.
- [ ] G7 final interview drill.

### G6 — optional follow-on (not a release blocker)

- [ ] G6.1 / C8: explicit go/no-go, training deps/environment/model/dialect/time/disk choices.
- [ ] G6.2: tiny GPU training feasibility run.
- [ ] G6.3: frozen data, database-based validation split and project leakage checks.
- [ ] G6.4: logged training, checkpoints and memory.
- [ ] G6.5: merge/conversion/GGUF feasibility, local serving and comparable E9.
- [ ] G6.6: evidence-driven EVAL/README update; applicable G7 checks before publishing updates.
- [ ] G6 interview drill.

## Session log

### 2026-10-05 — remaining G0.5 read-only preparation / new artifact checkpoint

Resumed clean feat/foundation at e46c4ba; reconciled AGENTS, active spec,
PROGRESS/DECISIONS and completed CLI commits. No new approved implementation plan
exists after the completed safe-CLI increment. Continued its actual Handoff:
prepare next data-work artifact, retaining native sequential execution, not a
second CLI/model/import/credential pass.

Checked the existing archive hash and all 11 SQLite members by ZIP inventory;
canonical JSON pins/counts confirmed. D: free 46,331,715,584 bytes at inspection.
Read official corrected release into memory only, revision
fe766045c55b6875a43b30e9ac7683df5582f8cf. Both sets 498 unique IDs, missing 119/120,
no unexpected IDs/db mismatches, variable original_* fields and string IDs.
SQL-only has 81/86 changed question/evidence fields against our canonical SQLite
copy, full 147/152; either 141/229. Corrected pair differs on 148 IDs (88 questions,
98 evidence). No semantic/ambiguity/result-validity inference. Upstream schema
tree has 75 description CSVs/76,445 bytes by metadata, not parsed/applied.

Prepared and self-reviewed
[corrected-label intake plan](superpowers/plans/2026-10-05-corrected-label-intake.md):
two test-first tasks, fixed four-file 645,140-byte acquisition, hash/size/exclusive
publish boundary, offline ID/text report; no dependencies or runtime/DB/model work.
Artifact review remains required before implementation or persisting the corpus.
This preparation is finished; G0.5/G0.5b are not. DATA/D-032/notebook distinguish
observed text drift from proven ambiguity and identity from conversion validity.

Fresh uv sync --locked: 27 packages checked. Full configured
uv run --env-file .env.setup --env-file .env.california pytest --tb=line:
719 passed, zero skips, 19.64s, including 165 actual PostgreSQL checks. No inference.
A scratch aggregate-printer attempt failed on tuple JSON keys; minimal reproduction
and output-shape-only correction succeeded. Repository source/tests untouched.
Final checks: all five embedded Python plan blocks parse; this is syntax only,
not execution of the proposed scripts/tests. Ruff check passed; all 27 existing
Python files already formatted; git diff --check passed. Placeholder scan found
none. Self-review moved the local-pin test into the initial RED gate and made
malformed optional difficulty fail closed in the planned example. No new
implementation tests were run or represented as finished code. Local checkpoint
message: docs(plan): prepare pinned correction intake checkpoint; exact staged
diff and author/committer/body inspected around the commit.


### 2026-10-04 — safe local CLI final review / one TDD correction pass and handoff

All three tasks completed, Task 3 saved at 3e1f72e with Kunal identities/body and
7 actual controls repeated (2.93s). Sole fresh read-only review d991bfc..3e1f72e
used template/spec/approved plan/all five focus checks/ledger. Independently
76 client/CLI passes (2.59s), clean Git/whitespace/identities/source-lock hashes;
no repeated actual database/live test. Critical none, Important two, Minor none.

Both Important accepted: valid overflowing usage could be discarded because
the other counter was missing/malformed; permissive SDK accepted missing/wrong
assistant role and malformed falsy optional tool/refusal fields. Both could
reach the executor in mocked controls, not a demonstrated permission bypass.
One correction pass: 30 new mocked cases, 27 RED/3 existing controls GREEN
(2.01s); independent counter validation/caps plus explicit envelope gate made
106 client/CLI checks pass (3.12s), including 67 provider checks. Unknown remains
null independently; legitimate empty optional fields/partial usage still work.
No direct addition, framework/private SDK switch, second reviewer or live repeat.

Final locked sync, no-env 554 passed/165 skipped (7.28s), setup-only 597/122 skipped
(10.27s), both private test environments 719/719 zero skips (29.95s), lint/27-file
format/whitespace pass. Original three inputs/existing boundaries unchanged,
healthy loopback PG/named volume preserved, runtime ignored/untracked, /api/ps empty,
no remote. CLI_SMOKE records original f8b8150 live hashes plus corrected client
hash; no stronger live/accuracy claim. D-031/notebook persist all 18 rulings/costs
and all 10 review exclusions. Finishing keeps feat/foundation/current checkout and
own ignored scratch under existing no-release/no-destructive-work instructions.

G0.7a complete; numbered G0 now 7/12, not project effort percentage. Resume original
remaining G0 data/validity/model/split/E0/C1-C2 order; full agent, UI/release later.

### 2026-10-04 — safe local CLI Task 3 / actual controls and sole live question

Task 2 saved at f8b8150 (Kunal identity/body verified), task-done repeats all
76 checks successfully. Actual fixed-provider CLI controls 7/7 (3.89s), full
configured suite 689/689 (18.51s) BEFORE live inference. Read-only preflight:
Ollama 0.35.1, existing exact pin, /api/ps empty; healthy PG loopback 55432 and
sqlwarden_pg16_data retained. Setup helper exclusively creates new ignored
.env.runtime; runtime-only validation passes, no displayed values/grant/rotation.

Exactly one frozen self-authored question at 22:29:44.4410470+05:30: How many rows
are in the schools table? Model receives SYSTEM + question only, not offline
17686/gold/rows/password/labels. Actual exit 0 answered/ok; validate -> generate ->
guard -> cost_execute -> answered, one complete scalar matches offline count.
One admitted preload/one generation, usage 89 prompt/18 completion tokens,
HTTP close confirmed. 11.387s is whole-process wall time, not isolated inference.
No retry/repair/tuning/model fallback; compact fingerprints in CLI_SMOKE, no raw run.

Bounded project-only Start-Process stop was rejected by tool policy before it ran.
No alternative launcher attempted. Read-only /api/ps shows project alias alone,
context 2048, 4628519320 GPU bytes and expiry 22:34:55.5704569+05:30. Actual
automatic unload was then observed as recorded below; no explicit-stop latency.

Post-live checks: locked sync; no-env 524 passed/165 skipped (5.11s); setup-only
567 passed/122 skipped (8.40s); both private test environments 689 passed/zero
skips (27.37s); lint/27-file format/whitespace pass. Original three planning
files and guard/executor/comparator/config unchanged; no remote. Sole final
read-only review follows Task 3 commit; G0.7a stays open. Read-only /api/ps
at 22:35:16.9458759+05:30 returned models=[]: actual automatic unload confirmed.
No explicit stop/process timing claimed; the blocked command was never retried.

### 2026-10-04 — safe local CLI Task 2 / validated one-shot flow

Provider Task 1 is saved at 227f869 (verified Kunal author/committer/body).
Wrote planned input/environment/guard/result/preview/cancellation/error/setup
tests and 3 inherited private-SDK-key checks before source; absent setup module
RED (0.21s), client/CLI 76 GREEN (1.96s), including 39 CLI checks. CLI validates
before construction/I/O; one generation -> immutable guard -> fixed restricted
executor (which independently guards again), no online comparator/reference.
Setup helper exclusively copies the one existing restricted key; not run yet.
Runtime rejects other WARDEN_/admin/test/private SDK settings. Failed/blocked
results expose neither SQL nor partial rows; complete results get an escaped
20-row preview, null unavailable counters/usage, separate HTTP-cleanup status.
No raw-SQL/security-off/provider/model flags, retries, repair or confidence score.

Locked sync and both installed CLI help commands pass without model/database
I/O. No-env suite 524 passed/158 skipped (3.91s), lint/26-file format/whitespace
pass. Full configured suite 682/682 (15.39s), no skips. No dependency change
beyond Task 1; added only installed CLI entrypoint.
README and notebook explain scope and exact safe commands. .env.runtime still
does not exist; no actual credential copy or live question happened in Task 2.
Task 2 shares Task 1's private-key refusal as recorded in D-028, no new ruling.

### 2026-10-04 — safe local CLI Task 1 / pinned provider

Added only the approved direct openai>=2,<3 and httpx>=0.28,<1 pair;
uv.lock resolves openai 2.54.0 / httpx 0.28.1 and 27 total packages. Inspected
installed public APIs, Python requirements and licenses. uv's cross-drive
hardlink warning used its ordinary copy fallback; no global setting changed.
Pinned loopback-only transport, 64KiB identity-response cap, zero retries/proxy/
redirect, separate 90s readiness/60s generation and 5s HTTP-close bounds. One
optional preload and one JSON SQL attempt; no database/reference input.
Reported missing usage remains null and HTTP close is not GPU unload evidence.

TDD: absent-module RED, 34 planned checks GREEN; installed SDK inherited-header/
admin/webhook settings produced 3 additional RED cases, then refusal before
client/network made all 37 pass (1.94s). No real network/model call occurred.
No-env suite 485 passed/158 skipped (5.72s). Initial full configured suite:
642 passed/1 existing external-cancellation timeout (26.36s). Debug inspection
found the test's original 2s active-observation and 1s disappearance bounds;
isolated control passed (1.20s), executor group 18/18 (2.79s), final full rerun
643/643 (17.76s). Cause was not proven; no production code or test bound changed.
Locked sync, lint, 23-file format and whitespace pass. D-028 records the rulings.

### 2026-10-04 — safe local CLI preparation and review gate

Resumed the exact comparator Handoff at clean feat/foundation, 9b8205f; read
BUILD_SPEC/PROGRESS/DECISIONS and reconciled the completed guard/runner/checker
with Git. No reimplementation, new worktree, reviewer or parallel implementation.
Architecture/native execution stay approved; a new artifact is not automatically
approved by the earlier comparator approval or current "proceed".

Prepared/self-reviewed [safe local CLI plan](superpowers/plans/2026-10-04-safe-local-cli.md):
three sequential tasks for the fixed local SDK provider, validated one-shot CLI,
then actual PostgreSQL controls and one frozen live question. Reuse guard/executor;
no raw-SQL flag, cache, retrieval, voting, repair, gold/reference input or hosted
fallback. Proposed direct additions are openai>=2,<3 and httpx>=0.28,<1; both are
absent locally. Installed public API/license/lock checks occur only after approval.
Official SDK, Ollama and HTTPX source links are saved in the plan.

The fixed four-column native schema capsule is not the full schema or E0 baseline.
Input bytes/output tokens, startup/generation/enclosing/cleanup deadlines, one
admitted generation attempt and optional one preload are explicit. Mock transport
tests own actual HTTP-request counts. Unknown usage/attempts are null, not zero.
HTTP close is separate from GPU unload; observe the project alias unloaded after
the one live acceptance probe. No inference requests, model load or generated SQL this turn.

Proposed setup-only helper exclusively creates ignored .env.runtime with only the
existing restricted credential under WARDEN_RUNTIME_CALIFORNIA_PASSWORD. It never
changes a password/grant or launches inference with .env.setup/.env.california.
No credential was displayed/copied and no runtime file was created during preparation.
The existing private test configuration was consumed only by the test launcher.

Inline self-review mapped all five Review Focus conditions to concrete tests,
checked interfaces, fixed planned callbacks' unbound loop variables and clarified
attempt/cleanup semantics. All eight Python fences parse; six assembled proposed
files pass static lint/format using the existing tools, without executing/importing
their snippets. These checks do not prove SDK or future CLI behavior. A checker-only
mixed-line-ending mismatch from PowerShell stdin was corrected without source edits.

Current unchanged code: locked sync passes; no-env 448 passed/158 skipped (3.32s),
setup-only 491 passed/115 skipped (3.91s), full both-env 606 passed/zero skips
(13.50s), including 158 actual PostgreSQL checks. Lint, 21-file format and whitespace
pass. PostgreSQL remains healthy on loopback 55432 with sqlwarden_pg16_data;
Ollama has no loaded model. No source/test/dependency/lock, historical input, data,
grant/credential, model, remote/push/publication, history edit or deletion.

D-027 records choices, tradeoffs, residual limits and the pending approval gate.
Learning notebook updated for the completed preparation only. G0 remains 6/12
numbered top-level items complete; G0.7a and the model/CLI remain open. Pause for
Kunal's review of the new written artifact and proposed additions/operations.

### 2026-10-04 — comparator final review and local-only handoff

Task 2 committed at 7d26e77 with verified Kunal author/committer/body; task-done
reran all 17 actual checks successfully (1.91s). One fresh read-only reviewer
examined both approved commits, 1ffb81d..7d26e77, the active spec, complete plan,
all five Review Focus conditions and recorded execution ruling. No Critical,
Important or Minor findings. No correction pass or second review. Deferred minors: none.

The reviewer independently passed 60 pure checks (0.20s), whitespace and both
commit identity/body checks, leaving HEAD and checkout unchanged. PostgreSQL,
full-suite, source fingerprints and environment checks were not independently
repeated in that review. Implementer final full suite: 606 passed, zero skips
(17.51s), including 158 actual PostgreSQL tests. Locked sync, lint/21-file format
and whitespace pass. The earlier no-env/setup-only evidence remains below.

D-026 resolves all six declined-to-judge boundaries and records all final rulings
and concrete costs in order, continuing D-024's setup ruling. Trusted internal
results, extra set memory, future validity/denominators/voting/leakage and
cross-dialect limitations remain explicit; this is not an exhaustive security
audit, official benchmark score or completed model/CLI flow.

Notebook updated after final review. Retain local feat/foundation and only this
plan's ignored scratch without merge, remote, push, publication or deletion.
No model load, generated SQL, dependency, data, grant or credential changes.
G0 remains six of twelve top-level items complete; G0.7a still needs the safe
one-database model/CLI flow under a separately reviewed plan. Do not redo these
completed tasks or dispatch another comparator reviewer.

### 2026-10-04 — comparator Task 2 / actual native handoff

Task 1 committed at a7be998 with verified Kunal author/committer/body; task-done
passed all 60 units (0.24s). Read the complete Task 2 brief before writing its
17 actual integration controls. Initial run: 17 passed, zero skips (2.19s).
The existing fixed restricted reader/executor ran only handwritten small controls:
native count, duplicate/order behavior, swapped columns, empty/NULL outputs,
Decimal/int, date/text, NaN and close floats. Both-side overflow/failure tests
prove non-ok outputs cannot match a complete prefix or select a denominator.
Stable engine errors/canaries do not reach application output, and the next query
works in the same pool. The guard refuses a DELETE control before database work.
No comparator, guard/executor/config, credential, grant or data fix was needed.

Fresh full suite with both private test files: 606 passed / zero skips (15.36s),
including 158 actual PostgreSQL checks. No-env 448 passed / 158 skipped (2.12s);
setup-only 491 passed / 115 skipped (3.70s). Locked sync, lint/21-file format,
whitespace and historical-input/dependency/runtime comparisons pass. Database
healthy on 127.0.0.1:55432 with sqlwarden_pg16_data preserved; model list empty,
no Git remote. D-025 records unchanged contracts and bounded evidence; no new
runtime ruling or deviation. Notebook updated after actual native acceptance.

Next: Task 2 commit/task-done, then one final fresh read-only reviewer of the
complete comparator increment 1ffb81d..HEAD. No per-task/second review, benchmark
score, gold execution, model load, generated SQL, dependency, publication or deletion.
G0 remains six of twelve top-level items complete; final comparator review and
the safe model/CLI prerequisite remain inside G0.7a.

### 2026-10-04 — comparator Task 1 / pure complete-result EX

Kunal's "yes do it" approves the new two-task plan prepared at 1ffb81d. Read
the native execution/TDD/testing/verification/workspace skills, plan/Task 1 brief,
active contracts and current result interface. Remain in D:/PROJECTS/SQLWARDEN
on feat/foundation under D-003. Locked sync and clean baseline 388 passed / 141
skipped (3.33s); scratch/ledger scoped to this comparator plan, no implementer
or per-task reviewer dispatched. Shared Task 1/2 interfaces match without conflict.

Added the 60 planned unit controls first. Observed expected RED: missing
sqlwarden.comparator collection error (0.39s). Added the small pure module; GREEN
60 passed (0.19s). It uses complete typed row sets and preserves the inspected
order/duplicate/column-position/native Python rule. Columns/byte metadata are
ignored. Non-ok predictions never match a prefix; malformed/hashing errors use
fixed reasons; invalid gold is unscorable, not an automatic exclusion. No SQL,
model I/O, environment/file loader, raw exception or reference-data output.

No-env whole suite 448 passed / 141 skipped (2.24s); lint/20-file format pass.
Database skips are not native comparator acceptance. Task 2's 17 real controls
and the single final review remain. Existing guard/executor/config/dependencies,
data, credentials and grants unchanged. D-024 records approval, interfaces and
the current-checkout ruling/cost. Notebook updated after this verified pure slice.
No generated SQL, gold execution, model load, benchmark score, remote or publication.

### 2026-10-04 — G0.7a pinned EX comparator preparation

Reconciled the clean feat/foundation checkout and completed executor handoff at
92ad554; no remote exists. Read the active contracts and resumed the next
subsystem rather than repeating guard, executor or import implementation/review.
The approved BUILD_SPEC supplies the architectural design. Kunal's current
continue request permits this preparation; writing-plans requires review of the
new written artifact before coding. Preserve the existing native method.

Re-read the exact primary Mini-Dev EX source/helper at revision
abd11b6db92a1c9f809b32f7564c7c71b34d67f0. In-memory HTTP byte/hash checks match
EX_COMPARATOR.md: 4779/4314 bytes and both recorded SHA-256 values. No upstream
source was stored or executed, no driver installed and no example credential used.
The row-set rule ignores order/duplicate counts/names, retains column positions,
and adds no rounding, tolerance or type tags. Synthetic native Python probes
confirm precise Decimal/float and date/text differences, numeric equality and
shared/distinct NaN behavior. Initial ad-hoc quoting/signature mistakes were
corrected in the read-only probes; no project failure or production fix occurred.

Saved/self-reviewed docs/superpowers/plans/2026-10-04-ex-comparator.md:
Task 1 pure complete-result EX and fixed outcomes; Task 2 actual restricted native
handoff. All five Review Focus conditions map to concrete controls. Invalid gold
returns an unscorable marker for the later validity manifest, never an automatic
exclusion; incomplete predictions cannot match, and voting remains separate.
Three Python fences parse and pass snippet lint/format without execution. The
missing proposed module initially received a third-party import classification;
snippet-only known-first-party configuration resolves that check, with production
config unchanged. AST counts 60 planned units and 17 planned real controls, not
passes. All 24 successful-pair SQL inputs pass the pure guard; none was run on
PostgreSQL. No new Python source/test file was created. D-023 records scope and
remaining approval. The notebook explains this preparation and the new terms.

Fresh existing-suite evidence: no-env 388 passed / 141 skipped (2.39s); setup-only
431 passed / 98 skipped (4.63s); both private files 529 passed / zero skips (13.14s),
including 141 actual PostgreSQL checks. An earlier yielded full run's final result
was not captured; only this completed fresh run is acceptance evidence.
Locked sync, lint, 18-file format and whitespace checks pass. Historical inputs,
dependency/lock files and existing guard/executor/config have empty working diffs.
Docker is healthy on 127.0.0.1:55432 with sqlwarden_pg16_data preserved; Ollama's
loaded-model list is empty. Both private test environment files remain ignored.
No model loaded, generated SQL, benchmark run, data/credential/grant change,
dependency addition, remote, push, publication, history edit or deletion.
G0 remains six of twelve top-level numbered items complete; comparator preparation
does not complete G0.7a or represent an overall-project effort percentage.

### 2026-10-04 — bounded executor final review and handoff

Task 3 committed at 0e9df33 with verified Kunal identities/body; task-done
reran all 18 real runner checks (2.17s). The provided package covers all three
approved executor commits df07434..0e9df33. One fresh read-only reviewer inspected
the package, active spec/plan/decisions, guard interfaces and installed asyncpg
behavior. It independently passed 144 executor/limits tests (0.89s) without
private files, PostgreSQL, inference or checkout changes. No Critical, Important
or Minor issue was reported. Its seven declined-to-judge items were each evaluated
against actual scope and reasonable caller expectations; none becomes a hidden
finding or broader safety claim. D-022 persists every ruling and cost, continuing
D-020/D-021. No correction/fix pass was needed and no second review was dispatched.

Fresh final full suite: 529 passed, zero skips (18.43s), including 141 actual
PostgreSQL checks. Earlier final no-env 388/141 skipped and setup-only 431/98
skipped apply to the same runtime/test code. Locked sync, lint, 18-file format,
whitespace and historical-input/lock/dependency comparisons pass. PostgreSQL is
healthy on 127.0.0.1:55432 with sqlwarden_pg16_data; no model is loaded; no remote.
The exposed test password remains revoked after the approved rotation.

Updated the notebook after final review. Retain local feat/foundation and this
plan's ignored scratch under D-003/G7 and the destructive-work approval rule.
All new commits have Kunal as sole author and committer, without extra body
credits. No merge, remote, push, pull request, publication or new dependency.
G0 still has six of twelve top-level numbered items complete plus guard/runner
inside G0.7a. Comparator and safe CLI remain before model-generated SQL; no
overall effort percentage or completed foundation/agent claim is made.

### 2026-10-04 — bounded executor Task 3 / actual PostgreSQL recovery

Task 2 committed at f52bbe6 with verified Kunal identities/body; task-done
reran 94 checks (1.00s). Read the full Task 3 brief before writing its tests.
The initial 18 actual executor checks passed (2.49s). They verify native count,
duplicate column positions, empty/NULL answers, order, exact bytes, UTF-8 cells,
row/cost/estimate overflow, sanitized errors, settings reset and recovery.
Cancellation observes the active restricted backend, cancels the task and
waits for that backend to disappear before the next query succeeds in the pool.
Statement timeout also produces no result prefix and a subsequent query works.

The first full run had 528 passes and one test-setup failure: its cold connection
authentication exceeded the test's 50ms pool configuration before the contention
test reached its target. Systematic debugging traced the nested connect/acquire
bounds in locked asyncpg. Five isolated repeats passed, confirming intermittency.
Keep finite normal connection creation and use a trusted QueryExecutor over the
same pool to test 50ms slot contention; five more repeats and all real checks pass.
No runtime limit or production implementation was relaxed or corrected.
Combined the observer/executor contexts for SIM117; their close order is unchanged.

That failed test's third-party traceback printed the restricted test credential
in the local chat. Kunal explicitly approved rotating only that password.
The ignored one-off local probe updated .env.california atomically; fresh login
with the new password succeeded, the old one was refused, and all eight role flags
were unchanged. No value is recorded here or committed. Setup/app/other credentials,
data, grants and the named volume were not changed. Use --tb=line for future private
test runs to prevent library argument dumps; never enable --showlocals.

After rotation/fixes: 18 real executor checks passed (2.12s); no-env 388 passed /
141 skipped (2.47s); setup-only 431 passed / 98 skipped (5.62s); full both-env
529 passed, zero skips (16.07s), including 141 actual PostgreSQL checks.
Locked sync, lint, 18-file format and whitespace pass. Existing source-fingerprint
checks ran in the full suite. Historical inputs/lock/dependency files unchanged,
no remote, healthy sqlwarden-postgres-1 with sqlwarden_pg16_data preserved,
and Ollama has no loaded model. D-021 records all deviations and residual limits.

Updated the learning notebook after this subtask. This completes executor tests,
not G0.7a, the comparator/CLI or AI question-answering. One required read-only
final review and any proven Important/Critical fixes remain before handoff.

### 2026-10-04 — bounded executor Task 2 / guarded restricted workflow

Task 1 committed at 3f005c8 with verified Kunal author/committer and empty extra
body; task-done reran 88 scoped tests successfully. Read Task 2's full brief and
continued natively. New driver-contract tests observed missing QueryExecutor
RED before the workflow implementation; initial 54 executor checks passed.
Additional failure, lifecycle and cleanup controls were written before evaluating
their paths; all 94 executor tests now pass (1.06s).

Implemented internal fixed-policy guarding, one bounded pool connection and one
read-only transaction for settings, identity, EXPLAIN and unchanged SQL. Fetch(1)
preserves complete-result semantics and detects cap-plus-one. Acquisition through
release shares the total deadline. Stable errors contain no driver text; external
cancellation propagates. Error/cancellation discards the connection synchronously.
The fixed-reader opener accepts a trusted reader password but loads no environment
file or setup credential. Its normal close has a separate finite bound.

Full suite: 511 passed, zero skips (14.67s), including the 123 existing actual
PostgreSQL checks; these are not real executor tests yet. Lint, 17-file format
and whitespace checks pass. The plan's B008/SIM105 style was corrected without
changing behavior; D-020 records the execution ruling and its cost. No raw
error-canary appeared in captured application output or rendered lifecycle errors.
The decoded row/cell/plan and transient JSON-allocation limits remain explicit;
application redaction does not establish server-log redaction.

Updated the learning notebook after this subtask. No dependency, model inference,
data/grant/password change, benchmark run or generated SQL execution occurred.
Task 3 follows under the same approval; PostgreSQL cancellation/replacement and
settings reset remain required before calling the executor verified.

### 2026-10-04 — bounded executor Task 1 / complete-result budgets

Resumed clean feat/foundation at df07434; Kunal continued after the written plan
review request, approving native execution of its three tasks. Baseline full
suite 407 passed (16.88s). Read the Task 1 brief; ignored plan-specific ledger
records matching producer/consumer interfaces with no conflicts.

Tests first: executor import observed missing-module RED; a separate limits
run had 10 new missing-field failures and 40 passing existing controls. Added
only the two approved estimate bounds to existing validated QueryLimits and the
pure QueryResult/_ResultBuffer/_check_plan implementation. Initial scoped 71
passed; all remaining plan controls then passed as characterizations.

Final scoped 88 passed (38 result/plan, 50 config). Full suite after mechanical
formatting: 455 passed, zero skips, including 123 real PostgreSQL checks (13.12s).
Lint, 17-file format and whitespace checks pass. No runner connection/cursor,
generated SQL, model, comparator or CLI exists in this increment. Budget bytes
include compact UTF-8 column/row JSON framing, not wire/heap memory or EX
canonicalization. Overflow clears every accumulated row; original cell types
and duplicates/order are retained. Estimate defaults are uncalibrated.

Updated the simple-English notebook after this subtask. No dependency, grants,
imported data, credentials, source planning inputs or benchmark changed.
Task 2 follows directly under the existing approval, without another check-in.

### 2026-10-04 — G0.7a bounded-executor preparation

Resumed D-017's exact Handoff at clean feat/foundation, 7fa0a2d. Reused the
approved BUILD_SPEC design and completed guard; prepared
[bounded executor plan](superpowers/plans/2026-10-04-bounded-sql-executor.md)
for review, with three native tasks: complete-result/estimate budgets, guarded
single-pool workflow, and real restricted-reader limits/recovery controls.
No executor code/tests or config defaults have changed. No dependency added.

Inspected the installed asyncpg 0.31.0 public cursor/transaction/pool APIs and
termination behavior, plus official PostgreSQL 16 EXPLAIN/timeout docs. Proposed
one fixed California pool, explicit readonly transaction-local settings, guarded
EXPLAIN without ANALYZE, fetch(1), finite acquire/total/cleanup, cap-plus-one and
prefix-free failure. Cost/row estimates start at proposed 100000 each, subject
to this plan review; they are not calibrated or benchmark-tuned. Byte sizing
uses a defined compact UTF-8 data envelope, not EX/voting canonicalization.

Inline self-review fixed short identity metadata and lifecycle error/cancellation
contracts, added concrete controls for all five Review Focus cases, and requires
actual cancelled-backend removal before pool recovery. All 12 proposed Python fences
were syntax-checked only, not run as implementation tests. Existing guard accepts
the two handwritten undefined-object controls; no SQL was executed by that probe.
Recorded transient decoding/encoding and administrator-log residual limits.

Fresh verification of existing code: no-env 284 passed / 123 skipped (1.60s);
setup-only 327 passed / 80 skipped (3.81s); both private test files 407 passed,
zero skips, including 123 actual PostgreSQL checks (13.59s). Locked sync,
ruff check, 15-file format check, relative file links and diff whitespace pass.
PostgreSQL healthy; Ollama has no
loaded model. Original planning files, runtime/test source and locks unchanged;
no data import, inference, download, remote, push or publication.

Updated the learning notebook with this preparation and simple runner/budget
terms. The writing-plans review gate requires review of the newly written plan
before implementation; prior guard-plan approval does not approve a new artifact.
No new execution-method question: native in this checkout remains selected.
This completes preparation only, not the runner or G0.7a.

### 2026-10-04 — G0.7a guard final review and one TDD fix pass

Task 2 committed at f8255de with verified Kunal author/committer and body.
One fresh-context read-only reviewer inspected the whole branch 2c77c72..f8255de,
reran 184 guard tests and probed 2475 small scope combinations. Two findings are
Important by actual effect: pinned parser builders can raise IndexError instead
of a sanitized decision, and unsupported CTE bodies can log raw SQL and be
accepted when unused. No Critical or Minor finding was reported.

Reproduced both actual parser inputs (VAR_MAP(1), LEVENSHTEIN_LESS_EQUAL()) and an
injected IndexError before fixing them: three RED failures. Added IndexError only
to the parser boundary's explicit exception list, without broad exception masking.
Guard 187 passed and full real suite 401 passed in 12.54s afterward.

Four real malformed CTE controls (used/unused literal, nested parentheses, CASE)
then observed RED because SQLGlot scope warnings contained the synthetic canary.
Require an unwrapped reviewed query root or VALUES before CTE scope traversal.
All four now reject without logging input, including the previously accepted
unused body. No global logger setting was changed. Two positive controls preserve
supported VALUES CTEs and nested query parentheses; original SQL is unchanged.
This complements parser warning redaction; that option alone did not cover scope
diagnostics. No unsafe reproduction was sent to PostgreSQL.

Verification: 193 guard tests pass; 56 scoped actual PostgreSQL acceptance checks
pass (3.42s). Full suite with both private test files: 407 passed, no skips,
including 123 actual database checks (12.65s). No-env: 284 passed / 123 skipped
(1.79s); setup-only: 327 passed / 80 skipped (2.85s). Locked sync, ruff check and
15-file format check pass. The single fix pass is complete; no re-review.
All eight reviewer declined-to-judge items have explicit D-017 rulings and costs;
no minor work is deferred. Updated the guard plan and simple-English notebook.

The normal current checkout has only feat/foundation and no remote. Keep it local
under D-003/G7; no merge/push/PR/publication. PostgreSQL stays healthy on loopback
55432 with its named volume; Qwen remains unloaded. No dependency, database grant,
imported row, private credential, historical planning input or benchmark changed.
Retain this plan's ignored review scratch: AGENTS.md asks for approval before
destructive work, so the skill's cleanup instruction does not authorize deletion.
All scratch rulings are preserved in DECISIONS. This completes the guard increment,
not G0.7a; the bounded executor/comparator/CLI are still required before AI SQL.

### 2026-10-04 — G0.7a real guard acceptance / approved plan Task 2

Task 1 committed at 2cca672 with verified Kunal author/committer and no additional
body attribution. Task-done reran its 184 guard checks successfully and recorded
83ac96a..2cca672; read the exact Task 2 brief before continuing natively.

Added 56 real PostgreSQL checks. Every test reuses california_connected and the
actual warden_sandbox_california_schools login in an explicit read-only transaction
with SET LOCAL statement_timeout=5s, lock_timeout=500ms and search_path ordered
pg_catalog, california_schools. Role, read-only state and all settings are asserted.
Only static handwritten approved reads execute: exact count 17686, all 13 admitted
function classes and eight cast types, small native-type operators, a three-row
native key join, CTE shadowing and uppercase/comment-metadata controls. NULLIF's
None and date/Decimal/numeric return types are checked, not treated as failures.

Read catalog metadata under that same restricted login using trusted test-only
inspection SQL, never runtime/guard-approved catalog reads. Reviewed 22 function
signatures, their aggregate helper routines, 12 operators, eight builtin types'
input/output routines and bigint->numeric's cast implementation. D-016 records
signatures and findings. All inspected implementations are pg_catalog C/internal,
immutable or stable where inspected, without SECURITY DEFINER. No untrusted
qualification is guard-approved; those rejected inputs are not executed. Catalog
metadata is intentionally readable; no hidden-catalog claim is made.

Initial run: 54 acceptance tests passed, catalog lookup failed for schema-qualified
SQL alias pg_catalog.int. Systematic inspection traced it to the test inventory,
not the guard: qualified physical names are int4/int8/float4/float8/bool. Corrected
those catalog lookup names and added one actual bigint->numeric cast control.
No policy, grants, data or connection identity changed. Final scoped run: 56 passed
in 3.32 seconds, no skips; separate catalog output confirmed recorded signatures.
Ruff's nested-context/line-length findings were resolved mechanically.

Verification in all modes: no env files 275 passed / 123 skipped in 1.63s;
setup-only 318 passed / 80 skipped in 2.91s; both private test environments 398
passed in 11.55s with no skips (275 unit/setup/data/guard + 123 real PostgreSQL).
Locked sync, ruff check, format (15 files) and whitespace checks pass. All three
historical planning inputs are unchanged; no remote or model is active. Notebook
updated after the completed subtask. No generated SQL, gold execution, benchmark,
runtime executor/pool, comparator, CLI, data reset or publication was performed.
One fresh read-only whole-branch review is next before the final guard handoff.

### 2026-10-04 — G0.7a pure guard / approved plan Task 1

Kunal approved both the written guard plan and direct SQLGlot addition. Reconciled
clean feat/foundation at 83ac96a and reused the required current checkout. Fresh
baseline: 158 passed in 5.70 seconds with both private test environments. Native
execution ledger is ignored under .superpowers/sdd/2026-10-03-minimum-sql-guard;
Task 1's immutable policy/decision interface matches Task 2's existing reader gate.

Added only sqlglot==30.21.0; locked sync succeeds. Installed metadata confirms
Python >=3.9, MIT, no required transitive dependencies and no optional compiled
extras. Independently downloaded the pure wheel into ignored .tools/parser:
763892 bytes, SHA-256 816d1a4815b7562b3976efcc0b561c928a743f976efd0fb8ad6db7a5b96c069e,
matching the pinned registry reference. uv's cross-drive hardlink warning fell
back to copies successfully; no existing dependency version changed.

Wrote tests first and observed missing sqlwarden.guard RED. Implemented the pure
guard, exact node/function/type allowlists, fixed input/AST/identifier budgets,
ASCII-only unquoted folding, every-scope relation checks and full Table accounting.
Accepted text is unchanged; rejected text is None with a stable category. No
database/model package is needed to import or use the guard. Error message context
is zero so parser fallback warnings cannot echo input literals; no global logger
setting was changed. The guard is not an execution capability or engine validator.

First implementation run: 182 passed, two additional test expectations failed.
Systematic inspection confirmed VALUES is already in the approved structural list
and resolves to a safe derived Scope, while Array inherits Func. Corrected those
extra expectations without changing the policy; all original 25 SAFE / 40 UNSAFE
cases passed unchanged. D-015 records the rulings and their costs. Ruff rejected
the plan's constant-string split style; its mechanical list rewrite/formatter
preserved every allowed name and resolved the lint/format findings.

Verified Task 1: 184 guard tests passed in 0.46 seconds; full suite 342 passed in
7.27 seconds, including the existing 67 actual PostgreSQL checks. Locked sync,
ruff check, format (14 files) and diff checks pass. Original planning inputs are
unchanged. Updated the simple-English notebook after this completed subtask.
Real-engine guard acceptance is next, not yet claimed. Strict unknown nodes,
qualified functions and parameterized/custom casts may reject benign queries;
G2 acceptance/attack audits remain later work. No AI SQL, EX score, model load,
runtime executor, comparator, CLI or publication was performed.

### 2026-10-03 — G0.7a preparation and guard-plan handoff

Reconciled clean feat/foundation at 5cf31fa; owner attribution and prior notebook
checkpoint are preserved. Read the active contracts, relevant detailed-plan
sections, limits and existing California test connection. Baseline rerun with
both private test environments: 158 passed in 8.28 seconds. Ollama ps is empty;
no model inference, installation, import or runtime SQL generation was started.

Used brainstorming to classify the next subsystem as architectural. Reused the
already approved BUILD_SPEC design instead of asking to approve its contracts
again. Used writing-plans to prepare the first independently testable prerequisite:
docs/superpowers/plans/2026-10-03-minimum-sql-guard.md. Two native tasks cover a
pure fail-closed, scope-aware guard and real restricted-reader acceptance checks.
The written plan is new and still requires review; the earlier continue is not
approval of an artifact that did not exist. Direct SQLGlot addition is also pending.

Checked primary upstream sources without running downloaded code. Official
Mini-Dev HEAD remains abd11b6, matching DATA; EX_COMPARATOR.md records exact file
hashes and comparison behavior. This is reference inspection, not a benchmark
freeze, score or completed comparator. The upstream runner is not used: its
connection configuration and extra drivers do not match this project. No source
code was vendored and no code license was assumed from the dataset license.

PyPI SQLGlot 30.21.0 supports Python >=3.9; its tag resolves to 5d16fa8 with MIT
license. Registry wheel metadata is recorded, not a local wheel verification.
Inspected pinned scope/expression/identifier sources; they use modular exports,
and identifier normalization can honor comment metadata. The proposed guard
must ignore those input-supplied controls, use PostgreSQL ASCII name folding,
inspect every table scope and leave accepted SQL unchanged. No dependency was
added. Web documentation paths that failed were replaced by pinned source/API
inspection rather than assumed successful reads. The plan self-review corrected
its oversized-input example so it tests the byte limit, not just blank input.

Updated the simple-English notebook with this completed preparation subtask,
separate from unimplemented runtime work. The executor, comparator, CLI and
model-readiness strategy remain subsequent G0.7a work. D-014 records the handoff.
Plan self-review assigns all five review-focus conditions to concrete test steps;
all local document links and six Python snippet syntax checks pass (snippets were
not executed). Ruff check/format and diff checks pass. Runtime, tests, dependencies
and all three original planning inputs remain unchanged.
The staged check caught one extra EOF blank line in the new EX source record
that the earlier tracked-only diff had not covered. Removed only that line;
the complete staged whitespace check now passes.

### 2026-10-03 — learning notebook and G0.6a local model smoke

Reconciled the clean owner checkout at 15616d4; original planning inputs remain
unchanged. Kunal requested one plain-language file updated after each completed
group/subtask, under the exact folder name explaination of project. Created
PROJECT_EXPLAINED.md there, with the completed foundation/import steps, actual
checks, unfinished features and AI/coding glossary. Added stable pointers and the
update rule to AGENTS/BUILD_SPEC; D-012 records this ongoing requirement.

Classified G0.6a as a feasibility spike, not a new runtime subsystem. Read primary
Ollama/Qwen sources and checked local resources. Ollama 0.35.1 was loopback-only,
with no models initially. Before memory was freed: GPU 3301 MiB free, RAM about
3.4 GiB available. After Kunal freed memory: GPU 6461 MiB free, RAM about 2.0 GiB.
He authorized the small local probe and cannot free more memory; do not close his
apps or demand further cleanup. Downloaded only the requested Qwen7B Q4_K_M,
verified all base layer hashes/sizes, and created the previously absent context-
2048/output-64 alias. No global settings, direct dependencies or remote inference.

The first cold request timed out at 60.031 seconds with usage unavailable. Used
systematic debugging: server log showed runner startup 45.30 seconds and no
successful first response; the loaded runner was then tested with the unchanged
limits. Six warm requests passed in 5.969 seconds: exact text, JSON object/schema,
one matching seed pair and a two-token cap with finish_reason=length. Successful
usage: 260 prompt + 54 output tokens; seven actual requests include the timeout,
whose usage is unknown. Ollama prompt/KV caching was active, not an application
response-cache replay. This is not SQL accuracy or benchmark throughput.

Ollama reported one active 2048-token model, 4628519320 bytes entirely on GPU.
Warm device-memory samples peaked at 5565 MiB across all applications, not an
exact model-only peak; available RAM reached 1958367232 bytes in these samples.
Unloaded the project model afterward: zero /api/ps models, device sample 1194 MiB
used / 6763 MiB free. Pull session 45141 and first probe session 39691 completed;
no model job remains running. The ignored .tools/probes/qwen_smoke.py is a
throwaway manual probe, not runtime code. MODELS.md and qwen-smoke-manifest.json
record source/artifact pins, actual checks, failed cold startup and limitations.
The exact upstream conversion revision is unavailable; the actual GGUF is pinned.
The learning notebook includes this completed task. Existing suite rerun: 158
passed including 67 real PostgreSQL checks; ruff check/format and diff checks pass.
No SQL, gold query, database data or credential entered the model; no publication.
Read-only final review found no Critical or Important issue. Clarified one Minor
notebook sentence about loopback addresses. The seven declined-to-judge items
received explicit rulings under D-013; no further model run or database change.

### 2026-10-03 — G0.5a final review follow-up and handoff

Task 3 committed at 13b6e6c with verified Kunal author/committer and no extra body
attribution. One fresh-context read-only review covered the complete foundation
branch (2c77c72..13b6e6c). Two findings remain Important after impact-based grading:
runtime credentials could connect to postgres/template1, whose function catalogs
have separate privileges; California cross-reader checks lacked the separate
dataset setup gate. Eight real connection probes and one no-connection harness
test reproduced all nine failures before either fix.

Added the shared idempotent cluster_hardening.sql to fresh bootstrap and applied
it twice successfully to this existing dedicated PostgreSQL 16 cluster. A container
recreation mounted the new script; sqlwarden_pg16_data and existing credentials/
rows remain intact. PUBLIC CONNECT/TEMP on postgres/template1 are revoked; actual
connections for all four runtime logins are denied. Catalog checks confirm both
privileges are false for every login/database pair, and template0 remains closed.
The existing PostgreSQL 17 service was not changed. Cross-reader checks now verify
the California setup gate before any other login connects; missing actual setup
still fails when both environment files are supplied.

Single review-fix pass: 9 RED -> 9 GREEN; complete suite 158 passed (91 unit/setup/
data + 67 real PostgreSQL), ruff check/format, uv lock --check and diff checks pass.
Without environment files: 91 passed, 67 skipped. Setup-only environment: 134
passed, 24 California checks skipped. With both private environments: no skips.
Native source/content fingerprints, labels, types and keys were rechecked by the
full suite; no source SQL, gold query, model inference or score was executed.
No second review was dispatched. No Critical or Minor findings were reported;
all seven declined-to-judge items and execution rulings are recorded in DECISIONS.
Keep feat/foundation locally under the existing workspace/G7 contracts. No remote,
push, merge, publication or data reset. G0.5a is complete for this one database.

### 2026-10-03 — G0.5a content/provenance / approved plan Task 3

Task 2 committed at 214b442, with Kunal as author and committer and no extra body
attribution. Tests first identified the missing compact manifest. Captured native
ordered COPY fingerprints using only the restricted reader, with fixed output
settings. Recorded all 89 source/native columns and types, PK/FK mapping, actual
NULL distributions, complete-content controls, source hashes/revisions and the
actual dirty Git state when the import ran. No raw rows or secret values are stored.
Live metadata verifies date/real(float4)/bigint, PK uniqueness and both validated
FKs/joins. A source-description check failed for four whitespace-padded frpm names;
trimmed description-name padding only and recorded exact aliases. All descriptions
now match native names uniquely; SQL identifiers and source files are unchanged.
Rechecked all eight pinned source artifacts, 500 unique aligned label IDs and
the 30 California IDs; question/evidence differences across the full release stay
explicit. Gold SQL was not executed or used for inference.
Full verification: 149 passed (90 unit/setup/data + 59 actual PostgreSQL), lint,
format, lock and diff checks passed. G0.5a is complete for this one database.
One fresh-context final whole-branch review remains before the final handoff.

### 2026-10-03 — G0.5a setup-only import / approved plan Task 2

Task 1 committed at 12e8aab with verified Kunal author/committer and clean body.
Credential and source validation tests observed RED, then passed. Exclusively
created private .env.california without changing either existing environment file.
The actual reader test failed for its missing login before import, then passed
after loading only native COPY data into the new schema/login. All three native
counts and complete typed row multisets verify; PK, NOT NULL and both FKs validate.
No dump SQL, owner commands or unrelated dataset was executed/imported.
Direct tests cover forbidden writes with the read-only default disabled, app/other
dataset reads, SET ROLE, TEMP/DDL, large-object/risky functions and future grants.
The three existing runtime logins cannot read California. Repeat import refuses
without changing existing rows. The content-mutation test failed under a temporary
disabled comparison, then passed after restoration; its changed value rolls back.
Current full checks: 146 passed (90 unit/setup/data + 56 actual PostgreSQL), lint,
format, lock and diff checks passed. All local credentials/native data are ignored.
No model, guard, executor or benchmark execution is claimed.

### 2026-10-03 — G0.5a native extraction / approved plan Task 1

Kunal approved the written native-import plan with proceed. Baseline 87 tests
passed on clean feat/foundation at 1e3878b. Kept the required current checkout.
Observed RED for missing metadata/extraction helpers and the native archive entry
point, then 25 new tests passed. Actual extraction streamed the checked archive to
EOF and selected only schools/frpm/satscores COPY bytes; all three row counts,
sizes and hashes match DATA.md. Existing source files were not overwritten.
Checked native identifiers, text/bigint/real/date mapping and source PK/FK metadata.
No archive SQL was executed, no PostgreSQL import/model inference has run.
Full verification: 112 passed including 37 actual PostgreSQL checks; lint,
format and diff checks passed. The lint-only loop-state initialization issue was
resolved without weakening tests.

### 2026-10-03 — G0.5a source preparation and next import plan

The G0.4 follow-up commit b2adedc has Kunal as both author and committer; its body
has no extra attribution. Read-only follow-up review found both findings addressed
and no substantive remaining issue in that change.

Checked primary source revisions and download metadata. The canonical HF repository
contains labels, not database files. Compared the official older package and the
July 2025 corresponding package; downloaded the latter (799944582 bytes) and pinned
its SHA-256. Before download about 63 GB was free on D:. Extracted only the 11 MB
California Schools SQLite source, three description CSVs and schema JSON, never
archive SQL. Raw downloads and selected artifacts are ignored and unchanged.
Extraction tests observed RED for the missing module, then seven passed after
implementation. They verify exact selection/hash manifests, missing/duplicate/
symlink/oversize/checksum failures, no partial output and overwrite refusal.

Read-only source checks: SQLite integrity ok and no FK violations; row counts
17686 schools, 9986 frpm, 2269 satscores. UTF-8 descriptions cover 49/29/11 columns.
Both pinned dialect label files contain 500 unique matched IDs in 11 databases;
question/evidence differences exist for some full-release IDs, but none of the
30 California items. DATA.md records the exact observed differences and hashes.

The native PostgreSQL dump is flat public, with different ordinary-identifier
casing and bigint/real/date types. Inspected the selected DDL and streamed the dump
read-only for source/COPY-block hashes and counts; did not execute any source SQL
or import BIRD into PostgreSQL. Proposed a selective native-data import under the
approved isolated-schema architecture. Wrote and self-reviewed the implementation
plan; the writing-plans skill requires Kunal's review before that new importer code.
Kunal's continue request was received while the plan was being prepared; the
written plan is now open and a review question is pending. Do not treat an earlier
continue as review of an artifact that did not yet exist.

Read-only review of this source-preparation increment found no actionable issues;
the review covered extraction correctness, bounded/atomic output and provenance.

Verified current increment: 87 tests passed (50 unit/setup/extraction + 37 actual
PostgreSQL), ruff check passed, format checked 8 files and git diff --check passed.
The sandbox could not open the securely created selection folder; the approved
read-only check with appropriate access succeeded. No data corruption was found.
No model download, inference, gold execution, benchmark result or BIRD import is claimed.

### 2026-10-03 — G0.4 review follow-up

Read-only review found that revoking lo_import/lo_export left large-object creation
and mutation functions executable. Effective ACL inspection confirmed the gap.
Six rollback-protected direct creation probes reproduced it; three ACL tests also
failed for the runtime logins. Revoked PUBLIC execution on every overload of the
unused large-object API using one shared idempotent setup script. Applied it to the
existing volume after a container restart; no data or credentials were deleted.
The two test-harness checks first failed for the missing rollback helper, then
passed after implementation. Destructive denial probes now always roll back,
including unexpected success; app-state and future-grant tests use it too.

Verified: 80 tests passed (43 unit/setup + 37 actual PostgreSQL integration), ruff
check and format passed, uv lock --check and git diff --check passed. A setup-only
catalog check found zero runtime-owned large objects after all reproduction tests.
This corrects the initial G0.4 write-boundary gap; it is not an exhaustive security
audit or a claim that the later guard, executor, tenant RLS or attack suite exists.

### 2026-10-03 — G0.4 boundary

G0.3 commit 94a2175 verified owner-only. Added approved asyncpg 0.31.0 and updated
the lock; no new unapproved runtime dependency. Local setup tests observed RED,
then 3 passed after exclusive credential creation with setup/runtime separation.
Direct database tests observed RED before the server existed. Created the new
SQLWarden container/network/volume only after confirming no colliding resources.
Pinned the downloaded official image digest and reviewed the bootstrap SQL.
PostgreSQL 16.15 is healthy on 127.0.0.1:55432, capped at 768 MiB and one CPU.
No BIRD data, tenant RLS, AST guard, model query or benchmark result is claimed.

Initial checks: 69 tests passed (43 unit/setup + 26 actual PostgreSQL integration),
ruff check passed, format check passed for 6 files, git diff --check passed;
.env and .env.setup are ignored. Direct tests bypass the guard and verify SELECT
on the assigned synthetic schema, forbidden writes even after disabling the
read-only default, app/other-schema denial, role changes, CREATE/TEMP denial,
file/sleep function denial, unprivileged flags/membership, and future object grants.
Custom settings/search_path do not grant other dataset access. Catalog metadata
is intentionally visible and is not a hidden-catalog claim.
The app can store its synthetic application state but cannot read dataset rows.
The earlier lint failure (nested async contexts) was fixed and the full checks rerun.

### 2026-10-03 — start

Kunal requested execution, confirmed identity, missing-tool installation and 15–20 hours/week.
Read all active execution contracts and detailed plan; original Appendix A is superseded.
Initialized local feat/foundation; configured owner-only identity, no remote.
Checks: workspace/Git inventory, GitHub refs, tool paths/versions, GPU/disk, ports, WSL/services.
Python install downloaded 3.12.15 and returned a minor-version-link error, but subsequent
inspection found the complete target and both direct execution and uv discovery succeeded.
No installation retry was needed; the cause of the transient reported error is unconfirmed.
Ollama installation completed with a verified installer hash. Docker Desktop started
(initial PID 55532); engine readiness is pending. No model has been downloaded.
G0.2 checks: staged whitespace check, ignore behavior, owner identity, empty remote list
and clean status passed. Commit 2c77c72 has Kunal as both author and committer and a clean body.
G0.3: uv locked/installed the minimal project with Python 3.12.15. Limits tests were
observed RED (missing constructor) before implementation, then all 40 passed.
Full checks: pytest 40 passed, ruff check passed, ruff format checked 3 files,
uv lock --check passed, git diff --check passed. Tests validate positive integer
bounds, cell/result budgets and timeout relationships. No database-security claim.
Ruff 0.16 also formats Python snippets in Markdown by default; explicitly scoped
its include list to Python and pyproject.toml to preserve the planning documents.
The sandbox could not write the pytest cache created during setup; a full run with
the needed access passed without warnings. uv's initial cross-drive hardlink warning
fell back to copies; dependency installation succeeded.
Resolved transitive dev dependencies were inspected: colorama, iniconfig, packaging,
pluggy, pygments and typing-extensions, plus the approved pytest/pytest-asyncio/ruff.
This inventory check is not a claim of a vulnerability scan.

Pre-flight contract reconciliation:
- G0/G2: the guard and restricted identities must exist before the first model query.
- G0/G3: EX comparison preserves the pinned official semantics; complete results are required.
- G1/G4: clarification and cancellation use explicit statuses and bounded atomic transitions.
- G3/G4: the Benchmark page uses real compact exports, never invented data.
- G5/G7: preparation precedes publication; no remote addition or push before release approval.

## Handoff

Current next action: Kunal's artifact review of the new
[corrected-label intake plan](superpowers/plans/2026-10-05-corrected-label-intake.md),
prepared 2026-10-05 at the preceding CLI checkpoint e46c4ba. D-032 records the
required approval boundary. No approved implementation task is left in the old
CLI plan; do not replay it. Native sequential execution remains selected.
After this exact artifact is approved, implement its two tasks test-first:
strict offline report, then only the four pinned correction/license resources
(645,140 content bytes) and actual offline acceptance. No new dependencies,
database import/permissions/secret changes, model/SQL runs, benchmark selection,
split freezing or publication. Raw sources stay ignored. Source pins, missing
IDs 119/120, baseline text drift and 75 upstream description-file inventory are
in DATA; inspect descriptions and remaining import/conversion work in a later
reviewed increment. G0.5/G0.5b remain incomplete, overall G0 checklist 7/12.
Use uv run python -m scripts.fetch_labels / scripts.inspect_labels only after
those scripts exist and approval; no env files needed. Do not repin changing
bytes or overwrite existing artifacts automatically. Current fresh regression
evidence is 719/719 with both setup/test envs, 165 actual PG, zero skips, 19.64s.
Private tests always --tb=line, never --showlocals; no extra live inference.

Safe-local-CLI plan is complete: tasks 227f869/f8b8150/3e1f72e and sole review's
verified parsing fixes/evidence. G0.7a complete, latest 719 configured passes
(165 actual PostgreSQL); no-env 554/165 skipped, setup 597/122 skipped. No Critical/
deferred Minor, all 18 rulings in D-031. Do not repeat component reviews, import,
credential setup/rotation or the sole live question automatically.
Next: remaining original G0.5/G0.5b(C1) data/validity work, then G0.6 second
model and G0.7/G0.8(C2) split/E0/model choices. Prepare any new multi-step plan
for artifact approval and obtain its relevant owner decisions; this approval
does not authorize downloads/benchmarks/new dependencies/publication/extra AI probes.
Native sequential execution remains selected. Reuse this client/CLI in G1.
Runtime launcher is `uv run --env-file .env.runtime sqlwarden ask --db california_schools <question>`;
never use setup/test envs. Resume this plan's
ledger at .superpowers/sdd/2026-10-04-safe-local-cli/progress.md, reconcile Git.
Do not repeat earlier reviews/import/rotation. Model was last observed unloaded;
no model was loaded by the 2026-10-05 preparation. Current
test commands and explicit uv path below remain valid. SDK inherited private
keys in D-028 must be rejected by the CLI before any I/O. The previous preparation/
component handoffs below are historical, superseded by this completed CLI work.

Historical component checkpoints (not the current next actions):

The
[comparator plan](superpowers/plans/2026-10-04-ex-comparator.md) is complete:
Task 1 at a7be998, Task 2 at 7d26e77, both task-done gates and the sole final
read-only review of 1ffb81d..7d26e77 pass. No actionable findings or deferred minors.
60 pure checks and 17 actual comparator controls; latest full configured suite
606 passed, zero skips (13.50s in CLI preparation), including 158 actual PostgreSQL checks.
Do not redo the tasks or dispatch another comparator reviewer. Preserve ignored
.superpowers/sdd/2026-10-04-ex-comparator without deletion. D-023–D-026 hold scope,
evidence and every ruling/cost; no method/dependency question remains for this
completed plan. No generated SQL or benchmark score; voting/reference validity
remain separate. This offline function returns no reference data; future online
wiring still needs its own leakage and budget checks.

The bounded-executor Tasks 1–3 and their single final review are complete:
94 executor units, 50 limits controls, 18 actual executor checks; 529 full-suite
passes, zero skips, 141 actual PostgreSQL checks. No findings or deferred minors.
Do not re-execute the plan, redo its review, or dispatch a second reviewer.
Preserve ignored .superpowers/sdd/2026-10-04-bounded-sql-executor without deletion.
The [bounded executor plan](superpowers/plans/2026-10-04-bounded-sql-executor.md)
was approved by Kunal's continue response and is finished. Keep native execution
here; do not ask again about method/dependencies or redo guard/import work.
D-018 approval update and D-019–D-022 hold contracts, all rulings and their costs.
The [minimum SQL-guard plan](superpowers/plans/2026-10-03-minimum-sql-guard.md)
and its final review are complete: 193 guard checks, 56 real acceptance checks,
407 full-suite passes (123 actual PostgreSQL), both Important findings fixed
test-first in one pass; no Critical or Minor findings. Do not redo its tasks or
dispatch a second review. D-015/D-017 hold all rulings and their costs. Ignored
.superpowers/sdd/2026-10-03-minimum-sql-guard is retained without deletion approval.
G0.7a still requires the safe CLI after the completed guard/runner/comparator.
EX_COMPARATOR.md includes pure, native and final-review evidence.
The previous native-import plan is complete; do not
re-execute its tasks. The ignored review scratch was retained because host policy
blocked cleanup; its ten rulings are preserved in DECISIONS.
Do not download the source
archive/labels again or overwrite data/bird_california. Source fingerprints and
native block hashes are in DATA.md. The current extractor refuses repeats by design.
Do not execute the flat public-schema source dump, add a broad reader, or turn the
synthetic fixtures into a claimed BIRD dataset.
Native extraction and PostgreSQL import completed. .env.california exists and is
private/ignored. Do not rerun initialization or import; both refuse existing targets.
C1 labels/splits are still later decisions.
Docker engine 29.6.2 and Ollama 0.35.1 respond. The postgres image pull completed.
Before executing generated SQL, implement/test the minimum guard, bounded executor
and comparator. A model endpoint smoke must not execute model output as SQL.
Do not touch the existing PostgreSQL 17 service or its data.

Known tool paths for this session:
- uv: C:/Users/Kunal/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uv.exe
- Docker: C:/Users/Kunal/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe
- winget: C:/Users/Kunal/AppData/Local/Microsoft/WindowsApps/winget.exe
- Git Bash (skill-script helper): C:/CODE/Git/bin/bash.exe

Use explicit paths if a fresh PowerShell cannot resolve commands; re-detect rather than
changing global settings.
Ollama installer session 90858 completed. Docker Desktop was started with PID 55532;
sqlwarden-postgres-1 is running and healthy on loopback port 55432, using the
sqlwarden_pg16_data named volume. No model download/inference is running.
No Git remote is configured and nothing has been pushed or published.
Qwen7B Q4_K_M and its context-2048 smoke alias are installed, hash-verified and
currently unloaded. No Ollama model is running. See MODELS.md and its compact
manifest before using the recorded alias; never silently pull/replace it again.
Cold first-use exceeded 60 seconds. The warm smoke passed, but later runtime
readiness/warmup must have a separate explicit bound. Only small prompts/context
were measured, not a full-schema workload. Do not close Kunal's other apps.
Native Ollama path: C:/Users/Kunal/AppData/Local/Programs/Ollama/ollama.exe.
Model unload: `ollama stop sqlwarden-qwen2.5-coder-7b-ctx2048:smoke-v1`.
Read-only status: `ollama ps` or GET http://127.0.0.1:11434/api/ps.
The temporary Python probe used `uv run python .tools/probes/qwen_smoke.py`,
without either environment file; do not treat it as the future runtime client.
After every completed task/group, update explaination of project/PROJECT_EXPLAINED.md
in simple English, preserving previous entries and expanding the term glossary.
Archive download session 71692 and read-only native inspection session 69421 completed.
No data download or inspection process remains running. Native extraction session
42513 completed. Database import is complete and no import process is running.

Python checks (project virtual environment):

`uv run pytest -q --tb=line`

Synthetic/bootstrap checks: `uv run --env-file .env.setup pytest -q --tb=line`.
Full PostgreSQL/California checks:
`uv run --env-file .env.setup --env-file .env.california pytest -q --tb=line`.
Use --tb=line for every private database test command, including task-done.
Third-party failure tracebacks can dump connection arguments; do not enable
--showlocals. The California test password was rotated with explicit approval
after one such dump. Do not rerun the ignored rotation probe without new approval.

Executor-only pure/workflow checks: `uv run pytest tests/test_executor.py -q --tb=line`.
Actual executor: `uv run --env-file .env.setup --env-file .env.california pytest tests/test_executor_postgres.py -q --tb=line`.

Comparator pure and actual controls (approved plan):
`uv run pytest tests/test_comparator.py -q --tb=line`.
`uv run --env-file .env.setup --env-file .env.california pytest tests/test_comparator_postgres.py -q --tb=line`.

Guard-only: `uv run pytest tests/test_guard.py -q --tb=line`.
Restricted PostgreSQL guard controls:
`uv run --env-file .env.setup --env-file .env.california pytest tests/test_guard_postgres.py -q --tb=line`.
Trusted builtin catalog metadata only:
`uv run --env-file .env.setup --env-file .env.california pytest tests/test_guard_postgres.py::test_actual_builtin_function_operator_and_type_inventory -q --tb=line -s`.
Do not use either private test environment to launch the runtime or prompt a model.

Restart: `docker compose --env-file .env.setup up -d --wait`.
Stop without deleting data: `docker compose --env-file .env.setup stop`.
Do not rerun credential initialization when either local env file exists.
The current volume already has db/function_hardening.sql and db/cluster_hardening.sql
applied. Their setup-only update commands are documented in README; do not rerun
the full bootstrap on existing data. Preserve the default-database CONNECT/TEMP
revocations; never grant a runtime login access outside sqlwarden.

The original source-selection command was `uv run python scripts/fetch_data.py`;
it has completed and must not be rerun against the existing destination. Current
full checks are `uv run --env-file .env.setup --env-file .env.california pytest -q --tb=line`.
The native extraction and one-time import have also completed; do not rerun them.

`uv run ruff check .`

`uv run ruff format --check .`

Open decisions: none for the approved comparator plan; native execution remains
selected and no new dependency is needed. Both tasks and the single final review
are complete. A new model/CLI implementation plan needs its own artifact review.
None for the approved bounded-executor plan.
None for the completed guard plan or approved SQLGlot addition.
None at C0. Later C1–C9 remain unanswered and apply at their milestones.

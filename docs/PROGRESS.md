# SQLWarden progress

Active spec: [BUILD_SPEC.md](BUILD_SPEC.md). Detailed product plan:
[sqlwarden-plan.md](../sqlwarden-plan.md). Preserve task IDs; the active spec
amends their order and checks.

Current group: G0. Last completed subtask: G0.7a guard plan Task 1, pure SQL guard.
Last completed commit before this update: 83ac96a. Kunal approved the written
guard plan and SQLGlot 30.21.0 addition on 2026-10-04. Current: Task 2, restricted
PostgreSQL acceptance checks. G0.7a is not complete.
Release order: G0 → G1 → G2 → G3 → G4 → G5 → G7; G6 is optional after release.

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
- [ ] G0.7a (early): tested minimum guard, bounded executor, EX comparator and one-database CLI smoke.
  - [x] Inspect/pin official EX source and prepare the first SQL-guard plan.
  - [x] Review/approve the written guard plan and direct SQLGlot addition.
  - [x] Implement/verify the pure scope-aware guard (184 unit checks).
  - [ ] Verify guard acceptance on real restricted PostgreSQL.
  - [ ] Implement/verify executor/comparator/CLI; no generated SQL yet.
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

Next: execute Task 2 of the approved
[minimum SQL-guard plan](superpowers/plans/2026-10-03-minimum-sql-guard.md) natively
in this checkout. Task 1 is implemented and verified; do not redo it. SQLGlot is
pinned/installed and guard.py exists. Keep the same guard for later components.
Task 2 runs only static authored read controls with california_connected;
never execute the UNSAFE cases or model output. One fresh final read-only review
follows the two native tasks. No runtime executor is produced by this plan.
G0.7a still requires the bounded executor, pinned EX comparator and safe CLI after
the guard. EX_COMPARATOR.md contains only source-reference evidence.
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

`uv run pytest -q`

Synthetic/bootstrap checks: `uv run --env-file .env.setup pytest -q`.
Full PostgreSQL/California checks:
`uv run --env-file .env.setup --env-file .env.california pytest -q`.

Restart: `docker compose --env-file .env.setup up -d --wait`.
Stop without deleting data: `docker compose --env-file .env.setup stop`.
Do not rerun credential initialization when either local env file exists.
The current volume already has db/function_hardening.sql and db/cluster_hardening.sql
applied. Their setup-only update commands are documented in README; do not rerun
the full bootstrap on existing data. Preserve the default-database CONNECT/TEMP
revocations; never grant a runtime login access outside sqlwarden.

The original source-selection command was `uv run python scripts/fetch_data.py`;
it has completed and must not be rerun against the existing destination. Current
full checks are `uv run --env-file .env.setup --env-file .env.california pytest -q`.
The native extraction and one-time import have also completed; do not rerun them.

`uv run ruff check .`

`uv run ruff format --check .`

Open decisions: none for the approved guard plan or SQLGlot addition.
None at C0. Later C1–C9 remain unanswered and apply at their milestones.

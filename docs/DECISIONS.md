# SQLWarden decisions

## D-001 — C0: execution and Git identity (2026-10-03)

Context: Kunal explicitly requested execution and supplied
https://github.com/Kunal874/sql-warden.git. The remote currently has no refs.
Options: configured identity or a different verified/noreply identity.
Decision: Kunal confirmed Kunal <kunalchandrakar2005@gmail.com> for author and committer.
Rationale: retain the owner's existing identity; configure this repository only.
No remote addition, push or publication has been approved under the G7 release gate.

## D-002 — C0: prerequisites and time (2026-10-03)

Context: the initial PATH check could not find uv, Docker or Ollama; only Python
3.14 was registered. Further installed-application inspection found uv 0.12.22
and Docker Desktop 4.83.0 in per-user locations. Node 24.18.0 is installed and
Node 24 is a supported LTS line; WSL 2.7.11.0 and a Docker distro are present.
Options: install missing tools, owner installs them, or files-only preparation.
Decision: Kunal authorized installation of missing prerequisites and confirmed
15–20 hours/week. Reuse existing uv/Docker; install managed Python 3.12 and Ollama.
Rationale: preserve the agreed stack without redundant installations or global
Python changes. No paid services, signup or spending is authorized.

## D-003 — C0: working directory and branch (2026-10-03)

Context: the revised execution brief requires the current workspace.
Options: current workspace or a separate checkout.
Decision: use D:/PROJECTS/SQLWARDEN on feat/foundation.
Rationale: the repository is new and this satisfies the explicit workspace rule.
Do not create a nested project or separate worktree for the foundation.

## D-004 — local PostgreSQL port (2026-10-03)

Context: an existing PostgreSQL 17 service is listening on 5432.
Decision: use a separate loopback-only port, initially 55432, for the project's
Docker PostgreSQL 16 once its availability is checked.
Rationale: keep the agreed database version without changing the existing service.
Cost if wrong: choose another free local port; no data migration is involved.

## D-005 — G0.3: minimal Python foundation (2026-10-03)

Context: the foundation needs a package and a meaningful check before the executor.
Decision:
G0.3 uses uv's bundled build backend, pinned to the installed uv version 0.12.22.
This is part of the approved uv toolchain, not an added runtime framework. Only
approved pytest/pytest-asyncio/ruff are needed initially; runtime dependencies
will be added when their tasks need them. Query limits validation replaces the
obsolete trivial foundation test and is reused by the early executor.
Rationale: use the selected toolchain and test a real resource-boundary contract.
Cost if wrong: packaging or limit defaults can be adjusted locally before C4.

## D-006 — G0.4: local database bootstrap (2026-10-03)

Context: database isolation must exist before generated SQL or benchmark import.
Decision: use the pinned official postgres:16 image digest
sha256:1a6ab3f5345eb6dbe04a1349529caabdb0ab09293a09590fad07b2246bfa4b54,
loopback port 55432, a new sqlwarden_pg16_data volume and two synthetic fixture schemas.
Each dataset gets its own restricted login; warden_app is limited to app;
warden_owner is NOLOGIN and separate from the Docker bootstrap administrator.
Generate random local credentials once and refuse overwrites. Separate setup-only
.env.setup from runtime .env; neither is versioned or printed. No existing service,
database or volume was changed or deleted.
Rationale: demonstrate real least-privilege behavior before importing benchmark data.
Cost if wrong: local limits/layout can be revised before C1/C4; preserve the volume
and credentials rather than recreating them silently.

Verified runtime: PostgreSQL 16.15. SQLWarden container healthy; 26 real integration
checks initially passed, including cross-schema denial and effective future grants.

## D-007 — G0.4: close the large-object permission gap (2026-10-03)

Context: review and direct rollback-protected tests showed that PUBLIC still had
execution rights on large-object creation/mutation functions. Disabling the mutable
read-only default allowed the restricted reader to create a large object.
Decision: revoke the complete unused large-object API (all overloads), alongside
the reviewed file/sleep functions. Use one idempotent function_hardening.sql in
fresh bootstrap and as a targeted existing-volume permissions update. Always roll
back mutating test probes, including unexpected success.
Rationale: the read-only project does not need this API; privileges must hold even
without the read-only default. Preserve data/credentials and avoid a volume reset.
Verification: 80 tests passed, including 37 real database checks; zero runtime-owned
large objects remained after reproduction. This is an initial boundary, not an
exhaustive security audit. PostgreSQL 16 documents the large-object SQL interface at
https://www.postgresql.org/docs/16/lo-funcs.html and its client/server functions at
https://www.postgresql.org/docs/16/lo-interfaces.html (checked 2026-10-03).

## D-008 — G0.5a: pin the first source selection (2026-10-03)

Context: the canonical HF revision has label JSON but no database files. The
official corresponding package is minidev_0703.zip, with a July 2025 modification
date; the older Aliyun package is dated 2024. Its complete archive is about 800 MB,
while California Schools SQLite is about 11 MB and has only three tables.
Decision: pin the canonical label revision and corresponding archive by SHA-256;
extract only California Schools and its metadata, keep raw data ignored/immutable,
and inspect source contents read-only. DATA.md holds exact URLs, hashes and counts.
Rationale: one small actual database is sufficient for the early safe slice. No
source SQL is automatically executed. Existing synthetic fixtures remain separate.
The native dump's flat layout and type/name differences are confirmed. The proposed
selective native import is awaiting review of its written implementation plan;
no BIRD role/schema/import or benchmark definition change is approved by this record.

## D-009 — G0.5a: approved selective native import (2026-10-03)

Context: SQLite and PostgreSQL differ in identifiers and numeric storage; the
downloaded dump also contains unrelated data and owner/session SQL.
Decision: Kunal's proceed approves the written native-import plan. Select only
three pinned COPY-data blocks, preserve native names/types and load them through
asyncpg into the isolated California schema with its own restricted login.
Rationale: reuse native PostgreSQL data without executing dump SQL or changing
the benchmark. Full typed-content and privilege checks are required before
marking G0.5a complete. Existing credentials, data and named volume stay intact.

## D-010 — G0.5a: description-name padding (2026-10-03)

Context: the actual metadata check found four frpm description names padded with
whitespace, while the native SQL identifiers have no such padding.
Decision: trim only the description-name padding and require a unique exact match
to checked native names; record all four source-to-description aliases in the
compact import manifest. Preserve source bytes, SQL names and benchmark labels.
Rationale: attach the supplied descriptions to their verified existing columns;
no schema correction, benchmark change or numeric conversion is made.
Cost if wrong: a description could be misattached; the schema and privilege
boundary are unchanged. All 89 descriptions now match uniquely.

## D-011 — final review: cluster boundary and setup gates (2026-10-03)

Context: fresh read-only review found two Important issues. Runtime logins could
connect to postgres/template1 despite hardening in sqlwarden; three California
cross-reader checks could run before that dataset was set up.
Decision: remove PUBLIC CONNECT/TEMP on these unused default databases with one
shared idempotent cluster_hardening.sql, included in bootstrap and applied to the
existing dedicated PostgreSQL 16 volume. Gate every California check on its
separate environment/login before connecting with another reader.
Rationale: database catalogs have independent privileges, and first synthetic
setup must work without a California import. Preserve data, credentials, the
named volume, template0's closed state and the existing PostgreSQL 17 service.
Verification: nine new tests observed RED before fixes, then GREEN; full suite
158 passed including 67 real PostgreSQL checks. Eight actual connection denials
and catalog checks verify the default-database restriction. Setup-only checks
pass with California checks skipped. This is not an exhaustive function audit.

## D-012 — simple-English project notebook (2026-10-03)

Context: Kunal requested a separate folder named explaination of project and a
file explaining every completed group/subtask and AI terminology simply.
Options: many separate reports, or one living notebook with completed-task entries
and an expanding glossary.
Decision: maintain explaination of project/PROJECT_EXPLAINED.md as one living file,
using very simple English, with historical completed tasks and new terms added
after each completed subtask/group. Preserve the exact requested folder name.
Rationale: one place is easy to find and read; technical evidence remains in the
existing progress, decisions and data records. Do not claim future features work.

## D-013 — G0.6a: bounded local Qwen probe (2026-10-03)

Context: the next approved milestone is Qwen endpoint smoke. Initial available
GPU/RAM were limited; Kunal freed memory and authorized the bounded local probe
without requiring him to close more programs.
Decision: use the originally requested Qwen2.5-Coder-7B-Instruct Q4_K_M from
Ollama, pin and independently hash its actual model/template/license artifacts,
and create a new context-2048/output-64 local alias without global changes.
Use only tiny synthetic text/JSON requests, not SQL/data/credentials. This is
a feasibility spike with no retained runtime client or added dependencies.
Rationale: measure one available local model before the guarded CLI. The first
cold call timed out at 60 seconds; after runner loading, the unchanged bounded
probe passed six warm calls. Preserve that failure and unavailable usage. One
seed pair matched, but this is not a general determinism or accuracy claim.
Ollama reported 100% GPU; the model was unloaded after testing. MODELS.md and
qwen-smoke-manifest.json hold source pins, measurements and limitations. Exact
upstream conversion ancestry is not declared; pin the actual GGUF, not an assumed
conversion revision. The runtime still uses the approved SDK in its later task.

G0.6a final-review rulings (no Critical or Important findings; the Minor loopback
wording was clarified):

- Existing foundation/database implementation: keep the unchanged verified
  foundation; this review covers only the model evidence and notebook.
- Repeating PostgreSQL tests in the reviewer: not needed; the executor reran all
  158 tests, including 67 real PostgreSQL checks, before this checkpoint.
- Repeating inference, weight hashing and unloading checks: retain the recorded
  probe/hash evidence; the executor freshly confirmed an empty Ollama model list.
  Do not reload the model merely to repeat the review.
- Exact upstream conversion ancestry: retain the explicit unavailable status;
  verified local artifact hashes do not establish its upstream conversion revision.
- Production hardening of the ignored manual probe: do not ship it as runtime
  code; the later provider needs its own approved SDK implementation and tests.
- Larger contexts, cancellation, concurrency, varied seeds, arbitrary schemas,
  the second model and SQL accuracy: remain unproved later work, not smoke claims.
- Future commit attribution and release checks: verify this commit's author,
  committer and body immediately; full-history/publication checks remain at G7.

## D-014 — G0.7a preparation and native guard-plan review (2026-10-03)

Context: Kunal requested continued progress after G0.6a. The active BUILD_SPEC
already approves the guard/executor/comparator/CLI design, but no implementation
plan exists for the new safety components.
Options: couple the guard to a CLI file, or implement one reusable pure guard
before its database/model consumers.
Recommendation: the latter, in two native tasks: pure guard then restricted-reader
acceptance checks. Reuse the accepted BUILD_SPEC; preserve this checkout and the
existing native execution method. The written minimum-sql-guard plan awaits review,
including the proposed direct addition of approved-list SQLGlot 30.21.0. No parser
dependency or guard runtime code has been added and no implementation approval is
inferred from the earlier continue.
Rationale: the first component can be tested without loading Qwen or touching
credentials/data. Subsequent G0.7a components consume it; this preparation does
not complete G0.7a or authorize generated SQL before all required controls pass.
Source findings: EX_COMPARATOR.md records the inspected official set comparison
at the same Mini-Dev revision as DATA. No benchmark definition/freeze, gold run,
code-license assumption or score is made. Parser source metadata and license
are documented in the plan; wheel integrity remains an installation-time check.

Approval update (2026-10-04): Kunal's "yes i approve move forward" approves the
written minimum-sql-guard plan and direct sqlglot==30.21.0 addition, as asked in
the preceding handoff. Execute both tasks natively in the current checkout.
The earlier pending status above is the historical preparation record.

## D-015 — G0.7a minimum guard policy and execution rulings (2026-10-04)

Context: the approved plan needs a pure guard before any executor or model query.
Decision: freeze/slotted policy and decision records, exact concrete AST classes,
reviewed functions and simple builtin cast types; PostgreSQL ASCII name folding,
complete relation scopes and unchanged accepted SQL. SQL input is limited to
8192 UTF-8 bytes, 1000 AST nodes and root-zero depth 64; identifiers to 63 bytes.
Rationale: unknown syntax/relations fail closed rather than relying on model
instructions or textual keyword checks. SQLGlot remains a parser, not an engine
validator. Qualified functions and parameterized/custom casts are intentionally
strict false-block risks, to be measured later; no benchmark has been altered.
Verification: Task 1's 184 guard tests and 342-test suite passed. Task 2 now adds
56 real guard acceptance checks; full suite 398 passes. The future executor must guard SQL itself
and establish restricted identity/settings; GuardDecision is not an authority token.

Execution rulings, in decision order:

- Task 1: Ruling: two additional test expectations disagreed with the approved node list / pinned API — VALUES is explicitly reviewed and resolves to a non-physical Scope; Array inherits Func and is rejected as function_not_allowed. Correct those extra expectations, not production policy — cost if wrong: a reviewed VALUES query could be accepted incorrectly, or a rejection could have the wrong category; restricted execution remains mandatory and absent.
- Task 1: Ruling: SQLGlot's unsupported-command warning can include input literals — use its error_message_context=0 parser option and test warning redaction, without changing global logging — cost if wrong: diagnostic messages may be less helpful; raw SQL must not leak into logs.

## D-016 — G0.7a actual builtin acceptance inventory (2026-10-04)

Context: an AST allowlist alone does not establish PostgreSQL behavior. Task 2
uses handwritten controls, the restricted California login and explicit readonly
transactions with 5s statement / 500ms lock timeouts and pg_catalog first in lookup.
Decision: retain the approved narrow policy unchanged after actual acceptance and
catalog checks; never add grants or use a setup identity to make a query pass.
Rationale: inspect concrete native overloads and underlying routines rather than
assuming every SELECT/function/type name is harmless. These are tested initial
controls, not an exhaustive overload, extension, arbitrary-policy or attack audit.

Actual PostgreSQL 16.15 inventory (all signatures below are in pg_catalog):

- Aggregates: count()->bigint, count("any")->bigint; sum(bigint)->numeric,
  sum(real)->real; avg(bigint)->numeric, avg(real)->double precision;
  min/max(text)->text, min/max(bigint)->bigint, min/max(real)->real,
  min/max(date)->date. Aggregate transition/final/combine/serialization/moving
  routines were also inspected: C/internal, pg_catalog, immutable/stable,
  no SECURITY DEFINER.
- Other functions: abs(bigint)->bigint, abs(real)->real;
  round(double precision)->double precision, round(numeric,integer)->numeric;
  length(text)->integer, lower(text)->text, upper(text)->text;
  row_number()->bigint. Stored functions/aggregates/windows are C/internal,
  immutable/stable, non-SECURITY-DEFINER and executable by the actual reader.
  CASE, COALESCE and NULLIF are SQL forms; no fabricated pg_proc grants are needed.
- Operators: bigint + / - / * / division / modulo / equality resolve respectively
  to int8pl/int8mi/int8mul/int8div/int8mod/int8eq(bigint,bigint);
  real addition/comparison to float4pl/float4lt(real,real);
  date comparison to date_lt(date,date); text equality/LIKE/ILIKE to
  texteq/textlike/texticlike(text,text). All inspected operator implementations
  are pg_catalog C/internal, immutable/stable, without SECURITY DEFINER.
- Cast targets use builtin base types int4/int8/float4/float8/numeric/text/date/bool,
  not a domain or composite type. Their inspected input/output routines are
  int4in(cstring)/int4out(integer), int8in(cstring)/int8out(bigint),
  float4in(cstring)/float4out(real), float8in(cstring)/float8out(double precision),
  numeric_in(cstring,oid,integer)/numeric_out(numeric), textin(cstring)/textout(text),
  date_in(cstring)/date_out(date), boolin(cstring)/boolout(boolean): builtin
  C/internal, immutable/stable, no SECURITY DEFINER. bigint->numeric uses the
  builtin function "numeric"(bigint). Literal/input-output casts and this explicit
  conversion were executed only on tiny synthetic constants.

Verification: 56 real checks pass. Untrusted function/operator/type qualification
is rejected without executing it. NULL results are allowed and expected where
appropriate. The initial schema-qualified alias lookup failure was corrected in
the test inspector by using physical catalog type names; policy is unchanged.
No AI-generated SQL or benchmark gold was used. The guard does not establish row,
byte, acquisition or total-run bounds, enforce application cancellation, or run
guarded EXPLAIN; those are required in the subsequent bounded executor.

## D-017 — minimum guard final review and handoff rulings (2026-10-04)

Context: one fresh-context read-only whole-branch review found no Critical or
Minor issues, but two Important defects: actual SQLGlot builder IndexError can
escape validation, and unsupported CTE bodies can leak SQL in scope warnings
and be accepted when unused. The parser redaction option in D-015 alone does
not protect the scope diagnostic path.
Decision: fix both in one TDD pass, without a second reviewer, policy expansion,
dependency upgrade, global log changes or database/data/credential changes.
Verification: three parser regressions observed RED then GREEN; full real suite
401 passed after that fix. Four malformed-CTE logging regressions observed RED
then GREEN; two positive controls preserve VALUES and query parentheses. Final
guard suite 193 passes; full suite 407 passes including 123 actual PostgreSQL
checks. The 56 scoped guard acceptance checks still pass. No-env mode 284 passes /
123 skips; setup-only 327 passes / 80 skips. Locked sync, lint and format pass.
All original planning inputs are unchanged. This completes only the guard
increment; the bounded executor, comparator and CLI remain before generated SQL.

Execution/final-review rulings continue D-015's two rulings, in decision order.
Each of the eight reviewer declined-to-judge items is resolved explicitly:

- Final: Ruling: the plan's parser exception list omits actual pinned-builder IndexError failures — add IndexError only at the parse boundary, not a broad Exception handler, because both concrete reproductions violate sanitized rejection — cost if wrong: an unknown parser failure may still escape and require another independently demonstrated regression; known builder failures now reject without widening SQL policy.
- Final: Ruling: individually allowed scalar nodes are not valid CTE query bodies — require an unwrapped reviewed query root or VALUES before traversing scopes; reject malformed bodies without muting global logs, because the scope builder otherwise logs SQL and can omit an unused body — cost if wrong: valid but unreviewed CTE forms may be falsely blocked; supported SELECT/set-operation/VALUES/parenthesized controls must remain accepted unchanged.
- Final: Ruling: reviewer did not repeat PostgreSQL operations — retain executor verification, freshly repeated after fixes (407 total, 123 actual database checks), rather than widening the read-only reviewer task — cost if wrong: a database boundary regression could be missed by those specific controls; no exhaustive security claim is made.
- Final: Ruling: executor deadlines/cancellation/guarded EXPLAIN, comparator and CLI are unfinished — keep generated SQL prohibited and hand off the next bounded-executor plan, rather than call the guard an end-to-end agent — cost if wrong: this component is not yet a usable question-answering flow.
- Final: Ruling: arbitrary datasets, custom types/extensions and exhaustive overload safety are unreviewed — retain only the fixed native California builtin evidence; review any expanded trusted policy before use — cost if wrong: an unreviewed routine could weaken isolation.
- Final: Ruling: parser acceptance of nonexistent function aliases or engine-invalid expressions — keep original SQL and the distinction between guard policy and PostgreSQL validation; do not rewrite or broaden acceptance to repair them — cost if wrong: some accepted queries can fail at the engine and the future executor must sanitize that failure.
- Final: Ruling: no hard parser wall-clock deadline or aggregate transient-encoding memory cap — retain the approved input/AST limits without claiming process isolation; future request/executor limits must account for this residual risk — cost if wrong: hostile validation input could consume excessive time or memory before rejection.
- Final: Ruling: concurrent administrator replacement of import files and ignored-dump aggregate processing limits — retain the trusted pinned offline workflow and prior native-import rulings; this guard increment changes neither importer nor files — cost if wrong: privileged local tampering could invalidate provenance, or ignored data could consume excessive processing time.
- Final: Ruling: repeated inference/hash/cold-start and conversion-ancestry checks — keep recorded local artifact evidence and explicit unknown ancestry; do not reload the model for guard work — cost if wrong: later live model behavior or upstream conversion details can differ from the recorded smoke evidence.
- Final: Ruling: README's foundation-era test total — retain its historical subset wording and use current PROGRESS/notebook totals, rather than rewrite historical evidence — cost if wrong: a reader could confuse the old subset with the current full-suite total.
- Final: Ruling: retain feat/foundation in the required current checkout — no base branch exists and G7 prohibits remote/push/publication; no merge, new branch or integration menu needed for this local-only increment — cost if wrong: integration remains postponed until an explicit owner decision.
- Final: Ruling: retain this plan's ignored scratch instead of the skill's deletion step — AGENTS.md requires approval before destructive work and no scratch-deletion approval was given; preserve all rulings in committed DECISIONS — cost if wrong: small redundant local review files remain on disk, not in Git.

Deferred minors: none reported or re-graded. Ignored review scratch is retained
under .superpowers/sdd/2026-10-03-minimum-sql-guard; no deletion was attempted.
No merge, remote, push, pull request or publication was performed.

## D-018 — bounded-executor preparation and review gate (2026-10-04)

Context: Kunal requested further progress and a progress update after D-017's
completed guard. The approved BUILD_SPEC supplies the executor design; its new
implementation plan still needs review. General continuation and approval of
the earlier guard plan do not approve this newly written artifact.
Options: add an all-dataset registry or per-request connections, versus reuse
one fixed California reader and a caller-owned one-connection pool.
Recommendation/pending review: the latter, in three native test-first tasks:
pure complete-result/estimate contracts; internally guarded restricted execution;
actual PostgreSQL budgets/cancellation/settings reset and pool recovery.
Keep the current checkout and installed dependencies. No executor runtime code,
new config fields or direct dependencies are added by this preparation.

Proposed contracts: only complete ok results contain data; overflow/errors never
return a prefix. Account for compact UTF-8 JSON {columns, rows} framing and cells,
while preserving original typed rows/order/duplicates. Fetch one row and detect
cap-plus-one. Add positive-integer max_estimated_cost/max_estimated_rows=100000
as uncalibrated initial knobs, not currency, gold-informed tuning or a benchmark
change. Guard internally before restricted, bounded EXPLAIN (FORMAT JSON);
never ANALYZE, LIMIT injection, caller-selected role/host or a forged decision.

One explicit readonly transaction holds settings/planning/fetching. Normal
results and budget blocks roll back/release within the deadline; error/cancellation
terminates the connection synchronously and the real tests must prove replacement.
External cancellation propagates. Pool lifecycle has a separate finite bound;
creation/close errors have a fixed, chain-suppressed category, while caller body
exceptions/cancellation retain themselves. No runtime loader reads test env files.

Residual limits: the driver receives/decodes one cell/row or EXPLAIN value before
checking it; sizing can transiently allocate encoded bytes. The envelope cap is
not a heap/wire cap, work_mem is not total memory isolation, synchronous checking
is not hard process preemption, and application error redaction does not prove
PostgreSQL administrator logs are redacted. No server logging/grant change made.

Evidence: official PostgreSQL 16 and asyncpg docs plus installed locked 0.31.0
source inspected; upstream GitHub tag/API browsing unavailable, so no upstream
commit pin claimed. The plan contains the sources and concrete controls for all
five Review Focus conditions; code blocks only syntax-checked, not implemented.
Fresh existing suite: 407 passed including 123 actual PostgreSQL checks, zero
skips; no-env 284/123 skipped; setup-only 327/80 skipped; sync/lint/format pass.
Foundation checklist has 6/12 numbered items complete plus partial G0.7a; no
effort-weighted overall percentage claimed. The notebook records preparation.
Await Kunal's review of docs/superpowers/plans/2026-10-04-bounded-sql-executor.md,
preserving native execution. No inference, data change or publication authorized.

Approval update (2026-10-04): Kunal's "continue with progress" follows the
presented written-plan handoff and approves its implementation. Execute its
three tasks natively in the current checkout. The pending proposal above is
the historical preparation record; no new dependency is requested.

## D-019 — executor complete-result and estimate contracts (2026-10-04)

Context: the approved executor plan Task 1 requires pure output/cost boundaries
before a connection workflow. Decision: add only the two validated positive-int
estimate fields, immutable QueryResult and private result/plan checks; retain all
other QueryLimits defaults. Only complete ok output may later score or vote.
Rationale: explicit prefix-free overflow and compact UTF-8 {columns, rows} sizing
preserve SQL semantics, original typed cells, duplicate names/rows and order.
An empty/NULL answer is not an error. Unsupported values/plan JSON fail safely.
The byte envelope is not a wire/heap cap or EX/voting canonicalization; estimates
are starting limits, not calibrated benchmark choices.
Verification: missing-module RED plus 10 new config-field failures, then initial
71 scoped passes and final 88 result/config passes. Full suite 455 passed, zero
skips, with 123 actual PostgreSQL checks after formatting; lint/format/diff pass.
This task does not yet produce a runner, database execution or model SQL.

## D-020 — internally guarded restricted executor (2026-10-04)

Context: approved runner Task 2 consumes the pure contracts from D-019.
Decision: reuse the guard internally and a trusted, fixed California reader
pool (maximum one connection). One read-only transaction checks actual identity
and settings before EXPLAIN and unchanged prepared SQL; fetch one row at a time.
Normal completion/budget rejection rolls back before bounded release. Unexpected
failure or cancellation terminates the connection; external cancellation keeps
its original meaning. A single public error boundary returns fixed categories,
not SQL, credentials, rows or driver exception text. The opener loads no env file.

Verification: missing QueryExecutor RED, then 54 initial and 94 final scoped
passes. Full suite 511 passed, zero skips (14.67s), with 123 existing real database
checks; actual executor recovery remains Task 3. Lint/format/whitespace pass.
No dependency, grant, data, credential, benchmark or inference change. Keep
D-018's decoded-value/transient-memory/server-log residual limitations.

Execution ruling, in decision order:

- Task 2: Ruling: Ruff rejects the plan's function-call default and try/except/pass cleanup style — use one module-level frozen QueryLimits default and contextlib.suppress for exactly InterfaceError, preserving the same behavior — cost if wrong: a shared default or cleanup exception policy could change behavior; the default is immutable and existing opener/detached tests must remain green.

## D-021 — actual executor bounds, recovery and approved credential rotation (2026-10-04)

Decision: keep D-018–D-020's fixed reader/pool and provisional estimate defaults;
actual PostgreSQL evidence now supports only the tested executor contracts.
The 18 real checks cover complete/empty/NULL/duplicate-position output, exact
row/byte/UTF-8 limits, estimate blocks, fixed error categories, finite acquisition,
statement timeout, external cancellation with backend removal, settings reset
and subsequent successful query. No runtime correction was required.
Retain decoded-value/transient-allocation, synchronous-validation and server-log
limitations. This is not universal resource isolation or benchmark calibration.

Tests were written before evaluation. Initial 18 passes; first full suite 528
passes / one cold-connection fixture failure. After its contention-only correction
and style cleanup, 18 passes (2.12s); final no-env 388/141 skipped, setup-only
431/98 skipped, both-env 529 passes including 141 actual PostgreSQL, zero skips
(16.07s). Sync/lint/18-file format/whitespace pass; original inputs unchanged.
No dependency, data/grant change, model inference, generated SQL or publication.

The failing fixture's library traceback exposed one restricted test-login password
in the local chat. Kunal approved its rotation explicitly. Updated only that role's
password and ignored .env.california via an ignored one-off probe; new login passed,
old login was refused, all role flags remained unchanged. No secret is recorded
in tracked artifacts; setup/app/other passwords were preserved. Future private
checks use --tb=line, not full argument/locals dumps. Application error redaction
and test-harness diagnostics are separate boundaries.

Execution rulings continue D-020, in decision order:

- Task 3: Ruling: the plan's 50ms connection setup can fail before the pool-contention control starts — create the same fixed-reader pool with normal finite connection bounds, then construct a trusted 50ms QueryExecutor over it for occupied-slot/recovery checks; do not relax production limits — cost if wrong: a separate cold-authentication regression could escape this contention control; deterministic acquisition/lifecycle controls and actual normal connections remain covered.
- Task 3: Ruling: the plan's nested observer/executor contexts fail SIM117 — combine the contexts without changing entry/exit order — cost if wrong: accidental lifetime changes could affect cancellation cleanup; the real observer/backend-removal test must stay green.
- Task 3: Ruling: a failed white-box connection test exposes its private argument in pytest's library traceback — use --tb=line for private checks and perform only Kunal's explicitly approved test-password rotation, verifying new/old authentication and unchanged role flags — cost if wrong: shorter diagnostics can hide useful failure detail, or cached local clients may retain the revoked password; investigate with sanitized evidence and reload the ignored test configuration.

## D-022 — bounded executor final review and local-only handoff (2026-10-04)

One fresh read-only reviewer examined the complete approved increment
df07434..0e9df33, including all five Review Focus conditions and recorded
execution rulings. No Critical, Important or Minor defect was found. Its own
144 deterministic tests passed (0.89s); it did not read credentials, rerun
PostgreSQL or inference, or modify the checkout. All seven declined-to-judge
items are ruled on below. Re-grading by caller effects yields no new actionable
finding; no correction pass or second review is needed. Deferred minors: none.

Final implementer verification: 529 passed, zero skips (18.43s), including 141
actual PostgreSQL checks; locked sync/lint/18-file format/whitespace pass.
Historical planning inputs and dependency/lock files remain unchanged. Healthy
fixed loopback database and named volume preserved, model unloaded, no remote.
Kunal-only author/committer identities verified for each of the three commits.
The exposed previous test password is revoked; no other credential changed.
Notebook updated. Next: a separately reviewed EX comparator plan and safe CLI,
not generated SQL, a completed G0.7a or a finished AI service.

Final rulings continue D-020/D-021, in decision order:

- Final: Ruling: no integration base branch exists for native feat/foundation — review all three commits of this approved executor increment against recorded df07434, reusing the earlier completed guard/import reviews and whole-suite checks — cost if wrong: an unchanged earlier-foundation issue can escape this incremental review; this is not a repository-wide audit.
- Final: Ruling: hard process-memory or synchronous CPU isolation is not established — retain explicit decoded-value/transient-encoding and synchronous-validation limits; row/input/AST bounds and the PostgreSQL container are not a Python process-isolation guarantee — cost if wrong: large allowed values or expensive synchronous work can consume excess time or memory before rejection.
- Final: Ruling: estimate calibration and benchmark coverage remain unreviewed — keep the two provisional defaults and defer development calibration/protocol decisions to their named checkpoints; estimates never replace runtime deadlines — cost if wrong: useful queries may be blocked or expensive work underestimated.
- Final: Ruling: comparator, voting, model/CLI and web admission consumers are absent — preserve the complete-ok-only handoff contract and prohibit generated SQL until comparator/CLI checks pass; make no end-to-end or aggregate-request claim — cost if wrong: this component is not yet a usable question-answering service and future consumers can mishandle its results.
- Final: Ruling: forged result objects, malicious custom pools/codecs and arbitrary trusted limits require internal Python control — retain the trusted constructor/configuration boundary; request input is SQL, not these objects or choices, and later wiring must preserve that separation — cost if wrong: exposing internal plumbing to requests could bypass execution or scoring boundaries.
- Final: Ruling: other datasets, custom types/extensions, exhaustive routine safety and administrator privilege changes are not reviewed — retain the fixed California builtin/import/guard boundary and require review before expanding trusted policy or changing it — cost if wrong: unreviewed objects or privileged changes could weaken isolation.
- Final: Ruling: PostgreSQL administrator logs and third-party test diagnostics are separate from runtime error redaction — keep stable application errors without SQL/log listeners, document server-log limits, and retain the approved rotation plus compact private-test output rather than changing server logging/grants — cost if wrong: server logs or future diagnostic harnesses may expose private SQL or connection details.
- Final: Ruling: the reviewer did not independently repeat database recovery, credential rotation, source fingerprints or model state — retain the implementer's actual controls and fresh 529-pass suite with 141 PostgreSQL checks, verified new/old authentication/role flags and unloaded-model status; do not label them independently repeated review evidence — cost if wrong: environmental or intermittent failures can escape those specific controls.
- Final: Ruling: retain feat/foundation in the required current checkout — D-003/AGENTS.md require this workspace, no base branch exists and G7 prohibits remote/push/publication; keep as-is without a merge or prohibited integration option — cost if wrong: integration remains postponed until an explicit owner decision.
- Final: Ruling: retain this plan's ignored scratch instead of deleting it — AGENTS.md requires approval before destructive work and no deletion approval was given; preserve every ruling in committed DECISIONS — cost if wrong: small redundant local review files remain on disk, not in Git.

All rulings are also retained in ignored .superpowers/sdd/2026-10-04-bounded-sql-executor.
No merge, remote, push, pull request, publication, history edit or scratch deletion.

## D-023 — pinned EX comparator preparation and review gate (2026-10-04)

Context: Kunal asks to continue after the completed executor increment at
92ad554. G0.7a next needs the official EX checker before a safe model/CLI slice.
The approved BUILD_SPEC already specifies this architectural subsystem; native
sequential execution remains selected in the existing checkout under D-003.
The Handoff and writing-plans require review of a newly written plan before coding.

Options: independently reproduce the tiny pinned equality rule over complete
typed results; copy/run the upstream database/evaluation runner; or introduce
rounding/type-tag/duplicate-preserving canonicalization for all comparisons.
The latter two would add inappropriate drivers/connection paths or change EX.

Preparation choice: write/self-review a two-task plan using existing QueryResult
and stdlib sets; do not implement it before Kunal reviews the new artifact. Source
revision abd11b6db92a1c9f809b32f7564c7c71b34d67f0 and both in-memory byte/hash
checks match EX_COMPARATOR.md. Preserve row-set/Python equality without extra
rounding, column matching or normalization. Retain primary citations without
vendoring or executing the upstream runner. No direct dependency or benchmark
change is proposed. Ponytail favors this existing-container/small-function design.

Proposed wrapper: usable reference first; successful complete row sets produce
match=1 or mismatch=0. Non-ok predictions produce prediction_failed=0 even with
a matching retained prefix; ordinary malformed/hash errors produce comparison_error=0.
A failed/malformed reference produces gold_invalid=None, not an automatic
exclusion. The later frozen validity manifest owns reference failures/denominators;
pending/interrupted jobs remain pending in the future orchestration. Voting stays
separate and must not see reference data. These are proposed implementation
contracts consistent with BUILD_SPEC, not approval to freeze/exclude/score data.

Rationale: compare complete typed cells, not the executor's sizing strings, and
keep errors fixed and private. All five Review Focus conditions have concrete
planned controls: 60 units and 17 restricted PostgreSQL cases. Three Python
fences pass syntax and snippet lint/format without execution; the proposed absent
module's first-party classification is explicit only in that lint invocation.
All 24 successful-pair SQL inputs pass the pure guard without database I/O.
No new test or runtime module exists yet. Existing full verification passes 529
tests, including 141 actual PostgreSQL controls, with zero skips (13.14s).

Cost if wrong: a caller could forge an internal ok result, expose the offline
reference path, silently discard gold-invalid items, or mistake EX for voting.
Native cell types can differ from source-dialect results; this does not establish
conversion validity or an official leaderboard score. Set construction allocates
additional memory and has no hard Python process deadline. Keep the trusted
constructor/offline boundaries and require later cache/manifest/CLI wiring checks.
These bounded checks are not an exhaustive SQL or information-flow audit.

Approval state at preparation: awaiting Kunal's review of
docs/superpowers/plans/2026-10-04-ex-comparator.md. No execution-method/dependency
question is reopened, and no parallel implementation or preparation reviewer
was used. Data, credentials, grants, dependency files and historical plans remain
unchanged; no generated SQL, model load, benchmark run, remote/push/publication,
history edit or deletion. Comparator/CLI and G0.7a remain unfinished.

Approval update: Kunal's "yes do it" on 2026-10-04 approves this written plan.
Native execution and existing dependencies remain selected; implementation
evidence continues D-024 onward. No benchmark, inference or publication approval.

## D-024 — complete-result EX implementation / Task 1 (2026-10-04)

Context: the approved comparator plan proceeds natively from 1ffb81d. Options,
source rule and invalid-gold/denominator contract remain D-023; no new package,
cell-normalization rule, benchmark definition or result-authority framework.
Decision: implement the exact pure QueryResult -> EXComparison interface, using
stdlib row sets. Reference checked first; prediction failures score zero, invalid
gold returns None, and only equal complete row sets score one. Fixed reasons are
match/mismatch/prediction_failed/gold_invalid/comparison_error; no raw data/error
output or database/model/file/env I/O. Future voting remains separate.

Evidence: planned missing-module RED (0.39s) before production source; 60 units
GREEN (0.19s), full no-env 448 passed / 141 skipped (2.24s), lint/20-file format
pass. All five Review Focus controls exist on the pure side. Native acceptance
and the single final read-only reviewer remain Task 2/final gates.

Execution ruling, in decision order:

- Setup: Ruling: stay in D:/PROJECTS/SQLWARDEN on feat/foundation rather than create a worktree — AGENTS.md and D-003 explicitly require this current checkout; it is clean and not main/master — cost if wrong: this work is not isolated from later edits made in this checkout; preserve unrelated changes and do not assume branch isolation.

Rationale/limits: reuse the trusted executor's EOF/typed-cell contract, not its
JSON sizing strings. Arbitrary forged internal results/custom hashing code and
hard process-memory/time isolation remain outside this function's guarantee.
These tests do not establish a benchmark score, valid conversion, online inference
noninterference or real database acceptance. Task 2 is next without another
approval request; no change to data, credentials, grants or original inputs.

## D-025 — restricted native EX acceptance / Task 2 (2026-10-04)

Context: Task 1 at a7be998 has 60 pure passes and its successful task-done gate;
the approved plan requires actual native controls before comparator acceptance.
Decision: retain the exact comparator/executor interfaces and all original
semantics. The 17 handwritten controls pass without a production correction,
SQL rewrite, new login, policy/limit change, dependency, import or credential update.
Task 1's initial RED owns the new comparison logic; Task 2 adds integration
evidence rather than deliberately breaking working code to manufacture RED.

Evidence: 17 actual comparator controls passed, zero skips (2.19s); full suite
606 passed / zero skips (15.36s), including 158 actual PostgreSQL checks. No-env
448/158 skipped (2.12s), setup-only 491/115 skipped (3.70s); locked sync, lint,
21-file format and whitespace pass. Historical plans/dependencies/existing runtime
remain unchanged; loopback volume healthy/preserved, no loaded model or remote.
No new execution ruling or runtime deviation; D-024's setup ruling still applies.

Rationale: check the true typed result handoff, normal failures, nonmatching
overflow and connection recovery using the real fixed reader, without reference
datasets or models. Gold-invalid None still cannot authorize exclusions or select
a denominator. Native-type controls do not establish converted-label validity or
official leaderboard equivalence. Future aggregate metrics, caches, voting and
online model/CLI consumers need their own bounds and leakage checks.

State: one final fresh read-only review of the complete comparator increment is
next, not a finished G0.7a or AI agent. No Critical/Important/Minor review result
is claimed before it runs. Preserve named data volume, private env files and the
PostgreSQL 17 service; generated SQL, publication and destructive work remain out.

## D-026 — comparator final review and local-only handoff (2026-10-04)

Context: both approved comparator tasks committed at a7be998/7d26e77 and their
task-done gates passed (60 units / 17 actual controls). One fresh read-only
reviewer examined the complete increment 1ffb81d..7d26e77 and all five Review
Focus conditions. No Critical, Important or Minor findings; no fix pass or second
review. Deferred minors: none. The six declined-to-judge items are resolved below
by reasonable caller effects, not assumed to be findings or independently proven.

Evidence: reviewer independently passed 60 units (0.20s), whitespace and both
commit identity/body checks; HEAD/status unchanged. Implementer final full suite
passed 606 tests, zero skips (17.51s), including 158 actual PostgreSQL checks.
Locked sync, lint/21-file format and whitespace pass. Database healthy on the
fixed loopback port with named volume preserved; no loaded model or remote.
Database/full-suite/source-fingerprint/environment checks are implementer
evidence, not independently repeated by the reviewer.

Decision: retain the implementation as approved, mark only the comparator child
complete, update the learning notebook and keep feat/foundation locally. G0.7a
still needs the separately planned model/CLI slice; G0 remains 6/12 numbered
top-level tasks complete. No generated SQL, benchmark score, dependency, data,
grant, credential, remote/push/publication, history edit or deletion.

Final rulings, in decision order, continue the setup ruling already recorded in
D-024. The first six resolve the reviewer's six declined-to-judge items; the
remaining four make verification, review range and local handoff limits explicit.

- Final: Ruling: retain the trusted executor-result boundary for forged ok statuses, inconsistent row widths and unsupported hashable/custom cells — this offline function consumes bounded complete typed internal results, not requests or unvalidated caches; future loaders must validate that contract — cost if wrong: forged or incorrectly decoded results can receive a bogus score or execute custom hashing behavior.
- Final: Ruling: keep set allocation and synchronous comparison without a hard process-memory/CPU sandbox — current executor results are bounded and the plan explicitly documents transient/additional memory; no hard deadline is claimed — cost if wrong: large trusted limits or costly internal values can consume excess memory/time before rejection.
- Final: Ruling: leave gold exclusions, aggregate denominators and interrupted-job accounting to the frozen validity manifest/evaluation runner — gold_invalid=None is only a marker and this function cannot drop items or score pending jobs — cost if wrong: future orchestration could omit hard questions or turn pending work into failed scores, inflating or distorting metrics.
- Final: Ruling: keep duplicate-preserving voting and online generation/repair leakage checks separate — this increment has no inference consumer, performs no I/O and returns no reference rows; EX is not a voting function — cost if wrong: future wiring may misuse set equality for voting or expose reference information to the model.
- Final: Ruling: defer cross-dialect label validity and official-score equivalence — native typed controls reproduce the comparison rule but do not validate converted labels or a frozen benchmark — cost if wrong: source/native value differences can yield misleading adapted or leaderboard claims.
- Final: Ruling: do not renew an exhaustive guard/executor/database-security or server-log audit — unchanged foundations retain their completed reviews and limits; this review covers only the comparator handoff — cost if wrong: an unrelated existing security or logging issue can escape this incremental review.
- Final: Ruling: treat PostgreSQL/full-suite/source-fingerprint/environment checks as implementer evidence, not reviewer repetitions — reviewer ran only isolated units/whitespace/identity; implementer final 606-pass run and saved source hashes provide separately labelled evidence — cost if wrong: environmental or intermittent failures may escape that specific independent review.
- Final: Ruling: use 1ffb81d..7d26e77 as the whole approved comparator review range — no integration base branch exists and earlier foundation reviews are complete; the package includes both planned commits rather than only HEAD~1 — cost if wrong: a defect outside this unchanged incremental scope could escape review.
- Final: Ruling: keep feat/foundation in the required current checkout without merge/remote/push/publication — D-003/AGENTS.md already choose this workspace and G7 forbids release actions; no valid integration target exists — cost if wrong: integration remains postponed until a later explicit owner decision.
- Final: Ruling: retain only this plan's ignored scratch rather than delete it — AGENTS.md requires destructive-work approval and none was granted; persist all rulings in committed DECISIONS — cost if wrong: small redundant local artifacts remain on disk, not in Git.

Next: prepare and self-review the safe one-database model/CLI plan, then obtain
review of that new artifact before implementation. Do not repeat the completed
comparator, guard, executor or import tasks/reviews. Broader validity, voting,
evaluation, tenant isolation, agent, UI and release remain their own milestones.

## D-027 — safe local CLI preparation and review gate (2026-10-04)

Context: the guard, executor and pinned comparator are complete/reviewed; the
exact Handoff at 9b8205f is preparation of a separate safe one-database model/CLI
plan. Kunal's current "proceed" authorizes that preparation. BUILD_SPEC already
approves the architecture/native method, but no new artifact or direct dependency
approval is inferred. G0 remains 6/12 numbered items; G0.7a is open.

Decision: prepare/self-review
[2026-10-04-safe-local-cli.md](superpowers/plans/2026-10-04-safe-local-cli.md), then
pause for Kunal's review. Three sequential tasks: fixed local provider; validated
single-candidate CLI and setup helper; real controls and one live demonstration.
Ponytail keeps one provider and existing guard/executor without registry, cache,
repair, retrieval, voting or orchestration framework. No online reference/comparator
input, confidence/EX score, raw-SQL flag or expanded agent milestone.

Options considered: standard-library HTTP spike, official SDK with HTTPX, or
full provider/agent infrastructure. Recommend official SDK/HTTPX as the existing
plan's public client/transport seam; the old smoke spike is not a second runtime.
Proposed additions openai>=2,<3 and httpx>=0.28,<1 are absent locally and require
explicit approval before uv resolves/locks them. Inspect installed public API,
Python compatibility, transitive packages and license metadata before coding;
do not claim the proposed calls ran or exact package versions are known now.
Cost: a larger dependency tree than stdlib, justified by the approved SDK contract;
no paid service, account, API key or hosted inference is requested.

Initial prompt is generate_smoke_v1 with only verified native
schools(cdscode, county, school, city) names/types. A 1024-byte content rule with
128 output tokens leaves generous headroom in the unchanged 2048-context alias,
but is not an exact tokenizer/provider-truncation proof. Report actual tiny
request usage; reject overflow, never silently trim. Cost: only a narrow demo;
no full 89-column schema, retrieval, full-schema baseline or general accuracy.
G1.4 still owns the full versioned prompt-file set.

Credential options: launch with setup/test files (rejected), manually retype the
same restricted value, or exclusive setup-only copy into a new ignored .env.runtime.
Recommend the copy after approval, containing only WARDEN_RUNTIME_CALIFORNIA_PASSWORD;
refuse existing files and wrong/inherited setup keys, never import the helper from
runtime. It reads only .env.california during setup and changes no database password
or grant. Cost: one additional private local credential file; runtime never receives
the administrator/test environment. No credential copy/display or runtime-file
creation happened now; existing private configuration was used only by tests.

Budget/readiness options: reuse a single 60s cold deadline, unlimited startup/
retry, or separate finite phases. Prior cold startup exceeded 60s; recommend 90s
readiness, 60s generation, 180s enclosing request, existing QueryLimits and 5s HTTP
close. Optional one empty-prompt preload, one generation attempt, no SDK/transport
retries/proxies/redirects and a 64KiB uncompressed response cap. Attempts admitted
are not completed work; mock transport counts real HTTP calls. Unavailable usage
or interrupted counters remain null. Cost: finite cold-start failure may still
occur; cooperative/chunk bounds are not hard process/heap isolation.

Cancellation/HTTP close does not prove Ollama stopped GPU/server work. The proposed
one-question acceptance requires stopping only the existing project alias and
observing actual unload; if unconfirmed, report it and ask. Never stop someone
else's model, close apps, redownload weights or modify global Ollama settings.
Local metadata pins assume trusted Ollama and do not lock out privileged/concurrent
changes. Cost: residual races/server work remain possible and honestly documented.

Evidence: unchanged code passes 606 configured tests (13.50s), zero skips,
158 actual PostgreSQL checks; no-env 448/158 skipped (3.32s), setup-only 491/115
skipped (3.91s); locked sync/lint/21-file format/whitespace pass. Eight plan fences
parse and six assembled proposed files pass static lint/format only. Self-review
fixed planned callback bindings and mapped all five Review Focus tests; no SDK,
future tests or model/CLI snippets were executed. No independent preparation
reviewer, repeated foundation review or parallel implementation.

Pending: Kunal's review of this new plan, direct additions, exclusive runtime-only
copy and exactly one frozen question: "How many rows are in the schools table?"
Expected offline scalar 17686 is not sent to the model. Run actual PostgreSQL
controls first; failed/blocked/wrong live output keeps G0.7a open, no silent retry.
One final read-only review after all three tasks, not per-task reviews. Current
work changes only preparation/progress/decision/learning documents; no code,
dependency, credential, model, database, benchmark, remote/push or release action.

Approval update (2026-10-04): Kunal explicitly approved this dated plan, adding
openai/httpx, copying the existing restricted credential into a runtime-only file
and exactly one bounded guarded local AI/database test. Implement sequentially
and update the notebook after each completed task. Native execution stays chosen;
no hosted, remote/push, extra live retry, credential rotation or release approval.

## D-028 — approved safe local provider (2026-10-04)

Kunal explicitly approved the dated plan and both direct additions. Installed
openai 2.54.0 (Apache-2.0, Python >=3.10) / httpx 0.28.1 (BSD-3-Clause,
Python >=3.8), inspected their public interfaces and resolved metadata. Only
the approved pair was added directly; 27 packages are locked. Local-only
inference remains selected, with no account/key/hosted request or real model
call in Task 1. 37 mocked-SDK checks and full 643-test configured suite pass.
The initial full suite had one existing cancellation-observation timeout;
isolated/group/full repeats passed unchanged. Root cause remains unproven.

Execution rulings in order (costs retained for final handoff):

- Setup: Ruling: stay in the existing feat/foundation checkout — AGENTS/D-003/approved plan require this workspace — cost if wrong: no extra checkout isolation; inspect Git before tasks/commits.
- Task 1: Ruling: write Step 4 budget/readiness tests with Step 2 before full Step 3 source — preserve tests-first for all planned behavior — cost if wrong: test-step order changes, not scope/contract.
- Task 2: Ruling: likewise move terminal/privacy tests before CLI/setup source — preserve tests-first — cost if wrong: test-step order changes, not security/scope.
- Task 1: Ruling: refuse OPENAI_CUSTOM_HEADERS, OPENAI_ADMIN_KEY and OPENAI_WEBHOOK_SECRET before client/network, sharing forbidden keys with Task 2 — installed SDK auto-reads them even with fixed local URL/key; all three cases failed first — cost if wrong: the local demo rejects inherited hosted SDK settings; no global environment is edited.

The four-column capsule and conservative byte rule are not full-schema retrieval
or an exact tokenizer. HTTP cleanup is independent of server/GPU unloading.
Task 2 is next; G0.7a and all model accuracy/benchmark claims remain open.

## D-029 — validated one-shot CLI and exclusive setup helper (2026-10-04)

Task 2 reuses the fixed provider, immutable guard and restricted California
executor. It adds no registry/framework/repair/voting/reference-loader and no
new dependency. Only the server-owned db/model/limits exist; bad inputs/config
stop before I/O, failures expose no SQL/rows, output is escaped JSON with a
labelled 20-row display preview of a complete result. Null usage/counters are
unknown, not zero; HTTP cleanup is not GPU cleanup.

Runtime accepts only WARDEN_RUNTIME_CALIFORNIA_PASSWORD for database credentials
and rejects all other WARDEN_/admin/test keys plus inherited private SDK/log
settings. Setup helper reads only the existing restricted .env.california key,
requires its exact 48-hex shape, and exclusively creates new ignored .env.runtime;
it is not imported by the runtime, changes no grants/password and was not run
in Task 2. Existing synthetic .env is not this CLI's launcher.

Evidence: absent-module RED, 39 CLI checks GREEN, combined 76 client/CLI checks;
524 no-env passes/158 actual checks skipped. Locked sync/help/lint/26-file format/
whitespace pass. Full configured suite 682/682 (15.39s), zero skips. No live
inference or model-generated SQL yet. Task 2 fulfills
the already recorded test-step-order/shared-private-key rulings in D-028; there
is no additional architecture/dependency/scope ruling. Task 3 and sole final
read-only review remain, so G0.7a is still open and G0 remains 6/12.

## D-030 — actual CLI controls and one successful local demonstration (2026-10-04)

All 7 fixed-provider CLI PostgreSQL controls and full 689-test configured suite
passed before the only live generation. Authorized exclusive runtime copy
contains only the existing restricted password under its runtime key, private/
ignored, validated without setup/test envs. No password/grant/volume change.

One frozen self-authored question answered/ok, matching offline scalar 17686,
11.387s whole-process wall time, one preload/one generation, 89/18 actual tokens.
Immutable guard and existing fixed executor were used; reference count/gold/data/
credentials were not inference inputs. CLI_SMOKE records actual pins/hashes and
limitations. This is not EX/accuracy/consensus/semantic correctness in general.

- Task 3: Ruling: bounded Start-Process stop helper was tool-policy rejected before execution; do not retry via another launcher, observe finite keep-alive automatic unload through read-only /api/ps instead — preserve tool controls and actual cleanup evidence — cost if wrong: GPU stays occupied longer and acceptance stays incomplete if unload is unconfirmed; explicit stop timing is unavailable.

Actual /api/ps after the answer showed only the project alias/context2048 and
finite expiry 22:34:55.5704569+05:30. At 22:35:16.9458759+05:30, read-only /api/ps
returned models=[]: automatic unload confirmed, no explicit stop timing claimed.
Sole final review is pending; HTTP close alone was not used as GPU evidence.
Post-live full configured suite 689/689 (27.37s); no-env 524/165 skipped, setup-only
567/122 skipped. Lint/27-file format/whitespace pass. Historical inputs/existing
boundaries unchanged, no remote/push. G0.7a still open pending remaining gates.

## D-031 — sole final CLI review and one test-first correction pass (2026-10-04)

Whole approved increment d991bfc..3e1f72e received one fresh read-only review
using the code-reviewer template, active spec/plan, all five focus conditions
and every ledger ruling. Reviewer independently repeated 76 client/CLI checks
(2.59s) and verified clean Git/whitespace/source-lock hashes/commit identities;
actual database/live evidence was implementer's, explicitly not repeated.

Critical none, Important two, Minor none. Both Important grades retained by
effect: a known overflowing token count could be erased when the other was
unavailable, and the permissive SDK could accept non-assistant or malformed
falsy tool/refusal fields. Neither demonstrated a database-permission bypass;
the existing guard still applied. Both defects also appeared in the planned
example, so correct its behavior rather than claim it was a reliable contract.

ONE TDD fix pass: 30 mocked response/flow cases written first, 27 RED/3 existing
controls GREEN (2.01s). Overflow 8, malformed-envelope 15, partial-usage 4 failed;
empty valid fields 2 and already-rejected empty function object 1 passed. Then
normalize/check each usage counter independently, require assistant role, allow
only absent/empty well-shaped tool/refusal fields and no function call. Valid
partial measurements are retained, unknowns remain null. Affected client/CLI
106/106 (3.12s), including 67 provider checks, then full 719/719 (29.95s), zero skips.
No dependency/private SDK toggle/framework, re-review or second live call.

Final locked sync; no-env 554/165 skipped (7.28s), setup-only 597/122 skipped
(10.27s), lint/27-file format/whitespace pass. Original planning inputs, existing
boundaries and frozen model/config unchanged. Runtime credential remains private/
ignored, PG healthy at 127.0.0.1:55432/named volume retained, /api/ps empty, no remote.
The sole live record remains explicitly at f8b8150, before this stricter parsing
fix; happy-path/actual controls remain green, inference was not repeated.

All G0.7a gates now pass: guard, executor, comparator, narrow CLI, actual PG
controls, successful one-question acceptance, observed automatic unload, final
review and verified fixes. Mark G0.7a complete, G0 numbered checklist 7/12, not
an overall effort percentage. Remaining data/validity/model/split/E0/C1-C2 work
and G1-G5/G7 remain unfinished. Keep feat/foundation locally, no release action.

### Exhaustive execution/review rulings (decision order)

- Setup: Ruling: stay in the existing feat/foundation checkout — AGENTS/D-003 and the approved plan require D:/PROJECTS/SQLWARDEN, with no nested worktree or release action — cost if wrong: there is no extra checkout isolation from concurrent local edits, so inspect Git before each task/commit.
- Task 1: Ruling: write Step 4's budget/readiness tests with Step 2 before Step 3 source — full planned source already implements those behaviors; tests-first requires their RED gate before implementation — cost if wrong: only test-step order differs, with the same behavior and acceptance contract.
- Task 2: Ruling: likewise write Step 3's terminal/privacy tests with Step 1 before adding CLI/setup source — preserve tests-first for the complete planned behavior — cost if wrong: only test-step order differs, not scope or security.
- Task 1: Ruling: refuse OPENAI_CUSTOM_HEADERS, OPENAI_ADMIN_KEY and OPENAI_WEBHOOK_SECRET before any client/network construction, and share these forbidden keys with Task 2 — the inspected SDK 2.54.0 auto-reads them even with a fixed dummy key/base URL; tests reproduce premature transport entry in all three cases — cost if wrong: this local-only demo rejects a child process that inherits those hosted SDK settings; never edit global environment to make it pass.
- Task 3: Ruling: bounded Start-Process stop helper was rejected by tool policy before execution; do not retry via an alternate launcher, observe finite keep-alive automatic unloading through read-only /api/ps instead — preserve tool controls and actual cleanup evidence, continuing independent checks while waiting — cost if wrong: GPU memory stays occupied longer and acceptance remains incomplete if unload is not confirmed; explicit stop timing is unavailable, not claimed.
- Final: Ruling: review d991bfc..Task 3 HEAD as the whole approved increment — no integration base branch exists and prior component reviews are complete; this includes all three tasks, not HEAD~1 — cost if wrong: unchanged earlier component defects may escape this fresh review; existing full regression evidence remains separately labelled.
- Final: Ruling: retain feat/foundation in the required current checkout without merge/remote/push/publication — AGENTS/D-003 already select it, there is no integration base branch, G7 approval is absent — cost if wrong: integration remains postponed until an explicit owner decision; finishing skill's release options are not authorized here.
- Final: Ruling: retain only this plan's ignored scratch instead of deleting it, and persist all rulings/minors in committed decisions/notebook — AGENTS requires destructive-work approval, none was granted — cost if wrong: small redundant local artifacts remain on disk, never in Git; sibling plan scratch is untouched.
- Final: Ruling: unchanged importer/guard/executor/comparator internals remain under their completed reviews; this review checks integration interfaces only — approved scope excludes repeated component review — cost if wrong: a pre-existing component defect can remain undiscovered by this increment review.
- Final: Ruling: live inference and actual database acceptance are implementer evidence, not independent reviewer repetitions — reviewer safely repeated only76 pre-fix units, approval allowed exactly one live question — cost if wrong: environment drift/intermittence may escape independent verification; actual165 integration checks still ran separately.
- Final: Ruling: earlier executor cancellation-observation timeout remains unproved/unfixed — unchanged component with isolated/group/full green repeats does not establish cause or fix — cost if wrong: the intermittent timing failure may return; no bound was weakened.
- Final: Ruling: byte policy is conservative, not exact tokenization/universal truncation protection — approved tiny capsule and measured89 tokens support only narrow smoke; independent known-counter overflow is now enforced — cost if wrong: provider truncation can remain undetected when usage is unavailable or prompts differ.
- Final: Ruling: cooperative deadlines/HTTP close are not hard process/heap isolation or guaranteed server/GPU cancellation — approved scope explicitly states these limits; actual automatic unload is separately observed — cost if wrong: allocation/work can exceed logical limits or outlive client cancellation.
- Final: Ruling: concurrent alias/model/global-setting changes are not exclusively controlled — pins trust native local Ollama; never change global settings/stop another model — cost if wrong: a privileged race can invalidate the checked artifact/configuration.
- Final: Ruling: hostile local filesystem/ACL manipulation during credential copy is outside trusted-workspace setup — exclusive target creation and exact restricted source remain, no broader permission-manager added — cost if wrong: a hostile local user/admin can interfere with/access private settings.
- Final: Ruling: concurrent/embedded LocalQwen/ask_once reuse and process-wide SDK logger changes remain unsupported — approved runtime is a fresh single-provider CLI invocation, not a multi-request host — cost if wrong: embedded/concurrent use could mix cleanup state or suppress unrelated SDK logging.
- Final: Ruling: incidental SDK completion id/timestamp/choice-index strict validation is not required here — fields are unused, execution-relevant assistant/optional-message shape is now checked — cost if wrong: malformed unused metadata can pass without affecting this execution decision.
- Final: Ruling: full-schema/semantic accuracy/retrieval/cache/repair/voting/benchmark/UI/hosting/release remain deferred milestones — approved single-candidate thin slice intentionally has none — cost if wrong: this demo cannot meet broader agent or production expectations; do not claim it can.

Deferred minors: none reported. Every declined-to-judge behavior has a ruling
above; no silent exclusion or repeated component review. All records retained
in this plan's ignored scratch because destructive cleanup was not approved.

## D-032 — remaining G0.5 intake preparation and artifact-review checkpoint (2026-10-05)

Approval update: Kunal's proceed forward after this exact artifact was linked
approves the two-task correction-intake plan and its four pinned resource files.
Native sequential execution retained; C1/benchmark/schema/import/model decisions
and all exclusions below remain outside that approval.

Context: resumed clean feat/foundation at e46c4ba. The approved three-task safe-CLI
increment and sole review are complete. Its Handoff explicitly requires a new
multi-step plan's artifact approval; earlier approval does not authorize more
corpus acquisition, benchmark choices, dependencies or model runs. Kunal asks
to proceed through routine approved work and pause only at required checkpoints.

Decision: complete the authorized read-only preparation now, retain native
sequential execution and propose a narrow two-task offline correction-intake
plan. Do not infer approval of that newly written artifact from approval of
the completed CLI plan or the overall product spec. No runtime implementation,
database mutation, new correction files or model inference in this preparation.
No execution-method question is reopened.

Inspected the already downloaded package and canonical label hashes plus the
official correction release in memory. Revision
fe766045c55b6875a43b30e9ac7683df5582f8cf, source/license URLs, observed sizes/hashes
and exact-ID drift counts are in DATA. Both correction sets have 498 unique IDs,
missing financial IDs 119/120; no unexpected IDs or db mismatches. Corrected IDs
are strings, canonical IDs integers; list order differs. SQL-only questions/
evidence differ from our canonical release at 81/86 IDs (141 either); full at
147/152 (229 either). Corrected-pair union is 148, not an automatic ambiguity label.
Variable original_* metadata is observational, not a trusted override.

Options: extend all database imports first, or establish this small pinned
label identity/drift report before expanded data/conversion work. Recommend the
latter: original/corrected sources must be distinguishable before C1 and split
freezing. No primary label set, benchmark denominator/exclusion, text normalization
or ambiguity rule has been selected. A stable ID/db match alone is not verified
question alignment or SQLite/PostgreSQL result equivalence.

Proposed approval scope: two tasks in
docs/superpowers/plans/2026-10-05-corrected-label-intake.md; existing httpx/stdlib
only, four fixed resources totalling 645,140 bytes, new ignored release directory,
bounded no-proxy/no-redirect/hash-checked acquisition, tests-first offline report
and relevant checks/documentation/local commits. Review required before coding/
persisting that corpus. No new dependency, account, money, database import/reset,
secret copy/rotation, model weights/probe, SQL execution or publication included.
The upstream schemas inventory is 75 description CSVs/76,445 bytes by Git metadata,
not a performed schema correction. Inspect contents/mapping in a later plan.

Rationale/cost: this small boundary exposes baseline drift rather than treating
all rewrites as ambiguity fixes. It leaves the ten remaining database imports
and full G0.5 acceptance unfinished; raw report validity is not a benchmark score.
The required artifact gate means implementation pauses until Kunal reviews this
specific scope, not because software prerequisites failed.

Verification: full unchanged suite 719 passed in 19.64s, zero skips, including 165
actual PostgreSQL checks; locked sync checked 27 packages. Preparation's first
aggregate printer failed because JSON dictionary keys were tuples; isolated
reproduction confirmed that cause, changing only the diagnostic output shape
made its repeated read-only inspection pass. No project source/test change or
database/credential action was used to resolve that scratch diagnostic failure.
Final lint/27-file format/whitespace checks pass; all five embedded Python plan
blocks parse, without executing proposed code/tests. Placeholder scan found
none. Self-review moved local-pin tests to the initial RED gate and rejected
malformed optional difficulty in the planned example. No fresh reviewer
dispatched for plan preparation; no new implementation test claims.


## D-033 — approved offline label checker / Task 1 (2026-10-05)

Context: Kunal approved the reviewed two-task artifact with proceed forward.
Reconciled clean feat/foundation at 399efed; baseline locked sync checked 27
packages, no-env suite 554 passed/165 skipped (7.00s). No broader G0.5/C1 approval.

Decision: implement the planned offline dictionary-based checker with stdlib
only. Exact local pins precede strict JSON/record checks and ID/db alignment.
Report counts and changed IDs, never gold text; source SQL is neither executed
nor exposed to the runtime. Text/anchor differences are observations, not an
ambiguity classifier or label selection. Four policy/validity states stay unset.
No acquisition, database mutation, credential operation, model or SQL run here.

Tests first: missing-module RED (0.18s), then first GREEN 38 passes/two errors
in the oversize case's setup/teardown; interim no-env suite 592 passes/165 skips/
two errors. Reproduced Windows rejecting pytest's 600001-character default
parameter ID in PYTEST_CURRENT_TEST. Corrected only the test name, retaining
the entire fixture and 600000-byte decoder cap. Fresh verification: 39 label
checks (0.10s); no-env 593 passes/165 database skips (4.86s); Ruff/29-file format
pass. Last actual PostgreSQL checkpoint remains the pre-change 719/719, not a
claim that today's skipped database tests passed.

Rulings in order:

- Setup: reuse current checkout under AGENTS/D-003 — cost if wrong: no separate
  checkout isolation. Sequential execution and current-task scope preserved.
- Task 1: short explicit raw-parameter IDs avoid Windows' 32767-character env
  limit — cost if wrong: diagnostic names omit raw fixtures; test bytes unchanged.
- Task 1: reverse the equivalent required-key comparison for Ruff SIM300 — cost
  if wrong: none intended; existing malformed-field checks remain required.

Task 1 only is complete. Task 2's fake-network tests, four-file intake/actual
alignment and sole whole-increment review remain. G0 remains 7/12; G0.5/C1 not done.

## D-034 — exclusive correction intake / Task 2 and nullable-hint ruling (2026-10-05)

Context: Task 1 saved at 64f51e4, confirmed Kunal author/committer/body; task-done
39 passes (0.11s). Task 2 is within the approved two-task/four-resource scope.

Decision: fixed four HTTPS URLs at the approved revision; existing httpx only,
no redirect/proxy inheritance, identity encoding, exact per-file byte/hash pins,
20s or remaining-budget I/O timeout, cooperative 120s deadline and new-release
publication only after all pins pass. Refuse pre-existing destinations before
network I/O and recheck before rename; never overwrite or change approved pins.
The trusted local filesystem/cooperative deadline limitations remain explicit.

Tests first: missing fetch_labels RED (0.19s), eight fake controls implemented;
47 combined passes (0.17s), locked sync 27 packages, Ruff/31-file format pass.
Preflight showed ignored destination absent, 46327619584 D: bytes free and fixed
645140 bytes. Sole actual acquisition passed; only newly owned temporary staging
cleaned. Four local pins rechecked, original labels reused, no extra fetch.

First actual alignment failed invalid text field. Read-only types/IDs-only
inspection established evidence null at corrected IDs 1507/1528 in both sources;
all other text fields strings. Regression observed invalid-text RED (0.05s).
Ruling: allow null only for corrected evidence, retain its exact value — it is
present in the approved pinned source schema, not corrupt or changing bytes —
cost if wrong: downstream readers may confuse absent and empty hints; these
must remain exact differences until C1 chooses an input policy. Original evidence
and all other text types stay strict. No row dropping, normalization or repin.
This is parsing support, not benchmark/ambiguity/label selection. Combined GREEN
48 passes (0.22s); original null rejection remains in the existing test matrix.

Actual assertions match earlier read-only observations: 500 originals, corrections
498 each/missing119,120, no unexpected/db/difficulty mismatch, question/evidence
81/86 and147/152, corrected-pair union148. SQL180/215 is text only, not EX. Manifest
records source/license/pins, observed bytes and exact pre-commit acceptance Git
state plus procedure/counts/IDs/anchor observations and undecided states; no gold
text. DATA/notebook updated. No query/model/secret/import/benchmark action.

Fresh regressions: no-env 602 passes/165 skips (5.71s), configured full suite
767 passes/zero skips (21.62s), including 165 actual PostgreSQL checks. Existing
database checks do not establish new corpus execution validity. Ruff/31-file
format/locked sync pass. Task 2 implementation complete; sole final review next.
G0 remains 7/12, G0.5/G0.5b not complete. No publication or remote configured.

## D-035 — sole correction-intake review / one TDD fix and local handoff (2026-10-05)

Context: both tasks saved at 64f51e4/676428f under confirmed sole owner identity.
Both task-done gates pass, latest 48 checks (0.18s). Sole fresh read-only reviewer
on most-capable explicit model covered 399efed..676428f, exact package, plan/spec,
all five focus conditions and ledger. No parallel implementation/second review.

Review evidence: 48 passes (0.20s), six distinct-text reorder probes, exact fresh
report/manifest equality, all six source pins and nullable IDs, Ruff/31-file
format/whitespace/owner identities. No download/database/model/SQL/source-text
output or checkout mutation. Reviewer inspected, did not rerun, configured suite.

Finding: one Important, no Critical/Minor. Installed HTTPX ByteChunker coalesces
iter_raw(chunk_size=4096), hiding a continuous trickle from the cooperative body
deadline until4096bytes/EOF; inactivity timeout does not stop active trickles.
Regraded Important by command-overrun effect; not a data-corruption finding or
an excuse to add hard-kill infrastructure. Regression observed RED1000logical
seconds vs120 (0.12s); change only iter_raw() unbuffered, preserve pre-extension
byte caps/exact pins. GREEN49 combined checks (0.18s), no-env603/165skips (7.24s),
configured768/zero skips (18.42s), including165actualPG. Ruff/31-file format pass.
Existing artifacts/manifest remain valid; no refetch/review repetition/gold SQL.

### Exhaustive final rulings (decision order)

Four earlier execution rulings are in D-033/D-034. These sixteen complete the
20-ruling record. Every declined-to-judge item is explicitly decided, not dropped:

1. Gold correctness/conversion survival: retain explicit deferral; no gold query
   executed — cost if wrong: corpus result validity remains unknown.
2. Label/exclusion/ambiguity/evidence policy/family splits: retain C1 gate and
   undecided states — cost if wrong: no defensible benchmark score yet.
3. Descriptions/remaining imports/content/type/key equivalence: outside this
   four-resource scope — cost if wrong: only California has verified import.
4. Future runtime label/null access: preserve current offline-only separation,
   require later leakage/input review — cost if wrong: future wiring can leak
   answer keys or mishandle absent hints.
5. New DB-security/model-capability claims: no such changes/claims; existing
   configured tests only — cost if wrong: no exhaustive security/model proof.
6. Privileged/ancestor-link/concurrent filesystem tampering: retain trusted
   local immutable-source workflow — cost if wrong: local tampering can invalidate
   pre-use checks; not hostile-filesystem protection.
7. Power loss/fsync/forced termination: normal-operation atomic visibility only,
   not crash durability — cost if wrong: interrupted writes need manual inspection;
   no automatic destructive recovery is authorized.
8. POSIX empty-destination race: retain supported Windows rename/refusal workflow
   — cost if wrong: a port can overwrite an empty raced target; cross-platform
   guarantees require separate checks.
9. DNS/TLS/header/blocked-file hard interruption: cooperative checks/I/O timeout
   only, with delivered-body defect fixed — cost if wrong: blocked operations can
   exceed wall-clock target; no OS hard-kill/memory-isolation promise.
10. Arbitrary build_report/pin arguments: internal production callers use decoded
    rows/fixed constants — cost if wrong: future bypass callers can get raw errors
    or invalid reports and need separate validation.
11. General JSON Unicode/scalar/uniform errors: pinned production bytes checked
    before decode; reject malformed input, do not trust it — cost if wrong: future
    unpinned use can raise ValueError on overlong integers or retain escaped
    surrogates, not a uniform LabelError/general-purpose JSON guarantee.
12. Anchor provenance/SQL-anchor semantics: retain observational-only report
    — cost if wrong: upstream provenance/answer defects remain undiagnosed.
13. General selection/retries/overwrite/recovery/repinning: retain fixed one-time
    refusal workflow — cost if wrong: new release/failure needs separately approved
    update; convenience intentionally absent.
14. Publication licensing clearance: checked declared local license and pin,
    defer distribution to G7 — cost if wrong: release needs additional licensing/
    attribution work; nothing published now.
15. Keep normal feat/foundation checkout local: user's local-only request and
    AGENTS/D-003 select keep-as-is, no base branch/remote — cost if wrong:
    integration postponed, no merge/publication inferred from completion.
16. Retain own ignored plan scratch: destructive SDD cleanup has no owner
    approval under AGENTS — cost if wrong: retained scratch uses disk. Only newly
    owned intake staging was cleaned automatically under this plan's approval.

Deferred minors: none. One verified fix pass, no re-review. Notebook/living records
updated, completed branch kept locally. No remote/push/publication/credential/model/
import/benchmark action. Next: separate reviewed description/layout/import plan,
then conversion/result validity and C1, second model and split/E0/C2. G0 still
7/12; G0.5/G0.5b remain incomplete, no benchmark score or changed denominator.

## D-036 — full-source inspection, batched plan and artifact approval (2026-10-05)

Context: resumed clean fc71084; corrected-label intake/final review fully done.
Kunal requests several checklist items in one run. Handoff required read-only
description/layout preparation and review of a new artifact before implementation.
Completed that preparation; Kunal explicitly approved the three-task
2026-10-05-full-source-preparation.md artifact during this session.

Options: proceed directly into all ten remaining administrative imports, or batch
fixed source extraction/acquisition and an offline source audit first. Decision:
the latter, three sequential tasks without intermediate continuation questions;
existing stdlib/httpx/SQLGlot only, no parallel implementation. PostgreSQL writes,
credentials, inference, gold SQL, benchmark policy and publication remain outside
this approval. Native execution and one fresh final read-only review retained.

Evidence: source-release-pins.json records all 11 SQLite source hashes, exact
original/corrected paths and 75 native table/COPY definitions/pins. Streamed native
dump has 798 columns/3898114 data lines; corrected descriptions cover all native
names. Four original/three corrected files need explicit local cp1252 decoding.
Original constructors has extra wins description; both financial/account files
have a populated unnamed field at data row 3. No original/corrected source bytes
rewritten; names/padding observations do not choose runtime descriptions.

Rulings in order:
1. Keep the mandated normal feat/foundation checkout — verified not main/master,
   user/AGENTS require this directory — cost if wrong: no separate checkout isolation.
2. Stream the native dump without another COPY tree — save about 1 GB during
   preparation; controlled COPY/admin import is later — cost if wrong: later
   preparation remains required before import.
3. Pin exact CSV paths and explicit per-file cp1252 interpretation; record padded/
   unmatched names and populated unnamed metadata — preserve bytes, no silent loss
   or primary-description adoption — cost if wrong: interpretation/mapping still
   needs human review and does not prove semantic correctness.

First original-CSV probe failed strict UTF-8 at 0x96. Isolated all 75 encodings:
four exceptions, strict cp1252 successful. The corrected-file diagnostic then
twice failed its path-depth assertion; changed investigation to numbered code/
Git tree path shapes, finding three relative path segments, not two. Corrected
only diagnostic shape and all 75 in-memory size/blob/hash/CSV checks passed.
No project test/security boundary, corpus byte, pin or benchmark was altered.

New raw footprint: 1493523124 bytes extraction plus 76445 CSV bytes, 1 GiB reserve.
D: free 46325698560 bytes and RAM free 1167319040 at preflight; sequential streaming,
one read-only SQLite at a time, not large in-memory deserialization. No system/model
resource request or user memory closure required.

Preparation verification: locked sync 27 packages; fresh unchanged configured
suite 768 passed/zero skips (20.75s), including 165 actual PostgreSQL checks.
Six embedded Python blocks syntax-parse; counts, hash shapes, unique output paths,
798 columns and declared-type totals checked. Proposed code/tests were not executed
during preparation. No implementation reviewer yet. G0 still 7/12, G0.5/C1 unfinished.
Next execute all three approved tasks, then one final review. No repeated intake,
California import, credential rotation or live question.

## D-037 — full-source batch Task 1 / actual checked extraction (2026-10-05)

Context: Kunal approved all three tasks; preparation 6be261c. Task 1 test file
first observed expected missing-module RED (0.30s), then 16 passing extraction
controls (0.26s). Boundary covers exact selection, forks, symlink/duplicate/
missing members, paths/case collisions, pins, disk reserve, deadline and refusal.

Options: archive-wide extraction or fixed members into a separate collection.
Decision: only fixed members, 1 MiB streaming chunks, per-file bounds/pins,
900s cooperative extraction deadline, 1 GiB reserve and staging rename/refusal.
Reuse existing file_sha256; no dependency, runtime or California loader change.
Cost if wrong: hostile filesystem/concurrent source tampering or hard interruption
is outside this local immutable-source guarantee; no crash-durability claim.

Ruling: remove unused Path fixture import and apply planned ruff formatting —
dead import/line layout only — cost if wrong: later fixtures must reimport Path.
Actual extraction once without env: 87 files/1493523124 bytes; all rehashed after
publication. No-env project suite 619 passed/165 skipped (5.90s); lint/format pass.
No new PostgreSQL import, secret/model/SQL/policy action. Next Tasks 2/3 proceed
under the same approval, no continuation question. G0 still 7/12.

## D-038 — full-source batch Task 2 / pinned descriptions (2026-10-05)

Context: approved batch, Task 1 saved 8a37707. Wrote network tests first; expected
missing-module RED (0.28s). Initial implemented run 5 failures/24 passes: content=
fake HTTPX responses preconsumed their bodies. Isolated/library comparison proved
stream=ByteStream is the correct fixture; production stream rules unchanged.

Options: use changing upstream files or the inspected fixed revision. Decision:
only 75 fixed-revision URLs/size/SHA-256 pins, no auth/proxy/redirect/retry; 180s
cooperative command envelope/20s max I/O and 32768-byte per-file bound. Refuse
existing destination and publish only the complete checked staged release.
Cost if wrong: real network/DNS/TLS/blocked I/O can outlast cooperative targets;
fixed metadata is trusted internal input, not a user-configurable source format.

Rulings in order:
1. Strengthen deadline fixture with no-third-chunk timing assertion — final-only
   timeout could satisfy planned exception-only test — cost if wrong: simulated
   timing does not establish a real network hard deadline.
2. Use ByteStream fixtures, matching working label tests and installed HTTPX —
   represent actual raw body state — cost if wrong: mocks are not live-network proof.

Mutation RED: removing per-chunk check yielded logical 1000s versus expected 181s
(0.15s), restored GREEN 29 combined (0.21s). No-env whole project 632 passed/
165 skipped (5.56s), lint/format pass. Actual fetch once: 75 files/76445 bytes,
each saved pin rechecked. No correction-label refetch, import, credentials, model,
benchmark policy or publication. Task 3 next under existing approval; G0 7/12.

## D-039 — full-source batch Task 3 / explicit source-key issues (2026-10-05)

Context: Task 2 e4433ab; expected missing-auditor RED (0.15s), then 52 batch GREEN.
Actual audit failed without publishing at European Football's FK definition.
Read-only isolation found no metadata/layout/count drift: all 75 table counts/
798 columns align; Team.team_fifa_api_id lacks a required unique constraint.
Three other sources report 955 FK violation records (779/88/88), not necessarily
distinct rows. Count equality alone is not source/converted answer validity.

Options at the required mismatch checkpoint: stop all Task 3 acceptance, or
explicitly record that FK check as uncheckable while finishing the observational
offline audit. Kunal approved the latter amendment during this session. No schema,
row, pin, role, source label/description, benchmark policy or import was changed.

Ruling: catch only SQLite's foreign-key schema-mismatch OperationalError; set
foreign_key_check_status=schema_mismatch and violation count null, never zero;
other OperationalErrors remain fatal — owner-approved observational report — cost
if wrong: source key validity remains unavailable and cannot justify enforcing or
waiving those constraints during a future import without review.

Real malformed-FK fixture RED (0.23s), specific handling GREEN; injected unrelated
interruption still rejects. 54 combined checks (0.46s). One successful acceptance
after amendment: 11 databases/75 tables/798 columns/3898114 rows, full native dump/
definitions/COPY fingerprints and all persisted source pins checked. Actual
metadata saved in source-audit-manifest.json; checked e4433ab plus dirty Task 3.
72 PK-declaring tables/105 FK component records. Type declarations DATETIME->
TIMESTAMPTZ for 11 columns need later timezone/content/result policy. Descriptions
retain extra original wins, 89 padding records and unnamed financial/account field;
corrected coverage 798, semantic/primary adoption unchosen. No raw cells/prose/SQL.

Fresh locked sync 27 packages; no-env 657 passed/165 skipped (5.81s), configured
822 passed/zero skips (16.75s), 165 actual PG, lint/37-file format pass. G0 remains
7/12. Final whole-batch read-only review remains; no additional implementation
review or admin import/model/gold action. Handoff afterward prepares separate
controlled COPY/import/content/conversion scope and its required artifact review.

## D-040 — full-source final review and local-only handoff (2026-10-05)

Context: preparation 6be261c; all three tasks saved at 8a37707/e4433ab/04817bf.
Task-done gates passed 16/29/54 checks. Sole fresh read-only reviewer inspected
6be261c..04817bf, the amended plan/spec and ledger. It repeated 54 checks (0.94s),
verified all audit fields against the ignored report (four provenance additions
only), source-pins hash, all 75 native block pins/totals, whitespace and owner
identities. Parent separately confirmed those relationships and no tracked raw
data/envs or remote. No acquisition/audit/PG/model/SQL operations repeated in review.

Findings: no Critical, Important or Minor issues. No fix pass or second review;
deferred minors: none. Regraded the thirteen declined scope judgments by actual
user effect: all are retained explicit limits, not defects in the approved fixed
offline preparation workflow. Do not infer future imports or stronger guarantees.

Options: expand this batch into new imports/security/content/benchmark claims,
or close its checked observational scope and carry limitations into the next
reviewed artifact. Decision: close this scope, keep the current local branch
and scratch, update notebook/Handoff, prepare the next scope read-only later.
No destructive cleanup, remote, push, publication or credential operation.

Fresh finishing verification: locked sync checked 27 packages; no-env 657 passed/
165 skipped (5.08s), configured 822 passed/zero skips (14.20s), including 165
actual PostgreSQL checks. Lint/37-file format/whitespace pass. .git equals common
Git directory; feat/foundation retained, no remote or tracked raw/envs. Private
setup/California settings used for tests only, never acquisition/audit/runtime.

### Exhaustive final rulings (decision order)

Seven earlier execution rulings are in D-036–D-039. These fifteen complete the
22-ruling record; every declined-to-judge line receives an explicit ruling/cost:

1. Ruling: Retain the trusted immutable local-filesystem boundary — hostile ancestor links, source replacement and destination races are not this tool's promise — cost if wrong: local tampering can invalidate pre-use checks/publication.

2. Ruling: Retain normal-operation staging, not crash durability — no fsync/power-loss/forced-termination recovery is implemented — cost if wrong: interruptions can leave staging and require manual inspection/recovery.

3. Ruling: Keep cooperative deadlines and HTTP I/O timeouts — hashing, ZIP, SQLite, filesystem and blocked network work cannot all be forcibly interrupted here — cost if wrong: some operations can exceed the elapsed target.

4. Ruling: Keep pin/configuration inputs fixed and internal — arbitrary external manifests, URLs and destinations are outside approved production usage — cost if wrong: future configurability needs validation and uniform errors.

5. Ruling: Check only the selected archive members — unrelated members are neither extracted nor executed — cost if wrong: unselected contents remain unreviewed.

6. Ruling: Keep the parser scoped to the pinned native dump layout/COPY data — full fingerprints and selected definitions are checked, not every ignored SQL statement — cost if wrong: a new dump needs parser review; no blanket SQL compatibility/approval.

7. Ruling: Audit only pinned immutable SQLite files — arbitrary SQLite features and mutable WAL-backed sources need a different workflow — cost if wrong: future mutable inputs need snapshot/WAL-aware handling.

8. Ruling: Do not repair or approve source FKs for import — source violation records and the unavailable count are retained exactly — cost if wrong: data/key problems and import-constraint policy remain unresolved.

9. Ruling: Defer typed values, timezones, cross-engine content and gold validity — layout/count preparation does not establish answer equivalence — cost if wrong: equal row counts can conceal differing values or timezone results.

10. Ruling: Defer description semantics, primary selection and encoding-policy redesign — strict reviewed decoding and anomaly observations are not runtime adoption — cost if wrong: prose/charset interpretation still needs human/C1 review.

11. Ruling: Make no new-dataset PostgreSQL security claim — no new imports, privileges or isolation changes; configured tests exercise existing boundaries — cost if wrong: future imports need actual restricted-role security checks.

12. Ruling: Do not treat fake transport coverage as a new live-network assessment — successful pinned acquisition and mocks do not exhaust DNS/TLS/proxy/server failures — cost if wrong: real failures can behave differently or outlast cooperative targets.

13. Ruling: Close stale Task 3/final-review bookkeeping now — the commits, task-done gates and completed review prove completion, not a code defect — cost if wrong: an inaccurate handoff could cause repeated work.

14. Ruling: Keep feat/foundation local as-is — Kunal's explicit local-only request and AGENTS/D-003 select retention, not merge/publication — cost if wrong: integration remains postponed.

15. Ruling: Retain this plan's ignored scratch — AGENTS requires approval for destructive work; no such cleanup approval — cost if wrong: retained scratch uses disk.

The executing-plans skill supplied test-first task gates and one independent
whole-batch review; finishing-a-development-branch keeps the verified branch
as-is under the already explicit owner choice. No new menu/approval for routine
continuation or redundant review. G0 remains 7/12; three nested preparation tasks
are finished, remaining imports/content/conversion/C1 are not. Source FK/timezone
issues and unselected runtime descriptions/labels must enter the next reviewed plan.

## D-041 — next G0 batch preparation and exact import-policy review (2026-10-05)

Context: clean 3f4b61f; source preparation and its one review fully complete.
Kunal asks to try finishing G0 in one run. BUILD_SPEC/Handoff require the next
import artifact/operations review and later C1/C2 decisions; this request does
not supply a new foreign-key, credential, label or benchmark policy decision.

Read-only evidence: dedicated PostgreSQL 16 identity/ownership markers pass;
only California schema/login exist, database 20585495 bytes. All 72 immutable
source PKs have zero null-key rows/duplicate groups; three tables lack a PK.
All 11 codebase DATETIME columns use text/null storage, not verified time meaning.
Remaining ten datasets: 72 tables/709 columns/3868173 rows/991363484 COPY bytes.
Largest COPY 280029547 bytes. D:44817014784/C:661347966976 free, Docker virtual
filesystem1008069328896 available, RAM1511016KiB free, GPU7956MiB free/0used.
New COPY/.env.datasets absent and ignored. No source/data/credential changes.

Options: (1) row-preserving native imports, enforce checked PKs and retain FKs as
unenforced metadata; (2) enforce every source FK, failing known violations/schema
mismatch; (3) repair/drop rows/keys, changing corpus. Recommendation only: option1
for the ten new datasets, preserve California's existing enforced keys. It needs
Kunal's explicit approval of the new written artifact and operation scope.
Source-audit schema_mismatch/null approval is not approval to waive/import keys.

Decision now: finish read-only preparation and
[four-task plan](superpowers/plans/2026-10-05-remaining-native-imports.md), not
execute pending writes. Reuse the approved architecture/importer/auditor/helpers
and existing dependencies; no parallel implementation. Plan batches controlled
COPY, setup-only importer/ten new restricted credentials, toxicology thin slice
with actual rollback/security/content checks, then remaining nine and full matrix.
Proposed UTC/float4 representative mappings, 69 PKs, named rolled-back probes,
2GB setup spill/900s transaction/3600s attempt envelope are explicit for review.
Runtime caps/settings/credentials and benchmark comparator stay unchanged.

Self-review: eight proposed Python blocks AST-valid, never executed. Interfaces,
all five Review Focus cases, exact refusal/transaction/data markers and spec
coverage checked. Clarified plan-only command_timeout=120 and 900s transaction
scope excluding prevalidation hashing; cooperative, not OS-hard time guarantee.
No placeholder plan steps, product files, new schema/login/password/gold/model run,
new dependency, overwrite/rotation/remote/push/publication or policy adoption.

Fresh unchanged project verification: locked27; no-env657passed/165skipped(5.77s);
configured822passed/zero skips(16.27s), including165actualPG; Ruff/37-file format/
whitespace pass. These existing tests do not establish pending import isolation.
Notebook explains source keys, sample versus full comparison and required gates.
G0 remains7/12. Full conversion/description/gold validity and measured C1, second
model artifact/smoke, frozen family-consistent splits/E0 and measured C2 are still
separate required outcomes, not silently accepted by a broad completion request.

## D-042 — approved remaining COPY preparation (2026-10-05)

Context: next four-task artifact committed at 09dedd2; Kunal answered “move
forward” to the explicit ten restricted-login/import and metadata-only-FK
question, and requests questions only for important new decisions. Reuse this
approval; routine artifact review questions waived, substantive spec gates stay.
Decision: execute native/sequentially in the required current checkout; fixed
IDs/pins, existing auditor with optional unpublished COPY sinks, stdlib staging.
No dependencies/parallel implementation/runtime redesign or remote operations.
Task 1 RED: new test collection identifies absent module, as brief expected.
GREEN: 61 extraction/audit/native tests (0.87s), 11 new controls. Actual bundle
published once: 72 COPY files/991363484 bytes/3868173 rows for ten datasets;
all persisted pins/layouts rechecked, California excluded. Source files unchanged.
Existing destination/corruption/deadline/disk/metadata/unsupported-ID refusal
covered. No SQL execution/new database role/password/model/gold work in this task.
Locked27/no-env668passed165skipped(6.29s); configured833passed/zero skips(23.90s),
165 actual PostgreSQL tests. Ruff/39-file format/whitespace pass.
No execution-plan conflict or policy deviation in Task 1. Ruff formatting/import
sorting normalizes the draft without behavioral changes.

## D-043 — fixed remaining importer and private credentials (2026-10-05)

Context: Task 1 committed 25b7697; approved new IDs/logins and metadata-only FKs.
Decision: setup-only fixed PostgreSQL16 identity/marker checks; refuse existing
targets and invalid IDs/passwords before writes. One atomic transaction/dataset,
native types/PK/NOT NULL, own-schema SELECT/default grants and restricted role
settings. 900s transaction/120s command and COPY/2GB setup spill remain explicit;
runtime stays unchanged. Existing native content helper's defaults are preserved.
Full native EXCEPT ALL and first/middle/last immutable SQLite representative
checks precede commit; float4/ISO DATE/UTC DATETIME mappings are sample-only,
not full SQLite/gold comparator acceptance. Unknown validity markers retained.
Task 2 expected missing-module RED then 58passed/22 unconfigured skips(0.73s)
for loader/bundle/California controls; 32 new importer checks. Private ignored
.env.datasets created once: ten distinct valid restricted-only passwords; no
bootstrap key, values never printed, not wired into runtime, no new login yet.
Locked27/no-env700passed165skipped(8.15s); fresh configured865passed/zero skips
(17.71s), 165 real PG. Ruff/41-file format/whitespace pass.
Ruling: preserve the existing cancellation test's exact deadlines and add only
a sanitized phase label — two full runs timed out, isolated test (0.44s) and
all18 executor controls(2.11s), then full865 passed without deadline changes;
cause not established, do not call it fixed — cost if wrong: timing flakiness
may recur and needs evidence, not silent timeout relaxation. No runtime change.
UTC alias/import sorting/string wrapping are mechanical draft normalization.

## D-044 — toxicology real import and boundary acceptance (2026-10-05)

Context: importer committed 0a29ad8; Task 3 actual tests written before import.
Expected 21 configured missing-login failures observed, no credential details.
Real first-COPY/second-COPY-interruption probe passed (0.40s), schema/login absent
after rollback. Target identity/California counts/source pins/container health
checked before actual import; Docker remains768MiB/1CPU with existing volume.
Toxicology committed once: atom9111/bond9156/connected18312/molecule343,
four tables/36922rows/four PKs. Complete typed native EXCEPT ALL and twelve
first/middle/last SQLite samples match BEFORE commit. FKs metadata-only.
22 actual acceptance checks passed(1.29s): counts/types/order/PK/NOTNULL, own reads,
role defaults/memberships/function ACLs, writes/temp/app/California/role/unused
cluster/old-reader denials, future scoped grants, existing-target refusal,
same-count changed-value detection/restored content and partial-COPY rollback.
No claimed blanket function/catalog security, SQLite full equivalence or gold
validity. Metadata-only evidence saved ignored then reviewed into
toxicology-import-manifest.json with actual returned result/provenance/pins.
Old configured full suite866passed/291skipped(21.65s): old165 PG plus synthetic
probe run; other291 require .env.datasets and are deliberately not enabled until
the remaining targets exist. Not a full new-release zero-skip claim.
No Task 3 scope deviation; row preservation/source/timeouts/credentials unchanged.
Final task repeat22passed(1.77s); no-env700passed457skipped(10.18s),
Ruff/42-file format/whitespace pass. No new-release checks silently counted green.

## D-045 — eight imports verified; timestamp interpretation blocks Task 4 (2026-10-05)

Context: Task 3 committed ff0d809; eight new datasets now installed: toxicology,
thrombosis_prediction, superhero, student_club, debit_card_specializing, formula_1,
financial and card_games. Ten distinct setup-only passwords remain private.
Eight imports: 57tables/439columns/2904731rows/54PKs, complete native typed
multisets and171SQLite samples verified before per-dataset commit. California
untouched; no inference, source repair, gold SQL, runtime wiring or publication.
Source FK issues preserved; no new FK constraints. Restricted actual checks:
1083passed/74deselected(39.20s), including383actualPG, all installed eight plus
original boundaries. Pending-target cases explicitly excluded, not passed.

Codebase's first actual attempt returned ValueError; sequence stopped as planned,
no retry/cap increase and European not attempted. Read-only target check proves
Codebase schema/login absent, European schema absent. Eight earlier datasets
remain saved. Native/SQLite sample coercions all succeed;24 selected DATETIME
cells differ by exactly-28800s under the approved naive-UTC comparison.
Full pinned read-only indexed-source-key timestamp audit: all11DATETIME columns,
882084non-null cells have native explicit+28800s offset and zero wall-clock
differences; all SQLite counterparts timezone-unspecified. 226789 null cells
agree, no null mismatch. These are data-preparation observations, not gold or
query equivalence. A sorted-merge diagnostic refused unordered COPY keys;
indexed PK lookups with8MiB SQLite cache/120s cooperative limit succeeded.
No raw cells/keys/passwords emitted or recorded. Ignored diagnostic artifacts
retained; metadata only in partial-import-manifest.json, full ignored evidence.

Decision: Task4 remains incomplete, sole final whole-batch review not dispatched.
Ask the important policy question: approve Codebase-only UTC+08 sample mapping,
test-first fix and one bounded retry, then European; or preserve UTC and leave
Codebase unimported. No owner answer yet; do not infer timestamp/gold policy.
Ruling: commit compact checked partial evidence while Task4 stays incomplete —
preserve57table counts/nulls/pins/key summaries and reference unchanged audit for
exact columns/keys rather than duplicate it — cost if wrong: inspecting complete
layout details requires the linked pinned audit. No success claimed for74 cases.

## D-046 — approved Codebase-only timestamp mapping and one retry (2026-10-05)

Kunal explicitly approved UTC+08:00 mapping and one retry in answer to the
important timestamp question. This updates Task4's setup sample interpretation
only, not source/native values, gold SQL, benchmark rules or runtime behavior.
Decision: native_sample_value receives fixed db_id; naive Codebase DATETIME
usesUTC+08 then convertsUTC; every other dataset remainsUTC. Explicit aware
offsets are honored, never double shifted. verify_sqlite_samples passes fixed
db_id and importer reports the dataset-specific policy. Five new tests first
failed (four missing db_id interface, one real fixture consumer mismatch), then
63loader/bundle/California checks passed/22unconfigured skips(0.70s). Thirty-seven
total importer checks now exist. No new dependency or inference path.
Task4 remains incomplete until the single approved retry and European import,
all-new actual matrix and fresh full suite pass. Preserve earlier eight; use
remaining original3600s attempt envelope, per-dataset900s/120s bounds unchanged.
Partial evidence is historical pre-retry snapshot; pending-policy text predates
this owner answer. Complete final manifest will supersede its status.
Regression: installed-target full1085passed/77deselected(36.25s); three new
pure cases also match the pending-ID filter and were verified separately in
the63-control run above. No-env705passed/457skipped(7.91s),
format42/lint/whitespace pass.

## D-047 — remaining native imports accepted (2026-10-08)

The original aggregate clock expired across the 2026-10-05 to 2026-10-08 pause.
Kunal explicitly approved one new3600s bounded continuation window for only the
already-approved Codebase retry, European import and verification. Per-dataset
900s transaction/120s command bounds remained unchanged. Docker Desktop and the
existing named PostgreSQL volume were restarted; no database reset occurred.

An initial operator command used the display shorthand `codebase`; argparse
rejected it before connecting. Read-only checks then confirmed the exact fixed
targets `codebase_community` and `european_football_2` were absent. This local
argument error was not the one real database retry and made no write. The one
actual Codebase retry succeeded:8tables/71columns/740646rows/8PKs/24 samples,
with the approved sample-onlyUTC+08→UTC mapping. European then succeeded:
7tables/199columns/222796rows/7PKs/21 samples. Its source FK remains explicit
schema_mismatch with null count; no zero/validity claim or constraint repair.

All ten new datasets total72tables/709columns/3868173rows/69 enforced PK tables.
Complete typed native multisets and216 representative immutable SQLite samples
matched before per-dataset commits. No new foreign keys were installed. Actual
release matrix292passed/zero skips(15.39s), including90 ordered new-reader pairs.
Fresh no-env705passed/457expected skips(8.64s); configured1162passed/zero skips
(29.86s); locked27 packages, Ruff lint/42-file format and whitespace pass.
The complete compact manifest fingerprints the ignored full metadata evidence.

Decision: Task4 implementation is accepted, but G0.5/C1 remain unfinished.
These checks prove preserved native content, representative adaptations and the
tested local restricted-role boundaries; they do not prove full SQLite query
equivalence, gold conversion validity, description/label meaning or benchmark
accuracy. No inference, source/gold mutation, runtime credential use, dependency,
remote/push or publication action occurred. One fresh whole-batch review remains.

## D-048 — remaining native imports final review (2026-10-08)

One fresh read-only reviewer inspected09dedd2..db784fc without changing HEAD,
the checkout or database. It independently passed80 real PostgreSQL checks and
19 pure DDL/value/timestamp checks, recaptured metadata matching all10 datasets/
72tables, reconciled manifest totals/fingerprints and passed range whitespace.
It did not repeat the already fresh1162-test full run. No Critical or Important
finding. One Minor: the already-approved import artifact/credentials/FK-policy
checklist entry remained unchecked. Correct it in this final handoff; no code or
behavior change and no automatic second review.

Reviewer set-aside rulings, in order:

- Full SQLite/gold equivalence, gold timestamp meaning and description/label choices: retain the explicit next G0.5/C1 checkpoint — cost if wrong: converted official questions could be scored on an invalid meaning or denominator.
- Runtime dataset routing, exhaustive function/attack coverage, tenant RLS, model evaluation and publication: keep outside this setup-import batch and at their existing gates — cost if wrong: later runtime or release claims could exceed the tested boundary.
- Concurrent administrator replacement of pinned inputs: retain the trusted immutable local-source assumption — cost if wrong: privileged local tampering could invalidate checks between fingerprinting and use.
- OS-hard deadlines and hard RAM guarantees: retain documented cooperative setup limits and unchanged Docker caps — cost if wrong: a blocked system call or driver allocation could outlive the cooperative budget.
- Crash-durable credential/report recovery and automatic import resumption: retain exclusive fail-stop operation and manual reconciliation — cost if wrong: interruption could require operator inspection instead of automatic safe continuation.
- Earlier executor cancellation flakiness root cause: retain the unknown-cause record, sanitized phase label and unchanged deadlines — cost if wrong: the timing failure may recur and still require separate diagnosis.

Decision: accept the four-task batch locally and keep feat/foundation without
merge, remote or push. G0 remains7/12; next is a separately reviewed gold/
description/conversion/C1 increment, not a repeat import or benchmark score.

## D-049 — C1 threshold reached below default; owner choice required (2026-10-08)

The fixed cross-dialect validator completed all three candidate comparisons under
the precommitted exact typed multiset and resource limits. Full correction survival
is365/498 aligned IDs (73.29%), below the95% automatic-selection threshold. The133
aligned nonmatches are75 undefined objects after transpilation,1 data error,3 other
database errors,2 timeouts and52 exact result mismatches; IDs119/120 are absent.
Original proposed PostgreSQL labels match439/500 (87.80%); SQL-only corrections
match378/498 (75.90%). Evidence is ignored, contains no SQL/results/questions/
credentials and hashes to8cb8fcf92dcb0096af629f703ce61371803d53b17c44fcaa07cef2270e5ca4d3.

Decision intentionally open: the active spec forbids silently selecting corrected
labels below95%. Owner must choose among (A) a conservative365-item corrected-only
verified pool, (B) the439-item verified original pool with corrections retained as
research candidates, or (C) a separate manual/adaptation review of the133 corrected
failures before C1. Cost of A: smaller, correction-biased pool. Cost of B: loses
corrected-SQL improvements as primary labels. Cost of C: delays G0 and adds human/
methodology work but may recover corrected coverage. No split, ambiguity-positive
claim, primary description/label policy or E0 run is permitted until this closes.

## D-050 — deterministic corrected-label recovery cannot reach 95% (2026-10-08)

Kunal chose the D-049 review/recovery route. Reviewed native identifier mapping and
explicit SQLite date/numeric/aggregate/string conversions were implemented test-first.
They recover 59 additional exact matches: full correction is now 424/498 (85.14%).
Remaining aligned outcomes are 58 exact mismatches, 8 undefined objects, 4 other
database errors, 2 data errors and 2 timeouts. No source/gold query/result changed;
no tolerance, rounding or denominator filtering was added. Recovery evidence hashes
to `280b1dde0a08a9add7a42ebdb017db5dc43469804756615e10ffb1a0772a4780`.

The automatic 95% route requires 473 matches. Repairing every remaining execution
failure and timeout could reach at most 442/498 (88.76%); 23 mismatches match only
under six-decimal diagnostic rounding, which the frozen lossless rule forbids.
Therefore continued syntax repair cannot close C1. Decision remains an actual owner
option: use 424 verified corrected items for correction fidelity, use 439 verified
originals for larger coverage, or explicitly change methodology. Recommend the 424
corrected pool because it preserves the selected correction source without weakening
evidence; cost: 15 fewer usable items and a potentially conversion-easier subset.

## D-051 — Arctic second local model accepted for E0 (2026-10-08)

The approved pinned Arctic Q4_K_M was acquired from community revision8e1a5118 and
hashes exactly to9c005244e3ab7fada2c53a9511999f4d22fbbd4f76a4416416a6d41d82702255
at4,683,074,144 bytes. Official upstream revision is2d73faca, Apache-2.0. The fixed
context8192 alias digest is d4e34b35065d29da2566b3b201d9e6bd54d005c565e1e182a9e318086168b19d.

Decision: accept Arctic as E0's second text-to-SQL candidate. Two exact repeated
synthetic calls produced parseable SQL and matching hashes; a four-token request
stopped at its cap. Only one model loaded, reported usage/context, and was unloaded.
No gold/database/credential input or SQL execution occurred. Do not use Arctic as
the general helper: its official card excludes general non-SQL use. C2 remains based
on measured E0; this smoke does not select a winner or claim benchmark accuracy.

## D-052 — fixed restricted dataset executor routing for E0 (2026-10-08)

The early executor was intentionally California-only. For E0, generated candidates
must run against any loaded release dataset without giving a caller or model a way
to choose database roles, schemas or credentials directly.

Decision: keep one immutable trusted dataset-policy map for the 11 loaded release
databases, and let the server derive `warden_sandbox_<db_id>` plus `pg_catalog,
<db_id>` from that fixed map. `open_dataset_executor(db_id, password)` rejects
unknown IDs before creating a pool; `dataset_password_key` maps only fixed IDs to
the expected private env key names. The existing `open_california_executor` remains
as a compatibility wrapper.

Rationale: E0 needs multi-dataset execution, but the security boundary remains
dataset-specific restricted logins and guard policies, not a broad login or a
client-supplied role. This is executor routing only; it does not select C1 labels,
freeze a split, run model evaluation, add runtime dataset credentials or weaken the
SQL guard.

Verification: new tests first failed on missing fixed policies and credential
mapping, then passed. Pure guard/executor/comparator checks: 355 passed. Actual
executor plus release PostgreSQL checks: 321 passed. Full no-env suite: 746 passed,
470 skipped. Full configured suite with setup, California and dataset envs: 1214
passed, 2 skipped. Ruff lint and format passed.

Cost if wrong: an incorrect fixed table list or role derivation could false-block a
valid local E0 query or misroute it to the wrong restricted login; the real identity
tests reduce that risk but do not replace the broader G2 security audit.

## D-053 — C1 uses the verified corrected pool (2026-10-08)

Kunal answered the C1 pool choice with “GO WITH CORRECTED ONCE.” This selects the
verified corrected track despite the precommitted automatic 95% line not being
reached. The tracked manifest is `docs/gold-validity-manifest.json`, generated
from ignored evidence SHA-256
`280b1dde0a08a9add7a42ebdb017db5dc43469804756615e10ffb1a0772a4780`.

Decision: use the 424 exact verified corrected items as the primary local
PostgreSQL-adapted gold pool. Corrected descriptions are primary; original
descriptions remain alternate/reference material. Matched IDs with literal
question/evidence text differences become ambiguity candidates, and matched IDs
with unchanged text become negative controls. This is a data/evaluation input
decision only: it does not change source SQL, gold results, rounding, tolerance,
lossless comparator rules, generated-SQL guard policy or database permissions.

Rationale: the corrected pool preserves the reviewed correction source and avoids
silently changing the scoring method after measurement. Cost: it is 15 items
smaller than the verified original pool and may be an easier or different subset;
therefore future E0 numbers must report this 424-item denominator and cannot be
presented as an official BIRD Mini-Dev leaderboard score.

Verification: manifest generation is test-covered and records only compact IDs,
database IDs, difficulty labels, candidate-control labels, counts, rates and
evidence fingerprints. It contains no raw question prose, SQL, result cells or
credentials. Split freezing, E0 and C2 remain separate steps.

## D-054 — E0 uses a deterministic 100-item development split (2026-10-08)

Task 3 freezes the first local evaluation protocol in `docs/e0-protocol.json`.
It derives from the C1 corrected manifest and uses seed `20261008`.

Decision: use 100 C1 items as the development slice and keep the remaining 324
as held-out. The splitter is deterministic, groups items by `family_id` if a
future manifest provides one and otherwise treats each question ID as its own
family, and allocates development items approximately by database/difficulty
strata. Bootstrap accuracy intervals use a seeded percentile method with explicit
empty/all-correct/all-wrong edge behavior.

Rationale: E0 needs enough local items to compare Qwen and Arctic speed/quality
without consuming the whole 424-item pool. A fixed seed and hashes make later
results reproducible. Cost: a 100-item development slice is still a local,
adapted subset; it is not an official leaderboard and may not represent every
database/difficulty perfectly.

Verification: new protocol tests first failed because the module did not exist,
then passed. The tracked protocol manifest stores IDs, stratum counts, hashes and
metric settings only. It contains no prompt text, SQL, answer payloads or secret
values. E0 itself has not been run.

## D-055 — E0 measured Arctic ahead on the local development slice (2026-10-09)

Task 6 ran the frozen 100 development IDs from `docs/e0-protocol.json` for Qwen and
Arctic, one model at a time, with guard and restricted PostgreSQL execution enabled.
The compact tracked result is `results/E0_smoke/summary.json`; raw per-item records
remain ignored under `results/E0_smoke/raw/`.

Observed local EX was later corrected by D-058 after the final review found the
first implementation had used the stricter duplicate-preserving conversion
comparator instead of the pinned EX set comparator. The current tracked summary is
the D-058 clean rebuild, not the numbers below.

Initial local EX:

- Arctic Text2SQL Q4_K_M ctx8192: 20/100 correct, EX 0.20, seeded 95% bootstrap
  interval 0.13–0.28, median 1.247s, p95 2.556s, peak VRAM 5,133,943,438 bytes.
- Qwen2.5-Coder Q4_K_M ctx2048: 3/100 correct, EX 0.03, seeded 95% bootstrap
  interval 0.00–0.07, median 1.2595s for completed calls, p95 1.514s, peak VRAM
  4,628,519,320 bytes.

Qwen failed generation before a model call on 86/100 items with `prompt_budget`,
because the required full-schema prompt plus 1024 reserved output tokens exceeded
its ctx2048 alias. Arctic had 20 exact matches, 43 result mismatches, 14 guard
blocks, 12 execution failures and 11 generation failures. No hidden retries,
repair, retrieval, voting, clarification or held-out tuning were used.

Decision: record E0 as development evidence for C2; do not claim official benchmark
accuracy. The next C2 step should use these measured results to choose the retained
model/helper strategy. Cost if wrong: a different context setting or prompt strategy
could improve Qwen later, but changing that now would be a new measured experiment
rather than this frozen E0.

## D-056 — C2 keeps Arctic for full-schema SQL generation (2026-10-09)

Context: corrected E0 ran both local models on the same frozen 100 development IDs
with full schema prompts, guard enabled and restricted PostgreSQL execution. Arctic
scored22/100 EX after the D-058 comparator/provenance fix and clean rebuild. Qwen
scored3/100 EX and failed86 items before any model call because the frozen
full-schema prompt plus reserved output did not fit its ctx2048 alias.

Decision: retain Arctic Text2SQL Q4_K_M ctx8192 as the local full-schema
SQL-generation model for the next G1 work. Keep the development slice at 100 IDs
and the held-out split at 324 untouched IDs. Do not tune from held-out results.
Keep Qwen available only for the already-tested safe local CLI/helper path and
future explicitly measured experiments; do not use Arctic as a general helper
because its model card is SQL-specific.

Rationale: Arctic is the only measured model that completed the frozen full-schema
E0 contract on most items and produced materially better exact-match results.
Changing Qwen's context or prompt now would be a new experiment, not the frozen E0
decision. Cost if wrong: a larger Qwen context or retrieval-first prompt might help
later, but that belongs behind a new measured C3/G1 decision.

Verification: C2 is based on tracked `results/E0_smoke/summary.json`, rebuilt from
ignored raw records produced at clean commit390c145 with `git_dirty=false`, and
the committed E0 protocol. No held-out inference, hosted inference, prompt change,
gold mutation, remote push or publication occurred.

## D-057 — G1.1 starts with a local provider/cache contract (2026-10-09)

Context: the active spec requires provider identity, bounded retries/timeouts,
usage accounting and a sample-safe response cache before the broader agent loop.

Decision: add a small stdlib-only provider/cache slice. `ProviderRequest` records
local-only Ollama URL, model/revision/digest/template, messages, params, seed and
zero hidden retries. `ProviderOutcome` records status, content hash, usage counters,
provider-call count and cache-hit status without inventing missing usage as zero.
`JsonDiskCache` uses a complete replay key, atomic create-only writes, exact replay
validation and refusal of corruption, symlink paths, oversize payloads, secrets and
gold-answer fields. Existing `LocalQwen` reuses the shared local provider config
without changing the public safe CLI behavior.

Rationale: this is enough for exact local replay later without adding dependencies,
hosted configuration or a second runtime abstraction. Cost if wrong: the first
cache is deliberately conservative and may refuse payloads that are safe but not yet
needed; loosening it later requires tests and a recorded reason.

Verification: provider/cache tests were written before the implementation and first
failed on missing modules/outcome types. Initial focused provider/cache/LLM/CLI
checks passed117 with1 expected Windows symlink skip; after D-058 review fixes,
focused review-fix tests passed57 with2 expected skips, full no-env suite passed783
with471 expected skips, and full configured PostgreSQL suite passed1251 with3
expected skips. Ruff lint, format check and diff whitespace passed. No prompt text,
generated SQL, gold SQL, result rows, credentials, model weights, raw runs, remote
or publication artifact was committed.

## D-058 — final finish-G0/G1.1 review fixes E0 evidence contracts (2026-10-09)

One fresh read-only reviewer inspected the complete finish-G0/start-G1 range
`6370ec3..0edae7c`. It made no filesystem, Git, database, import or live-inference
changes. It found no Critical issue. It found eight Important issues:

1. E0 used duplicate-preserving conversion comparison instead of the pinned EX row-set comparator.
2. Scored raw records lacked prediction/provenance needed for safe resume and rescoring.
3. E0 lacked explicit absolute generation/total-item deadlines and safe failure cleanup.
4. Invalid model output dropped real usage/latency measurements.
5. Full-schema prompts silently truncated selected descriptions.
6. Decimal canonicalization used context-dependent normalization and could collapse distinct values.
7. Cache reads and symlink/corruption refusal had boundary gaps.
8. Gold validation lacked the approved 30-minute per-track cap.

Decision: fix every Critical/Important item test-first before treating G0/C2 as
complete. Preserve the original raw E0 records as ignored legacy evidence instead
of overwriting them silently. Rebuild E0 after the fixes from a clean commit, with
raw records carrying git commit and dirty-state provenance. Defer only the three
Minor findings: protocol/runner bootstrap-sample mismatch is fixed now because it
was one-line and relevant; cache concurrent-writer no-clobber and stronger
secret/gold semantic detection remain later hardening, with the current cache
documented as a conservative local single-user slice.

Rulings on set-aside review areas:

- Retrieval, repair, voting, clarification and hosted inference stay outside G1.1.
- Wider function/operator attacks and tenant RLS stay in G2.
- Qwen context expansion or alternate prompting is a future measured experiment,
not a repair to frozen E0.
- Semantic ambiguity review is still not claimed; literal text differences remain candidates only.
- Concurrent privileged replacement of pinned inputs stays outside the trusted local-source workflow.
- Distributed cache and crash-durable recovery stay outside the current local slice.

Verification: fixes landed in `dbd267c` and `390c145`. Regression tests first failed
for the reviewed gaps, then passed: focused review-fix suite57passed/2expected
skips; no-env full suite783passed/471expected skips; configured full suite
1251passed/3expected skips; Ruff lint, format and diff whitespace passed. A clean
local E0 rebuild then produced `results/E0_smoke/summary.json`: Arctic22/100 EX
(CI0.14–0.30, median1.2865s, p952.235s, peakVRAM5133943438) and Qwen3/100 EX
(CI0.00–0.07, median1.356s, p951.608s, peakVRAM4628519320). Each model has100
ignored raw records with `git_commit=390c1454619a849ab80d798bde41c82440f7b34a`
and `git_dirty=false`; Ollama reported no loaded models after the run. No held-out
inference, hosted call, source/gold mutation, remote, push or publication occurred.

## D-059 — G1/C3 uses measured lexical retrieval and a small local loop (2026-10-09)

Context: G1 needs schema retrieval, prompts, repair, voting, clarification,
explanation and CLI loop settings before broader guardrail/evaluation work. The
project already has full schema metadata, corrected descriptions and a frozen
100-item development split, but no approved embeddings service or hosted helper.

Decision: implement G1 with a stdlib BM25-style lexical retriever over table/column
names and descriptions, plus bounded untrusted sample serialization. C3 selects
24 retrieved columns because the read-only dev-split measurement gave mean table
recall0.968333/full-table recall0.93, while 32 columns only improved to
0.971667/0.94 and costs more prompt space. Use n=3 candidates and k=1 repair for
the first loop. Do not add a general helper model to the core loop yet; keep
clarification and explanation as bounded helper seams covered by fake-LLM tests
until a local helper is separately measured.

Rationale: this satisfies the local G1 loop without a new dependency, hosted call
or held-out tuning. Top24 is a better prompt-budget trade-off than top32 for the
first measured agent. Cost if wrong: lexical retrieval can miss semantic aliases;
G3 can add a measured hybrid/embedding retriever later if it beats this baseline
without weakening security or budget accounting.

Verification: focused G1/CLI/LLM tests118passed after review fixes. Full no-env
suite795passed/471skipped and configured PostgreSQL suite1263passed/3skipped.
Ruff lint, format and diff whitespace passed. The measurement summary is
`results/G1_retrieval/summary.json`. No live model call, hosted inference,
credential change, source/gold mutation, raw run, remote or push occurred in this
slice.

## D-060 — C4 records explicit guardrail contract and tenant boundary design (2026-10-09)

Context: G2 starts the broader guardrails/sandbox group. The existing guard already
blocks unreviewed functions, qualified function calls, dangerous casts and
cross-schema relations, and the executor already has finite row/byte/time/cost
limits. C4 needs these choices made explicit before expanding attack coverage and
tenant RLS.

Decision: add `src/sqlwarden/security_contract.py` as the single local record for
reviewed SQL function classes, allowed scalar cast types, default query limits and
the future tenant-boundary design. The runtime guard derives its function and cast
allowlists from this contract. The default limits remain: 1000 rows, 2 MiB result,
64 KiB cell, 5 s statement timeout, 500 ms lock timeout, 5 s pool timeout, 15 s
total timeout, estimated cost cap100000 and estimated row cap100000. For tenant
isolation, G2.6 will use server-chosen role-specific database identities with
forced RLS policies; a client-supplied tenant id or mutable `app.tenant_id` setting
alone is rejected as an independent boundary.

Rationale: this makes the security policy auditable without adding dependencies or
claiming a broader sandbox than the current code has proven. Cost if wrong: the
explicit contract may be conservative and block benign queries until later review,
but that is safer than accidentally expanding SQL capability.

Verification: `tests/test_security_contract.py` first failed because the contract
module did not exist. After the minimal implementation, focused
`tests/test_security_contract.py tests/test_guard.py tests/test_executor.py`
passed298 and the full no-env suite passed798/471skipped. Ruff lint, format and
diff whitespace passed. No database object change, credential change, source/gold
mutation, live model call, hosted action, raw run, remote or push occurred.

## D-061 — G2.2 records guard coverage and safe-gold guard acceptance (2026-10-09)

Context: G2.2 requires at least 40 meaningful guard cases and a safe-gold acceptance
audit. Existing guard tests already exercise many safe/unsafe SQL boundaries, but
the count and corrected-gold guard acceptance had not been recorded in one compact
artifact.

Decision: add `scripts/audit_guard_gold.py` and
`docs/guard-gold-audit-manifest.json`. The script counts guard-case strings from
the existing guard test module and audits all 424 usable corrected gold items by
transpiling their corrected SQL and applying the pure guard. The tracked manifest
stores only counts by status, database and reason; it excludes SQL text, question
text, rows, credentials and prompts.

Result: the guard corpus contains 148 counted cases: 46 safe, 40 unsafe and 62
other guard-boundary cases. The corrected usable pool has 368 guard-accepted items
and 56 guard-blocked items. All 56 blocked items are `function_not_allowed`, so
future guard expansion can review those functions deliberately. This does not
change benchmark labels, gold SQL, execution scoring or guard policy.

Rationale: compact counts are enough to drive G2 work without committing sensitive
or benchmark-answer material. Cost if wrong: counting test strings is a coverage
proxy, not proof that every SQL attack is covered; G2.8 still owns the explicit
attack suite with threat-specific success predicates.

Verification: `tests/test_guard_audit.py` first failed because the audit script did
not exist. After implementation, focused guard/audit tests passed198 and the full
no-env suite passed800/471skipped. Ruff lint, format and diff whitespace passed.
The script regenerated `docs/guard-gold-audit-manifest.json`. No database
connection, SQL execution, credential change, source/gold mutation, live model
call, hosted action, raw run, remote or push occurred.

## D-062 — G2.3 records stable executor error categories (2026-10-09)

Context: the executor already enforces finite pool/statement/lock/total deadlines,
row/result/cell caps, guarded EXPLAIN cost checks, cancellation propagation, pool
recovery and sanitized error categories. G2.3 needs those categories explicit so
later API/UI and repair prompts do not depend on raw driver errors.

Decision: add `EXECUTOR_REASON_STATUS` to `src/sqlwarden/security_contract.py`.
The map documents every stable reason currently exposed by the guard/executor and
assigns it to one terminal status class: `ok`, `blocked`, `failed` or `overflow`.
This records the existing behavior rather than broadening SQL capability.

Rationale: a single audited reason map makes it harder for future code to leak raw
database/library details or invent new error strings accidentally. Cost if wrong:
the map may need updates when G2.4/G2.8 add new deliberate categories, but tests
will force that change to be explicit.

Verification: the new focused test first failed because `EXECUTOR_REASON_STATUS`
did not exist. After adding the map, `tests/test_security_contract.py` and
`tests/test_executor.py` passed103 and the full no-env suite passed801/471skipped.
Ruff lint, format and diff whitespace passed. No database object change,
credential change, SQL execution, source/gold mutation, live model call, hosted
action, raw run, remote or push occurred.

## D-063 — G2.4 records guarded EXPLAIN calibration evidence (2026-10-09)

Context: the executor already guards SQL before planning, runs
`EXPLAIN (FORMAT JSON)` under the same restricted identity/settings as execution,
and blocks excessive estimated cost or rows before preparing/cursoring a statement.
G2.4 needs that policy recorded and checked with real PostgreSQL evidence.

Decision: add `docs/executor-cost-calibration-manifest.json`. It records the
default thresholds: estimated cost cap100000, estimated row cap100000, 5 s
statement timeout, 500 ms lock timeout and 15 s total timeout. It also records the
EXPLAIN policy: guard before EXPLAIN, JSON format only, never ANALYZE, and same
restricted identity/settings as execution.

Rationale: the manifest makes the threshold/policy explicit without changing the
runtime or benchmark. Cost if wrong: estimates are not perfect and can miss
expensive work, so G2 keeps runtime deadlines and cancellation recovery as required
backstops.

Verification: the manifest test first failed because the file did not exist. After
adding it, focused manifest/unit executor checks passed7. Real PostgreSQL checks
for cost/estimated-row gates and transaction-local settings passed2. Focused
security/executor tests passed104 and full no-env suite passed802/471skipped. Ruff
lint, format and diff whitespace passed. No credential change, source/gold
mutation, live model call, hosted action, raw run, remote or push occurred.

## D-064 — G2.5 records effective grant and default-grant evidence (2026-10-09)

Context: the release PostgreSQL tests already connect directly as each restricted
dataset reader and bypass the SQL guard. G2.5 needs that effective-permission and
future-default-grant evidence named in one compact artifact before stronger
sandbox claims are made.

Decision: add `docs/grants-permission-manifest.json`. It records only fixed test
names and protection labels for all 11 restricted dataset logins: role flags,
memberships/inheritance, default read-only setting, search path, risky function
ACLs, denial of write/DDL/temp/app/peer/SET ROLE operations and dataset-specific
future SELECT-only grants.

Rationale: no database policy change is needed because the real tests already
exercise the boundary. The manifest makes the evidence easy to audit without
copying credentials, SQL rows, question text, prompts or raw run output. Cost if
wrong: the manifest can drift from the actual test names, so the contract test
checks the names and exclusions explicitly.

Verification: the manifest test first failed because the file did not exist. After
adding it, focused security-contract tests passed 6 and the real G2.5 PostgreSQL
permission checks passed 210 with `.env.setup`, `.env.california` and
`.env.datasets`. Full no-env suite passed 803/471 skipped. Ruff lint, format and
diff whitespace passed. No database object change, credential change, source/gold
mutation, live model call, hosted action, raw run, remote or push occurred.

## D-065 — G2.6 uses database roles, not mutable settings, for tenant RLS (2026-10-09)

Context: BUILD_SPEC prefers two isolated tenant logins with role-specific forced
RLS policies and rejects `current_setting('app.tenant_id')` as the sole boundary
for arbitrary SQL. The earlier demo had dataset roles but no tenant RLS fixture.

Decision: add a small `tenant_demo` schema to bootstrap with
`warden_sandbox_tenant_demo_a` and `warden_sandbox_tenant_demo_b`. Both are
restricted LOGIN roles with no privileged flags, no inheritance and no BYPASSRLS.
The shared `tenant_demo.orders` table has row-level security enabled and forced,
with one SELECT policy per tenant role. The server/database role chooses the
tenant; a mutable `app.tenant_id` setting is ignored by the policy.

Rationale: role-specific policies keep the independent boundary inside
PostgreSQL instead of trusting model/user SQL or client-provided tenant IDs. Cost
if wrong: this proves only the small synthetic tenant fixture and its direct
boundary tests; wider tenant-aware runtime routing remains later work.

Verification: the setup test first failed on missing tenant password keys. After
adding tracked setup/bootstrap support and updating ignored local env files plus
the existing local PostgreSQL volume, the setup test passed 1 and real tenant RLS
tests passed 4. Focused setup/synthetic-boundary tests passed 51/2 skipped and
full configured suite passed 1275/3 skipped. Ruff lint, format and diff whitespace
passed. No source/gold mutation, benchmark change, model call, hosted action, raw
run, remote or push occurred.

## D-066 — G2.7 bounds and escapes explanation data paths (2026-10-09)

Context: G1 had separate prompt builders and an explanation seam, but G2.7 needs
explicit untrusted-data and benign-control evidence. Schema samples and result
values can contain instruction-like text, so the safety boundary must be code and
database controls, not prompt wording alone.

Decision: keep schema samples labelled as untrusted and add regression coverage
that a poisoned sample cannot cause unsafe SQL execution. Add a bounded
`result_preview` to explanation prompts: at most three rows, each cell truncated
to 120 UTF-8 bytes, with row count and truncation metadata. Mark the preview as
untrusted data and escape returned explanation text as plain text before exposing
it from the agent.

Rationale: explanations need enough data to be useful without gaining an
execution path or a large/raw result channel. Cost if wrong: result previews may
be too small for some friendly explanations, but the full answer table remains in
the structured result and UI preview work can make a separate display choice.

Verification: focused tests first failed because explanation prompts had no row
preview and returned text was not escaped. After adding the preview and escaping,
the three G2.7 focused tests passed. No database object change, credential change,
source/gold mutation, model call, hosted action, raw run, remote or push occurred.

## D-067 — G2.8 records attack evidence without running layer-off E5 (2026-10-09)

Context: G2.8 needs at least 40 attack cases with threat-specific predicates,
explicit observed blockers, false-block evidence and safe handling of layer-off
experiments. Existing guard and agent tests already contain deterministic attack
fixtures, but they were not organized as an attack-suite artifact.

Decision: add `scripts/audit_attack_suite.py` and
`docs/attack-suite-manifest.json`. The manifest records 40 deterministic SQL
attack fixtures from `tests/test_guard.py::UNSAFE` and three model-mediated
fake-LLM controls from prompt/agent tests. It keeps fixture references and
metadata only. Layer-off E5 is not executed in this slice; the saved policy
requires a local disposable Docker project/volume and rejects hosted targets.

Rationale: this completes the documented all-layers-on attack evidence without
creating a destructive layer-off harness in the real project volume. Cost if
wrong: the manifest relies on fixture references rather than duplicating raw SQL,
so reviewers must inspect the named tests to see exact payload text.

Verification: tests first failed because the audit module/manifest did not exist.
After adding them and fixing direct script import behavior, G2.8 manifest tests
passed 3. Focused attack/guard/prompt tests passed 210. Full no-env suite passed
809/475 skipped. Ruff lint, format and diff whitespace passed. No database object
change, credential change, source/gold mutation, model call, hosted action, raw
run, remote or push occurred.

## D-068 — G2.9 documents current security evidence and residual limits (2026-10-09)

Context: G2.9 requires SECURITY documentation with evidence and limitations. The
repo had no existing root `SECURITY.md`; the Codex Security resolver inventory
returned an empty policy list before this slice.

Decision: add root `SECURITY.md` covering local-only system scope, trust
boundaries, attacker-controlled inputs, security invariants, evidence artifacts,
reportable finding criteria and known limitations. It points to the G2 evidence
manifests instead of duplicating secrets, raw SQL, prompts or result rows.

Rationale: security claims should be reviewable and bounded. The policy states
what has evidence and what remains residual risk, avoiding universal safety or
hosted-production claims. Cost if wrong: future reviewers may need to update this
policy when API/web/hosting work changes the actual exposure.

Verification: the SECURITY policy test first failed because `SECURITY.md` did not
exist. After adding it, the test passed 1 and the Codex Security resolver listed
and resolved the root policy. Final focused policy/security tests passed 10. Full
no-env suite passed 810/475 skipped. Full configured suite passed 1282/3 skipped.
Ruff lint, format and diff whitespace passed. No database object change,
credential change, source/gold mutation, model call, hosted action, raw run,
remote or push occurred.

## D-069 — G2 interview drill is recorded as a self-study artifact (2026-10-09)

Context: the only remaining G2 checklist item after G2.9 was the interview drill.
Kunal's current goal is to complete G2 completely, and earlier project rules allow
interview drills to be offered or skipped without changing implementation scope.

Decision: record the G2 interview drill in the simple-English notebook with
portfolio-style questions and sample answers instead of blocking on live oral
answers. This marks the G2 drill complete as a study artifact, not as proof that
Kunal personally rehearsed it aloud.

Rationale: the saved drill is the durable artifact Kunal can study/rehearse from,
and it avoids stopping the build on an optional conversational checkpoint. Cost if
wrong: Kunal may still want a live practice round later, but the G2 implementation
and written interview material are complete.

## D-070 — G3.1 adds E0 manifests and JSONL without migrating raw runs (2026-10-10)

Context: G3.1 requires fingerprinted E0 config/metadata, durable JSONL and safe
resume. The runner already had ignored per-question raw JSON records with
provenance checks, and the corrected E0 summary was already tracked.

Decision: keep the existing per-question raw JSON format and add two ignored
sidecar files for future runs: `manifest.json` for the protocol/model/git
fingerprint and `records.jsonl` for durable append-only records. Resume validates
the manifest when present, prefers valid JSONL records, tolerates only an
interrupted final JSONL line and falls back to legacy per-question JSON records.
Do not migrate or rewrite the existing ignored raw E0 evidence.

Rationale: this gives future E0/E-series runs a safer checkpoint without changing
the already-recorded development-slice result or exposing raw prompts, SQL, rows
or credentials in tracked files. Cost if wrong: legacy raw runs without a manifest
still rely on the older per-record provenance validation until they are rerun.

Verification: tests first covered JSONL truncation/corruption, manifest mismatch
and no-resume overwrite refusal. Final focused E0/evaluation tests passed 21.
Full offline tests passed 814/475 skipped. Ruff lint, format and diff whitespace
passed. No model call, database execution, raw run migration, benchmark score
change, remote or push occurred.

## D-071 — G3 freezes compact local evaluation evidence, not a public benchmark (2026-10-10)

Context: after G3.1, the remaining G3 checklist required phase metrics,
paired/statistical reporting, a C5 experiment matrix, failure labels, dashboard,
EVAL, README/resume evidence and an interview drill. Existing corrected E0 raw
records were available locally under ignored paths.

Decision: rebuild compact tracked evaluation artifacts from existing ignored E0
records without rerunning models or databases. `results/E0_smoke/summary.json`
now includes coverage, parse/guard/execution/EX phase metrics, answered-only EX,
boundary intervals and paired Arctic-vs-Qwen statistics. Add
`results/E0_smoke/dashboard.json`, `results/E0_smoke/failure-labels.json`,
`docs/evaluation-matrix.json`, `docs/EVAL.md` and `docs/RESUME.md`. Freeze E1-E4
and E6-E8 in the matrix with the approved 15-20 hour weekly budget. Keep E5 tied
to G2 security evidence and layer-off approval gates; keep E9 optional.

Rationale: G3 needs a defensible local evidence package and next-experiment
matrix, not a fresh inference run or public claim. Cost if wrong: phase labels
may need refinement before publication, but raw prompts, generated SQL, gold SQL,
rows and credentials remain excluded from tracked artifacts.

Verification: tests first failed for missing phase metrics, paired summary,
failure labels and resume generation. Final focused evaluation/artifact tests
passed 25. Full offline tests passed 818/475 skipped. Ruff lint, format and diff
whitespace passed. No model call, database execution, held-out evaluation,
benchmark-policy change, remote or push occurred.

## D-072 — G4 starts with dependency-free API/web core before FastAPI/Vite install (2026-10-10)

Context: G4 requires a tested run API/SSE/protections and three web pages. The
active stack names FastAPI, React, Vite and Recharts, but AGENTS.md requires
asking before adding direct dependencies. Kunal asked to proceed with G4.

Decision: implement a dependency-free local G4 core first instead of modifying
`pyproject.toml` or adding Node dependencies. Add `sqlwarden.api` with run IDs,
hashed bearer capabilities, body/origin/db/rate/admission checks, SSE event
serialization/replay, cancellation and restart interruption behavior. Add static
local Ask, Attack Lab and Benchmark pages plus a scripted local smoke that uses a
fake answered run. Do not check off full G4.1/G4.2/G4.4/G4.5 until the real
FastAPI adapter/routes and frontend dependency decision are complete.

Rationale: this advances the security/lifecycle contract under test while
respecting the dependency-approval gate. Cost if wrong: some adapter-specific
FastAPI/SSE/CORS/browser issues remain untested until the dependency-backed
server is approved and implemented.

Verification: tests first failed because `sqlwarden.api` and static smoke files
did not exist. Focused G4 core/static tests passed 6 after implementation. Full
offline tests passed 824/475 skipped. Ruff lint, format and diff whitespace
passed. No new dependency, model call, database execution, hosted action, remote
or push occurred.

## D-073 — G4 web dependencies approved; FastAPI adapter contract (2026-10-11)

Context: D-072 held the FastAPI/Vite install for an explicit approval. A working
tree from the previous session already added them without a recorded decision.
On 2026-10-11 Kunal approved all remaining steps ("ok i approve all the steps").

Decision: approve the direct dependencies already named by BUILD_SPEC section 2:
Python `fastapi>=0.143,<1` and plain `uvicorn>=0.54,<1` (the `[standard]` extra was
dropped; it added uvloop/httptools/watchfiles/websockets/pyyaml/python-dotenv that
the local server does not need); web `react`/`react-dom` 18, `recharts` 3,
`typescript` 5, `vite` 8 and React 18 type packages, locked in
`web/package-lock.json`. Node 24.18 satisfies Vite 8's Node requirement.

Adapter contract: `POST /api/ask` returns 202 with `run_id` and a capability and
starts the run in the background. Every run route checks the bearer capability
before any work; unknown runs and wrong tokens are both 401. Request bodies are
read with a byte cap before JSON parsing and must be exactly `{db_id, question}`.
A wrong `Origin` is refused; a missing `Origin` is treated as a non-browser
client because browsers always send it on POST. Client IP comes from the direct
socket only; forwarded headers are not trusted because no proxy is configured.
Overload is 503 with `Retry-After`; rate limiting is 429 and the bucket table is
capped (fail closed when full). SSE polls in memory, sends a heartbeat comment,
honours `Last-Event-ID`, and ends on a terminal or `needs_clarification` event so
the client reconnects after replying. Clarification accepts one offered option ID
or 200-character free text, expires after 600 s, and refuses db/tenant/role keys.
Runs have a 300 s total timeout, 256 events, and retention of 500 runs or 1 hour.
The built frontend is served from `web/dist` only, never the source folder.

Run state stays in process memory for the single-process local demo. Shutdown
marks unfinished runs interrupted; a crash loses them and the client treats an
unknown run as interrupted and offers an explicit retry. Durable run state and
Postgres-backed budgets belong to an approved hosted configuration (G5/G7).

Rationale: these are the agreed stack packages; the adapter fixes the review
findings from 2026-10-11 (source folder served, status awaited before auth,
unbounded body read, replay-only events, unbounded clarification options).
Cost if wrong: in-memory state cannot survive a process crash, and a missing
Origin header is accepted from non-browser clients.

Verification: new core and adapter tests failed first, then passed 20.

## D-074 — Web runtime runs the real agent; Qwen clarifies, a template explains (2026-10-11)

Context: the FastAPI adapter had only a demo runner. G1 left clarification and
explanation as fake-LLM seams, and the CLI loop still used a 4-column toy schema.

Decision: `sqlwarden.runtime` runs `run_agent` per request with the shared
`sqlwarden.catalog` (tracked audit manifest plus local corrected descriptions),
the dataset's own restricted reader login and `OllamaAgentProvider`. Arctic
generates and repairs; Qwen is the clarification helper, with JSON mode and a
256-token output cap so it fits its 2048 context. The provider unloads the other
model before a call (one GPU model at a time) and records swap time, tokens and
VRAM. The local explanation is a factual template (row count, columns, vote
count), not a model, because Arctic's card limits it to SQL and a helper swap per
answer adds seconds without measured value. Every trace event streams live.
All candidates failing on a model outage ends `failed` with that reason instead of
asking a clarification; all candidates blocked ends `blocked`. The runtime reads
only `WARDEN_RUNTIME_<DB>_PASSWORD` keys from ignored `.env.web`, written by the
setup-only `scripts/prepare_web_runtime.py` from the existing restricted reader
credentials; any setup/test key refuses startup. The CLI `--loop` mode now uses the
same real catalog and provider. C6: the three pages (Ask, Attack Lab, Benchmark)
stay the scope, with plain CSS, light/dark themes, keyboard focus and a narrow-
screen layout; no further polish pass.

Rationale: the web demo must exercise the same guarded path the evaluation
measures. Cost if wrong: a template explanation is less fluent than a model, and a
clarification costs one model swap (measured in E6).

## D-075 — Inference contract v2 for the E1-E8 matrix (2026-10-11)

Context: the first live run showed the G1 JSON-document prompts make Arctic emit
placeholder SQL such as `SELECT '1' AS result`, and Qwen echo the input structure.
E0 had used a different plain prompt with JSON-only output and no BIRD evidence;
no evidence policy was ever recorded.

Measured calibration (dev IDs only, first 20 of the frozen 100, Arctic, temperature
0): E0 prompt 3/20; E0 prompt with evidence 4/20; the prompt structure from the
Arctic-Text2SQL-R1 paper (arXiv:2505.20315, Appendix C, engine set to PostgreSQL)
with evidence 10/20, at a median 11.1 s and 514 output tokens per call versus 1.7 s.
Three of its ten misses were guard false blocks (fixed by D-076) and one was an
unquoted mixed-case column.

Decision: freeze contract v2 before any E1-E8 run. Evidence policy: every
configuration receives the corrected BIRD evidence followed by the question, as
in the paper; the web Ask page has no evidence. Prompts `g1_*_v2` follow the
paper's structure in our own wording: reasoning in `<think>`, final query in a
```sql block, parsed from the last block. Generation is not JSON-constrained and
has a 3072-token output cap inside Arctic's 8192 context (the largest full schema,
european_football_2, is about 4.2k estimated tokens). The schema serializer now
writes identifiers as PostgreSQL must read them (quoted when mixed-case, spaced or
reserved). Clarification is plain text with a JSON-only answer. E0 stays as the
historical smoke under its old contract and is not rescored.

Rationale: matching the model's training format is the largest measured lever,
and evidence is part of the standard BIRD input, not a gold answer. Cost if wrong:
about seven times more generation time per call; the 20-item probe is small and
the matrix, not the probe, is the measurement.

## D-076 — Reviewed date, text and rank functions join the guard allowlist (2026-10-11)

Context: the G2 guard/gold audit found 56 of 424 safe gold queries blocked as
`function_not_allowed`. Counting the function classes in those 56 queries found
only `to_char`, `CAST AS TIMESTAMP`, `substring`/`substr`, `current_timestamp`/`now`,
`rank`, `dense_rank`, `extract`, `strpos` and `date`.

Decision: add these to the reviewed contract (and TIMESTAMP to reviewed casts).
`EXTRACT(field FROM x)` allows a bare field only in that slot and only for YEAR,
MONTH, DAY, HOUR, MINUTE, SECOND, DOW and QUARTER. Still refused and tested:
`timestamptz` casts, `pg_catalog.`-qualified calls, `date_trunc`, `clock_timestamp`
and unreviewed EXTRACT fields.

Evidence: the real PostgreSQL inventory test confirms each added signature is a
`pg_catalog` built-in in internal/C language, immutable or stable, not security
definer, and executable by the restricted reader (56 real checks pass). The
regenerated audit accepts 421 and blocks 3 of 424 gold queries (all
`unsupported_node`). All 43 attack outcomes are unchanged.

Rationale: these functions read only their arguments (or the clock); they cannot
touch files, the network, the session or other schemas. Cost if wrong: a future
overload of one of these names could behave differently; the inventory test pins
the exact signatures.

## D-077 — C7: static pages plus laptop demo; container and CI prepared (2026-10-11)

Context: G5 must verify free hosting from official sources and prepare packaging
without provisioning anything. Checked 2026-10-11 (sources in [DEPLOY](DEPLOY.md)):
Render Free (512 MB, sleeps after 15 min, ephemeral), Hugging Face (Docker Spaces
now need a paid plan), Neon Free (1 GB/project; Console-made roles get BYPASSRLS),
Render Postgres Free (expires after 30 days), Groq Free (about 1K requests/day per
model), GitHub Pages (free static, 1 GB).

Options: (a) static Benchmark/Attack Lab on GitHub Pages plus the local demo;
(b) Render + Neon + Groq live Ask; (c) no public demo.

Decision: recommend (a) for G7. Option (b) needs three accounts only Kunal can
create, a separate hosted-model check, TLS database connections, Postgres budgets and
durable runs, and accepts that managed Postgres forbids the function-hardening
revokes; it stays documented as an approval-gated follow-up. Packaging: multi-stage
non-root image, read-only app compose file with its own project name and no setup
credentials, runtime address keys validated (model URL limited to local Ollama
addresses, so inference stays local), and a read-only CI workflow with pinned action
SHAs whose disposable database job uses a separate compose project.

Rationale: (a) costs INR 0, sends no question text to a third party and shows the
measured evidence. Cost if wrong: visitors cannot try live questions without
running the laptop demo.

## D-078 — E8 threshold rule fixed before any held-out run (2026-10-11)

Context: E8 needs a development-selected default agreement threshold; BUILD_SPEC
forbids tuning on held-out outcomes.

Decision: with three candidates the agreement score takes 1/3, 2/3 or 1. On the
complete 100-question development run of the full loop, choose the threshold with
the highest accuracy-when-answering among thresholds whose coverage is at least
50%; ties go to the lower threshold; if none reaches 50%, use 1/3 (answer whenever
the vote answers). `scripts/build_matrix_report.py --freeze-threshold` writes
`docs/e8-threshold.json` once and refuses if any held-out record exists. The rule
was written and tested (`tests/test_matrix_report.py`) while the development run was
still in progress.

Rationale: a fixed rule with a coverage floor stops the threshold from trading away
almost all answers for a high but tiny-sample precision. Cost if wrong: another
rule could suit a different product need; the full curve is reported either way.

## D-079 — E1/E3/E7 scope for this local release (2026-10-11)

Context: BUILD_SPEC requires any smaller experiment scope to be recorded. GPU time
is about 11 s per generation call, so every held-out configuration costs hours.

Decision:

- Held-out runs: the full loop (retrieval, three candidates, one repair) and the
  full-schema single-candidate baseline. Single-candidate, repair-only and
  no-repair voting results are re-scored from the same recorded attempts (same
  inputs), not separate generations.
- E1/E3 label re-scoring uses every run; the separate original-wording run
  (an input change) is development-only.
- E4 messy names and E7 clarification are development-only.
- E7 uses the C1 literal text-difference candidates and clear negatives. The
  simulated reply is the corrected wording, so the result is labelled
  oracle-assisted. The roughly 50 self-authored ambiguity examples were not built;
  that subset and a non-oracle simulated user remain future work.
- E5 layer-off variants and E9 fine-tuning are not run in this release.

Rationale: keeps the primary claims (held-out loop versus baseline, threshold,
latency) on the full held-out set while staying inside about a day of laptop GPU
time. Cost if wrong: E4/E7 effects are measured on 100 development questions only
and have wide intervals.

## D-080 — E5 layer-off runs one layer at a time (2026-10-11)

Context: Kunal reversed D-079's two deferrals on 2026-10-11: the E5 layer-off
variants and the self-authored E7 set must run before any push. The written but
untested harness turned off two layers in two of its five configurations, scored
`SET ROLE` as success whenever the statement ran, and scored a query that ran past
the limit and then errored as prevented.

Decision: six configurations: all layers on, then exactly one of L3 SQL guard, L5
restricted role, L5 read-only transaction or L6 statement timeout off, plus an
all-off positive control (broad read/write login with file and program rights, no
superuser). With L6 off, a 6 s harness-only cap still ends runaway queries. Success
comes from observed state through a separate admin connection: data/canary
fingerprints, `current_user` after a role switch, elapsed time, and canary text in
returned rows. Local Docker endpoints only, one-time passwords, and cleanup limited
to project `sqlwarden_e5_disposable` and its volume.

Result (3b3ad20, `results/G3_matrix/e5-layer-off.json`): all layers on prevented
29 of 29 attacks (28 by the guard; the four-way cross join passes the guard and the
timeout stops it). One layer off let two through: `version()` with the guard off,
and the cross join with the timeout off. Role-off and read-only-off let none through,
because the guard stops each attack. The positive control succeeded on 28; `CREATE
EXTENSION dblink` still needs superuser.

Rationale: switching off one layer at a time is how the plan defines defense in
depth for E5. Cost if wrong: L1, L2, L4, L7 and L8 are not switched off here. The
real executor's L4 EXPLAIN cost check, which is not modelled, is the layer meant to
stop the cross join before execution.

## D-081 — E7/E6 runner rulings and the final matrix report (2026-10-12)

Context: completing the matrix exposed three runner gaps. A clear self-authored
question received a (false) clarification ask but clear items have no frozen
reply; the response cache refuses outputs containing secret or gold terms, so a
few answers cannot be replayed; and the stored re-scoring skipped records where a
candidate produced no SQL, which reported them as pending.

Decision:
- A false ask on a clear self-authored question is answered by restating the
  question as asked; ambiguous items still reply with their frozen intended meaning.
  Neither reply sees candidate SQL or results. The 33 records from the crashed run
  were set aside and all 50 items reran from clean commit 8efef91.
- Replay marks each question `fully_replayed`; E6 times only fully replayed questions
  and reports the rest (1 of 100 on development). The 10 records of the aborted
  replay were set aside and the replay reran from clean commit 4f7f990.
- The report re-derives a missing outcome from per-attempt result fingerprints with
  the vote rules, counting an SQL-less candidate as failed (5 records). Against stored
  outcomes the fallback agrees in 1,678 of 1,680 cases; the 2 differences are equal
  numbers written differently.
- Findings are reported as measured, including unfavourable ones: on held-out the
  full-schema single candidate beat the full loop end to end, and 56 of 58 dev
  repairs repeated the same failure. No prompt or loop setting was changed after
  seeing held-out results.

Rationale: every question stays in its denominator and every reported number traces
to clean-provenance records. Cost if wrong: replay latency excludes one question;
two fallback-derived outcomes could differ from a full re-execution.

## D-082 — Release: private repository, MIT code license, no Pages yet (2026-10-12)

Context: G7.3 needed the repository, visibility, license and hosting choices.

Decision: Kunal chose https://github.com/Kunal874/sql-warden as a private repository
and delegated the license; the code is MIT (simple, permissive, compatible with all
dependencies). Data (CC BY-SA 4.0) and model (Apache-2.0) terms stay separate and are
not covered by the MIT file. `feat/foundation` is pushed as `main`. GitHub Pages is not
published: free accounts cannot serve Pages from a private repository, so the static
site waits until the repository is made public.

Rationale: private keeps the work unpublished while CI runs. Cost if wrong: no public
demo page until visibility changes.

## D-083 — G6 requested; bounded training pilot proposed (2026-10-12)

Kunal requests fine-tuning for resume value. This authorizes pursuing G6; the
specific new libraries/environment/model/budgets still require C8's answer.
Options: native Windows QLoRA pilot; install Ubuntu and use WSL; defer training.
Recommend native Windows first because official bitsandbytes CUDA wheels support
it and Ubuntu is absent. Proposed model is pinned Qwen2.5-Coder 1.5B Instruct;
use an isolated uv environment and 20 steps on invented SQL examples. Proposed
packages and resource caps are in the 2026-10-12 G6 pilot plan. Approval pending.

Measured preflight: GPU 7956 MiB free, D: ~35.2 GiB free, system RAM ~1.05 GiB
free. Do not load training below 4 GiB available RAM. No installation/download/
training or benchmark change occurred. Full data/dialect/conversion decisions
follow the feasibility result. Costs if wrong: Windows package compatibility may
fail, and the pilot may not extrapolate to long database schemas. A successful
pilot supports a feasibility claim only; accuracy requires comparable E9 runs.

## D-084 — C8 pilot approved; isolated native CUDA stack works (2026-10-12)

Kunal explicitly approves all presented plans and asks only important questions.
Proceed sequentially without further plan reviews. The pilot's native Windows,
pinned Qwen Coder 1.5B, six direct packages and resource caps are now approved.
Resolved stack: torch 2.8.0+cu128, transformers 4.57.6, peft 0.18.1,
accelerate 1.12.0, bitsandbytes 0.50.2, huggingface-hub 0.36.2. Separate
`training/uv.lock`; runtime lock and dependencies unchanged. Stable older
transformers/PEFT versions avoid an unnecessary major-version migration.

Actual GPU NF4 forward/backward succeeds on the RTX 4060. The 16-wide probe
warned that it used a slower kernel; Qwen's real projections are larger.
Installed environment occupies ~7.19 GiB, leaving ~28.0 GiB on D:. RAM rose
to ~4.3 GiB available without terminating user apps. Tests first cover resource
floors, live disk monitoring, timeouts, masked labels and raw-SQL exclusion.
Full training-data/dialect/merge choices will be concretely recorded after the
pilot measures feasibility; paid/cloud/publication actions remain unapproved.

## D-085 — Official filtered BIRD intake through bounded ranges (2026-10-12)

Read-only source preparation is part of the authorized fine-tuning workflow.
Use the official BIRD team's filtered 6601 SQLite examples at revision
4068469807b255fcfc0816bdd520946fe460d256 and the official train archive's
69 schemas. Fetch only train_tables.json through strict 206 Content-Range,
length/ETag checks, 8 MiB per-request/32 MiB total caps and ZIP member CRC.
Actual archive reads total 48,532 bytes; raw labels and schemas stay ignored.
Source member hashes and limitations are in training-source-manifest.json.
Costs if wrong: archive ETag is not a full-content SHA-256, and source SQLite
labels still need PostgreSQL conversion/audit. No train/validation split or
label execution validity is claimed by acquiring these files.

## D-086 — Pilot passes; recover finalization without repeating training (2026-10-12)

The actual 20-step pilot at clean d865f20 completed, changed LoRA weights, saved
and reloaded the adapter exactly, then generated a nonempty bounded response.
28.625 s training/save, peak reserved 3.254 GiB, 1,089,536 trainable parameters.
Loss fell 0.20414→0.00201 on eight invented examples. This proves local GPU
feasibility, not execution accuracy or generalization. All weights remain ignored.

The parent failed after the completed child because script-mode sys.path omitted
the repo root. Fix reproduced test-first; `--finalize` validates the existing
evidence and publishes it without another GPU run. Quantized `.numel()` counts
packed storage rather than logical parameters, so rename that metadata field;
the raw original evidence and adapter hash remain intact. Costs if wrong: the
pilot's short synthetic sequences understate full-schema training memory/time.
Existing checkpoint/generation-option warnings are recorded in the ignored log;
their measured run still passed save/reload and finite-loss controls.

## D-087 — PostgreSQL transpile-only labels explicitly accepted (2026-10-12)

Kunal chose "Use structurally checked converted labels, explicitly marked
execution-unverified" after the pilot. Use official filtered BIRD training inputs,
database-family-separated training/validation, project leakage checks and a fixed
base-versus-tuned E9 on verified PostgreSQL evaluation questions. Do not claim
converted training labels are execution-verified. Costs if wrong: conversion
noise may improve or worsen scores or teach incorrect PostgreSQL behavior; the
real comparison must measure it. No tuning on existing held-out outcomes.

## D-088 — Full training data/recipe freeze (2026-10-12)

Execute the full-training plan without routine review questions, as Kunal requested.
Keep numeric-suffix variants together; conservatively treat Codebase variants as
one family and movie/movies variants as one family. Exclude families used by
evaluation, exact shared source-table schemas and normalized question/SQL duplicates.
Costs if wrong: conservative exclusions may remove useful independent examples;
schema/text checks do not establish full database-content separation.

5822 usable structural records, 5521 train/301 validation before token limits.
Freeze 2000 training examples across57 databases and128 validation across6 separate
databases,2048 tokens,seed42. One500-step pass, same pilot rank8 q/v LoRA settings;
save/validate every100steps and pick lowest validation loss (earlier tie), never EX.
Use a2-step length probe before the full run, then a2-hour full cap; preserve the
12GiB training footprint/20GiB disk reserve. Actual model training remains local.
The50-record structural sample and8 complex source/converted pairs expose SQLGlot's
NULLIF denominator rewrite,quoted case restoration and IIF→CASE. No source-result
equivalence claim. Costs if wrong: short-schema subset selection can bias learning
and empty reasoning targets may differ from Arctic's reasoning style.

## D-089 — Full engine validation/checkpoint contract (2026-10-12)

The full worker reads fingerprinted2048-token records, validates response labels,
and never trains on the separate validation DBs. Five checkpoints at100-step
intervals carry validation loss and adapter hashes; choose lowest validation
loss, earlier tie. Use finite-loss checks, gradient clipping, non-reentrant
checkpointing and verify every adapter tensor after reload. Record logical model
parameter count using PEFT's quantization-aware method. A2-step length probe
validates the same input shapes before the500-step pass. Costs if wrong: frozen
labels are still execution-unverified, and validation-loss improvement does not
guarantee better EX. The supervisor keeps the same12GiB/20GiB reserve limits and
sets a2-hour cap for the full run.

## D-090 — Full-length GPU feasibility measured (2026-10-12)

Clean6e87f7c length probe passed:2 optimizer updates at2048 tokens,12.484 s
including adapter saves; peak reserved6.861 GiB, saved/reloaded weights identical.
Proceed with the frozen500-step run under the2-hour cap. Estimated~1 hour
including separate validation; actual timing will be recorded. Costs if wrong:
the8-example probe is small and may understate worst-case GPU pressure.
Probe checkpoint loss is training loss (no validation run); do not present it
as validation quality or an accuracy result. Logical model size1,544,803,840
parameters comes from PEFT's quantization-aware count, including the adapter.

## D-091 — Full run completed; validation selects step400 (2026-10-12)

Clean a96690b run completed500 updates on2000 records in3462.078 s for the
training/checkpoint/validation loop,peak reserved6.426 GiB measured in that loop.
Validation mean token loss0.8337786 before training; best0.0938427 at step400
versus0.0939261 at500. Select400 by the previously frozen rule, without looking
at evaluation EX. Every adapter tensor matches its saved checkpoint on reload;
SHA-256 verified and bounded generation succeeded. Process exit0 and GPU unload
verified. No accuracy improvement is inferred from these losses.

Ruling: distinguish the2000-example full run from the selected400-step model's
1600-example prefix — scientific/resume claims must not imply the selected
adapter consumed all2000 — cost if wrong: an overstated training claim.
Ruling: retain unchanged Arctic full_n1 as an explicitly historical reference
after config/input/IDs/models/prompts/protocol/gold/audit/original-validity
checks all match and relevant runtime code is unchanged — cost if wrong:
latency/environment timing is historical, not a same-session measurement.

Serving budget12→24 GiB question remains pending; no merge/model import yet.

## D-092 — Matched E9 tooling; no fabricated result (2026-10-12)

Reuse the existing guarded run_item with an optional LocalModel; preserve Arctic
as its default so G3 callers do not change. Base/tuned E9 is full-schema n1/k0,
Q4_K_M,8192-context/3072-output,prompt v2,seed42 and no response cache. Pin actual
generator digests, serving manifest and runtime lock. Reject setup credentials,
dirty Git, changed resumes, duplicate/unknown IDs and damaged JSON tails.
Costs if wrong: strict resume requires explicit recovery for a partial record;
the runner intentionally does not silently drop or repair evidence.

Report only complete fresh pairs against valid gold. Reuse existing exact and
paired bootstrap statistics; keep failures in every denominator and unknown
memory null. Compact outputs exclude raw SQL/prompts/rows. Tests reproduce and
fix legacy Arctic model metadata leaking into the E9 manifest and a report
accepting an altered generator alias with the same digest. No real E9 inference,
merge or Ollama import yet; the12→24 GiB resource question remains unanswered.
Costs if wrong: loss improvement cannot establish better database answers.

The first configured E9-driver regression hit D-043's pre-existing cancellation
observe-removal timeout. Isolated test passed, full repeat and final configured
suite passed (1455/3 skips). No executor/deadline change or root-cause claim.

## D-093 — Serving-input integrity and tiny CPU merge check (2026-10-12)

While the artifact-limit choice is pending, perform only a tiny invented CPU
model check using installed libraries, plus read-only input hashing. No real
weights are loaded into RAM and no full merge/import starts. Original weights
SHA-256 equals the pinned public Hugging Face LFS hash; chosen adapter hash matches
training evidence. Metadata only is recorded in g6-serving-inputs.json.

The tiny Qwen2 FP16 check establishes adapter effect, approximate merge/logit
agreement, exact saved-tensor/logit reload and nonfinite safe-merge refusal.
It records source hash and dirty Git rather than pretending a clean benchmark run.
Costs if wrong: tiny-model CPU behavior does not establish full Qwen RAM fit,
Ollama conversion/template compatibility or EX. Temporary invented weights were
owned and automatically removed; source checkpoints/caches remain untouched.

Measured approved footprint10.23 GiB. Merged weights alone add about2.88 GiB;
the12 GiB cap cannot cover that, even with adequate free disk. Retain the existing
cap until Kunal answers the pending24 GiB choice; do not delete caches or choose
an adapter-only comparison that bypasses the requested serving/E9 end state.
Sources checked: https://docs.ollama.com/import and installed PEFT0.18.1
peft/tuners/lora/layer.py and peft/tuners/tuners_utils.py.

## D-094 — Resume evidence uses training, not invented accuracy (2026-10-12)

Use the already completed training record to add a resume bullet and five
interview answers now, while E9 waits for its resource choice. README/EVAL label
training complete and comparison unrun; preserve G3 headlines. Explicitly state
full500/2000 versus selected400/1600, training-loop timing/memory scope and
execution-unverified labels. No base/tuned accuracy, serving-latency or Arctic
parity claim. Costs if wrong: readers may confuse lower token loss with EX;
the docs explicitly distinguish them. G6.6/full drill remain incomplete.

These factual addenda are manual, separate from G3's generated section. Its
existing generator is G3-only; preserve/integrate the G6 evidence before later
full regeneration. Do not run a regeneration merely to overwrite this addendum.

## D-095 — G3 regeneration preserves independently versioned G6 evidence (2026-10-12)

The real writer reproduced loss of manual G6 sections. Keep the existing G3
renderers and preserve the E9/G6 tail from the versioned document, rather than
inventing a second source of training facts or a new report framework. Match
stable section prefixes, not the pending-status title. Repeated generation keeps
exactly one addendum. Costs if wrong: G6 is intentionally maintained independently;
updating its measurements still requires new verified evidence, not a G3 rerun.

The first actual byte-equality check failed because persisted JSON sorts keys,
reordering G3 tables. It also exposed top-four failure reasons being selected
by dictionary order, falsely implying alphabetic entries were most frequent.
Reproduced test-first; rank by count descending and name for ties. EX, counts,
benchmark definitions and model settings stay unchanged. Incidental output
reordering was removed; isolated actual-input checks verify G6 retention and
unchanged G3 result lines, plus correct top failure frequencies. No live AI/DB run.

The same unanswered12→24 GiB authority checkpoint has recurred across at least
three consecutive goal continuations. It did not prevent earlier independent
preparation; that preparation is now checked. Actual serving/E9 cannot proceed
without the resource decision. Do not treat automatic goal continuation as new
resource authority or redefine completion as training-only resume evidence.
Kunal's explicit resource answer subsequently arrived in this same continuation;
the authority blocker is now resolved by D-096, without applying blocked status.

## D-096 — C8 serving artifacts increased to24 GiB (2026-10-12)

Kunal chooses "Finish local Ollama conversion with the24 GiB limit" in response
to the exact resource question. Count G6 artifacts across D: and new Ollama C:
cache artifacts; preserve at least20 GiB free on D:. This approves the merged
weights and matching base/tuned Q4_K_M models for the local comparison. No new
libraries, paid services, uploads or pushes. Preserve pre-existing caches/models;
record baseline cache membership so new G6 artifacts can be distinguished.
Costs if wrong: native conversion can require intermediate files/memory beyond
the estimate; fail within the approved cap rather than silently expanding it.
Training remains complete; continue only serving/conversion/E9 and final evidence.

## D-097 — Approved pinned GGUF tooling and temporary Docker pause (2026-10-12)

Actual Ollama0.35.1 synthetic Safetensors creation rejects Q4_K_M (only newer
native quantization types accepted); no alias was created. Kunal chooses pinned
llama.cpp conversion/quantization, adding only gguf/sentencepiece/protobuf/
ml_dtypes to the isolated training environment. Do not upgrade Torch, NumPy or
runtime libraries. Tool/source pins and actual tiny Qwen2 API sanity evidence
are in g6-conversion-tools.json. This is not all-architecture compatibility or
full-model quantization proof. Keep base/tuned Q4_K_M matching; no benchmark change.

Kunal says RAM is freed and explicitly permits stopping unnecessary Docker tasks.
Gracefully stop Desktop, preserve volumes, record the five running container IDs,
and restore the same services before E9/final handoff. Other project services pause
temporarily; no broad kill/prune. With5.08 GiB free RAM and free8GB GPU, perform
FP16 safe merge on GPU,500MB save shards, sequential unload/reload, exact saved
tensors and logits checks. Keep4 GiB cold loading floor and1 GiB live safety
reserve,20 GiB D reserve and24 GiB combined D/new-C artifacts. The cache baseline
guards existing membership/size, not content authenticity against a local admin.
Costs if wrong: a peak can still exceed the estimate; stop the owned job, preserve
partial artifacts and diagnose. No source checkpoint overwrite or retraining.

## D-098 — Full GPU merge passed; matching conversion next (2026-10-12)

Clean fc7f3d7 actual selected400 merge passed all finite/changed-weight,
saved-tensor/tied-head, exact reload-logit and bounded synthetic-generation checks.
Worker11.748s, peak4.24 GiB GPU, seven500MB shards; source checkpoint preserved.
Generation flag/padding-mask warnings recorded: generation proves nonempty reload,
not query accuracy. Continue exact pinned F16 GGUF then Q4_K_M, both models,
four CPU threads and15-minute per-tool cap, projected C storage counted before
each tool. Keep intermediates C-side to retain20 GiB free D. Existing cache
membership/size and combined24 GiB cap stay enforced. Output collisions require
investigation, not silent overwrite; partial files stay local and ignored.
Costs if wrong: conversion can fail or require recovery despite valid merge;
do not substitute training loss or the synthetic probe for measured E9 EX.

## Native-import execution and final-review rulings

Recorded in decision order; all seven reviewer declined-to-judge items received
an explicit ruling. No Critical or Minor findings were reported. Two Important
findings were fixed in one TDD pass; no re-review or publication was performed.

- Task 1: Ruling: SQLite forbids ASCII case-colliding columns itself, so exercise duplicate native columns at the COPY boundary and keep a defensive metadata collision check — no contrived corrupt SQLite fixture — cost if wrong: a malformed source may raise sqlite3.DatabaseError instead of ValueError.
- Task 3: Ruling: four pinned frpm description names have leading/trailing whitespace — strip only description-name padding, require a unique exact native-name match and record all four aliases; source files and SQL identifiers remain unchanged — cost if wrong: a description could be misattached, while the schema/privilege boundary remains unchanged.
- Final: Ruling: concurrent replacement of locally hashed sources — retain the trusted immutable-source workflow; this offline setup tool is not a defense against an administrator modifying its files mid-import — cost if wrong: local tampering could invalidate pre-use source verification.
- Final: Ruling: no aggregate cap for ignored COPY data — retain streaming line/selected-block bounds because the complete archive is pinned and its known dump is about 1 GB — cost if wrong: processing time/CPU could be excessive despite bounded memory.
- Final: Ruling: corrupt SQLite errors need not be converted to ValueError — retain the current error classification for a hash-pinned, checked source, consistent with Task 1 — cost if wrong: malformed source handling could expose a less uniform error/traceback.
- Final: Ruling: four trimmed description aliases — retain Task 3's unique recorded matches; source bytes and SQL names are unchanged — cost if wrong: a description could attach to the wrong column.
- Final: Ruling: guard/executor, RLS and model/evaluation are not implemented — retain the approved G0.5a-only scope, with generated SQL prohibited until G0.7a controls pass — cost if wrong: this working database is not yet a usable end-to-end agent.
- Final: Ruling: no injected mid-import rollback test — retain the explicit single PostgreSQL transaction and existing rollback-protected controls; review found no atomicity defect — cost if wrong: a future partial-import regression could escape this coverage.
- Final: Ruling: unreviewed PostgreSQL functions beyond the initial boundary — retain the stated non-exhaustive limitation and defer the broader function review to G2, before making stronger claims — cost if wrong: residual function capabilities could weaken isolation.
- Final: Ruling: retain feat/foundation locally in the current checkout — AGENTS.md/D-003 require this workspace, no base branch exists, and G7 forbids remote/push publication before approval — cost if wrong: integration remains postponed until an explicit owner decision.

## Source checks

- Node 24 LTS: https://nodejs.org/en/about/previous-releases (checked 2026-10-03).
- uv managed Python: https://docs.astral.sh/uv/guides/install-python/ (checked 2026-10-03).
- Docker per-user paths: https://docs.docker.com/desktop/setup/install/windows-install/
  (checked 2026-10-03).
- Ollama Windows installation: https://docs.ollama.com/windows (checked 2026-10-03).

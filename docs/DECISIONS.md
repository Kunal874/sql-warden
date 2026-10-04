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

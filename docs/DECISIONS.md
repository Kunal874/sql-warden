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
Verification: 184 guard tests and the full 342-test suite pass; Task 2's actual
guard acceptance checks remain pending. The future executor must guard SQL itself
and establish restricted identity/settings; GuardDecision is not an authority token.

Execution rulings, in decision order:

- Task 1: Ruling: two additional test expectations disagreed with the approved node list / pinned API — VALUES is explicitly reviewed and resolves to a non-physical Scope; Array inherits Func and is rejected as function_not_allowed. Correct those extra expectations, not production policy — cost if wrong: a reviewed VALUES query could be accepted incorrectly, or a rejection could have the wrong category; restricted execution remains mandatory and absent.
- Task 1: Ruling: SQLGlot's unsupported-command warning can include input literals — use its error_message_context=0 parser option and test warning redaction, without changing global logging — cost if wrong: diagnostic messages may be less helpful; raw SQL must not leak into logs.

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

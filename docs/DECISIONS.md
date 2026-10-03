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

## Source checks

- Node 24 LTS: https://nodejs.org/en/about/previous-releases (checked 2026-10-03).
- uv managed Python: https://docs.astral.sh/uv/guides/install-python/ (checked 2026-10-03).
- Docker per-user paths: https://docs.docker.com/desktop/setup/install/windows-install/
  (checked 2026-10-03).
- Ollama Windows installation: https://docs.ollama.com/windows (checked 2026-10-03).

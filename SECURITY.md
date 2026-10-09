# Security Policy

SQLWarden is a local portfolio project for read-only text-to-SQL experiments. This
policy tells reviewers what security properties matter today and what is still
unfinished. It is not a production SaaS security promise.

## System and Scope

Covered code is the local Python backend, PostgreSQL setup scripts, deterministic
security tests and compact evidence manifests in this repository. The current
security boundary is local only: PostgreSQL runs on `127.0.0.1:55432`, inference is
local, and there is no approved hosted deployment, public API or pushed release.

Important assets:

- setup/admin credentials and ignored local environment files;
- restricted dataset credentials and tenant demo credentials;
- source datasets, benchmark gold SQL/results and result rows;
- application tables under the `app` schema;
- tenant rows in the synthetic `tenant_demo` fixture.

Out of scope for current claims: hosted infrastructure, public traffic, user
accounts, arbitrary uploaded databases, write-query features and production
multi-tenant routing.

## Threat Model and Trust Boundaries

Attacker-controlled inputs include user questions, model-generated SQL, schema
descriptions, sample values, result values shown to the explanation step and any
future web/API request bodies. The local model is not trusted to follow
instructions. Database permissions, SQL guard checks and bounded execution are the
security controls.

Trusted code chooses the dataset id, database role, connection settings, query
limits and tenant role. A user, prompt, model response or SQL string must not be
able to choose a broader role, disable the guard or supply a tenant identity.

Gold SQL/results are offline evaluation data only. They must not be sent to
retrieval, generation, repair, voting or explanation prompts.

## Security Invariants

- Generated SQL must pass the SQL guard before planning or execution.
- Rejected SQL must not return executable SQL text.
- The executor must use the server-owned dataset mapping and restricted
  `warden_sandbox_<db_id>` login for each dataset.
- Runtime dataset readers must have no superuser, CREATEDB, CREATEROLE,
  REPLICATION, BYPASSRLS, inheritance or cross-reader membership.
- Read-only defaults, bounded timeouts, row/result/cell limits and guarded
  `EXPLAIN (FORMAT JSON)` must stay enabled for untrusted SQL.
- Direct database permissions must deny writes, DDL, temp table creation, app
  schema reads, peer-dataset reads, risky functions and `SET ROLE`.
- Tenant isolation must use separate database roles and forced RLS policies, not a
  mutable `app.tenant_id` setting as the independent boundary.
- Untrusted schema samples and result previews may influence model text, but they
  must not bypass guard/executor controls. Explanation output must be plain text
  escaped before display.
- Security-layer ablations or layer-off E5 experiments must run only in a
  disposable local Docker project/volume and must reject hosted targets.

## Evidence

Current G2 evidence is local and test-backed:

- `docs/guard-gold-audit-manifest.json` records guard coverage and safe-gold guard
  acceptance counts.
- `docs/executor-cost-calibration-manifest.json` records guarded EXPLAIN policy
  and default cost/row/time thresholds.
- `docs/grants-permission-manifest.json` records real direct-connection grant and
  default-grant checks for the 11 restricted dataset logins.
- `docs/attack-suite-manifest.json` records 40 deterministic SQL attack fixtures,
  three model-mediated/fake-LLM controls, false-block evidence and the local-only
  disposable E5 policy.
- Real PostgreSQL integration tests cover restricted readers, direct denials,
  future grants, executor cost gates and forced tenant RLS.

## Reportable Findings and Severity Context

Report a finding if code reachable from the local runtime can:

- execute unguarded or guard-rejected SQL;
- use setup/admin credentials, a broad owner role or the wrong dataset role for
  untrusted SQL;
- expose source/gold answers, credentials, raw result rows or stack traces to a
  model prompt or public output path;
- bypass tenant RLS or let a user/model choose another tenant identity;
- disable security layers through request/config inputs that should only control
  quality ablations;
- turn a documented local-only or disposable-only operation into a hosted,
  destructive or broad cleanup operation.

Severity depends on reachability and impact. Credential exposure, cross-dataset or
cross-tenant reads, writes through untrusted SQL and bypassing guard/executor
checks are high-impact in this project even if currently local-only.

## Known Limitations and Accepted Risk

- This is not a production SaaS and has no approved hosted deployment yet.
- No official benchmark score is claimed from the G2 security work.
- Layer-off E5 experiments have not been run; only the disposable-only policy is
  recorded.
- The attack manifest references test fixtures instead of duplicating raw payload
  SQL. Reviewers should inspect the named tests for exact inputs.
- The current evidence does not prove universal prompt-injection resistance.
  Escaping, labels and delimiters reduce risk, but database controls remain the
  real boundary.
- PostgreSQL estimates can miss expensive queries, so runtime deadlines remain
  required even after cost checks.
- Database `work_mem` is not a total memory cap. Large expressions, parser work or
  internal Python values may still consume resources before a limit fires.
- Some catalog metadata is normally visible to database users; read-only roles do
  not hide every catalog fact.
- Some benign corrected-gold SQL is currently false-blocked because its functions
  are not reviewed yet.
- Tenant RLS is proven on the small synthetic `tenant_demo`; tenant-aware runtime
  routing is still later work.

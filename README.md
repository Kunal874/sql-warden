# SQLWarden

SQLWarden is a read-only text-to-SQL agent with schema retrieval, bounded repair,
result voting, clarification and abstention. Its portfolio evidence will include
versioned BIRD Mini-Dev evaluations and tests of database isolation and SQL controls.

## Current status

The foundation passes 87 tests: 50 unit/setup/data-extraction checks and 37 real PostgreSQL
integration checks. The local database is PostgreSQL 16.15 on 127.0.0.1:55432.
There are no model results, accuracy claims or
published security measurements yet. The first milestone is one real database
and local model answering a question through a tested guard and bounded executor.

The first BIRD database source and canonical labels are downloaded and pinned.
[Data provenance](docs/DATA.md) records actual hashes, counts and dialect differences.
The PostgreSQL import is not yet implemented;
the [native import plan](docs/superpowers/plans/2026-10-03-bird-native-import.md)
is awaiting review. No downloaded SQL dump has been executed.

The intended stack is Python 3.12, FastAPI, PostgreSQL 16, sqlglot and the official
OpenAI Python SDK against native Ollama. React 18, TypeScript and Vite follow after
the CLI and evaluation pipeline work.

## Development

Work from `D:/PROJECTS/SQLWARDEN`. Read the [active build spec](docs/BUILD_SPEC.md)
and [current handoff](docs/PROGRESS.md) before continuing.
[Decisions](docs/DECISIONS.md) record confirmed choices.

With uv available in your terminal:

```powershell
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

For a first local database setup:

```powershell
uv run python scripts/init_local.py
docker compose --env-file .env.setup up -d --wait
uv run --env-file .env.setup pytest
```

The setup script refuses to overwrite existing credentials. On later runs, skip
that first command. Private .env.setup holds bootstrap credentials for database
setup/tests; .env contains only runtime credentials. Both are ignored by Git.
Do not print either file or run a resolved Compose config that displays secrets.

The two current PostgreSQL datasets are synthetic permission-test fixtures. They are not
BIRD data. Each has its own SELECT-only login; the app login can write only
application tables. Direct tests cover writes with the read-only default disabled,
cross-schema reads, role changes, temporary objects, risky functions and future
table grants. Catalog metadata remains visible. This is an initial privilege
boundary, not the completed SQL guard, executor, RLS or attack suite.

Unused large-object functions are denied to all runtime logins. Mutating denial
probes always roll back, even if a privilege regression lets a probe succeed.

The named volume persists across restarts. Bootstrap scripts run only when it is
empty; changing them does not migrate existing data. Never delete that volume to
apply changes without an explicit decision. To pause the server without deleting
data, use `docker compose --env-file .env.setup stop`.

To update the function permissions on a volume created before this hardening,
keep its credentials and data, then run the setup-only migration:

```powershell
docker compose --env-file .env.setup up -d --wait
docker compose --env-file .env.setup exec -T postgres psql -X -U warden_bootstrap -d sqlwarden -v ON_ERROR_STOP=1 --single-transaction --file /opt/sqlwarden/function_hardening.sql
uv run --env-file .env.setup pytest
```

Fresh bootstrap includes this same idempotent permissions script.

The original [plan](sqlwarden-plan.md), [execution brief](SQLWARDEN_EXECUTION_PROMPT.md)
and [plan review](SQLWARDEN_PLAN_REVIEW.md) are preserved. The active spec overrides
historical instructions, unsupported claims and unsafe architecture in the plan.

Dependencies, data and models are installed locally; raw artifacts and secrets
are excluded from Git. Public release and hosting remain gated at G7.

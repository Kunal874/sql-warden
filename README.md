# SQLWarden

SQLWarden is being built as a read-only text-to-SQL agent with schema retrieval, bounded repair,
result voting, clarification and abstention. Its portfolio evidence will include
versioned BIRD Mini-Dev evaluations and tests of database isolation and SQL controls.

## Current status

The foundation and local CLI pass 719 configured tests, including 165
real PostgreSQL checks (2026-10-04) and 39 deterministic CLI flow checks.
One bounded local AI/database question returned the expected count of 17,686;
[compact evidence](docs/CLI_SMOKE.md) records the exact scope and limits.
Automatic model unload and final review/fix verification are complete. This
finishes the first thin slice (G0.7a), not the full agent. The local database
is PostgreSQL 16.15 on 127.0.0.1:55432.
There are no text-to-SQL accuracy results or
published security measurements yet. The first milestone is one real database
and local model answering a question through a tested guard and bounded executor.

The first BIRD database source and canonical labels are downloaded and pinned.
[Data provenance](docs/DATA.md) records actual hashes, counts and dialect differences.
California Schools is imported into its own schema and read-only login. Complete
typed content matches the native COPY data. The
[native import plan](docs/superpowers/plans/2026-10-03-bird-native-import.md)
is verified. The [compact import manifest](docs/california-import-manifest.json)
records source/content hashes, types, keys, NULL counts and observed checks.
No downloaded SQL dump has been executed.

The first local Qwen smoke passed six tiny warm requests, including text/JSON
responses and an output cap; the first cold request timed out. [Model evidence](docs/MODELS.md)
records the exact artifact, memory and limitations. The separate CLI demo has now
run one guarded model-generated query, not an accuracy benchmark.

The intended stack is Python 3.12, FastAPI, PostgreSQL 16, sqlglot and the official
OpenAI Python SDK against native Ollama. React 18, TypeScript and Vite follow after
the CLI and evaluation pipeline work.

## Safe local CLI (narrow demonstration)

The CLI accepts only a normal-language question for `california_schools`. It
uses the pinned local Qwen alias with a four-column schools capsule, not the
full 89-column schema or retrieval. One optional empty preload, one generation,
then the existing SQL guard and fixed restricted executor; no raw-SQL flag,
repair/retry, voting, online reference answer, accuracy or confidence score.

```powershell
# Setup-only, once; no environment file is used to launch this copy helper.
uv run python -m scripts.prepare_cli_runtime
# Runtime: never substitute .env.setup, .env.california or synthetic .env.
uv run --env-file .env.runtime sqlwarden ask --db california_schools 'How many rows are in the schools table?'
```

The helper exclusively creates ignored `.env.runtime` by copying only the
existing restricted password; it refuses an existing file and changes no grants
or password. Never display/commit this file. Runtime rejects setup/admin/test
keys and OPENAI_LOG/CUSTOM_HEADERS/ADMIN_KEY/WEBHOOK_SECRET settings. The old
synthetic `.env` serves earlier development fixtures, not this CLI.

Output is escaped JSON: answered, blocked or failed. Only a complete successful
result gets SQL/rows; display shows at most 20 rows with a labelled preview.
Missing usage stays null. Budgets: 90s readiness, 60s generation, 180s enclosing
flow, separate 5s HTTP close, and existing database limits (1,000 rows, 2MiB,
5s statement/15s total). Cooperative deadlines/chunk checks are not hard process
or heap isolation. HTTP close does not prove server cancellation or GPU unload.
Interactive use retains Ollama's finite keep-alive; unload only this alias when
finished and check `ollama ps`. No other model/apps/global settings are changed.
Task 3 ran actual controls before the one approved live question. That question
passed once; no automatic repeat/retry is authorized by this acceptance record.
The runtime file exists locally: do not rerun the exclusive copy helper.

## Development

Work from `D:/PROJECTS/SQLWARDEN`. Read the [active build spec](docs/BUILD_SPEC.md)
and [current handoff](docs/PROGRESS.md) before continuing.
[Decisions](docs/DECISIONS.md) record confirmed choices.
For a beginner-friendly account of completed work and AI terms, read the
[project explanation](explaination%20of%20project/PROJECT_EXPLAINED.md).

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

For a fresh California import, first obtain the exact archive and label files
under data/raw using the URLs and hashes in [DATA.md](docs/DATA.md). The following
one-time commands extract/import local files; they do not download them:

```powershell
uv run python -m scripts.fetch_data
uv run python -m scripts.fetch_data --native
uv run python -m scripts.init_local --bird
uv run --env-file .env.setup --env-file .env.california python -m scripts.load_bird
```

This checkout has already completed these one-time steps. Do not repeat them:
existing output, credentials and import targets are intentionally refused.
Private .env.california contains only the separate restricted dataset credential.
The setup-only administrator must never launch the runtime or enter model prompts.

Run the complete current checks, including the real California database:

```powershell
uv run --env-file .env.setup --env-file .env.california pytest -q
```

Without the dedicated California environment, its checks skip before connecting.
With both environments supplied, a missing login/schema is a failure, not a skip.

Two PostgreSQL datasets are synthetic permission-test fixtures, not BIRD data;
California Schools is the first real BIRD import. Each has its own SELECT-only login;
the app login can write only
application tables. Direct tests cover writes with the read-only default disabled,
cross-schema reads, role changes, temporary objects, risky functions and future
table grants. Catalog metadata remains visible. This is an initial privilege
boundary, not the completed SQL guard, executor, RLS or attack suite.

Runtime logins cannot connect to the unused postgres/template1 databases;
template0 remains closed. Unused large-object functions are denied to all runtime
logins in sqlwarden. Mutating denial
probes always roll back, even if a privilege regression lets a probe succeed.

The named volume persists across restarts. Bootstrap scripts run only when it is
empty; changing them does not migrate existing data. Never delete that volume to
apply changes without an explicit decision. To pause the server without deleting
data, use `docker compose --env-file .env.setup stop`.

To update function/default-database permissions on a volume created before this
hardening, keep its credentials and data, then run the setup-only migrations:

```powershell
docker compose --env-file .env.setup up -d --wait
docker compose --env-file .env.setup exec -T postgres psql -X -U warden_bootstrap -d sqlwarden -v ON_ERROR_STOP=1 --single-transaction --file /opt/sqlwarden/function_hardening.sql
docker compose --env-file .env.setup exec -T postgres psql -X -U warden_bootstrap -d sqlwarden -v ON_ERROR_STOP=1 --single-transaction --file /opt/sqlwarden/cluster_hardening.sql
uv run --env-file .env.setup pytest
```

Fresh bootstrap includes both idempotent permissions scripts. On this checkout,
both migrations are already applied and the named volume is preserved.

The original [plan](sqlwarden-plan.md), [execution brief](SQLWARDEN_EXECUTION_PROMPT.md)
and [plan review](SQLWARDEN_PLAN_REVIEW.md) are preserved. The active spec overrides
historical instructions, unsupported claims and unsafe architecture in the plan.

Dependencies, selected data and the first Qwen model are local. The tested model
is currently unloaded; its weights remain installed for reuse.
Raw artifacts and secrets are excluded from Git. Public release and hosting
remain gated at G7.

# SQLWarden

SQLWarden is a read-only text-to-SQL agent with schema retrieval, bounded repair,
result voting, clarification and abstention. Its portfolio evidence will include
versioned BIRD Mini-Dev evaluations and tests of database isolation and SQL controls.

## Current status

The locked Python foundation and validated query budgets pass 40 unit tests.
Database setup is next. There are no model results, accuracy claims or
published security measurements yet. The first milestone is one real database
and local model answering a question through a tested guard and bounded executor.

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

The original [plan](sqlwarden-plan.md), [execution brief](SQLWARDEN_EXECUTION_PROMPT.md)
and [plan review](SQLWARDEN_PLAN_REVIEW.md) are preserved. The active spec overrides
historical instructions, unsupported claims and unsafe architecture in the plan.

Dependencies, data and models are installed locally; raw artifacts and secrets
are excluded from Git. Public release and hosting remain gated at G7.

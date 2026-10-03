# SQLWarden project instructions

Read [BUILD_SPEC](docs/BUILD_SPEC.md), [PROGRESS](docs/PROGRESS.md), and
[DECISIONS](docs/DECISIONS.md) at session start. Reconcile them with Git and resume
the Handoff. The active spec overrides the original plan's Appendix A.

## Scope and workflow

- Work in this directory. Implement only the current task; keep a safe thin slice first.
- Python 3.12 with uv; PostgreSQL 16 in Docker; native Ollama; React 18/TypeScript later.
- Use the approved dependency list in the plan. Ask before adding direct dependencies,
  spending money, accounts, benchmark changes, publication, destructive work or history edits.
- Keep inference local until a hosted configuration is explicitly approved.
- No remote addition or push before the G7 release approval.
- No parallel implementation unless Kunal asks. Keep the runtime a plain Python state machine.
- Preserve the three original planning files as historical inputs.
- After a task, run its relevant checks and update progress with truthful results.
- After each completed group/subtask, update [the simple-English notebook](explaination%20of%20project/PROJECT_EXPLAINED.md) with what changed, checks, new AI/coding terms and what remains unfinished.
- Use tests first for security boundaries, result comparison, voting, budgets and state transitions.
- Real PostgreSQL integration tests must run before database security claims.

## Authorship and secrets

Kunal is the sole author and committer. The confirmed repository identity is
Kunal <kunalchandrakar2005@gmail.com>. Never add assistant/bot contributor credits,
co-author trailers or generated-by signatures. Keep necessary third-party licenses and citations.
Inspect staged changes and the exact message before each Conventional Commit;
check author, committer and body after it. Do not change global Git identity.

Never commit secrets, downloads, model weights, caches or raw runs. Do not print
connection credentials or put them in model prompts. Setup credentials stay out
of the runtime and generated SQL always uses restricted dataset-specific logins.

## Commands

Use PowerShell and uv from the repository root:

- `uv sync --locked`
- `uv run pytest`
- `uv run --env-file .env.setup pytest` (includes real local database checks)
- `uv run ruff check .`
- `uv run ruff format --check .`

Additional commands and any local tool-path workaround belong in PROGRESS's Handoff.
The database is bound to 127.0.0.1:55432. Preserve its named volume. The .env.setup
file is setup/test-only; never use it to launch the runtime or send its values to a model.

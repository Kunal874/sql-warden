# Complete G1 agent core

Date: 2026-10-09
Owner: Kunal <kunalchandrakar2005@gmail.com>
Scope: local-only G1 implementation after G0/G1.1 completion.

## Guardrails

- Keep inference local and reuse the existing provider/cache, guard and executor contracts.
- Do not change raw datasets, source archives, model weights, benchmark labels, or credentials.
- Do not add dependencies unless an existing repository tool cannot do the job.
- Use fake LLMs for loop/terminal tests; only database security claims need real PostgreSQL tests.
- Update `docs/PROGRESS.md`, `docs/DECISIONS.md`, and `explaination of project/PROJECT_EXPLAINED.md` after completed slices.
- Commit checked work with Kunal as author and committer.

## Scope map

Code likely touched:

- `src/sqlwarden/`: schema retrieval, prompts, voting, state machine, and CLI wiring.
- `tests/`: focused tests for schema retrieval, prompts, voting, agent limits/states and CLI output.
- `scripts/`: a tiny read-only retrieval measurement script if needed for C3.
- Docs: progress, decisions and the simple-English notebook.

Existing pieces to reuse:

- `evaluation.extract_sql`, `guard.guard_sql`, `executor.QueryResult`,
  `executor.open_dataset_executor`, `provider.ProviderRequest`, `cache.JsonDiskCache`,
  and the current CLI rendering/env protections.

## Tasks

1. G1.2 schema catalog and bounded serializer
   - Add a small schema catalog that preserves table/column descriptions, primary keys,
     foreign keys and bounded untrusted sample values.
   - Keep the existing E0 serializer behavior compatible.
   - Tests: bounds, untrusted sample labeling, keys/descriptions, and bad-input refusal.

2. G1.3 / C3 retrieval measurement and decision
   - Add BM25-style lexical retrieval without a new dependency.
   - Measure top-k recall on the pinned dev split using existing gold/audit inputs.
   - Record C3 choice for retrieval size, candidate count, repair count and helper setup.
   - Tests: scope-aware ranking and recall-summary shape.

3. G1.4 versioned prompts
   - Add versioned generation, repair, clarification and explanation prompt builders.
   - Keep output formats explicit and per task.
   - Tests: prompt versioning, no secrets/gold, JSON contracts and untrusted text boundaries.

4. G1.5-G1.8 plain Python state machine
   - Add typed events/results with explicit terminal states.
   - Implement generate, guard, execute, one bounded repair, vote, clarification and explain.
   - Keep failed candidates in voting denominators; ties/no valid rows abstain; n=1 is not
     high-confidence consensus.
   - Tests: fake LLM limits, malformed output, provider error, repair limit, ties, abstention,
     clarification pending/resume rejection and terminal states.

5. G1.9 CLI loop options
   - Extend the early CLI with local loop settings and a trace summary while preserving the
     existing safe one-candidate command behavior.
   - Tests: invalid args do not echo unsafe input or touch model/database; loop summary renders.

6. Final G1 docs and review
   - Run focused tests, then full no-env tests, configured tests when relevant, ruff and diff check.
   - Request one fresh read-only review if the implementation is complete.
   - Fix validated findings, update docs and commit the final checked G1 state.

## Done criteria

- G1.2-G1.9 checkboxes in `docs/PROGRESS.md` are true or truthfully marked incomplete.
- C3 is recorded in `docs/DECISIONS.md`.
- Fake-LLM tests cover loop limits and terminal states.
- CLI can show a bounded local agent trace without leaking credentials.
- No raw runs, downloads, model weights, caches or secrets are staged.

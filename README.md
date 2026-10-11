# SQLWarden

SQLWarden is a read-only text-to-SQL agent that runs on a laptop. It turns a question
into PostgreSQL, but every generated query passes a SQL guard, runs under a
one-dataset read-only login with hard limits, and is accepted only when several
independent candidates agree on the complete result. When they disagree it asks one
clarifying question or abstains instead of guessing. Every claim below comes from a
tracked result file or test.

## How a question flows

```
question ─► retrieve 24 relevant columns (BM25 + keys)
         ─► generate 3 SQL candidates (Arctic-Text2SQL-R1-7B, local Ollama)
         ─► per candidate: SQL guard ─► EXPLAIN cost check ─► restricted execution
                           └─ on failure: one repair attempt
         ─► vote on complete results ─► answer │ ask one clarification │ abstain
```

The loop is a plain Python state machine ([agent.py](src/sqlwarden/agent.py)), not an
agent framework. The web app streams each step live over Server-Sent Events.

## Results

<!-- results:start -->
Local PostgreSQL-adapted BIRD Mini-Dev subset with corrected labels and a 4-bit 7B model; not an official BIRD score.

**Held-out (324 questions, primary)**

| Setting | Correct | EX | 95% CI (exact) | Answered | EX when answered |
| --- | --- | --- | --- | --- | --- |
| Full schema, 1 candidate | 176/324 | 54.3% | 48.7%–59.8% | 86.1% | 63.1% |
| Retrieval (24 columns), 1 candidate | 148/324 | 45.7% | 40.2%–51.3% | 82.4% | 55.4% |
| Retrieval + 1 repair | 148/324 | 45.7% | 40.2%–51.3% | 82.4% | 55.4% |
| Retrieval, 3-candidate vote | 139/324 | 42.9% | 37.4%–48.5% | 67.6% | 63.5% |
| Retrieval + repair + 3-candidate vote (full loop) | 139/324 | 42.9% | 37.4%–48.5% | 68.5% | 62.6% |

- Retrieval (24 columns), 1 candidate vs Full schema, 1 candidate: -8.6 pp (95% CI -12.7%–-4.6%, n=324).
- Retrieval + 1 repair vs Retrieval (24 columns), 1 candidate: +0.0 pp (95% CI 0.0%–0.0%, n=324).
- Retrieval + repair + 3-candidate vote (full loop) vs Retrieval + 1 repair: -2.8 pp (95% CI -6.2%–0.6%, n=324).
- Retrieval, 3-candidate vote vs Retrieval (24 columns), 1 candidate: -2.8 pp (95% CI -6.2%–0.6%, n=324).
- Retrieval + repair + 3-candidate vote (full loop) vs Full schema, 1 candidate: -11.4 pp (95% CI -15.7%–-7.1%, n=324).
- With the development-chosen agreement threshold 2/3, the loop answers 61.7% of these questions and is correct on 66.5% of the ones it answers (end-to-end 41.0%).
- Full loop median 32.117 s per question on an RTX 4060 laptop GPU; peak VRAM 5.1 GB.

**Development (100 questions, used for calibration)**

| Setting | Correct | EX | 95% CI (exact) | Answered | EX when answered |
| --- | --- | --- | --- | --- | --- |
| Full schema, 1 candidate | 48/100 | 48.0% | 37.9%–58.2% | 79.0% | 60.8% |
| Retrieval (24 columns), 1 candidate | 48/100 | 48.0% | 37.9%–58.2% | 81.0% | 59.3% |
| Retrieval + 1 repair | 48/100 | 48.0% | 37.9%–58.2% | 82.0% | 58.5% |
| Retrieval, 3-candidate vote | 42/100 | 42.0% | 32.2%–52.3% | 67.0% | 62.7% |
| Retrieval + repair + 3-candidate vote (full loop) | 42/100 | 42.0% | 32.2%–52.3% | 67.0% | 62.7% |
| Messy column/table names, 1 candidate | 33/100 | 33.0% | 23.9%–43.1% | 68.0% | 48.5% |
| Original BIRD wording, 1 candidate | 40/100 | 40.0% | 30.3%–50.3% | 80.0% | 50.0% |
| Original BIRD wording, full loop | 39/100 | 39.0% | 29.4%–49.3% | 71.0% | 54.9% |
<!-- results:end -->

Full method, intervals and per-experiment detail: [EVAL](docs/EVAL.md). These are
local PostgreSQL-adapted BIRD Mini-Dev numbers with corrected labels and a quantized
7B model. They are **not** official BIRD leaderboard scores and are not comparable to
published full-precision SQLite results.

## Security model

Defense in depth, each layer tested on its own ([SECURITY](SECURITY.md)):

| Layer | What it enforces |
| --- | --- |
| L3 SQL guard | one statement; SELECT/WITH/set operations only; scope-aware table checks; a reviewed function and cast allowlist (sqlglot AST) |
| L4 cost gate | `EXPLAIN (FORMAT JSON)` under the same restricted login; never `EXPLAIN ANALYZE` |
| L5 database identity | one login per dataset with SELECT on its own schema only; read-only default; no superuser, CREATEROLE or BYPASSRLS |
| L6 limits | statement, lock, pool and total deadlines; row, byte and cell caps; no partial results |
| L7 row-level security | the tenant demo uses forced RLS chosen by server-side login, not a mutable setting |
| L8 untrusted text | schema descriptions, sample values and results are marked untrusted; explanations have no execution path |

The attack suite has 43 recorded attacks (40 deterministic SQL, 3 model-mediated) with
threat-specific success predicates. The guard also accepts 421 of the 424 safe gold
queries. A blocked attack is evidence for that attack and configuration, not proof
that nothing else works.

## Run it locally

Requirements: Docker Desktop, [uv](https://docs.astral.sh/uv/), Node 24 (to rebuild the
web app) and [Ollama](https://ollama.com) with the two pinned model aliases. The full
runbook, container and hosting notes are in [DEPLOY](docs/DEPLOY.md):

```powershell
uv sync --locked
docker compose --env-file .env.setup up -d --wait
uv run python scripts/prepare_web_runtime.py
cd web; npm ci; npm run build; cd ..
uv run --env-file .env.web uvicorn sqlwarden.runtime:create_runtime_app --factory --port 8000
```

`.env.setup` is used only by Docker Compose and tests; the runtime refuses to start
with setup or test credentials. Checks:

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run --env-file .env.setup --env-file .env.california --env-file .env.datasets pytest
```

## Repository map

| Path | Contents |
| --- | --- |
| `src/sqlwarden/` | guard, executor, agent loop, voting, prompts, catalog, provider, API |
| `scripts/` | data import and validation, experiment runner, report builder, smoke checks |
| `web/` | React pages: Ask, Attack Lab, Benchmark |
| `docs/` | spec, progress, decisions, data/model provenance, evaluation and deployment |
| `results/` | compact tracked summaries; raw runs and caches stay local |

## Limitations

- One local 7B model at 4-bit; accuracy is far below published full-precision results.
- The model sometimes writes SQLite functions such as `strftime`; the guard refuses
  them and these count as failures (counted in EVAL's failure taxonomy).
- On held-out questions the simplest setting (full schema, one candidate) had the
  highest end-to-end accuracy. Retrieval and voting lowered it, and the single repair
  almost never fixed a failure because it sees only a sanitized error category. The
  loop's measured value here is accuracy when it chooses to answer, not coverage.
- When candidates disagree the loop abstains, and abstentions count as wrong in
  end-to-end EX; the coverage curve in EVAL shows the trade-off.
- Hosted live inference is not deployed; the public option is a static evidence site
  plus this local demo ([D-077](docs/DECISIONS.md)).
- Layer-off attack variants (E5) need a separate approved disposable environment and
  have not run. Catalog metadata stays visible to readers, as in normal PostgreSQL.

## Data, models and licenses

- BIRD Mini-Dev ([bird-bench/mini_dev](https://github.com/bird-bench/mini_dev),
  labels [birdsql/bird_mini_dev](https://huggingface.co/datasets/birdsql/bird_mini_dev)),
  CC BY-SA 4.0. Raw data is not included in this repository.
- Corrected labels and descriptions: Arcwise-Plat from
  [uiuc-kang-lab/text_to_sql_benchmarks](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks),
  CC BY-SA 4.0.
- [Snowflake/Arctic-Text2SQL-R1-7B](https://huggingface.co/Snowflake/Arctic-Text2SQL-R1-7B),
  Apache-2.0 (paper: arXiv:2505.20315); Qwen2.5-Coder-7B-Instruct, Apache-2.0.
  Weights are not redistributed.
- Exact pins, hashes and checks: [DATA](docs/DATA.md) and [MODELS](docs/MODELS.md).

## Project records

[Build spec](docs/BUILD_SPEC.md) · [Progress](docs/PROGRESS.md) ·
[Decisions](docs/DECISIONS.md) · [Evaluation](docs/EVAL.md) ·
[Security](SECURITY.md) · [Deployment](docs/DEPLOY.md) ·
[Simple-English notebook](explaination%20of%20project/PROJECT_EXPLAINED.md).
The original plan, execution brief and plan review are preserved as historical inputs.

Code license: [MIT](LICENSE). Data and model licenses above are separate.

Author: Kunal.

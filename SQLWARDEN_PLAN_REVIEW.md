# SQLWarden plan review

Reviewed on 2026-10-03. This is a design and prompt review, not an implementation or security test report.

Inputs: `sqlwarden-plan.md` and the separately pasted build prompt. The existing plan remains unchanged. The replacement execution prompt is `SQLWARDEN_EXECUTION_PROMPT.md`.

## Verdict

The project already has enough features. Its strongest idea is the combination of measured text-to-SQL quality, corrected benchmark labels, and tested database controls. The missing pieces are precise security boundaries, experiment contracts, runtime failure behavior, and a build order that produces a small working result early.

Use the revised prompt instead of Appendix A. It retains the product scope and G/C/E identifiers, while overriding the unsafe or contradictory instructions described below.

## Changes that matter before implementation

| Gap | Why it matters | Change in the execution prompt |
| --- | --- | --- |
| One sandbox login can read every benchmark schema | A schema-qualified query can read another granted schema despite `search_path`. The AST guard is then the only isolation layer. | Use a distinct restricted login per dataset, with no membership in the other reader roles; test direct SQL with the guard bypassed. |
| Tenant RLS trusts a mutable session variable | A policy based only on `app.tenant_id` does not independently constrain arbitrary SQL from that same session. | Prefer tenant-specific database identities and role-specific policies for the small synthetic demo. Test attempted setting and role changes. |
| Security appears after the initial agent and benchmark runs | The first real generated query already needs a safe execution boundary. | Move minimum guard, privileges, read-only transactions, limits and cancellation into G0; deepen them in G2. |
| Claims of universal safety and two defenses per attack | Read-only permissions do not block every catalog read, expensive query, or malicious explanation. Some layers are not independent. | Publish observed outcomes and limitations per threat. Never claim the agent cannot be tricked or that every attack has a backup defense without evidence. |
| Row caps and result equality are underspecified | Comparing truncated results can make different answers look identical. Rewriting SQL with LIMIT changes what is evaluated. | Keep query semantics, detect incomplete results, and never count a matching prefix as EX success or vote agreement. |
| Confidence is described too strongly | Agreement is not a probability of correctness; failed candidates, ties and n=1 need explicit behavior. | Divide by all requested candidates; abstain on unresolved ties; identify n=1 as having no agreement evidence. |
| Sampling and response caching can collide | Reusing one cached completion n times can create artificial unanimity. Seeds and provider compatibility also vary. | Identify each logical sample in the cache; test provider capabilities and record unsupported parameters. |
| Corrected inputs and corrected labels are conflated | Re-scoring fixed predictions isolates label changes; changing the question/evidence/schema also changes the task. | Separate SQL-only re-scoring, corrected-input reruns, and interactive clarification experiments. |
| Question differences are treated as ambiguity labels | A wording correction can fix a typo or a factual error instead of ambiguity. | Treat differences as candidates for manual classification, with clear negative examples and frozen intended interpretations. |
| A simulated user can leak the gold answer | Giving gold SQL, expected rows, or a label-informed choice to the agent inflates measured accuracy. | Give the simulator only a prewritten natural-language intent response; report it as simulated/oracle assistance, separately from noninteractive EX. |
| Data adaptation is verified too loosely | Equal row counts do not establish equivalent data; corrected releases may also change schema metadata. Dropping hard questions can bias results. | Pin sources, map IDs, validate content and conversions, freeze exclusions before model scoring, and label PostgreSQL-adapted results explicitly. |
| Run lifecycle and public trace access are missing | In-process work can disappear on restart; clarification can race; run IDs alone are not a complete access policy. | Define statuses, atomic continuation, bearer capabilities, bounded run storage, SSE replay, timeouts and restart behavior. No account system is added. |
| A semaphore and call counter are not complete budgets | Waiting tasks can grow without bound; retries and token limits can exhaust a free tier. | Bound admission and waiting, reserve calls/tokens atomically, include every actual attempt, and use a total run deadline. |
| G5 deploys before G7 permits any remote or push | The planned sequence cannot reliably satisfy both rules. | G5 prepares deployment locally. G7 contains explicit approval, initial push, publication and public smoke checks. |
| Fine-tuning is called optional but required by “full” completion | An expensive extension can delay the portfolio release indefinitely. | Release G0–G5 + G7 without G6; run G6 only after an explicit go decision. |
| Claude-specific tools and configuration | `AskUserQuestion`, `.claude/settings.json`, and automatic `CLAUDE.md` loading are not a portable execution contract. | Use `AGENTS.md`, available clarification tools or chat, and verify actual Git metadata. Do not invent an attribution setting. |
| Repeated approvals, arbitrary context limits and two-error stops | These can interrupt ordinary debugging and create paperwork instead of progress. | Keep consequential decision gates, inspect the environment directly, record decisions once, and create handoffs at real stopping points. |

### Evidence behind the two isolation corrections

PostgreSQL documents `search_path` as name resolution: qualified names can reference schemas outside it when permissions allow. This directly contradicts the original plan's claim that setting the path alone prevents cross-schema access. The separate-login recommendation is a design inference from that behavior. [PostgreSQL schemas](https://www.postgresql.org/docs/16/ddl-schemas.html), [connection settings](https://www.postgresql.org/docs/16/runtime-config-client.html).

PostgreSQL exposes `set_config` to change session or transaction settings. Consequently, the proposed custom-setting policy needs more than “the server sets it” to be an independent boundary against arbitrary SQL. Role-bound policies avoid relying on that mutable value in this small demo. Superusers, BYPASSRLS and ownership also need explicit checks. This is a design finding; no exploit was executed during this review. [Configuration functions](https://www.postgresql.org/docs/16/functions-admin.html), [row security](https://www.postgresql.org/docs/16/ddl-rowsecurity.html).

`work_mem` is an operation-level allowance, not a total per-query memory cap. The revised prompt requires both database settings and process/container limits, while documenting residual resource risks. [PostgreSQL resource settings](https://www.postgresql.org/docs/16/runtime-config-resource.html).

## Source checks

These are source checks as of the review date, not proof that downloads, conversions, hosting accounts, or local model execution work.

| Item | What the source supports | What still needs execution-time verification |
| --- | --- | --- |
| BIRD Mini-Dev | The official project documents multiple SQL dialects, including PostgreSQL. Its current EX function compares sets of rows. [Repository](https://github.com/bird-bench/mini_dev), [EX implementation](https://raw.githubusercontent.com/bird-bench/mini_dev/main/evaluation/evaluation_ex.py). | Pin the exact dataset revision and evaluator commit; inspect database files, duplicate IDs, description files, timeouts and execution helpers. |
| Corrected release | The repository calls its releases Arcwise-Plat-SQL and Arcwise-Plat; the latter uses `arcwise_plat_full_with_diff.json` and mentions schema corrections. [Release repository](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks). | Inspect actual files and required schema corrections. Do not silently equate a “Full” filename with an independently versioned benchmark. |
| The 52.8% finding | The VLDB paper reports 263 of 498 unique Mini-Dev examples with annotation errors; the first release had 500 entries, including two duplicates. [Paper](https://arxiv.org/html/2601.08778v3). | Preserve denominators and distinguish this audit from the paper's separate leaderboard re-evaluation. |
| Dataset licensing | The BIRD Hugging Face card identifies CC BY-SA 4.0; the corrections repository also displays that license. [Dataset card](https://huggingface.co/datasets/birdsql/bird_mini_dev), [corrections repository](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks). | Inspect the terms of each redistributed artifact, including underlying databases and derived examples. Keep data notices separate from the code license. |
| Arctic-Text2SQL-R1-7B | The model card reports 68.9% BIRD-dev EX and Apache-2.0. It explicitly excludes general natural-language generation from intended use. [Model card](https://huggingface.co/Snowflake/Arctic-Text2SQL-R1-7B). | Verify GGUF provenance, template, output extraction and memory use. Choose a capable helper for clarification/explanation instead of assuming Arctic supports both. |
| Ollama compatibility | Ollama documents compatibility with parts of the OpenAI API. [Compatibility guide](https://docs.ollama.com/api/openai-compatibility). | Smoke-test structured output, sampling, usage fields, context limits and timeout behavior for the installed versions. |
| Render | Its free-service documentation describes sleeping services, ephemeral local storage and a 30-day free Postgres lifetime. [Official free-tier documentation](https://render.com/docs/free). | Account eligibility, current limits, actual measured memory and permitted publication path at C7/C9. Persistent budgets cannot rely on the container's disk. |
| Groq | The public table currently lists gpt-oss-120b at 1K requests/day and 200K tokens/day, alongside minute limits. [Official rate limits](https://console.groq.com/docs/rate-limits). | The account's dashboard limits and exact hosted model availability; a daily call cap alone is insufficient. |
| Hugging Face Spaces | The current overview requires a paid plan to create ordinary Docker/Gradio Spaces, with a separate limited ZeroGPU exception and free static Spaces. [Official overview](https://huggingface.co/docs/hub/en/spaces-overview). | Recheck when hosting is chosen; do not infer account eligibility from a general exception. |
| Security motivation | Both cited papers are available and relevant to SQL/analytics-agent attacks. [P2SQL](https://arxiv.org/abs/2308.01990), [Data Agents Under Attack](https://arxiv.org/abs/2606.08661). | Read the exact methods before claiming this project's attack suite reproduces them. |
| Codex instructions | Official documentation identifies `AGENTS.md` as repository guidance read by Codex. [AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md). | Inspect actual author/committer metadata and generated commit messages; a prompt is not evidence that the final Git record is correct. |

The LiteLLM incident narrative and broad claims that competing products lack evaluation were not independently established in this review. The rewrite preserves the decision not to use LiteLLM without repeating that incident as a verified rationale. Product comparisons should describe SQLWarden's goals and verified differences, not make unsupported claims about competitors.

## Authorship rule

The execution prompt explicitly forbids adding Codex, OpenAI, Claude, any assistant, or a bot as an author, committer, co-author or project contributor. Once Kunal confirms his identity, every new commit must use it for both author and committer and must be inspected after creation. No “Generated with” signatures or co-author trailers are permitted. Upstream dataset/model citations and required license notices remain intact.

There is currently no Git repository in this workspace. This review did not initialize one, create commits, change Git identity, install dependencies, download datasets/models, or begin the build.

## Recommended next step

Read `SQLWARDEN_EXECUTION_PROMPT.md`. When ready, instruct the agent to execute that file starting at G0.1. The first work should be a read-only environment check and confirmation of missing Git identity details, followed by the small safe local slice.

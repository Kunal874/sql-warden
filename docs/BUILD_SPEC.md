# SQLWarden: active build specification

Activated on 2026-10-03 by Kunal's explicit request to start execution. C0 identity,
prerequisite setup, current workspace and a 15–20 hour weekly budget were confirmed.
This is the revised execution brief; the original planning inputs remain preserved.

Change log:
- 2026-10-03: activated the revised execution brief without changing its contracts.
- 2026-10-03: Kunal requested one living simple-English explanation in
  `explaination of project`, updated after every completed group/subtask.

Prepared on 2026-10-03 for Kunal's review. This file becomes an instruction to build only when Kunal explicitly asks to start or execute it. Reviewing, opening, or editing it is not authorization to run the build.

## 1. Role, objective and source of truth

Act as a senior AI engineer and patient mentor. Build SQLWarden with Kunal in small, tested increments that he can explain in interviews. Measure before making claims. Keep the project small enough to ship.

Workspace: `D:/PROJECTS/SQLWARDEN`. Use the current workspace; do not create a nested `sqlwarden` directory.

Read this file and `sqlwarden-plan.md` before implementation. The existing plan supplies the detailed product requirements, task IDs, experiment IDs and interview context. Treat its Appendix A as a superseded prompt and Appendix B as historical tool advice, not instructions to execute. This revised prompt overrides conflicting architecture, workflow and completion rules in that plan. Preserve its other requirements. Later explicit instructions from Kunal and recorded decisions update the project requirements.

`SQLWARDEN_PLAN_REVIEW.md` contains dated source checks and the reasons for these changes. Re-verify external claims against primary sources before relying on them, especially licenses, published results, model availability and hosting limits. Do not repeat unsupported competitor comparisons or the original LiteLLM incident narrative as established facts.

After initial approval, save this revised execution brief as `docs/BUILD_SPEC.md`, with a pointer to `sqlwarden-plan.md` for detailed requirements. Preserve the original plan. Do not copy the obsolete build prompt into the active spec. Maintain a short change log for later approved spec changes.

Product: a read-only text-to-SQL agent with schema retrieval, bounded repair, result voting, clarification and abstention; a measured attack suite; and Ask, Attack Lab and Benchmark pages. Evaluate correctness and failure modes using pinned BIRD Mini-Dev releases and verified corrections.

The goal is a credible portfolio project, not a production SaaS platform. Say which attacks were blocked under which configuration; never promise that the system cannot be tricked or is universally secure.

## 2. Non-negotiable constraints

- Kunal is the sole author and committer of new project commits. Never add Codex, OpenAI, Claude, another assistant or a bot as an author, committer, co-author or project contributor. No `Co-Authored-By` trailers, generated-by signatures, assistant credits, contributor entries or assistant package-author metadata.
- Keep legitimate third-party citations and required dataset, model and software license notices. Those are distinct from project contributor credits.
- No remote creation, remote addition, push, public deployment, tunnel exposure, package publication or model-weight publication until the applicable release approval in G7. Read-only public research/downloads are allowed after execution starts. Never upload proprietary files or secrets.
- Budget: INR 0 recurring. Any one-time spend, at most INR 1,500, needs explicit approval. Never assume a credit card, paid fallback or service signup is authorized.
- Hardware: Windows 11, RTX 4060 Laptop GPU with 8 GB VRAM, 16 GB RAM. Use PowerShell-compatible commands, uv, Docker Desktop and native Ollama. Load one GPU model at a time.
- Backend: Python 3.12, FastAPI, PostgreSQL 16, asyncpg, sqlglot, official `openai` Python SDK with compatible provider endpoints. Frontend: React 18, TypeScript, Vite, plain CSS, Recharts.
- Use a supported Node LTS compatible with the selected Vite version; verify versions instead of assuming “Node 20+” remains adequate. Lock Python and web dependencies. Do not silently upgrade the agreed stack.
- Keep the original exclusions: no user accounts, uploaded databases, write-query feature, semantic-layer DSL, UCI Online Retail, runtime multi-agent system, LangChain, LlamaIndex, LiteLLM, vector database service, Redis/queues, Kubernetes, or Project 2 work.
- If Kunal requests a scope change later, explain the trade-off and record his decision; do not refuse solely because an earlier plan excluded it.
- Use approved dependencies from the original plan. Adding a direct dependency requires a reason and approval. Prefer stdlib `argparse`, `tomllib`, `sqlite3`, hashing and statistics where suitable. Training libraries and embeddings remain gated choices. Audit resolved transitive dependencies without asking about each one individually.
- Implement only files needed by the current task. Do not generate the entire directory tree, empty abstractions, trivial tests or optional features in advance.

## 3. Git identity and persistent instructions

Before the first commit, inspect existing Git state, effective author/committer identity, commit templates and relevant hooks without exposing secrets. Ask only for missing information: Kunal's chosen name and verified GitHub email or noreply address. Do not invent or infer an email from his name.

Once confirmed, set identity repository-locally. Do not change global Git settings, forge another person's identity, remove existing contributors, or rewrite history. Do not initialize a repo if one already exists.

Create a concise root `AGENTS.md` containing project rules, the no-assistant-attribution rule, run/check commands and links to the memory files. Use `CLAUDE.md` only if Kunal later wants compatibility with that tool; keep it as a pointer instead of a second source of truth. Do not create `.claude/settings.json` for a Codex build or invent a Codex attribution switch.

Before each commit, review the staged diff and exact commit message. Stage only files belonging to the task. Use a Conventional Commit for a completed logical change, with no co-author trailers or assistant signature. After committing, inspect:

```powershell
git log -1 --format=fuller
git log -1 --format=%B
```

Verify both author and committer match Kunal's confirmed identity. At release, inspect the entire history, including all author/committer names and emails, co-author trailers and generated-by signatures. If unexpected attribution exists, report the exact commits and ask before rewriting. Do not claim to control GitHub's contributor display without checking its eventual state.

Do not create a test commit solely to test identity. Verify the first real foundation commit. Never commit secrets, data downloads, model weights, caches, raw run output or unrelated user changes. Use `.gitattributes` with `* text=auto eol=lf`.

## 4. Work cadence, checkpoints and memory

On each session, read `AGENTS.md`, `docs/BUILD_SPEC.md`, `docs/PROGRESS.md` and `docs/DECISIONS.md` if they exist. Check `git status` and recent history if this is a repository. Summarize current state, next task, open decisions and failures in four short lines. Resume the exact next task; do not restart setup.

`docs/PROGRESS.md` holds the original task checklist with the amendments in section 11, task checks, a concise session log and a Handoff. Record completed, incomplete, blocked and deliberately skipped work accurately. `docs/DECISIONS.md` uses D-001 onward with context, options, decision, rationale and date. `AGENTS.md` stays mostly stable; do not duplicate a growing session log into it.

Kunal's learning notebook is `explaination of project/PROJECT_EXPLAINED.md`. Update
that one file after every fully completed group/subtask, in very simple English:
what changed, why it matters, actual checks and explanations of new AI/coding
terms. Keep earlier entries and distinguish finished work from future plans.

At a substantive checkpoint, present a recommendation and at most three short questions. Use an available user-input tool or ordinary chat; never require a tool named `AskUserQuestion`. Inspect versions and local state directly instead of asking Kunal to perform checks you can run.

Continue routine, reversible work within the accepted design. Ask before changes to scope, new dependencies, spending, accounts, publication, benchmark definitions, destructive operations or history rewriting. Reuse approvals already given. Do not ask again about a recorded decision unless new evidence changes the trade-off. Kunal saying “you decide” delegates that decision; record the choice.

After each task: run the relevant check, review the diff, update progress and commit the logical change when identity is confirmed. Report the task ID, outcome, check and actual commit hash, or explicitly say uncommitted. Never claim skipped checks passed. Store the last known completed commit in the next progress update; do not create endless commits just to record a commit's own hash.

Use tests first for security boundaries, EX comparison, voting, metrics, rate limiting, budgets, state transitions and attack outcomes. Fake the LLM for deterministic control-flow tests. Mark Postgres integration tests clearly; they must actually run before a milestone makes database-security claims. Do not weaken tests to make broken behavior pass.

If a failure repeats twice, change the investigation instead of blindly repeating commands. Escalate only when blocked on missing information, unavailable dependencies/data, a consequential decision, or a material budget overrun. Do not claim to know an exact context percentage; write a handoff at milestones, real context pressure, or a requested stop. Record running process IDs and resume commands. No empty progress commits.

At group completion, offer the original three-question interview drill; “skip” proceeds. Keep frontend effort near the original 25% limit. Any development subagents are optional read-only research helpers, not part of the runtime architecture; do not start parallel implementation without Kunal's request.

## 5. Establish the database boundary before the first model query

Retain one dataset per schema when the source format supports it. Record adaptation details and let C1 confirm the layout. `search_path` controls name lookup; it does not grant or restrict access.

Use separate restricted dataset logins, conceptually `warden_sandbox_<db_id>`, each with USAGE and SELECT only on its own dataset. No membership in other reader/admin roles, no ownership, no superuser, CREATEDB, CREATEROLE, REPLICATION or BYPASSRLS. Do not route untrusted SQL through a broad login that can switch into all dataset roles. Choose credentials only from a server-owned db_id mapping. Bound the total connection count across lazily created pools.

Keep `warden_app` limited to the application schema. Setup credentials and ownership roles must not be available to the runtime container or model. Separate the Docker bootstrap administrator from normal setup ownership where required.

Inspect effective privileges, including PUBLIC grants. Revoke unnecessary CREATE, TEMP and dangerous function/extension access using setup credentials, and verify the effect. Check existing objects and future default grants. Read-only defaults are defense in depth, not a substitute for privileges and explicit read-only transactions. Avoid writable schemas in name resolution.

For `tenant_demo`, prefer two isolated tenant logins with explicit role-specific RLS policies. The server chooses the login; the client/model cannot supply a tenant identifier or role. Enable and force RLS. Each login must lack membership or privilege to assume the other identity. A missing or unrecognized identity must fail closed.

Do not use `current_setting('app.tenant_id')` as the sole independent tenant boundary for arbitrary SQL: a custom setting is mutable in the session. If a different design is proposed at C4, demonstrate why generated SQL cannot change the authorization identity before adopting it.

Required direct-connection tests bypass the AST guard: writes, other dataset schemas, app tables, tenant reads, SET ROLE, `set_config`, temporary objects, and risky functions. State exactly what L5/L7 prevent. Some catalog metadata is normally visible to database users; do not claim all catalogs are hidden merely because a role is read-only.

## 6. SQL guard, bounded execution and attacks

Before real generated SQL runs, implement a minimum fail-closed sqlglot guard plus restricted execution. Expand the guard and attack coverage in G2.

- Parse PostgreSQL with exactly one statement. Allow SELECT, read-only CTEs and set operations. Reject unsupported parsing, modifying nodes anywhere, SELECT INTO, locks, COPY, SET, DO, CALL, DDL and DML.
- Resolve table references by SQL scope, including nested CTEs and aliases; do not exempt every reference that happens to match a CTE name. Handle quoted/case-sensitive identifiers and schema qualification. Permit only approved dataset relations; reject catalogs, foreign schemas and unapproved table functions.
- Use an explicit function allowlist, including review of overloads, qualification, operators and casts that can invoke functions. Reject session-mutating, file/network, extension and unreviewed functions. SQL keywords such as CASE need AST handling, not a fabricated function grant.
- Security checks cannot be disabled through API inputs. Agent-quality ablations may toggle retrieval/repair/voting/clarification; security-layer ablations require the disposable local attack harness.
- Run `EXPLAIN (FORMAT JSON)` only after guarding, under the same restricted identity and bounded transaction settings as execution. Never EXPLAIN ANALYZE untrusted SQL for a cost check. Estimates can miss expensive work; keep runtime deadlines regardless of estimated cost.
- Stream/fetch bounded batches. Define row, byte, per-cell, statement, lock, pool-acquisition and total-run limits in config. Handle cancellation, rollback and pool reuse after failure. Database work_mem is not a total memory cap; bound container resources and document residual risks from large expressions/results.
- Preserve query semantics. Do not silently inject LIMIT into benchmark SQL. Detect truncation/overflow explicitly, including the cap-plus-one boundary; identical prefixes do not establish equal complete results. UI preview limits and evaluation limits are distinct.
- Errors use stable categories and sanitized details. A repair receives only information it needs, never credentials, stack traces with secrets, or raw internal connection details.

Keep L1–L8 and A1–A7 as organizing IDs. Build at least 40 meaningful attack cases and guard cases spanning the original categories. Separate deterministic malicious-SQL tests from attacks mediated by a stochastic model. Each attack needs a threat-specific success predicate, input/poison fixture, seed/configuration, observed layer/outcome and evidence. A rejection message alone does not prove no protected data was exposed or modified.

Layer-off experiments must use a separately named disposable local Docker project and volume, synthetic canaries, no runtime/admin secrets from the real project, no host-directory mounts, and network/resource restrictions. The runner must reject hosted targets. Cleanup may delete only the explicitly identified disposable resources; never use a broad volume prune. Authorization to run the documented disposable suite does not authorize deleting unrelated data.

For poisoned rows, distinguish unsafe SQL execution, cross-boundary disclosure and explanation manipulation. A quoted canary is not automatically successful instruction-following. Compare against a benign control and score the intended unwanted behavior. Escaping and delimiters reduce ambiguity but cannot guarantee prompt-injection resistance. The explanation step has no execution capability; poisoned retrieval samples can still influence generation and must pass all SQL controls.

Measure benign false blocks. Do not guarantee every attack has two independently effective defenses. Attack Lab shows the observed blocker; any claimed backup must have separate test evidence. Hosted runs offer only a fixed safe subset, with every security layer enabled.

## 7. Agent and model contracts

Implement the original loop as a plain Python state machine:

`RETRIEVE -> CLARIFY? -> GENERATE(n) -> [GUARD -> COST -> EXECUTE -> REPAIR(<=k)] -> VOTE -> EXPLAIN -> terminal status`

- Use typed request, candidate, result and event models. A candidate retains its ID through repairs. Bound generation, repair, structured-output retries, transport retries and total elapsed time. Never expand n or k automatically.
- BM25 retrieves columns, then adds keys and bounded join paths. Include schema descriptions and truncated sample values as untrusted data. Resolve gold table/column references with scope-aware parsing for recall metrics, including aliases and stars. Record unresolved references instead of inventing recall.
- A full-schema baseline must really use the documented full schema. Check the context budget before sending; record overflow rather than silently truncating. Reserve output space and account for model reasoning tokens.
- Empty results and NULL aggregates can be correct. Repair execution/validation failures by default. Any semantic “suspicious result” rule is an explicit measured heuristic and must not use gold SQL/results.
- Clarification pauses the run, releases scarce resources, and accepts at most one bounded reply by default. Validate structured output. Record malformed output; do not silently classify it as an unambiguous question.
- A proposed interpretation can be rejected by the user. An invalid option, expired run or mismatched database cannot resume execution. Re-retrieve if clarification changes relevant schema needs.
- Vote only on complete successful results. Define deterministic canonicalization of NULL, decimals, timestamps, floats and column positions. Prefer duplicate-preserving row multisets; preserve order when required by the answer contract and abstain on incompatible ordering assumptions. Test this separately from official EX semantics.
- Agreement = largest valid group / number of requested candidates. Failed candidates remain in the denominator. Each candidate contributes at most one vote. An unresolved tie or no valid candidate abstains. Do not interpret n=1 as high-confidence consensus.
- Display agreement as an agreement score, not a calibrated probability of correctness. Tune abstention only on the development slice. Measure whether it helps on held-out items.
- Explanations see bounded result data and final SQL, and have no execution/tool path. Their output is escaped plain text. A failed explanation can fall back to a factual template without losing a successful table result. User traces contain decisions and SQL, not a promise of access to private model reasoning.

Use Qwen2.5-Coder-7B-Instruct and Arctic-Text2SQL-R1-7B as the initial requested baselines, subject to verified availability. Pin model revision, GGUF source/checksum, quantization, template and Ollama digest. Do not compare published full-model BIRD-dev scores directly with this quantized PostgreSQL subset as if they were equivalent.

Test the installed provider/model's capabilities: structured JSON, seeds, usage reporting, context and output limits, and response parsing. The OpenAI-compatible endpoint is an interface, not a guarantee that all features work. Do not assume Arctic can generate general explanations or clarification JSON; choose and document a capable helper at C2/C3. Account for helper model loading and latency while keeping one GPU model loaded at a time.

The response cache key includes provider, model/revision/digest, template and schema/data fingerprints, messages, generation parameters, logical sample index and supported seed. Replaying candidate 1 must never supply all n votes. Distinct sampled calls may legitimately match. Use atomic cache writes and mark hits. Fixed seeds do not guarantee reproducible generation on every backend; cached outputs permit exact replay, while fresh runs remain a separate measurement.

Coordinate SDK and application retries to avoid multiplying attempts. Include every actual provider call in usage and budgets. Cached replay must not be reported as live inference latency or zero original generation cost. Missing token/VRAM measurements are unavailable, not zero.

## 8. Data and evaluation contracts

Before full downloads, estimate disk and memory needs. Pin dataset/model URLs to revisions where possible and keep a manifest of SHA-256 hashes, sizes, license sources, question IDs, database identifiers and evaluator version. Keep raw downloads immutable and gitignored. Validate archive paths and inspect SQL dumps before administrative import; do not execute unreviewed setup statements against a valuable database.

Start with one small dataset. Then load the remaining 11-database release, checking row counts, representative content/types/keys and deterministic fingerprints where feasible. Inspect descriptions, dialect differences, collation, dates, numeric division and SQLite typing. Equal row counts alone are insufficient.

For original and corrected labels:

1. Inspect the actual release names/files. The corrections project uses Arcwise-Plat-SQL and Arcwise-Plat, including schema corrections; “Plat-Full” may be a convenient local alias, not an official separate version.
2. Map examples by stable IDs plus verified database/question mapping, never list position. Account for duplicates and missing examples explicitly.
3. If converting SQLite labels, use corresponding source databases and required corrected schema/metadata. Compare original-dialect gold results with converted PostgreSQL results under a documented canonicalization. Classify mismatches; do not silently round away errors.
4. Freeze a gold-validity/exclusion manifest before scoring predictions. Report the original count, aligned count, survivors and reasons by database/difficulty. If fewer than 95% of aligned corrections verify, take C1 with options; do not quietly replace the benchmark or discard difficult items.
5. Call converted/subset results “PostgreSQL-adapted” with their exact denominator. They are not automatically official BIRD leaderboard scores. Preserve any approved native-dialect comparison as a separately named track.

Define the experiment protocol before tuning:

- A seeded 100-item development slice, stratified by database and difficulty, is the default. Freeze its IDs and the held-out IDs after deduplication/alignment. Related original/corrected/messy variants stay in the same split. Report held-out results as primary, full-set results as descriptive; never hard-code “400 held out” when the usable corpus differs.
- All configurations use the same evidence policy and frozen dataset. Gold SQL/results are accessible only to offline scoring, conversion validation and explicitly labelled analysis, never to retrieval, generation, repair, voting or inference-time decisions.
- Pin and reproduce the selected official BIRD EX comparator, with tests for duplicates, order, NULL, floats, empty outputs and errors. Do not modify its semantics to improve scores. Separately report any stricter semantic comparator.
- Incomplete predicted results, invalid SQL, guard blocks and timeouts are failures for end-to-end EX, with separate reason counts. Gold failures are handled by the frozen manifest. An interrupted job is pending/incomplete, not silently removed from the denominator.
- Separate parse-valid, guard-accepted and successfully executed rates. Report EX, answered-only accuracy, coverage and abstentions together; abstention must not inflate end-to-end EX.
- Original-vs-SQL-corrected analysis re-scores the SAME predictions for matched unchanged inputs. Corrected questions/evidence/schema require a separate run; do not attribute the resulting gain solely to better labels.
- Text/evidence differences are candidate ambiguity labels. Review the reason for each change; include clear negative examples. The approximately 50 self-authored examples need intended interpretations and gold SQL frozen before evaluation, with tuning/evaluation partitions.
- Simulated clarification may return only a frozen natural-language description of the user's intended meaning. It must not inspect candidate SQL, results or the correct option to improve the answer. If gold-derived rewritten questions are used, label this oracle-assisted evaluation and report it separately. Measure false asks and unsuccessful clarification too.
- Calibrate retrieval, repair, cost limits and abstention on the development slice. Do not use held-out gold costs/functions to tune behavior after seeing outcomes. Safety coverage audits and any resulting protocol change must be logged and followed by a newly frozen evaluation.
- Use 95% bootstrap intervals with 10,000 seeded resamples and n. Use paired comparisons on the same item IDs. State the resampling unit and avoid claims of generalization across unseen databases from item-level intervals alone. Mark multiple ablation comparisons exploratory unless a correction is predefined. Zero coverage has undefined selective accuracy, not 100%.
- For binary rates at the boundary, such as zero successful attacks, also report a suitable binomial interval or upper bound. A degenerate bootstrap interval must not be presented as proof of zero future risk.

Keep E0–E9 with these definitions:

| ID | Required interpretation |
| --- | --- |
| E0 | Small safe smoke first, then the frozen 100-item slice for the two available baselines. |
| E1 | Baselines against versioned original and corrected labels, with separate corrected-input runs where needed. |
| E2 | Same inference inputs: full schema, retrieval, repair, voting, then separate abstention and clarification effects. Include inference-call/token cost. |
| E3 | Matched re-scoring and case studies that separate annotation changes from input changes. |
| E4 | Seeded messy-schema transformation; verify rewritten gold results and prevent unintended original-name leakage in each condition. |
| E5 | Deterministic SQL and model-mediated attacks, all-layers-on and approved disposable layer-off variants, plus benign false blocks. |
| E6 | Fresh inference latency, cached replay, tokens, helper overhead, VRAM and throughput reported distinctly. |
| E7 | Audited ambiguity set, clear negatives, self-authored subset and separately labelled simulated/oracle assistance. |
| E8 | Held-out accuracy-coverage curve with a development-selected default threshold. |
| E9 | Optional fine-tuned small model versus its base and Arctic under comparable prompts, loop settings, quantization and budgets. |

Keep per-item records with dataset/label/split fingerprints, git commit and dirty status, model/provider identity, prompt/config hashes, candidate/sample IDs, outcomes, original usage and cache-hit status. Resume only when the manifest matches. Append results safely and tolerate an interrupted final JSONL record without discarding earlier items.

Commit small summaries, protocol/config manifests and a compact per-question dashboard export. Keep raw generations, full rows and caches gitignored. The dashboard must actually have the records it needs. Generate SQLWarden performance numbers in README/resume artifacts from results files; external published claims use citations. Never fabricate a metric, timing, success rate or failure case.

## 9. API, frontend and runtime behavior

Keep the original FastAPI routes, with explicit continuation and cancellation:

- `POST /api/ask` accepts a new `{db_id, question}` and returns `202` with `run_id` and an opaque run capability.
- `POST /api/runs/{id}/clarification` accepts exactly one option ID or bounded free text for that pending run; it cannot change db_id or tenant.
- `POST /api/runs/{id}/cancel` cancels work and releases resources.
- Keep health, databases, run status/events, attacks/run and benchmark routes. Provide readiness separately from liveness.

Use cryptographically unguessable, narrowly scoped bearer capabilities for viewing/continuing/cancelling a run. Store only hashes server-side; never put these secrets in URLs or logs. Choose fetch-based SSE parsing if a header is needed, rather than putting the token into EventSource query strings. This is run access control, not a user-account system. Public benchmark exports are separately sanitized static data.

Statuses include pending, running, needs_clarification, answered, abstained, blocked, failed, cancelled, expired and interrupted. State transitions and clarification acceptance are atomic. Duplicate continuation requests must not start duplicate LLM work. Bind pending options to the original run/version and expire them.

Use one API process and one worker for the intended small deployment. Bound active runs, admission waiting and LLM concurrency; reject overload promptly instead of accumulating unlimited waiting tasks. Persist run/event state before responding where needed. On restart, mark unfinished work interrupted and let the user explicitly retry; automatic resumability belongs to the evaluation runner, not an unimplemented durable web queue.

Every SSE event has an increasing sequence ID; support reconnection with Last-Event-ID, bounded replay, heartbeat and a terminal event. A broken browser stream must not create a second run or leave an unlimited background job. Define a finite total-run timeout and explicit cancel behavior. Test disconnects, duplicate requests, expired clarification, restart and cancelled-query pool recovery.

Enforce original input limits, bounded JSON request bodies, db_id allowlists, CORS/origin policy and safe output escaping. Derive client IP only from a trusted proxy chain; a hop count alone is insufficient if clients can reach the origin directly and spoof headers. Expire inactive rate-limit buckets and cap their memory.

Reserve hosted call/token budgets atomically in Postgres before calls. Include clarification, generation, repairs, explanation and retries, plus minute limits and a total-run cap. Reconcile usage conservatively when the provider does not report it. Account for the configured reset boundary. A restart cannot reset the daily budget; provider limits still need handling even with local counters.

Retain at most 500 recent hosted runs plus a finite age limit, with cascading event cleanup and bounded trace/result sizes. Protect raw questions and run capability tokens from logs; keep admin credentials out of the running app. No client-supplied raw SQL or layer-off endpoint.

Build Ask, Attack Lab and Benchmark. Include loading, overload, model-unavailable, interrupted, empty, truncated, blocked and abstained states. Chart only suitable bounded data; label previews. Support keyboard navigation and readable mobile layouts. Do not inject model HTML. Do not invent benchmark values before real artifacts exist.

FastAPI serves the built frontend in the production container. Local Python talks to native Ollama at `localhost`; the Docker API must use an explicitly configured host address such as Docker Desktop's `host.docker.internal`. Verify container reachability and Ollama binding without exposing it publicly.

## 10. Hosting, licensing and fine-tuning

At C7, check official current documentation for API hosting, Postgres and model providers. Record the verification date, free limits, storage/egress, sleep behavior and measured application memory. Confirm the database provider supports required roles, grants, RLS and limits; do not quietly deploy under a broad owner login if it does not.

Measure a 50-question development check of the proposed hosted model and report it separately. Public benchmark data/sample values sent to a third-party model must be deliberate and documented. Keep inference/caches local unless that hosted configuration is approved.

Persistent budgets and run state live in the hosted database, not ephemeral container files. Configure paid overage prevention where available; no unapproved paid fallback. If no suitable free setup exists, present the static Benchmark plus explicitly approved laptop-demo option. A tunnel is publication and needs the same approval.

Prepare a non-root multistage image, explicit health/readiness checks, environment validation, TLS database connections, pinned locks and a clean local runbook. Prepare CI early as configuration: lint, typecheck/build, unit tests and a small disposable Postgres security integration job. CI never commits and uses minimal token permissions. Actual hosted CI results exist only after the approved push.

Separate code licensing from dataset/model terms. Preserve source provenance and required notices for permitted derived artifacts. Do not include raw datasets in Git or publish weights by default. Verify notices before the public per-question explorer is shipped.

G6 is optional and does not block release. C8 must explicitly approve environment, training dependencies, base model, dialect approach, time/disk budget and conversion steps. Validate GPU training with a tiny run first. Split training/validation by database and check against evaluation DB IDs/content; do not assume different split names prove no leakage. Distinguish project-level leakage checks from unknown pretraining contamination.

Prefer execution-verified training SQL where feasible. If a transpile-only training subset is accepted, record that its labels are unverified and audit a sample; do not claim conversion noise can only hurt scores. Include adapter merging/GGUF conversion RAM and disk in feasibility checks. Compare base and tuned models using a fixed evaluation contract. Any weight publication needs separate approval.

## 11. Build order and acceptance gates

Preserve the original detailed task IDs in PROGRESS, but amend their dependencies and checks as follows. A task with an unresolved decision is not complete. Move already implemented functionality forward instead of building a second version in a later group.

| Group | Execution and gate |
| --- | --- |
| G0.1 / C0 | Read-only preflight: workspace contents, Git/identity, Docker, uv/Python, Node/npm, Ollama, GPU, disk and ports. Use SQLWarden and the current path as defaults. Ask only for missing Git identity, prerequisite choices and available time. |
| G0.2–G0.4 | Initialize only if needed; create active spec/memory files and minimal locked project. Set up Postgres with restricted dataset/app identities. Check meaningful Python behavior and direct denial of writes/forbidden reads. |
| Early G0 additions | Add G0.5a (one small dataset), G0.6a (Qwen endpoint smoke) and G0.7a (minimum tested guard/executor/EX + CLI). Produce question -> SQL -> bounded result on one database before downloading all models or building advanced agent features. All safety controls in sections 5–6 apply. |
| Remaining G0 / C1–C2 | Extend data loading/verification, freeze IDs/splits, decide corrected-label handling at C1, smoke-test the second model, then run E0. C2 selects development models/slice/helper strategy from observed speed and memory. A missing optional second model must not be hidden or indefinitely block the working first slice. |
| G1 / C3 | Complete client/cache, schema retrieval, versioned prompts, state machine, repair/vote/clarify/explain and CLI. C3 chooses BM25/hybrid, retrieval size, n/k and helper setup from measurements. Fake-LLM tests cover all loop limits and terminal states. |
| G2 / C4 | Expand the early guard/executor; finalize allowlist, limits, tenant policies and cost thresholds. Run actual Postgres privilege/RLS tests and E5 on the disposable target. Document findings and limitations in SECURITY. |
| G3 / C5 | Freeze the protocol and full experiment matrix/time budget. Reuse the E0 runner and add resumability, metrics/statistics, E1–E4/E6–E8, failure analysis and generated reports. Label 50 failures if available; otherwise all observed failures, without inventing any. |
| G4 / C6 | Implement tested run API/SSE/protections and the three web pages. C6 confirms the existing page scope/polish. A clean local full-stack run and scripted request/clarification/result flow must pass. |
| G5 / C7 | Deployment preparation only: verify providers, prepare image/runbook/CI, hosted-model development comparison where already authorized, README and publication preview. Prepare hosted DB scripts without provisioning or exposing resources yet. |
| G7 / C9 | Clean local clone test, full-history author/committer and secret checks, licenses and concrete release preview. Obtain approval for exact repo name/visibility, initial push, hosting target and publication actions. Then create/push, provision permitted resources, deploy, run bounded public smoke/abuse checks and actual CI, and produce resume/interview artifacts. |
| G6 / C8 | Optional follow-on after the first release by default. If approved, train/convert/evaluate E9, then run applicable G7 verification before publishing updates. |

This replaces G5's earlier publication tasks: move G5.3 hosted provisioning, G5.4 deployment and G5.5 public checks to G7 after approval. Keep G5's local packaging checks. Normal release order is G0 -> G1 -> G2 -> G3 -> G4 -> G5 -> G7; G6 is optional afterward.

Milestones:

1. Thin slice: one real database/model, safe CLI, bounded execution, tested comparator and honest smoke outputs.
2. Local portfolio demo: core loop, security evidence, agreed E0–E8 matrix, reports and three local pages. Any smaller experiment scope needs an explicit recorded decision.
3. Released portfolio project: local milestone plus approved public repo/demo or approved static fallback, actual CI, source/license notices and generated resume claims. G6 is not required.

Final release checks must include the guard and comparator tests, actual sandbox/RLS integration tests, state/budget races, frontend typecheck/build, clean-install runbook, secrets, Git attribution and consistency of published numbers with result artifacts. A simple pattern search is not equivalent to a full secret scan; use an available verified scanner or document the limitation.

## 12. Start and stop behavior

When Kunal says “start” or explicitly asks to execute this prompt:

1. Inspect the current workspace without modifying it. If implementation/memory exists, reconcile code and history with the Handoff and resume there.
2. Otherwise perform G0.1 preflight. Present findings and ask only the unanswered C0 questions. Do not guess the Git email or install missing system software silently.
3. Once C0 is answered, record it and proceed to the early safe thin slice. Pause only for the relevant unanswered checkpoints or approvals; continue independent work while an optional choice is pending.
4. Stop when Kunal asks. Save a truthful Handoff with exact next commands, incomplete changes, checks and background-run state. Do not commit unrelated or failing work as completed.

Do not start the entire multi-week plan because the prompt was merely reviewed. Every session should leave a small working increment, a clear next step and evidence for its claims.

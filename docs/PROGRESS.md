# SQLWarden progress

Active spec: [BUILD_SPEC.md](BUILD_SPEC.md). Detailed product plan:
[sqlwarden-plan.md](../sqlwarden-plan.md). Preserve task IDs; the active spec
amends their order and checks.

Current group: G0. Last completed task: G0.3 (Python checks passed; commit pending).
Last completed commit: 2c77c72. Next: G0.4 restricted PostgreSQL boundary.
Release order: G0 → G1 → G2 → G3 → G4 → G5 → G7; G6 is optional after release.

## Preflight evidence (2026-10-03)

- Workspace initially contained only the three planning documents; no Git repo or implementation.
- GitHub repository has no refs (read-only `git ls-remote`).
- Confirmed Git name/email: Kunal <kunalchandrakar2005@gmail.com>.
- RTX 4060 Laptop GPU: 8188 MiB VRAM; 16 GB system RAM; roughly 66 GB free on D:.
- Node 24.18.0/npm 11.16.0, uv 0.12.22, Docker Desktop 4.83.0, WSL 2.7.11.0.
- uv/Docker are installed per-user and not on this session's PATH.
- Python 3.14.0 existed; managed Python 3.12.15 now runs successfully.
- Ollama 0.35.1 installed successfully (installer hash verified by winget).
- PostgreSQL 17 service owns 5432. API 8000, Vite 5173, Ollama 11434 had no listeners.
- No active Git hook path, commit template or author/committer environment override was found.
- No model inference, database import or security integration checks have run.

## Task checklist

### G0 — foundation and data

- [x] G0.1 / C0: inspect tools, GPU/disk/ports, identity and time; record owner answers.
- [x] G0.2: initialize local repo; instructions/spec/memory/ignore files; verified owner-only foundation commit.
- [x] G0.3: minimal locked Python 3.12 src project; ruff/pytest; meaningful behavior check.
- [ ] G0.4: isolated Docker PostgreSQL 16, restricted dataset/app logins; direct denial tests.
- [ ] G0.5a (early): inspect/fetch one small pinned dataset; provenance, safe import and data checks.
- [ ] G0.6a (early): Qwen endpoint smoke; availability, digest/template/capabilities and measured memory.
- [ ] G0.7a (early): tested minimum guard, bounded executor, EX comparator and one-database CLI smoke.
- [ ] G0.5: remaining datasets/descriptions/corrections; ID alignment and conversion validity manifest; DATA.
- [ ] G0.5b / C1: confirm layout, labels, conversion survival and ambiguity-label policy.
- [ ] G0.6: second model smoke, recorded availability, one GPU model at a time.
- [ ] G0.7: freeze split; E0 on the development slice; measured summaries with exact n.
- [ ] G0.8 / C2: model/slice/helper choices from speed and memory evidence.
- [ ] G0 interview drill (may be skipped by Kunal).

### G1 — agent core

- [ ] G1.1: LLM providers, bounded retries/timeouts, usage and sample-safe atomic cache.
- [ ] G1.2: schema extraction/serializer, keys/descriptions and bounded untrusted samples.
- [ ] G1.3 / C3: BM25, scope-aware recall; choose retrieval size, n/k and helper strategy.
- [ ] G1.4: versioned generation/repair/clarify/explain prompts and per-model output formats.
- [ ] G1.5: typed state machine/events, quality ablations and explicit terminal states.
- [ ] G1.6: complete-result voting, ties/failed denominator/n=1, agreement and abstention.
- [ ] G1.7: bounded clarification and labelled simulated/oracle assistance.
- [ ] G1.8: fake-LLM limits, errors, malformed output, ties and abstention tests.
- [ ] G1.9: extend the early CLI with loop settings and trace summary.
- [ ] G1 interview drill.

### G2 — guardrails and sandbox

- [ ] G2.1 / C4: reviewed functions, limits, cost thresholds and role-specific tenant design.
- [ ] G2.2: expand guard to at least 40 meaningful cases plus safe-gold acceptance audit.
- [ ] G2.3: expand executor settings/caps/deadlines/cancellation and sanitized error categories.
- [ ] G2.4: guarded EXPLAIN, same identity/settings and calibrated cost checks.
- [ ] G2.5: effective grants/default grants; real direct-connection permission tests.
- [ ] G2.6: forced tenant RLS, separate tenant identities and boundary tests.
- [ ] G2.7: untrusted data and explanation isolation tests with benign controls.
- [ ] G2.8: at least 40 attacks, threat-specific success predicates; disposable-only E5 and false blocks.
- [ ] G2.9: SECURITY with evidence and residual limitations.
- [ ] G2 interview drill.

### G3 — evaluation

- [ ] G3.1: extend E0 runner: fingerprinted config/metadata, durable JSONL and safe resume.
- [ ] G3.2: separately report parse/guard/execution/EX, coverage and answered-only metrics; tests.
- [ ] G3.3: seeded bootstrap/paired comparisons, boundary-rate intervals and exact n.
- [ ] G3.4 / C5: freeze protocol, experiment matrix and time budget before tuning.
- [ ] G3.5: agreed E1–E4 and E6–E8, unchanged-input rescoring versus separate reruns.
- [ ] G3.6: label 50 observed failures if available; otherwise all; taxonomy/examples.
- [ ] G3.7: EVAL, compact dashboard export and result-driven README/resume generation.
- [ ] G3 interview drill.

### G4 — API and web

- [ ] G4.1: API, capabilities, atomic lifecycle, SSE replay, admission/budgets/rate limits and CORS.
- [ ] G4.2: API lifecycle/races/restart/disconnect/cancellation tests.
- [ ] G4.3 / C6: confirm existing three-page scope and polish level.
- [ ] G4.4: Ask, Attack Lab, Benchmark with real artifacts and complete failure/loading states.
- [ ] G4.5: clean local full-stack run and scripted request/clarification/result flow.
- [ ] G4 interview drill.

### G5 — deployment preparation only

- [ ] G5.1 / C7: verify current free tiers and suitable grants/RLS/resources; hosting recommendation.
- [ ] G5.2: non-root multistage image, health/readiness, pinned locks and local runbook.
- [ ] G5.3: prepare hosted dataset/role scripts; actual provisioning deferred to approved G7.
- [ ] G5.4: prepare deployment instructions; publication deferred to approved G7.
- [ ] G5.5: prepare bounded public checks; execute only after approved G7 deployment.
- [ ] G5.6: minimal-permission CI: lint, Python tests, web typecheck/build, disposable Postgres job.
- [ ] G5.7: complete README with actual results, citations, licenses and limitations.
- [ ] G5 interview drill.

### G7 — release

- [ ] G7.1: clean local clone/install/runbook verification.
- [ ] G7.2: full-history author/committer/body and verified secret scan; license checks.
- [ ] G7.3 / C9: concrete release preview; approve exact repo/visibility, push and hosting actions.
- [ ] G7.4: approved remote/push/provision/deploy; actual CI and bounded public smoke/abuse checks.
- [ ] G7.5: result-derived resume bullets and 12 evidence-backed interview questions.
- [ ] G7 final interview drill.

### G6 — optional follow-on (not a release blocker)

- [ ] G6.1 / C8: explicit go/no-go, training deps/environment/model/dialect/time/disk choices.
- [ ] G6.2: tiny GPU training feasibility run.
- [ ] G6.3: frozen data, database-based validation split and project leakage checks.
- [ ] G6.4: logged training, checkpoints and memory.
- [ ] G6.5: merge/conversion/GGUF feasibility, local serving and comparable E9.
- [ ] G6.6: evidence-driven EVAL/README update; applicable G7 checks before publishing updates.
- [ ] G6 interview drill.

## Session log

### 2026-10-03 — start

Kunal requested execution, confirmed identity, missing-tool installation and 15–20 hours/week.
Read all active execution contracts and detailed plan; original Appendix A is superseded.
Initialized local feat/foundation; configured owner-only identity, no remote.
Checks: workspace/Git inventory, GitHub refs, tool paths/versions, GPU/disk, ports, WSL/services.
Python install downloaded 3.12.15 and returned a minor-version-link error, but subsequent
inspection found the complete target and both direct execution and uv discovery succeeded.
No installation retry was needed; the cause of the transient reported error is unconfirmed.
Ollama installation completed with a verified installer hash. Docker Desktop started
(initial PID 55532); engine readiness is pending. No model has been downloaded.
G0.2 checks: staged whitespace check, ignore behavior, owner identity, empty remote list
and clean status passed. Commit 2c77c72 has Kunal as both author and committer and a clean body.
G0.3: uv locked/installed the minimal project with Python 3.12.15. Limits tests were
observed RED (missing constructor) before implementation, then all 40 passed.
Full checks: pytest 40 passed, ruff check passed, ruff format checked 3 files,
uv lock --check passed, git diff --check passed. Tests validate positive integer
bounds, cell/result budgets and timeout relationships. No database-security claim.
Ruff 0.16 also formats Python snippets in Markdown by default; explicitly scoped
its include list to Python and pyproject.toml to preserve the planning documents.
The sandbox could not write the pytest cache created during setup; a full run with
the needed access passed without warnings. uv's initial cross-drive hardlink warning
fell back to copies; dependency installation succeeded.
Resolved transitive dev dependencies were inspected: colorama, iniconfig, packaging,
pluggy, pygments and typing-extensions, plus the approved pytest/pytest-asyncio/ruff.
This inventory check is not a claim of a vulnerability scan.

Pre-flight contract reconciliation:
- G0/G2: the guard and restricted identities must exist before the first model query.
- G0/G3: EX comparison preserves the pinned official semantics; complete results are required.
- G1/G4: clarification and cancellation use explicit statuses and bounded atomic transitions.
- G3/G4: the Benchmark page uses real compact exports, never invented data.
- G5/G7: preparation precedes publication; no remote addition or push before release approval.

## Handoff

Next: commit the verified Python project, then G0.4 PostgreSQL roles and direct
connection tests. Docker engine 29.6.2 and Ollama 0.35.1 respond successfully.
Port 55432 is free. Official postgres:16 image pull session 43259 is in progress.
Do not touch the existing PostgreSQL 17 service or its data.

Known tool paths for this session:
- uv: C:/Users/Kunal/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uv.exe
- Docker: C:/Users/Kunal/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe
- winget: C:/Users/Kunal/AppData/Local/Microsoft/WindowsApps/winget.exe

Use explicit paths if a fresh PowerShell cannot resolve commands; re-detect rather than
changing global settings. External installed-tool access may require sandbox escalation.
Ollama installer session 90858 completed. Docker Desktop was started with PID 55532;
no project containers or model inference processes have been started.

Python checks (project virtual environment):

`uv run pytest -q`

`uv run ruff check .`

`uv run ruff format --check .`

Open decisions: none at C0. Later C1–C9 remain unanswered and apply at their milestones.

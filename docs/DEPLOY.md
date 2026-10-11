# Deployment preparation (G5)

Preparation only. Nothing here has been provisioned, pushed or published; G7 needs
Kunal's explicit approval of the exact repository, visibility and hosting target.

## Local runbook (laptop demo)

Requirements: Windows 11 or Linux, Docker Desktop, uv 0.12.22, Node 24.18 (only to
rebuild the web app), native Ollama with the two pinned aliases from
[MODELS](MODELS.md), and the loaded datasets from [DATA](DATA.md).

1. Start PostgreSQL on the preserved volume:
   `docker compose --env-file .env.setup up -d --wait` (setup credentials are used by
   Docker Compose only; they never reach the runtime).
2. Create the runtime-only credential file once:
   `uv run python scripts/prepare_web_runtime.py` (writes ignored `.env.web` with the
   restricted per-dataset reader passwords; refuses to overwrite).
3. Build the web app: `cd web && npm ci && npm run build`.
4. Run the API and pages, either natively:
   `uv run --env-file .env.web uvicorn sqlwarden.runtime:create_runtime_app --factory --port 8000`
   or as the container: `docker compose -f docker-compose.app.yml up -d --build --wait`.
5. Open `http://127.0.0.1:8000`. Readiness: `GET /api/ready` returns 503 with
   `model_unavailable` or `database_unavailable` until both are reachable.
6. Scripted check: `uv run python scripts/smoke_g4_local.py --base http://127.0.0.1:8000 --abuse`.

Stop without deleting data: `docker compose -f docker-compose.app.yml down` and
`docker compose --env-file .env.setup stop`. Never use `down --volumes` locally.

## Container (G5.2)

[Dockerfile](../Dockerfile) builds the web app with Node 24.18, then a Python 3.12.15
slim runtime with `uv sync --locked --no-dev`. It runs as UID 10001, has a health
check on `/api/health`, and copies only reviewed metadata, the compact result
summaries and the corrected column descriptions. `.dockerignore` keeps `.env*`,
raw data, caches and `.git` out of the build context. The app compose file runs it
read-only with `/tmp` as tmpfs, all capabilities dropped, no-new-privileges, 1 GB
memory, 2 CPUs and 128 PIDs, published on 127.0.0.1 only. It joins the database
network and reaches native Ollama through `host.docker.internal`.

Configuration is validated at startup: the runtime refuses any `WARDEN_*` key other
than `WARDEN_RUNTIME_<DB>_PASSWORD`, `WARDEN_DB_HOST`, `WARDEN_DB_PORT` and
`WARDEN_OLLAMA_URL`; the model URL must be one of the local Ollama addresses.

## C7 hosting check (verified 2026-10-11 from official pages)

| Need | Option | Free terms observed | Fit |
| --- | --- | --- | --- |
| Static pages | GitHub Pages | Free for public repos; site at most 1 GB; soft 100 GB/month bandwidth; no commercial SaaS use ([limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)) | Good for Benchmark/Attack Lab |
| API container | Render Free web service | 512 MB RAM, under 1 CPU, sleeps after 15 min idle (about 1 min wake), ephemeral disk, 750 instance hours/month, may restart at any time ([docs](https://render.com/docs/free), [pricing](https://render.com/pricing)) | Possible, cold starts |
| API container | Hugging Face Spaces | Docker/Gradio Spaces now need a paid plan to create; Static Spaces free ([docs](https://huggingface.co/docs/hub/spaces-overview)) | Static only |
| PostgreSQL | Neon Free | 1 GB per project, 20 GB account, 100 CU-hours/project, scale-to-zero after 5 min, no card ([pricing](https://neon.com/pricing)) | Small subset only |
| PostgreSQL | Render Free Postgres | 1 GB, one per workspace, expires after 30 days ([docs](https://render.com/docs/free)) | Too short-lived |
| Hosted model | Groq Free | Per model, e.g. `qwen/qwen3.8-27b`: 30 req/min, 1K req/day, 8K tokens/min, 200K tokens/day ([limits](https://console.groq.com/docs/rate-limits)) | 20-60 questions/day |

Recommendation (D-077): publish a static build of Benchmark and Attack Lab on
GitHub Pages and keep live Ask as the documented laptop demo. That needs no account
beyond GitHub, sends no question text to a third-party model and costs INR 0.

## Hosted live Ask: prerequisites if approved later

Not started. Each item needs approval and Kunal's own accounts:

- Neon roles must be created with SQL: roles made in the Neon Console/API join
  `neon_superuser` and get BYPASSRLS ([docs](https://neon.com/docs/manage/roles)).
- `db/function_hardening.sql` and `db/cluster_hardening.sql` revoke rights on
  `pg_catalog` objects and other databases; a managed provider will not allow that,
  so the guard allowlist (L3) and role privileges become the only function barrier.
- 1 GB fits only a subset of the 11 datasets; pick the subset explicitly.
- The executor uses `ssl=False` for the local socket; hosted connections need TLS
  (`ssl="verify-full"`) before any deployment.
- A hosted model needs a separate 50-question dev check (BUILD_SPEC section 10),
  deliberate disclosure that public BIRD schema/questions go to that provider,
  Postgres-backed call/token budgets and durable run state (D-073 lists both as
  hosted-only work).

## Public checks (G5.5, run only after an approved deployment)

`scripts/smoke_g4_local.py --base <url> --abuse` runs health, readiness, static app,
one ask/clarify/result flow, cancel, then bounded refusals: wrong origin 403,
oversize body 413, unknown dataset 400, invalid JSON 400, missing or wrong
capability 401, and a burst that admits at most `max_active` runs (cancelled at
once) before 503/429 refusals.

## CI (G5.6)

[.github/workflows/ci.yml](../.github/workflows/ci.yml): read-only token, pinned
action SHAs, no credential persistence. Jobs: Python lint/format/offline tests,
web typecheck/build, and a disposable PostgreSQL boundary job with fresh random
credentials under its own compose project name. It has not run on GitHub yet; it
first runs after the approved push in G7.

# syntax=docker/dockerfile:1
# Local runtime image: built web app + locked Python runtime, non-root, no secrets baked in.

FROM node:24.18.0-bookworm-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/index.html web/tsconfig.json web/vite.config.ts ./
COPY web/src ./src
RUN npm run typecheck && npm run build

FROM python:3.12.15-slim-bookworm AS app
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev
# Reviewed, compact metadata the runtime reads; raw data and credentials stay outside.
COPY docs/source-audit-manifest.json docs/attack-suite-manifest.json ./docs/
COPY results/E0_smoke/dashboard.json ./results/E0_smoke/dashboard.json
COPY results/G3_matrix/summary.json ./results/G3_matrix/summary.json
COPY data/description-corrections/arcwise-fe766045 ./data/description-corrections/arcwise-fe766045
COPY --from=web /web/dist ./web/dist
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin warden
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"]
CMD ["/app/.venv/bin/uvicorn", "sqlwarden.runtime:create_runtime_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

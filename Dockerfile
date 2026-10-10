# syntax=docker/dockerfile:1.7
# Single multi-target Dockerfile for the whole workspace.
# Targets:
#   api       – production api / worker image (uvicorn app.main:app | python -m app.worker)
#   api-dev   – uvicorn --reload with app/ bind-mounted (docker-compose.dev.yml)
#   web-dev   – vite dev server with src bind-mounted (docker-compose.dev.yml)
#   nginx     – nginx serving the built web app and proxying /api (docker-compose.yml)
#   nginx-dev – nginx proxying / to the vite container and /api to the api (docker-compose.dev.yml)

ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=22
ARG NGINX_VERSION=1.27

# ---------------------------------------------------------------------------
# Python api: dependencies from the lockfile into /app/.venv, then the sources.
FROM python:${PYTHON_VERSION}-slim AS api-base
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH
WORKDIR /app
COPY api/pyproject.toml api/uv.lock api/.python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project --no-dev

FROM api-base AS api
COPY api/ ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app
EXPOSE 3000
# Health checks are defined per service in docker-compose.yml (the worker shares this image).
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "3000", "--proxy-headers", "--forwarded-allow-ips", "*"]

FROM api-base AS api-dev
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project
COPY api/ ./
EXPOSE 3000
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "3000", "--reload", "--reload-dir", "app"]

# ---------------------------------------------------------------------------
# Web: pnpm workspace (web + packages/*) built with the committed OpenAPI document.
FROM node:${NODE_VERSION}-alpine AS web-base
ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    HUSKY=0 \
    CI=1
RUN corepack enable && apk add --no-cache libc6-compat
WORKDIR /app

FROM web-base AS web-deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY web/package.json web/
COPY packages/openapi/package.json packages/openapi/
COPY packages/eslint-config/package.json packages/eslint-config/
COPY packages/tsconfig/package.json packages/tsconfig/
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store pnpm install --frozen-lockfile

FROM web-deps AS web-build
COPY packages ./packages
COPY web ./web
RUN pnpm --filter web run build

FROM web-deps AS web-dev
COPY packages ./packages
COPY web ./web
WORKDIR /app/web
EXPOSE 5173
CMD ["pnpm", "dev"]

# ---------------------------------------------------------------------------
FROM nginx:${NGINX_VERSION}-alpine AS nginx-base
ENV NGINX_ENVSUBST_FILTER=^APP_
COPY nginx/proxy.conf /etc/nginx/proxy.conf

FROM nginx-base AS nginx-dev
COPY nginx/templates-dev/ /etc/nginx/templates/

FROM nginx-base AS nginx
COPY nginx/templates/ /etc/nginx/templates/
COPY --from=web-build /app/web/dist /usr/share/nginx/html

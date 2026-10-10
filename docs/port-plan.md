# Port plan: AI Support Assistant on FastAPI

Handoff written 2026-10-10 for the session that continues this work. The goal is a Python/FastAPI
backend for the same product as `../ai-support-assistant` (TypeScript, Fastify, Smithy spec-first),
reusing that repository's React web app unchanged. Read this file first; everything else is on
disk in the two repositories.

## 1. State of this repository right now

Already copied in from `../ai-support-assistant` (nothing Python exists yet):

| Path                               | Origin                                             | Notes                                                                   |
| ---------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------- |
| `web/`                             | `web/`                                             | React app, unchanged. Depends on workspace packages below.              |
| `packages/eslint-config`, `packages/tsconfig` | same                                    | Needed by `web/` (`@app/eslint-config`, `@app/tsconfig`).               |
| `packages/openapi/reference-smithy.json` | `packages/openapi/openapi.json`              | The frozen contract the web app was built against. Keep as the compatibility reference. |
| `packages/openapi/package.json`    | same                                               | `web/scripts/gen-api-types.mjs` reads `../../packages/openapi/openapi.json` (to be exported from FastAPI). |
| `nginx/`                           | same, without `certs/`                             | Templates proxy `/api` to `api:3000`; keep port 3000 for the Python api. |
| `scripts/tls/`                     | same                                               | mkcert setup.                                                           |
| `api/prompts/`                     | `api/prompts/`                                     | Prompt templates with `{{name}}` placeholders. Exact text matters.      |
| `api/seed/guidelines/`             | same                                               | Two sample guideline documents (Bookshop, VPN SaaS).                    |
| `api/eval/*.json`                  | `api/eval/*.json`                                  | Retrieval and corrections datasets.                                     |
| `.prettierrc`, `.editorconfig`, `.npmrc`, `.gitignore`, `pnpm-workspace.yaml`, `docker-compose.tls.yml` | same | `pnpm-workspace.yaml` still lists `api`; change to `web` and `packages/*` only. |

Not yet present: root `package.json`, `api/pyproject.toml` and all Python code, `Dockerfile`,
`docker-compose.yml`, `docker-compose.dev.yml`, `.env.example`, `README.md`, tests, CI.

Tooling on this machine: `uv 0.13` (Homebrew) with a managed CPython 3.12.15
(`uv python find 3.12`), Docker Desktop 28, pnpm 10.34 via corepack, Node 24. The system
Python is 3.9 and must not be used.

The Gemini key lives in `../ai-support-assistant/.env` (git-ignored). Copy that file to this
repository's `.env` when a live check is needed; never commit it.

## 2. Decisions already made with the user

- **Code-first with FastAPI.** Pydantic models are the contract. FastAPI's generated OpenAPI is
  exported to `packages/openapi/openapi.json` and committed; a test fails when the committed file
  drifts from `app.openapi()`. The web client types are regenerated from that file
  (`pnpm --filter web api:types`).
- **Same web UI, unchanged.** The backend must be wire-compatible with the Smithy contract in
  `packages/openapi/reference-smithy.json`: same paths, methods, status codes, query and header
  parameter names, JSON property names, and error envelope. A second test checks that
  compatibility against the reference (paths and methods present; for each operation the
  request body properties and the 200 response properties match after resolving `$ref`).
- Smithy is dropped. No code generation except the OpenAPI export and the web types.
- Models: `gemini-3.8-flash` with thinking level `medium`, `gemini-embedding-2` at 768
  dimensions, same env variable names as the TypeScript api (`GEMINI_CHAT_MODEL`,
  `GEMINI_THINKING_LEVEL`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_EMBEDDING_DIMENSIONS`, …; the full
  list is in `../ai-support-assistant/.env.example` and `api/src/config.ts`).
- Stack mapping agreed with the user:

| TypeScript                       | Python                                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| Fastify + Smithy server SDK      | FastAPI + Pydantic v2, uvicorn                                                              |
| zod config                       | pydantic-settings                                                                           |
| Drizzle + SQL migrations         | SQLAlchemy 2 (async, asyncpg) + Alembic; `pgvector` package for the `Vector(768)` columns   |
| pg-boss                          | Procrastinate (Postgres-backed, async, `queueing_lock` for the singleton key) behind the same two-method `JobQueue` interface; in-memory implementation for tests |
| `@google/genai`                  | `google-genai` (same SDK family; see §4 on embeddings)                                      |
| jose + argon2                    | PyJWT (HS256) + argon2-cffi                                                                 |
| pino                             | structlog, JSON to stdout, request id bound per request                                     |
| Langfuse JS SDK                  | `langfuse` Python SDK v3                                                                    |
| pdf-parse, mammoth               | pypdf, mammoth (Python)                                                                     |
| PGlite in tests                  | testcontainers Postgres (`pgvector/pgvector:pg17`), one container per test session, a fresh database per test |
| vitest                           | pytest, pytest-asyncio, httpx `AsyncClient` over `ASGITransport`                            |
| eslint + prettier                | ruff (lint + format), mypy strict                                                            |

## 3. Contract details the web app depends on

Read `../ai-support-assistant/web/src/api/api-error.ts` and `errors.ts` before writing the error
handling; the UI switches on these.

- Every error response carries header `x-amzn-errortype: <ErrorName>` and a JSON body with at
  least `message`. Error names and bodies (from `reference-smithy.json`):
  `ValidationException` (400, `fieldList: [{path: "/field", message}]`, JSON-pointer paths),
  `UnauthorizedError` (401), `NotFoundError` (404, `resource`, `id`), `ConflictError` (409),
  `GuidelinesNotReadyError` (409, `companyId`, `latestStatus`), `GuidelinesConflictError` (409,
  `latestVersionId`, `uploadedBy: User`, `uploadedAt`), `PayloadTooLargeError` (413, `maxBytes`),
  `UnsupportedMediaTypeError` (415, `supported: [..]`), `RateLimitedError` (429,
  `retryAfterSeconds`), `AiProviderError` (502, `provider`), `InternalServerError` (500,
  `requestId`). Status codes per operation are in the reference document.
- FastAPI's default 422 must become a 400 `ValidationException` with `fieldList`; Pydantic error
  `loc` (`body`, `correctedAnswer`) maps to path `/correctedAnswer`.
- Every response echoes `x-request-id`. nginx sends `X-Request-Id`; use it when present, else a
  uuid4. Bind it into the log context.
- Protected routes must answer 401 before the body is validated (no token, no information).
  A router-level dependency that raises first achieves this in FastAPI.
- Public operations: `Health`, `Login`, `RefreshToken`, `Logout`. Everything else needs
  `Authorization: Bearer <access token>`.
- Timestamps are ISO-8601 strings (`AwareDatetime`). Pydantic's `Z` suffix is fine.
- Upload is `PUT /api/companies/{companyId}/guidelines` with a raw `application/octet-stream`
  body and headers `X-Filename` (required), `X-File-Content-Type`, `X-Expected-Version`.
- The web only imports these schema names, so the Pydantic classes must be named exactly:
  `User, Company, GuidelineStatus, GuidelineVersionSummary, GuidelineChunk, Conversation,
  ConversationSummary, Message, MessageKind, MessageRole, Coverage, AssistantGuidance,
  Correction, FeedbackRating, FeedbackSummary, RetrievedChunk, UsedCorrection`. Name the
  request and response models like the reference too (`SendMessageRequestContent`,
  `ListCompaniesResponseContent`, …) so the component names line up. Enums as `str, Enum`
  subclasses with those class names.
- A first-pass Pydantic file generated from the reference with datamodel-code-generator is a
  good starting point:
  `uvx --from datamodel-code-generator datamodel-codegen --input packages/openapi/reference-smithy.json --input-file-type openapi --output-model-type pydantic_v2.BaseModel --target-python-version 3.12 --use-standard-collections --use-union-operator --field-constraints --use-annotated --enum-field-as-literal all`
  then replace the `RootModel[Literal[...]]` enums with `str, Enum` classes and drop the
  generated `*ResponseContent` wrappers you do not need.

## 4. Behaviour to port, file by file

Source of truth is `../ai-support-assistant/api/src` (about 4,900 lines) and its tests
(`api/test`, `api/src/**/*.test.ts`, about 2,100 lines). Port behaviour, not structure, but keep
the module split so the two code bases can be compared:

| TypeScript module                     | What it does (port all of it)                                                                                                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config.ts`                           | Env schema and defaults.                                                                                                                                                       |
| `db/schema.ts`, `drizzle/*.sql`       | Tables, enums, HNSW and GIN indexes, generated `search_vector` tsvector column, `thinking_tokens`/`total_tokens` on messages (migration 0002). Write the Alembic initial migration from the SQL files verbatim. |
| `auth/*`                              | Login, HS256 access tokens (15 min, issuer `ai-support-assistant`, jti), opaque refresh tokens stored as SHA-256 hashes with rotation, family revocation on reuse, logout, seed users. |
| `companies/service.ts`, `guidelines/mappers.ts` | Company list/get/create/update with active and latest version summaries and the caller's own conversation count; unique name (lower-cased index) → `ConflictError`. |
| `guidelines/service.ts`               | Upload (size limits, sha256 dedupe against the active version, `X-Expected-Version` conflict, supersede in-flight versions, enqueue ingestion with singleton key), get active (text + chunks), list versions, get, retry failed, activate, `set_active_version` (never lets an older version overwrite a newer active one unless forced; deactivates corrections of other versions). |
| `ingestion/parsers.ts`, `chunker.ts`, `job.ts` | File-kind detection, text extraction (txt, md, pdf, docx), heading-aware chunking with overlapping-window fallback, resumable parse → chunk → embed → ready job with superseded checks. Chunker has unit tests; port them. |
| `jobs/queue.ts`                       | `enqueue(name, payload, singleton_key)` / `subscribe(name, handler)` / `stop()`; Procrastinate in production, in-memory with `drain()` in tests.                                 |
| `rag/templates.ts`, `prompt.ts`       | Template loading with placeholder checks, prompt assembly (history window, rolling summary, retrieved sections, corrections as few-shots, token budget with oldest-first dropping, customer text wrapped as untrusted data). Tests exist for both. |
| `rag/embeddings.ts`                   | Gemini embedder: up to 100 texts per call, **one `Content` object per text** (a plain list of strings is merged by the SDK into one multi-part document, which `gemini-embedding-2` embeds as a single vector), `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` task types, unit-length normalisation, retry on 429/500/503 with doubling delay, per-request timeout. Fake embedder (hashed bag of words) for tests. |
| `rag/llm.ts`                          | Gemini chat model: JSON mode with the `AssistantGuidance` response schema, temperature 0.3, `max_output_tokens` 8192, `thinking_config.thinking_level` from config, `MAX_TOKENS`/`SAFETY` finish reasons raised as `ChatModelError`; records prompt, completion, thinking (`thoughts_token_count`) and total tokens; `summarize` call (temperature 0.2, 512 tokens). Fake chat model for tests. |
| `rag/retrieval.ts`                    | pgvector cosine top-k with threshold, keyword rescue (Postgres full-text, a stemmed content word occurring in at most a quarter of the version's sections and at least twice in the candidate), correction retrieval, `mergeRetrieved`. `retrieval-rescue.test.ts` runs the real SQL. |
| `rag/guidance.ts`                     | Response schema and the server-side gate: parse, validate, keep only cited ids that were provided, downgrade coverage when the reply contains code, etc.                         |
| `conversations/service.ts`            | Create/list (cursor paging, company and coverage filters, private per agent)/get (paged messages)/`sendMessage`: history window and rolling summary, retrieval incl. correction-anchored retrieval, prompt, generation, gate, persistence of guidance, retrieval scores, corrections used, model, all four token counts, latency, trace id; failed turns stored with `status: failed`. The tracer records retrieval and generation. |
| `feedback/service.ts`                 | Thumbs up/down, thumbs down requires `correctedAnswer` (raise `ValidationException` with `fieldList`), one feedback per message and user, query embedding stored for similarity, corrections list and toggle. |
| `observability/tracer.ts`             | `Tracer` with noop, recording (tests) and Langfuse implementations: one trace per chat turn with retrieval span and generation (usage: input, output, reasoning, total), one per ingestion, feedback as scores. |
| `db/seed.ts`, `db/reembed.ts`         | Seed users and the two sample companies at first start; `reembed` CLI that re-embeds every chunk of ready versions and every correction vector (needed after an embedding-model change). |
| `server.ts`, `worker.ts`, `app.ts`    | api entry: migrations, seed, serve; worker entry: subscribe to `ingest-guidelines`. Both refuse to start when `GEMINI_EMBEDDING_DIMENSIONS` differs from the schema constant. Swagger UI at `/api/docs`, document at `/api/openapi.json`. |
| `eval/retrieval-eval.ts`, `corrections-eval.ts` | Port both harnesses to Python (`api/eval/`) so the numbers in `../ai-support-assistant/docs/evaluation-report.md` can be reproduced: top-1, top-4 recall, margins, thresholds, keyword rescue, hybrid BM25 fusion; baseline vs with-correction judged 1–5 with `EVAL_JUDGE_MODEL`. |

## 5. Suggested layout and conventions

```
api/
  pyproject.toml            uv project; deps: fastapi, uvicorn[standard], pydantic-settings, sqlalchemy[asyncio], asyncpg,
                            alembic, pgvector, procrastinate, google-genai, pyjwt, argon2-cffi, structlog, pypdf, mammoth,
                            langfuse, httpx; dev: pytest, pytest-asyncio, testcontainers[postgres], ruff, mypy
  app/
    main.py                 create_app(settings, deps) + uvicorn entry; worker.py for the job consumer
    config.py  logging.py  errors.py  request_id.py  deps.py  schemas.py  openapi_export.py
    db/ (base, session, models, seed, reembed)   alembic/ + alembic.ini
    auth/ companies/ guidelines/ conversations/ feedback/   (service.py + router.py each)
    rag/ (embeddings, llm, prompt, templates, guidance, retrieval)   ingestion/ (parsers, chunker, job)
    jobs/queue.py   observability/tracer.py
  prompts/  seed/  eval/  tests/
packages/openapi/openapi.json   exported by `uv run python -m app.openapi_export`; committed
web/  nginx/  Dockerfile  docker-compose.yml  docker-compose.dev.yml  docker-compose.tls.yml  .env.example  README.md
```

- Dependency injection through `create_app(...)` taking the embedder, chat model, queue and
  tracer, so tests pass fakes exactly like the TypeScript `buildApp`.
- Async everywhere (SQLAlchemy async session per request, `asyncpg`).
- Keep env variable names, defaults, queue name (`ingest-guidelines`), log field names and
  error messages identical where the UI or docs show them.
- Root `package.json` keeps a pnpm workspace for `web` and `packages/*` only, with scripts
  `codegen` (export OpenAPI then `pnpm --filter web api:types`), `lint`, `test`, and a husky
  pre-commit running lint-staged (prettier/eslint for web, ruff for api).
- `Dockerfile` targets: `api` (python:3.12-slim, uv sync, `uvicorn app.main:app --port 3000`;
  the worker runs `python -m app.worker` from the same image), `nginx` (web built with pnpm,
  copied from the existing multi-stage pattern in `../ai-support-assistant/Dockerfile`),
  `api-dev`, `web-dev`, `nginx-dev` for `docker-compose.dev.yml`. Compose files mirror the
  TypeScript repo's, including the optional `observability` profile for Langfuse.

## 6. Order of work and how to verify

1. Skeleton: pyproject, config, logging, errors and request-id middleware, SQLAlchemy models,
   Alembic migration, `schemas.py`, `create_app`, health route, `JobQueue` interface with the
   in-memory implementation, pytest fixtures (testcontainers, fakes). `uv run pytest` green on
   the health test.
2. Auth and companies, with tests ported from `api/test/auth.test.ts` and `companies.test.ts`.
3. Ingestion, guidelines, worker, Procrastinate queue; tests from `guidelines.test.ts`,
   `seed.test.ts`, chunker unit tests.
4. RAG, conversations, feedback, tracer; tests from `conversations.test.ts`, `feedback.test.ts`,
   `retrieval-rescue.test.ts`, `summary.test.ts`, `turn-failures.test.ts`,
   `messages-paging.test.ts`, `prompt.test.ts`, `templates.test.ts`, `guidance.test.ts`.
5. OpenAPI export, snapshot test, compatibility test against `reference-smithy.json`; run
   `pnpm --filter web api:types`, then `pnpm --filter web typecheck` and `pnpm --filter web test`
   must pass with the regenerated types (that is the proof the UI is unchanged).
6. Docker, compose, `.env.example`, README. Bring the stack up, log in as `agent1`/`agent1pass`,
   upload the seed guidelines, send a message, check the "why this answer" panel shows all four
   token counts.
7. Eval harnesses; run them with the key and compare with
   `../ai-support-assistant/docs/evals/*` (top-1 84.8 %, top-4 98.7 % / 100 % with rescue;
   corrections 3.67 → 4.33 with the judge pinned to `gemini-3.6-flash`).
8. Commit in steps, no co-author trailer (the user asked for none), push to
   `git@github.com:abhijeet4som1/ai-support-assistant-fastapi.git` on `main`.

Independent modules can be ported in parallel by sub-agents once the skeleton (step 1) exists,
because they only share the models, session, schemas and the `JobQueue`/`Embedder`/`ChatModel`/
`Tracer` interfaces defined there.

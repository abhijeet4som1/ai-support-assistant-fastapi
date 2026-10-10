# AI Support Assistant (FastAPI)

AI assistant for customer-support teams: agents paste a customer message, the assistant answers
from the company's guideline document (retrieval-augmented generation over pgvector), and agents
rate and correct answers so later answers improve. Guidelines are uploaded per company, versioned
and processed in the background; every chat turn records what was retrieved, which corrections
were used, the model and all four token counts, so an agent can see _why_ an answer was given.

This repository is a Python port of [`ai-support-assistant`](https://github.com/abhijeet4som1/ai-support-assistant)
(TypeScript, Fastify, Smithy spec-first). The React web app is reused unchanged: the backend is
wire-compatible with the original API contract, which is kept as
`packages/openapi/reference-smithy.json` and checked by a test.

| Layer         | This repository                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------ |
| API           | FastAPI + Pydantic v2 (code-first; the OpenAPI document is exported from the models)             |
| Database      | PostgreSQL 17 + pgvector, SQLAlchemy 2 (async, asyncpg), Alembic                                 |
| Jobs          | Procrastinate (Postgres-backed) behind a two-method `JobQueue` interface                         |
| LLM           | Gemini (`google-genai`): `gemini-3.8-flash` chat with thinking, `gemini-embedding-2` at 768 dims |
| Auth          | HS256 access tokens (PyJWT) + rotated refresh tokens, argon2 passwords                           |
| Observability | structlog JSON logs with request ids; optional Langfuse tracing                                  |
| Web           | React 19, TanStack Router/Query, generated API types (`openapi-typescript`)                      |
| Tooling       | uv + Python 3.12, pytest with a pgvector testcontainer, ruff, mypy strict                        |

## Start the project

Requirements: Docker Desktop, a Gemini API key (https://aistudio.google.com/apikey).

```sh
cp .env.example .env        # set GEMINI_API_KEY and JWT_SECRET
docker compose up --build -d
open http://assistant.localhost       # NGINX_PORT=8080 docker compose up -d  if port 80 is taken
```

On first start the api runs the migrations, seeds the users `agent1`/`agent1pass` and
`agent2`/`agent2pass`, creates the sample companies _Bookshop_ and _VPN SaaS_ and queues their
guideline files; the worker ingests them within seconds (parse → chunk → embed → ready).

Swagger UI: `http://assistant.localhost/api/docs`; document: `/api/openapi.json`.

### Optional: HTTPS

```sh
scripts/tls/setup.sh                                     # mkcert certificates into nginx/certs
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

### Optional: Langfuse tracing

Uncomment `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` in `.env` and start the stack with
`docker compose --profile observability up -d`; open http://localhost:3001
(`admin@example.com` / `langfuse-admin-1`). Every chat turn becomes a trace (summary, retrieval,
generation with usage), every ingestion a trace, and agent feedback is attached as scores.

## Test each flow end to end

1. **Log in** as `agent1`. The session is a short-lived JWT plus a rotated refresh token.
2. **Companies and guidelines.** Both sample companies show _ready_ guidelines. Upload a new
   `.txt`, `.md`, `.pdf` or `.docx`: the previous version stays active until the new one is
   ready; re-uploading the same file is a no-op; an older ready version can be re-activated.
3. **Chat.** Start a conversation for Bookshop and paste a customer message, e.g. "My order was
   supposed to arrive last week and the tracking has not updated." The answer cites the
   _Shipping Issues_ section; the "why this answer" panel shows the retrieved sections with
   scores, the model and prompt / completion / thinking / total tokens. Send an instruction
   ("make it shorter") to revise it. An out-of-scope message is answered `not_covered` with an
   escalation.
4. **Feedback.** Rate an answer down with a corrected answer: a later, similar question in any
   conversation of that company receives the correction as a few-shot example (and the sections
   its original question retrieved). Corrections are deactivated when the guidelines are replaced
   and can be toggled in the corrections list.
5. **History.** Conversations are private per agent, filterable by company and coverage, paged
   with cursors; long threads load page by page and older turns are folded into a rolling summary.

## Repository layout

```
api/
  app/
    main.py            create_app(deps) + production_app(); server.py is the uvicorn entry
    config.py          environment (same variable names as the TypeScript api)
    schemas.py         Pydantic models = the API contract (names match the reference document)
    errors.py          modelled errors; x-amzn-errortype + JSON envelope
    request_id.py      X-Request-Id middleware; auth/middleware.py answers 401 before routing
    routers/           one router per resource (health, auth, companies, guidelines, conversations, feedback)
    auth/ companies/ guidelines/ conversations/ feedback/   services
    rag/               embeddings, llm, prompt, templates, guidance gate, retrieval
    ingestion/         parsers, chunker, resumable ingestion job
    jobs/queue.py      JobQueue: Procrastinate (production) and in-memory (tests)
    observability/     Tracer: noop, recording (tests), Langfuse
    db/                SQLAlchemy models, session, migrate, seed, reembed
    worker.py          python -m app.worker
    openapi_export.py  writes packages/openapi/openapi.json
  alembic/             migration replaying the original SQL (alembic/sql/) verbatim
  prompts/             prompt templates ({{placeholders}}); seed/ sample guidelines; eval/ harnesses
  tests/               pytest (pgvector testcontainer, fakes for Gemini, in-memory queue)
web/                   React app, unchanged from the original
packages/openapi/      openapi.json (exported) and reference-smithy.json (frozen contract)
nginx/                 reverse proxy templates (prod, dev, tls)
```

## Development

```sh
cd api && uv sync                 # Python 3.12 managed by uv
uv run pytest                     # needs Docker (pgvector testcontainer); TEST_DATABASE_URL=... to reuse a server
uv run ruff check . && uv run ruff format . && uv run mypy
pnpm install && pnpm --filter web test && pnpm --filter web typecheck
pnpm dev                          # hot reload: docker compose with docker-compose.dev.yml
```

### Changing the API

The Pydantic models in `api/app/schemas.py` and the routers are the contract.

```sh
pnpm codegen      # = uv run python -m app.openapi_export && pnpm --filter web api:types
```

`tests/test_openapi.py` fails when the committed `packages/openapi/openapi.json` is stale, and
checks the document stays compatible with `reference-smithy.json` (paths, methods, parameters,
status codes, request and response properties, schema names and enums). The web client types in
`web/src/api/schema.d.ts` are generated from the exported document.

### Database

Migrations run at api start-up; `uv run python -m app.db.migrate` runs them by hand. After
changing `GEMINI_EMBEDDING_MODEL`, re-embed stored vectors with
`uv run python -m app.db.reembed`; changing `GEMINI_EMBEDDING_DIMENSIONS` needs a migration and
a re-ingest, and the api and worker refuse to start on a mismatch.

## Configuration

Every variable is listed in `.env.example` with its default: Gemini models and thinking level,
retrieval top-k and thresholds, history window and prompt token budget, upload limit, token
TTLs, seed users and Langfuse keys. Values are validated at start-up with a readable list of
problems.

## Evaluation

`api/eval/` holds the retrieval harness (top-1, top-4 recall, margins, thresholds, keyword
rescue, hybrid BM25 fusion) and the corrections harness (baseline vs with-correction answers
judged 1–5). They need a Gemini key:

```sh
cd api && uv run python -m eval.retrieval_eval
cd api && uv run python -m eval.corrections_eval
```

Results and the decisions they drove are in `docs/evaluation-report.md` of the original
repository; `docs/evals/` here holds the runs made with this port.

## Testing

`uv run pytest` runs 100+ tests against a real pgvector Postgres (one container per session, a
fresh database per test app): authentication, companies, guideline ingestion with supersede and
retry, chat with retrieval and the coverage gate, failed-turn persistence and retry, rolling
summaries, message paging, feedback and corrections, keyword rescue SQL, re-embedding, the
Procrastinate queue, the OpenAPI snapshot and the contract compatibility check. Gemini is
replaced by a deterministic fake embedder (hashed bag of words) and a fake chat model.

## Prompt-injection defences

Customer text is wrapped in `<customer_message>` tags with spoofed tags stripped and declared
untrusted in the system prompt; the server-side gate forces `not_covered` when nothing was
retrieved, restricts citations to sections that were actually provided and downgrades any reply
that contains source code.

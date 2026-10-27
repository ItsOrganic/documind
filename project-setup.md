# DocuMind — Project Setup

This file records how the DocuMind FastAPI project was set up. The layout follows the
"Suggested Repository Layout" section of `project1_rag_python.pdf`.

## 1. Starting point

The repo was created with `uv init` and FastAPI was added:

```bash
uv init documind
uv add "fastapi[standard]"
uv add --dev pytest ruff mypy
```

That produced `pyproject.toml`, `uv.lock`, `.python-version` (3.14), `.gitignore`, `README.md` and `main.py`.

## 2. Folder structure

The app code lives in a single `documind/` package, not in top-level folders. The spec runs
the eval CLI as `python -m documind.evals ...`, so `documind` has to be an importable package.
The empty top-level folders `api/`, `db/`, `evals/`, `ingestion/`, `llm/`, `observability/` and
`retrieval/` were moved into `documind/`.

```
documind/                     # repo root
├── main.py                   # entry point; re-exports documind.api.main:app
├── pyproject.toml / uv.lock
├── .env.example              # every config value comes from env (requirement 7)
├── docker-compose.yml        # api, worker, postgres+pgvector, redis, prometheus, grafana (M11)
├── docker/
│   ├── api.Dockerfile
│   └── worker.Dockerfile
├── http/documind.http        # request file covering every endpoint (submission guideline)
├── configs/                  # eval run configs
│   ├── baseline.yaml
│   ├── hybrid.yaml
│   └── hybrid_rerank.yaml
├── storage/uploads/          # local file storage for uploads (M2); gitignored
├── tests/
│   ├── conftest.py           # fake LLM / fake embedder fixtures go here
│   ├── unit/                 # chunking, RRF, citation validation, metrics
│   └── integration/          # ingestion flow, /ask with fake LLM, re-upload idempotency
└── documind/                 # the Python package
    ├── config.py             # pydantic-settings Settings (LLM_BASE_URL, DB, Redis, thresholds…)
    ├── api/                  # FastAPI app, routers, schemas
    │   ├── main.py           # creates the FastAPI app and includes routers
    │   ├── deps.py           # dependencies (DB session, settings, LLM client)
    │   ├── schemas.py        # Pydantic models: Citation, Answer, request/response bodies
    │   └── routers/
    │       ├── health.py     # GET /healthz (implemented), /metrics
    │       ├── chat.py       # POST /chat, /chat/stream (M1)
    │       ├── collections.py# POST /collections
    │       ├── documents.py  # POST /collections/{id}/documents, GET/DELETE /documents/{id}
    │       ├── search.py     # POST /search
    │       ├── ask.py        # POST /ask, /ask/stream (SSE)
    │       └── evals.py      # GET /evals/runs, /evals/runs/{a}/compare/{b}
    ├── ingestion/            # ingestion service (Redis Streams worker)
    │   ├── worker.py         # consumer group, XACK, XAUTOCLAIM, DLQ after 3 failures
    │   ├── events.py         # document.uploaded / indexed / failed payloads + stream names
    │   ├── cleaner.py        # header/footer removal, whitespace, hyphenation fixes
    │   ├── embedder.py       # batched embeddings with retry + exponential backoff
    │   ├── extractors/       # one per file type: pdf, markdown, html, text
    │   └── chunkers/         # fixed.py (token window + overlap), structure.py (heading-aware)
    ├── retrieval/            # retrieval service (importable and testable on its own)
    │   ├── vector.py         # pgvector cosine search (HNSW)
    │   ├── keyword.py        # tsvector + websearch_to_tsquery + ts_rank_cd
    │   ├── rrf.py            # Reciprocal Rank Fusion, k = 60
    │   ├── reranker.py       # cross-encoder re-ranker
    │   └── service.py        # combines the modes, filters, top_k
    ├── llm/
    │   ├── client.py         # OpenAI-compatible client (base_url from env)
    │   ├── prompts/          # versioned prompt templates
    │   ├── structured.py     # structured output + retry when validation fails
    │   └── citations.py      # citation validation against the retrieved set
    ├── evals/
    │   ├── __main__.py       # lets `python -m documind.evals` work
    │   ├── cli.py            # `run --config ...` and `compare <a> <b>`
    │   ├── metrics.py        # Recall@k, MRR, hit rate
    │   ├── judge.py          # LLM-as-judge: faithfulness, relevance, citation precision
    │   └── dataset/          # golden dataset (50+ items)
    ├── observability/
    │   ├── metrics.py        # Prometheus histograms and counters
    │   └── tracing.py        # OpenTelemetry spans for each stage
    ├── db/
    │   ├── models.py         # collections, documents, chunks, query_logs, eval_runs, eval_results
    │   ├── session.py        # async SQLAlchemy engine/session
    │   └── migrations/       # Alembic (versions/)
    └── ui/                   # Streamlit or HTMX UI (M11)
```

Every Python file except `health.py`, `api/main.py` and root `main.py` is an empty
placeholder, to be filled in milestone by milestone.

## 3. Code written so far

- **`documind/api/routers/health.py`**: `GET /healthz` returns `{"status": "ok"}`.
- **`documind/api/main.py`**: creates `FastAPI(title="DocuMind")` and includes the health router.
  Add each new router here as its milestone is built.
- **`main.py`** (root): before, it imported `api.routers.ingest/query`, which did not exist, so
  it crashed on import. It now just re-exports `app` from `documind.api.main`.
- **`.env.example`**: placeholders for `DATABASE_URL`, `REDIS_URL`, `LLM_BASE_URL`, `LLM_API_KEY`,
  `LLM_MODEL`, `EMBEDDING_MODEL`, `UPLOAD_DIR`. Copy it to `.env` and fill in the values.
- **`.gitignore`**: now ignores `.env` and uploaded files (`storage/uploads/*`).

## 4. Check that it works

```bash
uv run fastapi dev main.py          # http://127.0.0.1:8000/healthz, docs at /docs
```

This was checked with FastAPI's `TestClient`: `GET /healthz` returns `{"status": "ok"}`.

## 5. Next steps (Milestone 1)

Add the dependencies when each milestone needs them, not all at once:

```bash
uv add openai tiktoken pydantic-settings          # M1
uv add pypdf markdown-it-py beautifulsoup4        # M2
uv add "sqlalchemy[asyncio]" asyncpg alembic pgvector   # M3
uv add "redis>=5"                                 # M9
uv add prometheus-client opentelemetry-sdk        # M10
uv add sentence-transformers                      # M8 (bonus)
```

Then build `config.py` (Settings) and `routers/chat.py` (`POST /chat` + `/chat/stream` with SSE)
for M1.

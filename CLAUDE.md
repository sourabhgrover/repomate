# CLAUDE.md — RepoMate-Lite

## What this project is
A RAG-based system that answers natural-language questions about a GitHub
repository. Single-pass retrieval-and-generation with hybrid search and
syntax-aware chunking — NOT an autonomous multi-tool agent. This scope
decision is deliberate (team is new to agentic AI); do not introduce
LangGraph, ReAct loops, or multi-step tool-calling agents without an
explicit decision to change scope.

## Tech stack (all open source / free-tier — zero budget project)
- RAG framework: LangChain (EnsembleRetriever + ConversationalRetrievalChain)
- Chunking: tree-sitter (AST-aware, Python only for MVP)
- Embeddings: sentence-transformers, `BAAI/bge-small-en-v1.5`, self-hosted
  (no paid embedding APIs)
- Keyword search: Atlas Search (Lucene-based, built into MongoDB Atlas)
- Vector + document store: MongoDB Atlas (free M0 cluster, 512MB cap)
- LLM: open-weight model (Llama 3.3 or Mistral) via a free-tier inference
  provider — do not introduce paid LLM APIs
- Backend: FastAPI
- Frontend: React + Vite (minimal — chat + citations only, no streaming
  inspector or Mermaid viewer in MVP scope)
- Deploy: Docker → free-tier cloud host (Render/Fly)

## Key architecture decisions (do not silently change these)
- **MongoDB Atlas, not Postgres/pgvector or Chroma** — chosen for native
  hybrid search (Vector Search + Atlas Search in one cluster) and to avoid
  vector-store data loss on redeploy with ephemeral disks.
- **No SSE streaming in MVP** — plain synchronous `/chat` endpoint. Adding
  streaming is a stretch goal only after core scope is stable.
- **Demo repo size cap: ~100-150 files.** Ingestion runs on the hosted
  backend as an async job (`POST /index` → `job_id`, poll `GET /status`);
  larger repos are out of scope, documented as a known limitation, not a bug.
- **Secret/binary sanitization is mandatory before chunking** — strip
  `.git/`, `node_modules/`, lockfiles, binaries; redact API keys and `.env`
  contents. This runs BEFORE any embedding step, never after.
- **Chunking must never split mid-function or mid-class.** Use tree-sitter
  boundaries; a chunk should always be a complete syntactic unit.
- **Any accuracy/latency/cost number in the README must come from an
  actual run of the eval suite** — never estimate or assume a metric.

## Coding conventions
- Python 3.11+, type hints on all function signatures
- Config via `.env` / environment variables — never hardcode API keys or
  connection strings, even in examples or tests
- Chunk schema fields: `repo_id`, `file_path`, `language`, `chunk_type`,
  `symbols`, `content_hash`, `line_start`, `line_end`
- Format with `black`; this should run automatically via a PostToolUse hook

## Team roles & workflow
- `main` is protected — no direct pushes, feature branches only
  (`feat/short-description`)
- PRs require the automated review bot to run first; address its comments
  before requesting human review
- Lead owns: architecture, retrieval chain/prompt design, final review and
  merge, eval design, deployment
- Ingestion & Storage role owns: GitHub ingestion, sanitization, AST
  chunking, embedding pipeline, MongoDB schema
- Retrieval & API role owns: hybrid retriever, conversational chain,
  FastAPI routes, frontend integration

## Evaluation
- Question set: 10-15 questions covering architecture, API usage, and
  debugging-style queries against 1-2 known public repos
- Must include at least one "insufficient context, correctly refuses"
  test case
- Re-run after any retrieval or prompt change before claiming improvement

## When in doubt
Ask before assuming. If a ticket's acceptance criteria don't cover a case
you've hit, flag it rather than guessing — this project prioritizes
defensible, well-understood code over broad but shaky feature coverage.
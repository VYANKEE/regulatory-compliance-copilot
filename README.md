# Regulatory Compliance Copilot

A multi-agent system that reads new RBI circulars, diffs them against prior circulars and internal policy, and produces a citation-backed compliance impact memo for human review.

Status: Phases 0-9 done (document pipeline, hybrid RAG + eval, 6-agent LangGraph pipeline, MCP server, guardrails, threat model, HITL approval). Phase 10 (backend API) done. Phase 11 (Postgres-backed checkpointing, background job queue) done. Phase 13 (frontend) scaffolded. See `docs/adr/` for architecture decisions.

## Running locally

**Infra (Postgres + Redis):**
```
docker compose up -d postgres redis
```

**Backend API:**
```
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

**Background worker** (a separate terminal — analysis runs happen here, not inside the API process):
```
cd backend
python -m app.jobs.worker
```

Required in `.env` (see `.env.example`): `GOOGLE_API_KEY`, `NVIDIA_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `FIREBASE_CREDENTIALS_PATH`.

**Frontend:**
```
cd frontend
npm install
npm run dev
```
Runs at http://localhost:5173, proxies `/api/*` to the backend. Required in `frontend/.env` (see `frontend/.env.example`): Firebase web-app config.

## Why a background worker

`POST /analysis/start` used to run the full 6-topic multi-agent pipeline (many LLM calls, 30-90+ seconds) directly inside the HTTP request. That doesn't hold up in production — client timeouts, one request pinning a whole API worker, no retry if it crashes mid-run. It now just enqueues the job (Redis + RQ) and returns immediately with `status: "pending"`; the actual work happens in `python -m app.jobs.worker`, and the frontend polls `GET /analysis/{id}` until the status flips to `awaiting_approval`. Run more worker processes to increase throughput — that's the horizontal-scaling lever here.

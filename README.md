# NIRIKSH

**AI-powered regulatory compliance copilot for NBFCs.** A multi-agent LangGraph system that reads new RBI circulars, diffs them against prior circulars and an uploaded internal policy, and produces a citation-backed compliance impact memo — with guardrails, an evaluation suite, and a mandatory human approval gate before anything is finalized.

## What it does

An NBFC's compliance team gets a new RBI circular every few weeks and has to manually work out: *what changed from the last one, does our policy already cover it, and if not, what exactly needs to be updated.* NIRIKSH automates the first pass of that work — grounded in the actual regulatory text, not a model's memory of it — and hands a human the final call.

1. Upload your NBFC's policy document (a sample is provided to try the flow).
2. The agent pipeline retrieves the relevant RBI circular clauses, diffs the new circular against the prior one, assesses impact against your policy, and drafts findings — each one tagged `Met` / `Not Met` / `Partial` with a citation.
3. A dedicated **Verifier Agent** independently re-checks every claim against the source text before the report is compiled.
4. The report goes through **guardrails** (grounding, PII, sanity checks) and stops at a **human approval gate** — nothing ships without an explicit approve/reject decision.
5. Once approved, you can keep asking follow-up questions in the same thread, grounded in the same retrieved clauses.

## Agent pipeline

```
Supervisor → Retrieval → Diff → Impact → Verifier → Report → [Human approval]
```

| Agent | Role |
|---|---|
| Supervisor | Orchestrates the run, routes between agents |
| Retrieval | Pulls the relevant clauses from the RBI corpus (hybrid-tested; baseline retriever ships to prod — see Evaluation) |
| Diff | Identifies what changed vs. the prior circular |
| Impact | Assesses each change against the uploaded policy, drafts findings |
| Verifier | Independently re-checks every finding's citation against the source text, separate from Impact's context |
| Report | Templates the final memo — deliberately not an LLM call, so it can't introduce new hallucinations at the last step |

Built on LangGraph with Postgres-backed checkpointing, so a run survives a process restart mid-analysis.

## Guardrails & AI safety

Regulatory compliance output has to be more careful than most, not less. NIRIKSH runs defense-in-depth checks that are deliberately independent of each other:

- **Input guardrails** — query length limits and prompt-injection pattern checks, run before any LLM call.
- **Output guardrails** — `check_citations_grounded` re-verifies every citation against an independently-loaded corpus map (separate from the Verifier Agent's own check), `check_no_pii_leak` scans for PAN/Aadhaar-shaped patterns, plus a minimum-length sanity check. Any failure blocks delivery.
- **Human-in-the-loop, mandatory** — the graph pauses at a real `interrupt()`; no memo reaches anyone without an explicit human approve/reject decision, and rejection feedback is recorded in the audit log.

These are plain rule-based checks, not model opinions — a missing citation or a PII-shaped pattern blocks delivery regardless of how confident the model sounds.

## Evaluation

A 30-question golden set (20 grounded, 2 change-detection, 8 deliberately unanswerable) is scored against real retrieval and generation output — no metric here is asserted, all are computed from `evals/results_*.jsonl`:

| Metric | Result |
|---|---|
| Retrieval hit-rate (grounded + diff questions, 22 total) | **82%** (18/22) |
| Correct abstention on unanswerable questions | **100%** (8/8) |
| Hybrid retriever (BM25 + dense + reranker) — tested, not shipped | 77% (17/22) |

The hybrid retriever was built and evaluated as a genuine attempt to improve retrieval; it scored *lower* than the simpler baseline, so the baseline is what runs in production. Kept as a measured, honest result rather than hidden — see `backend/app/evaluation/`.

## Tech stack

- **Agents / RAG**: LangGraph, LangChain, ChromaDB, Gemini (`langchain-google-genai`), NVIDIA embeddings, BM25 + reranking (evaluated, see above)
- **Backend**: FastAPI, PostgreSQL (SQLAlchemy + Alembic), Redis + RQ (background job queue), Firebase Auth
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Framer Motion
- **Observability**: OpenTelemetry, Prometheus, structured JSON logging
- **Interop**: MCP servers for retrieval/policy/circular access
- **CI**: GitHub Actions — frontend lint + build, backend syntax check + tests, on every push

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

**Background worker** (separate terminal — analysis runs happen here, not inside the API process):
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

`POST /analysis/start` used to run the full multi-agent pipeline (many LLM calls, 30-90+ seconds) directly inside the HTTP request. That doesn't hold up in production — client timeouts, one request pinning a whole API worker, no retry if it crashes mid-run. It now just enqueues the job (Redis + RQ) and returns immediately with `status: "pending"`; the actual work happens in `python -m app.jobs.worker`, and the frontend polls `GET /analysis/{id}` until the status flips to `awaiting_approval`. Run more worker processes to increase throughput — that's the horizontal-scaling lever here.

## Project structure

```
backend/app/
  agents/        # the 6-agent LangGraph pipeline
  guardrails/    # input + output guardrail checks
  evaluation/    # golden-set eval runner and scoring
  api/           # FastAPI routes
  jobs/          # background worker + queue
  retrieval/     # retriever(s), incl. the evaluated hybrid variant
frontend/src/    # React app (marketing site + product)
evals/           # golden set + eval run results
mcp_servers/     # MCP servers for retrieval/policy/circular access
docs/            # architecture decisions, threat model
```

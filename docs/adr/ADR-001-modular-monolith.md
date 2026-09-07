# ADR-001: Modular Monolith over Microservices

## Status
Accepted

## Context
The system needs several logical components: auth, document ingestion, retrieval,
a multi-agent analysis pipeline, evaluation, and background jobs. With one developer
building this end-to-end for a portfolio project, the question is whether these should
be separate deployable services (microservices) or modules within one application.

## Options considered
1. **Microservices** — each concern (auth, retrieval, agents, jobs) as an independently
   deployed service communicating over the network.
2. **Modular monolith** — one FastAPI application with strict internal module boundaries
   (auth / documents / retrieval / agents / evaluation / jobs), each module exposing a
   clean interface and not reaching into another module's internals.
3. **Fully flat monolith** — one application, no enforced boundaries at all.

## Decision
Modular monolith (option 2). Two things still run as separate processes because they
have a concrete reason to:
- **MCP servers** (circular-server, policy-server) — credential isolation and a sandbox
  boundary; they should not share the main app's process/credentials.
- **Worker / job runner** — long-running analysis (30-60s) needs to scale independently
  from the request-serving API.

Vector DB: switched from Qdrant to **ChromaDB running embedded** (in-process,
persisted to `data/chroma_db/`) — at our scale (tens to low hundreds of
documents) an extra standalone vector DB service buys nothing. Extraction
trigger: move to a standalone vector DB (Qdrant/Milvus) if the corpus grows
into the tens of thousands of chunks or needs to be queried by more than one
service.

## Why not microservices
- One developer, one codebase — the distributed-systems tax (service discovery,
  network failures, distributed transactions) buys nothing at this scale.
- Debugging a distributed system is meaningfully harder than debugging one process.
- Deployment cost and operational complexity go up with no corresponding benefit here.

## Trade-offs accepted
- All modules currently scale together (can't scale `retrieval` independently of `auth`).
- A bug in one module can, in principle, affect the whole process (mitigated by clean
  interfaces and tests).

## Extraction triggers
Re-evaluate turning a module into its own service when:
- A specific module's load pattern diverges sharply from the rest (e.g. `retrieval`
  needs 10x the compute of everything else).
- A module needs an independent deployment cadence or independent scaling in production.
- Team size grows past what one codebase's ownership boundaries can cleanly support.

Until then: extraction is a known, planned path — not a default.

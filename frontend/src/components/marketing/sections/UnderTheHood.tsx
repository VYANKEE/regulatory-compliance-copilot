import { Reveal, RevealGroup, RevealItem } from '../Reveal'

const STACK = [
  { layer: 'Frontend', detail: 'React 19 · TypeScript · Vite' },
  { layer: 'API layer', detail: 'FastAPI · rate limiting · structured JSON errors' },
  { layer: 'Agentic orchestrator', detail: 'LangGraph StateGraph (agentic AI) · Postgres-backed checkpointing' },
  { layer: 'Specialized agents', detail: 'Retrieval · Diff · Impact · Verifier · Report' },
  { layer: 'Retrieval (RAG)', detail: 'NVIDIA NIM + Gemini · similarity search over embedded circular clauses' },
  { layer: 'MCP tool server', detail: 'Standalone server exposes retrieval as MCP tools (search_circulars, diff_topic) for other AI clients' },
  { layer: 'Validation', detail: 'Independent grounding check + output guardrails' },
  { layer: 'Human-in-the-loop', detail: 'LangGraph interrupt() · approve / reject' },
  { layer: 'Output', detail: 'Persisted memo · Postgres · audit log' },
]

export function UnderTheHood() {
  return (
    <section id="under-the-hood" className="mx-auto max-w-6xl px-6 py-32">
      <Reveal>
        <span className="label-tag">Under the hood</span>
        <h2 className="font-display mt-4 max-w-2xl text-4xl font-medium leading-tight sm:text-5xl">
          What actually happens behind the interface.
        </h2>
        <p className="mt-4 max-w-2xl leading-relaxed text-[var(--ink-soft)]">
          Three architectural bets this system is built on: agentic AI orchestration (LangGraph, not a
          single prompt), RAG for every factual claim (retrieval before generation, never memory alone),
          and an MCP tool server so the same retrieval can be called by other AI clients, not just this
          app.
        </p>
      </Reveal>

      <RevealGroup className="glass-card mt-16 divide-y divide-[var(--border)] overflow-hidden" stagger={0.05}>
        {STACK.map((s, i) => (
          <RevealItem key={s.layer}>
            <div className="flex items-center gap-6 px-6 py-5">
              <span className="font-mono-ui w-8 shrink-0 text-xs text-[var(--ink-faint)]">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="w-48 shrink-0 text-sm font-medium">{s.layer}</span>
              <span className="font-mono-ui flex-1 text-xs text-[var(--ink-soft)] sm:text-sm">{s.detail}</span>
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--signal)]" />
            </div>
          </RevealItem>
        ))}
      </RevealGroup>
    </section>
  )
}

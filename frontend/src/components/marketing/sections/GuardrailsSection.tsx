/** Shows the real guardrail/eval layer -- what actually checks each analysis, and the measured numbers behind it. */
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Reveal } from '../Reveal'

type CheckState = 'pending' | 'active' | 'done'

const CHECKS = [
  {
    label: 'Input validation',
    detail: 'Length + prompt-injection pattern check, before any LLM call runs.',
  },
  {
    label: 'Grounded retrieval',
    detail: 'Every clause comes from the real RBI corpus, never from the model’s memory.',
  },
  {
    label: 'Independent verification',
    detail: 'A separate LLM call re-checks each claim against its cited source text.',
  },
  {
    label: 'Citation grounding',
    detail: 'Every citation is re-confirmed against the corpus, independently of the Verifier.',
  },
  {
    label: 'PII scan',
    detail: 'The report is scanned for PAN/Aadhaar-shaped patterns before it can ship.',
  },
  {
    label: 'Human approval',
    detail: 'Nothing is finalized until a person explicitly approves or rejects it.',
  },
]

const CYCLE_MS = 1300

function CheckPipeline() {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setActive((i) => (i + 1) % (CHECKS.length + 1)), CYCLE_MS)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {CHECKS.map((c, i) => {
        const state: CheckState = i < active ? 'done' : i === active ? 'active' : 'pending'
        const color = state === 'pending' ? 'var(--ink-faint)' : state === 'active' ? 'var(--cyan)' : 'var(--signal)'
        return (
          <div
            key={c.label}
            className="rounded-xl border p-4 transition-colors duration-300"
            style={{
              borderColor: state === 'active' ? 'var(--border-signal)' : 'var(--border)',
              background: state === 'active' ? 'rgba(82,199,232,0.06)' : 'var(--surface)',
            }}
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="relative flex h-4 w-4 shrink-0 items-center justify-center">
                <AnimatePresence mode="wait">
                  {state === 'done' ? (
                    <motion.svg
                      key="check"
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      viewBox="0 0 16 16"
                      className="h-4 w-4"
                    >
                      <path d="M3 8.5l3 3 7-7" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </motion.svg>
                  ) : (
                    <motion.span
                      key="dot"
                      initial={{ scale: 0.6, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.6, opacity: 0 }}
                      className={`h-2 w-2 rounded-full ${state === 'active' ? 'animate-pulse' : ''}`}
                      style={{ background: color }}
                    />
                  )}
                </AnimatePresence>
              </span>
              <span className="label-tag" style={{ color: state === 'pending' ? 'var(--ink-faint)' : 'var(--ink)' }}>
                {c.label}
              </span>
            </div>
            <p className="text-sm leading-relaxed text-[var(--ink-soft)]">{c.detail}</p>
          </div>
        )
      })}
    </div>
  )
}

const SAFETY_MEASURES = [
  {
    title: 'Defense-in-depth, not one layer',
    detail:
      'The Verifier Agent (at generation time) and the output guardrails (right before delivery) are deliberately independent -- a bug in one doesn’t take the other down with it.',
  },
  {
    title: 'Injection-resistant input layer',
    detail:
      'Input checks are plain length + regex rules that run before any model call, so they can’t be talked around by clever prompt wording the way an "LLM judges itself" guardrail could be.',
  },
  {
    title: 'Nothing ships on trust alone',
    detail:
      'A missing/invalid citation, a PII-shaped pattern, or a suspiciously short report all block delivery -- these are plain checks, not model opinions.',
  },
  {
    title: 'Human-in-the-loop is mandatory',
    detail:
      'The pipeline pauses at a real approval gate (LangGraph’s interrupt()); no memo reaches anyone without an explicit human decision.',
  },
]

export function GuardrailsSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-32">
      <Reveal>
        <span className="label-tag">Guardrails & evals</span>
        <h2 className="font-display mt-4 max-w-2xl text-4xl font-medium leading-tight sm:text-5xl">
          Every claim is checked before it reaches a person.
        </h2>
        <p className="mt-4 max-w-2xl leading-relaxed text-[var(--ink-soft)]">
          An AI system that assesses regulatory compliance has to be more careful than most, not less.
          Here is what actually runs on every analysis, and the real numbers behind it -- not a marketing
          claim.
        </p>
      </Reveal>

      <Reveal delay={0.1} className="glass-card mt-12 p-6 sm:p-8">
        <p className="label-tag mb-5 text-[var(--ink-faint)]">What runs on every analysis</p>
        <CheckPipeline />
      </Reveal>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <Reveal delay={0.15} className="glass-card p-7">
          <p className="label-tag mb-4 text-[var(--ink-faint)]">Evaluation, measured</p>
          <div className="mb-5 grid grid-cols-2 gap-4">
            <div>
              <p className="font-display text-3xl font-medium">30</p>
              <p className="text-xs text-[var(--ink-soft)]">golden-set questions (20 grounded, 2 change-detection, 8 deliberately unanswerable)</p>
            </div>
            <div>
              <p className="font-display text-3xl font-medium" style={{ color: 'var(--signal)' }}>
                82%
              </p>
              <p className="text-xs text-[var(--ink-soft)]">retrieval hit-rate across every question with a known source clause -- grounded + diff (18/22)</p>
            </div>
            <div>
              <p className="font-display text-3xl font-medium" style={{ color: 'var(--signal)' }}>
                100%
              </p>
              <p className="text-xs text-[var(--ink-soft)]">correct abstention -- never invents an answer when there isn't one (8/8)</p>
            </div>
            <div>
              <p className="font-display text-3xl font-medium text-[var(--ink-soft)]">77%</p>
              <p className="text-xs text-[var(--ink-soft)]">a hybrid search + reranker variant, measured and rejected -- see below</p>
            </div>
          </div>
          <p className="text-sm leading-relaxed text-[var(--ink-soft)]">
            A hybrid (BM25 + dense + reranker) retriever was built and run against the same 30 questions --
            it scored <em>lower</em> than the simpler retriever above, so the simpler one is what actually
            runs in production. Kept as a measured, honest result rather than hidden.
          </p>
        </Reveal>

        <Reveal delay={0.2} className="glass-card p-7">
          <p className="label-tag mb-4 text-[var(--ink-faint)]">AI security & safety, concretely</p>
          <div className="space-y-4">
            {SAFETY_MEASURES.map((m) => (
              <div key={m.title}>
                <p className="text-sm font-medium">{m.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--ink-soft)]">{m.detail}</p>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  )
}

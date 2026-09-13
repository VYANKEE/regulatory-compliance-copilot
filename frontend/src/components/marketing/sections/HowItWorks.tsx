import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Reveal } from '../Reveal'

const LAYERS = [
  {
    id: 'input',
    label: 'Input',
    title: 'Circular + policy',
    detail: 'A regulatory circular reference and your uploaded internal policy PDF.',
  },
  {
    id: 'pipeline',
    label: 'Agentic pipeline',
    title: 'Retrieval → Diff → Impact',
    detail:
      'Six regulatory topics are analyzed concurrently. Retrieval finds the relevant clauses; Diff and Impact run side by side per topic: Diff traces what changed, Impact checks your policy against it.',
  },
  {
    id: 'reasoning',
    label: 'Reasoning',
    title: 'LLM + retrieval + rules',
    detail: 'Every judgment is grounded in retrieved clause text, never the model reasoning from memory alone.',
  },
  {
    id: 'validation',
    label: 'Validation',
    title: 'Independent verification',
    detail:
      'The Verifier Agent re-checks each finding against raw corpus text on its own. A finding survives only if it is actually grounded, not because the model that produced it said so.',
  },
  {
    id: 'human',
    label: 'Human',
    title: 'Human-in-the-loop review',
    detail: 'The pipeline pauses. A person reads the compiled memo and approves or rejects it before anything is final.',
  },
  {
    id: 'output',
    label: 'Output',
    title: 'Compliance memo',
    detail: 'A structured memo: what changed, what your policy is missing, and the exact clause behind every line.',
  },
]

export function HowItWorks() {
  const [active, setActive] = useState(LAYERS[1].id)
  const activeLayer = LAYERS.find((l) => l.id === active)!

  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-32">
      <Reveal>
        <span className="label-tag">How Niriksh works</span>
        <h2 className="font-display mt-4 max-w-2xl text-4xl font-medium leading-tight sm:text-5xl">
          One pipeline, six checkpoints, a human at the end.
        </h2>
      </Reveal>

      <Reveal delay={0.1} className="mt-16">
        <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
          {LAYERS.map((l) => (
            <button
              key={l.id}
              onClick={() => setActive(l.id)}
              className="group relative flex-1 rounded-xl border px-4 py-4 text-left transition-colors"
              style={{
                borderColor: active === l.id ? 'var(--border-signal)' : 'var(--border)',
                background: active === l.id ? 'rgba(84,232,178,0.06)' : 'var(--surface)',
              }}
            >
              <span className="label-tag" style={{ color: active === l.id ? 'var(--signal)' : 'var(--ink-soft)' }}>
                {l.label}
              </span>
              <span className="mt-1 block text-sm font-medium">{l.title}</span>
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeLayer.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.35 }}
            className="glass-card mt-6 p-8"
          >
            <p className="font-display text-2xl font-medium">{activeLayer.title}</p>
            <p className="mt-3 max-w-2xl leading-relaxed text-[var(--ink-soft)]">{activeLayer.detail}</p>
          </motion.div>
        </AnimatePresence>
      </Reveal>
    </section>
  )
}

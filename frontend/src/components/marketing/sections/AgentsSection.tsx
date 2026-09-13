import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { AGENTS, HUMAN_REVIEW } from '../../../lib/agents'
import { Reveal, RevealGroup, RevealItem } from '../Reveal'

export function AgentsSection() {
  const [open, setOpen] = useState<string | null>(null)

  return (
    <section id="agents" className="mx-auto max-w-6xl px-6 py-32">
      <Reveal>
        <span className="label-tag">The agents behind the decision</span>
        <h2 className="font-display mt-4 max-w-2xl text-4xl font-medium leading-tight sm:text-5xl">
          Six specialized agents. One shared corpus. Zero unverified claims.
        </h2>
      </Reveal>

      <RevealGroup className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" stagger={0.06}>
        {AGENTS.map((agent) => {
          const isOpen = open === agent.id
          return (
            <RevealItem key={agent.id}>
              <motion.button
                layout
                onClick={() => setOpen(isOpen ? null : agent.id)}
                className="glass-card glass-card-hover w-full p-6 text-left"
              >
                <div className="flex items-center justify-between">
                  <span className="label-tag text-[var(--signal)]">Agent</span>
                  <span className="h-2 w-2 rounded-full bg-[var(--signal)]" />
                </div>
                <h3 className="font-display mt-3 text-xl font-medium">{agent.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">{agent.role}</p>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-5 space-y-3 border-t border-[var(--border)] pt-5 text-sm">
                        <Field label="Receives" value={agent.receives} />
                        <Field label="Analyzes" value={agent.analyzes} />
                        <Field label="Tools" value={agent.tools} />
                        <Field label="Produces" value={agent.produces} />
                        <Field label="Communicates with" value={agent.talksTo} />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <span className="label-tag mt-4 inline-block text-[var(--ink-faint)]">
                  {isOpen ? 'Collapse ↑' : 'Details ↓'}
                </span>
              </motion.button>
            </RevealItem>
          )
        })}

        <RevealItem>
          <div className="glass-card flex h-full flex-col justify-center border-dashed border-[var(--border-strong)] p-6">
            <span className="label-tag text-[var(--amber)]">Not an agent: the checkpoint</span>
            <h3 className="font-display mt-3 text-xl font-medium">{HUMAN_REVIEW.name}</h3>
            <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">{HUMAN_REVIEW.role}</p>
          </div>
        </RevealItem>
      </RevealGroup>
    </section>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="label-tag block text-[var(--ink-faint)]">{label}</span>
      <p className="mt-1 leading-relaxed text-[var(--ink-soft)]">{value}</p>
    </div>
  )
}
